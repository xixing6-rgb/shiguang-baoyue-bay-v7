---@id 196f161a-57f0-46be-bdbd-b4075e26ed00
---@sourceScriptId 2a039d00-17e6-483b-9400-7d56ccd9352f
---@referenceName camera-25d-controller.lua
---@start
---@var PitchDeg:number=36
---@name 固定2.5D俯仰角
---@desc 固定斜俯视俯仰角度（默认 36 度）
---@group 2.5D相机
---@var YawDeg:number=0
---@name 固定2.5D偏航角
---@desc 固定朝向抱月湾北岸偏航角度（默认 0 度）
---@group 2.5D相机
---@var DistanceMeters:number=15.5
---@name 固定跟拍距离
---@desc 相机与主角的距离（默认 15.5 米）
---@group 2.5D相机
---@var TargetOffsetY:number=1.15
---@name 目标点高度偏移
---@desc 相机焦点相对主角脚底的 Y 轴高度偏移
---@group 2.5D相机
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Time = UnityEngine.Time
local CameraService = DouyinCameraService or (CS and CS.DouyinCameraService)
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local RendererType = typeof(UnityEngine.Renderer)

local NPC_DEFS = {
  { id = "C01", nodeName = "NPC_Amu", displayName = "阿木", fallbackPos = Vector3(-2.5, 1.15, 3.6) },
  { id = "C02", nodeName = "NPC_Mianmian", displayName = "绵绵", fallbackPos = Vector3(9.8, 1.15, 5.8) },
}

local npcRefs = {}
local reapplyTimer = 2.5
local warnedCamera = false

local function ensureSharedBus()
  if _G.SHIGUANG_25D == nil then
    _G.SHIGUANG_25D = {}
  end
  return _G.SHIGUANG_25D
end

local function traverseDescendants(rootTransform, callback)
  if rootTransform == nil then return end
  local stack = { rootTransform }
  while #stack > 0 do
    local tr = table.remove(stack)
    callback(tr)
    local cnt = tr.childCount
    for i = 0, cnt - 1 do
      table.insert(stack, tr:GetChild(i))
    end
  end
end

local function hideInvisibleSeaBoundaries()
  local hiddenCount = 0
  traverseDescendants(self.transform, function(tr)
    local n = tr.name or ""
    if string.find(n, "Invisible_Sea_Boundary", 1, true) ~= nil then
      local renderers = tr.gameObject:GetComponentsInChildren(RendererType)
      if renderers ~= nil then
        for idx = 0, renderers.Length - 1 do
          local r = renderers[idx]
          if r ~= nil then
            r.enabled = false
            hiddenCount = hiddenCount + 1
          end
        end
      end
    end
  end)
  print(string.format("[camera-25d] Hidden sea boundary renderers: %d", hiddenCount))
end

local function cacheNpcTransforms()
  npcRefs = {}
  local foundMap = {}
  traverseDescendants(self.transform, function(tr)
    local n = tr.name or ""
    for _, def in ipairs(NPC_DEFS) do
      if n == def.nodeName or string.find(n, def.nodeName, 1, true) ~= nil then
        if foundMap[def.id] == nil then
          foundMap[def.id] = tr
        end
      end
    end
  end)

  for _, def in ipairs(NPC_DEFS) do
    table.insert(npcRefs, {
      id = def.id,
      displayName = def.displayName,
      nodeName = def.nodeName,
      transform = foundMap[def.id],
      fallbackPos = def.fallbackPos,
    })
  end
end

local function isPhotoMode()
  if CameraService == nil or CameraService.IsPhotographMode == nil then
    return false
  end
  local ok, res = pcall(function()
    return CameraService.IsPhotographMode()
  end)
  return ok and res == true
end

local function applyFixed25DCamera()
  local bus = ensureSharedBus()
  if bus.cameraOverride == true then return end
  if CameraService == nil or isPhotoMode() then return end

  local pitch = tonumber(PitchDeg) or 36.0
  local yaw = tonumber(YawDeg) or 0.0
  local dist = tonumber(DistanceMeters) or 15.5
  local off = Vector3(0, tonumber(TargetOffsetY) or 1.15, 0)

  local ok, err = pcall(function()
    if CameraService.SetPitch ~= nil then CameraService.SetPitch(pitch) end
    if CameraService.SetYaw ~= nil then CameraService.SetYaw(yaw) end
    if CameraService.SetDistance ~= nil then CameraService.SetDistance(dist) end
    if CameraService.SetOffset ~= nil then CameraService.SetOffset(off) end
  end)
  if not ok and not warnedCamera then
    warnedCamera = true
    UnityEngine.Debug.LogWarning("[camera-25d] DouyinCameraService call failed: " .. tostring(err))
  end
end

local function getLocalPlayerPosition()
  if PlayerService == nil then return nil end
  local ok, pos = pcall(function()
    local player = PlayerService.GetLocalPlayer()
    if player == nil then return nil end
    local actor = player:GetActor()
    if actor == nil then return nil end
    return actor.position
  end)
  if ok then return pos end
  return nil
end

local function getNpcWorldPos(entry)
  if entry.transform ~= nil then
    return entry.transform.position
  end
  if self ~= nil and self.transform ~= nil then
    return self.transform:TransformPoint(entry.fallbackPos)
  end
  return entry.fallbackPos
end

function Start()
  local bus = ensureSharedBus()
  hideInvisibleSeaBoundaries()
  cacheNpcTransforms()

  bus.ReapplyCamera = function(seconds)
    reapplyTimer = math.max(reapplyTimer, tonumber(seconds) or 0.6)
    applyFixed25DCamera()
  end
  bus.GetLocalPlayerPosition = getLocalPlayerPosition
  bus.GetNpcList = function()
    local res = {}
    for _, entry in ipairs(npcRefs) do
      table.insert(res, {
        id = entry.id,
        displayName = entry.displayName,
        nodeName = entry.nodeName,
        worldPos = getNpcWorldPos(entry),
      })
    end
    return res
  end

  reapplyTimer = 3.0
  applyFixed25DCamera()
  print("[camera-25d] Fixed 2.5D controller ready")
end

function LateUpdate()
  if reapplyTimer > 0 then
    reapplyTimer = reapplyTimer - Time.deltaTime
  end
  applyFixed25DCamera()
end

function OnDestroy()
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.ReapplyCamera = nil
    _G.SHIGUANG_25D.GetNpcList = nil
    _G.SHIGUANG_25D.GetLocalPlayerPosition = nil
  end
end
