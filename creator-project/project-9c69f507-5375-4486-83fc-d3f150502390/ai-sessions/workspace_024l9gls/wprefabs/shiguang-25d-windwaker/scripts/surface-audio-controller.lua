---@id e904d07d-889a-4289-a345-99a7b9242925
---@referenceName surface-audio-controller.lua
---@displayName 地表脚步与海岸水声控制
---@start
---@var GrassSound:UnityEngine.AudioClip=nil
---@name 草地脚步音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var GrassSoundVolume:number=0.65
---@name 草地脚步音量
---@desc 0–1，0 表示静音
---@var GrassSoundMaxDistance:number=20
---@name 草地脚步最大作用范围
---@desc 距声源的可听半径，单位米；小于等于 0 时不播放
---@var SandSound:UnityEngine.AudioClip=nil
---@name 沙地脚步音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var SandSoundVolume:number=0.68
---@name 沙地脚步音量
---@desc 0–1，0 表示静音
---@var SandSoundMaxDistance:number=20
---@name 沙地脚步最大作用范围
---@desc 距声源的可听半径，单位米；小于等于 0 时不播放
---@var WaterSound:UnityEngine.AudioClip=nil
---@name 水面踩水音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var WaterSoundVolume:number=0.78
---@name 水面踩水音量
---@desc 0–1，0 表示静音
---@var WaterSoundMaxDistance:number=22
---@name 水面踩水最大作用范围
---@desc 距声源的可听半径，单位米；小于等于 0 时不播放
---@var WaveSound:UnityEngine.AudioClip=nil
---@name 海湾轻浪音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var WaveSoundVolume:number=0.32
---@name 海湾轻浪音量
---@desc 0–1，0 表示静音
---@var WaveSoundMaxDistance:number=42
---@name 海湾轻浪最大作用范围
---@desc 距声源的可听半径，单位米；小于等于 0 时不播放
---@var DistanceDrivenFootsteps:boolean=false
---@name 按移动距离模拟脚步
---@desc 默认关闭；动画落脚事件可调用 SHIGUANG_25D.NotifyFootstep
---@end

local UnityEngine = CS.UnityEngine
local GameObject = UnityEngine.GameObject
local Vector3 = UnityEngine.Vector3
local Time = UnityEngine.Time
local AudioSourceType = typeof(UnityEngine.AudioSource)
local AudioRolloffMode = UnityEngine.AudioRolloffMode
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("surface-audio")
local runtimeScope = RuntimeScope.from(self)

-- Priority when overlapping multiple material voxels at transitions
local MATERIAL_PRIORITY = {
  wood = 5,
  water = 4,
  road = 3,
  sand = 2,
  grass = 1,
}

-- Coarse shoreline anchor samples in local bay space (X, Z) for 3D wave attenuation
local SHORE_RING_POINTS = {
  { -66, -42 }, { -50, -44 }, { -36, -34 }, { -22, -28 }, { -6, -28 }, { 10, -28 },
  { 26, -28 }, { 41, -39 }, { 56, -42 }, { 67, -30 }, { 68, 0 }, { 68, 30 },
  { 56, 56 }, { 42, 67 }, { 0, 68 }, { -42, 67 }, { -57, 54 }, { -68, 28 },
  { -68, -4 }, { -68, -32 }, { -20, -37 }, { 0, -36 }, { 14, -39 }, { 28, -48 },
  { 8, -54 }, { -14, -54 }, { -34, -48 },
}

local footstepGo = nil
local footstepSource = nil
local waveGo = nil
local waveSource = nil
local currentWaveClip = nil

local activeVoxels = {} -- voxelKey -> materialId
local currentVoxelMaterial = nil
local lastPlayerPos = nil
local accumDist = 0.0
local stepCooldown = 0.0
local shoreUpdateTimer = 0.0
local totalSteps = 0
local stepCounts = { grass = 0, sand = 0, water = 0, road = 0, wood = 0 }
local voxelEnterCounts = { grass = 0, sand = 0, water = 0, road = 0, wood = 0 }

local function ensureSharedBus()
  if _G.SHIGUANG_25D == nil then
    _G.SHIGUANG_25D = {}
  end
  return _G.SHIGUANG_25D
end

local function createChildAudioSource(childName, loop)
  local go = GameObject(childName)
  go.transform:SetParent(self.transform, false)
  local src = go:AddComponent(AudioSourceType)
  src.playOnAwake = false
  src.loop = loop
  src.spatialBlend = 1.0
  src.rolloffMode = AudioRolloffMode.Linear
  return go, src
end

local function resolveActiveMaterial()
  local bestMat = nil
  local bestPrio = -1
  for _, mat in pairs(activeVoxels) do
    local p = MATERIAL_PRIORITY[mat] or 0
    if p > bestPrio then
      bestPrio = p
      bestMat = mat
    end
  end
  return bestMat
end

local function onVoxelChanged(voxelKey, matId, isInside)
  if voxelKey == nil then return end
  if isInside then
    if activeVoxels[voxelKey] == nil and stepCounts[matId] ~= nil then
      voxelEnterCounts[matId] = (voxelEnterCounts[matId] or 0) + 1
    end
    activeVoxels[voxelKey] = matId
  else
    activeVoxels[voxelKey] = nil
  end
  currentVoxelMaterial = resolveActiveMaterial()
end

local function getLocalPlayerPos()
  if PlayerService == nil then return nil end
  local ok, pos = pcall(function()
    local p = PlayerService.GetLocalPlayer()
    if p == nil then return nil end
    local actor = p:GetActor()
    if actor == nil then return nil end
    return actor.position
  end)
  if ok then return pos end
  return nil
end

local function inferFallbackMaterial(worldPos)
  if self == nil or self.transform == nil or self.transform.parent == nil then
    return "grass"
  end
  local lp = self.transform.parent:InverseTransformPoint(worldPos)
  if lp.y < 0.16 then
    return "water"
  elseif lp.y < 0.52 then
    return "sand"
  end
  return "grass"
end

local function configureSource(src, clip, vol, maxDist)
  if src == nil then return false end
  local v = math.max(0.0, math.min(1.0, tonumber(vol) or 0.0))
  local d = tonumber(maxDist) or 0.0
  if clip == nil or v <= 0.0 or d <= 0.0 then
    return false
  end
  src.volume = v
  src.minDistance = math.min(1.0, d * 0.1)
  src.maxDistance = d
  return true
end

local function playSurfaceStep(matId, playerPos)
  if footstepSource == nil or footstepGo == nil then return end
  footstepGo.transform.position = playerPos

  local clip = GrassSound
  local vol = GrassSoundVolume
  local dist = GrassSoundMaxDistance
  local pitchBase = 1.0

  if matId == "sand" then
    clip = SandSound
    vol = SandSoundVolume
    dist = SandSoundMaxDistance
  elseif matId == "water" then
    clip = WaterSound
    vol = WaterSoundVolume
    dist = WaterSoundMaxDistance
  elseif matId == "road" or matId == "wood" then
    clip = SandSound
    vol = (tonumber(SandSoundVolume) or 0.68) * 0.72
    dist = SandSoundMaxDistance
    pitchBase = (matId == "wood") and 1.12 or 1.22
  end

  if configureSource(footstepSource, clip, vol, dist) then
    footstepSource.pitch = pitchBase + (math.random() * 0.10 - 0.05)
    footstepSource:PlayOneShot(clip)
  end

  totalSteps = totalSteps + 1
  if stepCounts[matId] ~= nil then
    stepCounts[matId] = stepCounts[matId] + 1
  end

  if matId == "water" then
    local bus = _G.SHIGUANG_25D
    if bus ~= nil and bus.SpawnWaterStepRipple ~= nil then
      pcall(bus.SpawnWaterStepRipple, playerPos)
    end
  end
end

local function getFootstepMaterial()
  local pos = getLocalPlayerPos()
  return pos and (currentVoxelMaterial or inferFallbackMaterial(pos)) or nil
end

local function notifyFootstep()
  local pos = getLocalPlayerPos()
  if pos == nil or footstepSource == nil or not self.gameObject.activeInHierarchy then return false end
  playSurfaceStep(currentVoxelMaterial or inferFallbackMaterial(pos), pos)
  return true
end

local function updateShoreWaves(playerPos)
  if waveSource == nil or waveGo == nil then return end
  if currentWaveClip ~= WaveSound then
    waveSource:Stop()
    currentWaveClip = WaveSound
  end

  if not configureSource(waveSource, currentWaveClip, WaveSoundVolume, WaveSoundMaxDistance) then
    if waveSource.isPlaying then
      waveSource:Stop()
    end
    return
  end

  if playerPos ~= nil and self.transform.parent ~= nil then
    local lp = self.transform.parent:InverseTransformPoint(playerPos)
    local bestPt = SHORE_RING_POINTS[1]
    local bestD2 = 1e12
    for _, pt in ipairs(SHORE_RING_POINTS) do
      local dx = lp.x - pt[1]
      local dz = lp.z - pt[2]
      local d2 = dx * dx + dz * dz
      if d2 < bestD2 then
        bestD2 = d2
        bestPt = pt
      end
    end
    local worldShore = self.transform.parent:TransformPoint(Vector3(bestPt[1], 0.2, bestPt[2]))
    waveGo.transform.position = worldShore
  end

  if waveSource.clip ~= currentWaveClip then
    waveSource.clip = currentWaveClip
  end
  if not waveSource.isPlaying then
    waveSource:Play()
  end
end

function Start()
  footstepGo, footstepSource = createChildAudioSource("FootstepAudioSource", false)
  waveGo, waveSource = createChildAudioSource("ShoreWaveAudioSource", true)

  local bus = ensureSharedBus()
  bus.NotifyMaterialVoxel = onVoxelChanged
  bus.GetFootstepMaterial = getFootstepMaterial
  bus.NotifyFootstep = notifyFootstep
  bus.GetAudioDebugState = GetAudioDebugState

  logger:info("地表材质音效控制器就绪")
end

function Update()
  local dt = Time.deltaTime
  if stepCooldown > 0.0 then
    stepCooldown = stepCooldown - dt
  end

  local playerPos = getLocalPlayerPos()
  shoreUpdateTimer = shoreUpdateTimer + dt
  if shoreUpdateTimer >= 0.12 then
    shoreUpdateTimer = 0.0
    updateShoreWaves(playerPos)
  end

  if DistanceDrivenFootsteps ~= true or playerPos == nil then return end
  if lastPlayerPos == nil then
    lastPlayerPos = playerPos
    return
  end

  local dx = playerPos.x - lastPlayerPos.x
  local dz = playerPos.z - lastPlayerPos.z
  local moveStep = math.sqrt(dx * dx + dz * dz)
  lastPlayerPos = playerPos

  if moveStep > 3.5 then
    -- Ignore teleports
    accumDist = 0.0
    return
  end

  accumDist = accumDist + moveStep
  if accumDist >= 1.15 and stepCooldown <= 0.0 then
    accumDist = 0.0
    stepCooldown = 0.34
    local matId = currentVoxelMaterial or inferFallbackMaterial(playerPos)
    playSurfaceStep(matId, playerPos)
  end
end

function OnDisable()
  if footstepSource ~= nil then footstepSource:Stop() end
  if waveSource ~= nil then waveSource:Stop() end
end

function OnDestroy()
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.NotifyMaterialVoxel = nil
    _G.SHIGUANG_25D.GetFootstepMaterial = nil
    _G.SHIGUANG_25D.NotifyFootstep = nil
    _G.SHIGUANG_25D.GetAudioDebugState = nil
  end
  if footstepSource ~= nil then
    footstepSource:Stop()
    UnityEngine.Object.Destroy(footstepSource)
    footstepSource = nil
  end
  if waveSource ~= nil then
    waveSource:Stop()
    UnityEngine.Object.Destroy(waveSource)
    waveSource = nil
  end
  if footstepGo ~= nil then
    UnityEngine.Object.Destroy(footstepGo)
    footstepGo = nil
  end
  if waveGo ~= nil then
    UnityEngine.Object.Destroy(waveGo)
    waveGo = nil
  end
end

function GetAudioDebugState()
  return {
    currentMaterial = getFootstepMaterial(),
    voxelMaterial = currentVoxelMaterial,
    distanceDrivenFootsteps = DistanceDrivenFootsteps == true,
    totalSteps = totalSteps,
    stepCounts = {
      grass = stepCounts.grass,
      sand = stepCounts.sand,
      water = stepCounts.water,
      road = stepCounts.road,
      wood = stepCounts.wood,
    },
    voxelEnterCounts = {
      grass = voxelEnterCounts.grass,
      sand = voxelEnterCounts.sand,
      water = voxelEnterCounts.water,
      road = voxelEnterCounts.road,
      wood = voxelEnterCounts.wood,
    },
    clipsReady = {
      grass = GrassSound ~= nil,
      sand = SandSound ~= nil,
      water = WaterSound ~= nil,
      waves = WaveSound ~= nil,
    },
    waveIsPlaying = waveSource ~= nil and waveSource.isPlaying == true,
  }
end
