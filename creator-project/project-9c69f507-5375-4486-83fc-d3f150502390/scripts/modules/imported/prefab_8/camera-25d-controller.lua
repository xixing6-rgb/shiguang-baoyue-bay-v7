---@id c8df2766-4118-45dd-af78-d4f62ef64fa2
---@sourceScriptId 2a039d00-17e6-483b-9400-7d56ccd9352f
---@referenceName camera-25d-controller.lua
---@start
---@var PitchDeg:number=45
---@name 固定45度轴测俯仰角
---@desc 固定45度斜俯视轴测俯仰角度（默认 45 度）
---@group 2.5D相机
---@var YawDeg:number=45
---@name 固定45度轴测偏航角
---@desc 固定45度斜对角轴测偏航角度（默认 45 度）
---@group 2.5D相机
---@var DistanceMeters:number=22.5
---@name 固定轴测跟拍距离
---@desc 相机与主角的跟拍距离（默认 22.5 米）
---@group 2.5D相机
---@var AxonometricFov:number=38
---@name 轴测视场角
---@desc 准轴测窄视场透视角度（默认 38 度）
---@group 2.5D相机
---@var BodyCenterHeight:number=0.85
---@name 角色居中心高度
---@desc 角色视觉重心相对脚底的 Y 轴高度偏移（默认 0.85 米）
---@group 2.5D相机
---@var FollowSmoothing:number=4.5
---@name 延迟跟随平滑系数
---@desc 人物移动时镜头延迟跟随的指数追赶速率（越小延迟越明显）
---@group 2.5D相机
---@var MaxLagMeters:number=1.8
---@name 最大延迟偏移距离
---@desc 镜头漂移延迟跟随的最大水平偏移（默认 1.8 米）
---@group 2.5D相机
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Mathf = UnityEngine.Mathf
local Time = UnityEngine.Time
local CameraService = DouyinCameraService or (CS and CS.DouyinCameraService)
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local InputService = DouyinInputService or (CS and CS.DouyinInputService)
local RendererType = typeof(UnityEngine.Renderer)

local NPC_DEFS = {
  { id = "C01", nodeName = "NPC_Amu", displayName = "阿木", fallbackPos = Vector3(-2.8, 1.56, -1.5) },
  { id = "C02", nodeName = "NPC_Mianmian", displayName = "绵绵", fallbackPos = Vector3(12.7, 1.56, 5.5) },
}

local npcRefs = {}
local reapplyTimer = 2.5
local warnedCamera = false
local originalFov = nil
local smoothedFocusPos = nil
local prevPlayerPos = nil
local playerSpeed = 0.0
local autoCenterBiasY = 0.0
local lastLagWorld = Vector3.zero
local lastAppliedOffset = Vector3.zero
local lastViewportPoint = Vector3(0.5, 0.5, 0.0)
local offsetSpaceMode = "world" -- "world", "camera", or "world_neg"

local lookStartListener = nil
local lookPerformListener = nil
local lookCancelListener = nil
local cameraModeListener = nil

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

local function getActiveCamera()
  if CameraService == nil or CameraService.GetCamera == nil then
    return nil
  end
  local ok, cam = pcall(function()
    return CameraService.GetCamera()
  end)
  if ok then return cam end
  return nil
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

local function worldLagToOffset(lagWorld, yawDeg, pitchDeg)
  if offsetSpaceMode == "world_neg" then
    return Vector3(-lagWorld.x, -lagWorld.y, -lagWorld.z)
  elseif offsetSpaceMode == "camera" then
    local invRot = Quaternion.Inverse(Quaternion.Euler(pitchDeg, yawDeg, 0))
    return invRot * lagWorld
  end
  return lagWorld
end

local function applyFixed25DCamera(isLateUpdate)
  local bus = ensureSharedBus()
  if bus.cameraOverride == true then return end
  if CameraService == nil or isPhotoMode() then return end

  local pitch = tonumber(PitchDeg) or 45.0
  local yaw = tonumber(YawDeg) or 45.0
  local dist = tonumber(DistanceMeters) or 22.5
  local fov = tonumber(AxonometricFov) or 38.0
  local centerH = tonumber(BodyCenterHeight) or 0.85
  local smoothing = tonumber(FollowSmoothing) or 4.5
  local maxLag = tonumber(MaxLagMeters) or 1.8

  local dt = Time.deltaTime or 0.016
  if dt <= 0 or dt > 0.25 then dt = 0.016 end

  local cam = getActiveCamera()
  if cam ~= nil then
    if originalFov == nil then
      originalFov = cam.fieldOfView
    end
    if Mathf.Abs(cam.fieldOfView - fov) > 0.05 then
      cam.fieldOfView = fov
    end
  end

  local playerPos = getLocalPlayerPosition()
  if playerPos ~= nil then
    if prevPlayerPos ~= nil and isLateUpdate then
      playerSpeed = (playerPos - prevPlayerPos).magnitude / dt
    elseif prevPlayerPos == nil then
      playerSpeed = 0.0
    end
    prevPlayerPos = playerPos

    local focusBase = playerPos + Vector3(0, centerH, 0)
    if smoothedFocusPos == nil then
      smoothedFocusPos = focusBase
    elseif (focusBase - smoothedFocusPos).magnitude > 12.0 then
      -- Instant snap on teleports / long jumps
      smoothedFocusPos = focusBase
    elseif isLateUpdate then
      local alpha = 1.0 - math.exp(-smoothing * dt)
      smoothedFocusPos = Vector3.Lerp(smoothedFocusPos, focusBase, alpha)
    end

    local lagWorld = smoothedFocusPos - focusBase
    local lagHorizontal = Vector3(lagWorld.x, 0, lagWorld.z)
    if lagHorizontal.magnitude > maxLag then
      lagHorizontal = lagHorizontal.normalized * maxLag
    end
    lagWorld = Vector3(lagHorizontal.x, lagWorld.y, lagHorizontal.z)
    lastLagWorld = lagWorld

    if cam ~= nil then
      local vp = cam:WorldToViewportPoint(focusBase)
      lastViewportPoint = vp
      if isLateUpdate and vp.z > 0 and playerSpeed < 0.15 and lagHorizontal.magnitude < 0.05 then
        local errY = 0.50 - vp.y
        if Mathf.Abs(errY) > 0.006 then
          autoCenterBiasY = Mathf.Clamp(autoCenterBiasY - errY * 1.6 * dt, -1.5, 1.5)
        end
      end
    end
  end

  local lagOffset = worldLagToOffset(lastLagWorld, yaw, pitch)
  local off = Vector3(lagOffset.x, centerH + autoCenterBiasY + lagOffset.y, lagOffset.z)
  lastAppliedOffset = off

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

local function attachListeners()
  if InputService ~= nil then
    lookStartListener = function()
      applyFixed25DCamera(false)
    end
    lookPerformListener = function()
      applyFixed25DCamera(false)
    end
    lookCancelListener = function()
      reapplyTimer = 0.4
      applyFixed25DCamera(false)
    end
    pcall(function()
      if InputService.onLookInputStart ~= nil then
        InputService.onLookInputStart:AddListener(lookStartListener)
      end
      if InputService.onLookInputPerform ~= nil then
        InputService.onLookInputPerform:AddListener(lookPerformListener)
      end
      if InputService.onLookInputCancel ~= nil then
        InputService.onLookInputCancel:AddListener(lookCancelListener)
      end
    end)
  end

  if CameraService ~= nil and CameraService.onCameraModeChanged ~= nil then
    cameraModeListener = function()
      reapplyTimer = 0.6
      applyFixed25DCamera(false)
    end
    pcall(function()
      CameraService.onCameraModeChanged:AddListener(cameraModeListener)
    end)
  end
end

local function detachListeners()
  if InputService ~= nil then
    pcall(function()
      if lookStartListener ~= nil and InputService.onLookInputStart ~= nil then
        InputService.onLookInputStart:RemoveListener(lookStartListener)
      end
      if lookPerformListener ~= nil and InputService.onLookInputPerform ~= nil then
        InputService.onLookInputPerform:RemoveListener(lookPerformListener)
      end
      if lookCancelListener ~= nil and InputService.onLookInputCancel ~= nil then
        InputService.onLookInputCancel:RemoveListener(lookCancelListener)
      end
    end)
  end
  if CameraService ~= nil and cameraModeListener ~= nil and CameraService.onCameraModeChanged ~= nil then
    pcall(function()
      CameraService.onCameraModeChanged:RemoveListener(cameraModeListener)
    end)
  end
  lookStartListener = nil
  lookPerformListener = nil
  lookCancelListener = nil
  cameraModeListener = nil
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

local function getCameraDebugState()
  local cam = getActiveCamera()
  local camPos = cam ~= nil and cam.transform ~= nil and cam.transform.position or nil
  local fov = cam ~= nil and cam.fieldOfView or nil
  local pitchNow = nil
  local yawNow = nil
  pcall(function()
    if CameraService ~= nil and CameraService.GetPitch ~= nil then pitchNow = CameraService.GetPitch() end
    if CameraService ~= nil and CameraService.GetYaw ~= nil then yawNow = CameraService.GetYaw() end
  end)
  local playerPos = getLocalPlayerPosition()
  local vpNow = lastViewportPoint
  if cam ~= nil and playerPos ~= nil then
    vpNow = cam:WorldToViewportPoint(playerPos + Vector3(0, tonumber(BodyCenterHeight) or 0.85, 0))
  end
  return {
    pitchTarget = tonumber(PitchDeg) or 45.0,
    yawTarget = tonumber(YawDeg) or 45.0,
    pitch = pitchNow,
    yaw = yawNow,
    distanceTarget = tonumber(DistanceMeters) or 22.5,
    fov = fov,
    offsetSpaceMode = offsetSpaceMode,
    autoCenterBiasY = autoCenterBiasY,
    playerSpeed = playerSpeed,
    lagWorld = { x = lastLagWorld.x, y = lastLagWorld.y, z = lastLagWorld.z },
    lagMagnitude = Vector3(lastLagWorld.x, 0, lastLagWorld.z).magnitude,
    appliedOffset = { x = lastAppliedOffset.x, y = lastAppliedOffset.y, z = lastAppliedOffset.z },
    playerViewportXY = { x = vpNow.x, y = vpNow.y, z = vpNow.z },
    cameraPosition = camPos ~= nil and { x = camPos.x, y = camPos.y, z = camPos.z } or nil,
    isPhotoMode = isPhotoMode(),
  }
end

function Start()
  local bus = ensureSharedBus()
  hideInvisibleSeaBoundaries()
  cacheNpcTransforms()
  attachListeners()

  bus.ReapplyCamera = function(seconds)
    reapplyTimer = math.max(reapplyTimer, tonumber(seconds) or 0.6)
    applyFixed25DCamera(false)
  end
  bus.GetLocalPlayerPosition = getLocalPlayerPosition
  bus.GetCameraDebugState = getCameraDebugState
  bus.SetCameraOffsetMode = function(mode)
    if mode == "world" or mode == "camera" or mode == "world_neg" then
      offsetSpaceMode = mode
    end
    return offsetSpaceMode
  end
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
  applyFixed25DCamera(false)
  print("[camera-25d] 45deg axonometric + centered lag-follow controller ready")
end

function LateUpdate()
  if reapplyTimer > 0 then
    reapplyTimer = reapplyTimer - Time.deltaTime
  end
  applyFixed25DCamera(true)
end

function OnDestroy()
  detachListeners()
  local cam = getActiveCamera()
  if cam ~= nil and originalFov ~= nil then
    pcall(function()
      cam.fieldOfView = originalFov
    end)
  end
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.ReapplyCamera = nil
    _G.SHIGUANG_25D.GetNpcList = nil
    _G.SHIGUANG_25D.GetLocalPlayerPosition = nil
    _G.SHIGUANG_25D.GetCameraDebugState = nil
    _G.SHIGUANG_25D.SetCameraOffsetMode = nil
  end
end
