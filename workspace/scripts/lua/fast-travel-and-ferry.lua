---@id b0db7871-23a3-45f2-a6fb-6f52737fb26e
---@referenceName fast-travel-and-ferry.lua
---@displayName 邮差单车快传、摇橹渡船与林间下行木滑道
---@start
---@var TravelMode:string="BikeHub"
---@name 通行模式
---@desc BikeHub(F42单车驿站) / FerryRoute(F01-F40-F26摇橹渡船) / TimberSlide(F35下行木滑道)
---@group 快速通行
---@var StationId:string="F42_Zone0"
---@name 站点编码
---@desc F42_Zone0/F42_ZoneW/F42_ZoneE/F42_ZoneN 或 F01/F40/F26 或 F35W/F35E
---@group 快速通行
---@var TargetStationId:string="F42_ZoneW"
---@name 默认目的站点
---@desc 玩家按E直接触发通行时的默认下一站编码
---@group 快速通行
---@var InteractDistance:number=3.5
---@name 触发半径
---@desc 玩家靠近站点或滑道入口时可激活的距离（米）
---@group 交互
---@var TransitionSeconds:number=1.5
---@name 过渡时长
---@desc 单车1.5s / 渡船2.0s / 滑道约5.0s平滑滑行
---@group 快速通行
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local Time = UnityEngine.Time
local ActorService = DouyinActorService or (CS and CS.DouyinActorService)
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("fast-travel")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local BIKE_HUBS = {
  F42_Zone0 = { zone = "Zone0", pos = { 6.0, 1.8, 3.0 }, yaw = 180.0, nextHub = "F42_ZoneW" },
  F42_ZoneW = { zone = "ZoneW", pos = { -38.0, 1.8, -8.0 }, yaw = 90.0, nextHub = "F42_ZoneE" },
  F42_ZoneE = { zone = "ZoneE", pos = { 40.0, 1.8, 5.0 }, yaw = -90.0, nextHub = "F42_ZoneN" },
  F42_ZoneN = { zone = "ZoneN", pos = { -12.0, 3.6, 32.0 }, yaw = 0.0, nextHub = "F42_Zone0" },
}

local FERRY_DOCKS = {
  F01 = { zone = "Zone0", pos = { -6.0, 0.35, -22.0 }, yaw = 180.0, nextDock = "F40" },
  F40 = { zone = "ZoneS", pos = { -5.0, 0.35, -36.0 }, yaw = 45.0, nextDock = "F26" },
  F26 = { zone = "ZoneE", pos = { 48.0, 0.35, -24.0 }, yaw = -90.0, nextDock = "F01" },
}

local SLIDE_SPLINES = {
  F35W = {
    p0 = { -26.0, 4.5, 35.0 },
    p1 = { -30.5, 3.1, 23.5 },
    p2 = { -34.0, 1.8, 12.0 },
    duration = 5.0,
    yaw = 195.0,
  },
  F35E = {
    p0 = { 27.0, 4.5, 36.0 },
    p1 = { 31.8, 3.1, 25.0 },
    p2 = { 36.0, 1.8, 14.0 },
    duration = 5.0,
    yaw = 165.0,
  },
}

local activeTransition = nil
local wasInteractPressed = false
local cooldownTimer = 0.0
local lastTravelLabel = "就绪"

local function getHost()
  if runtimeScope ~= nil then
    local host = runtimeScope:GetRuntimeHostScript("narrative-host.lua")
    if host ~= nil then return host end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.narrativeHost or nil
end

local function getLocalActor()
  if ActorService ~= nil and type(ActorService.GetLocalActor) == "function" then
    local ok, actor = pcall(function() return ActorService.GetLocalActor() end)
    if ok and actor ~= nil then return actor end
  end
  if PlayerService ~= nil then
    local ok, actor = pcall(function()
      local p = PlayerService.GetLocalPlayer()
      return p ~= nil and p:GetActor() or nil
    end)
    if ok and actor ~= nil then return actor end
  end
  return nil
end

local function teleportActorSafe(posArr, yawDeg)
  local actor = getLocalActor()
  if actor == nil then return false end
  local targetVec = Vector3(posArr[1], posArr[2] + 0.15, posArr[3])
  local targetRot = Quaternion.Euler(0, yawDeg or 0.0, 0)
  local ok = pcall(function()
    if type(actor.Teleport) == "function" then
      actor:Teleport(targetVec, targetRot)
    elseif type(actor.SetPosition) == "function" then
      actor:SetPosition(targetVec)
    elseif actor.transform ~= nil then
      actor.transform.position = targetVec
    end
  end)
  return ok
end

local function evalQuadraticBezier(p0, p1, p2, t)
  local u = 1.0 - t
  local x = u * u * p0[1] + 2.0 * u * t * p1[1] + t * t * p2[1]
  local y = u * u * p0[2] + 2.0 * u * t * p1[2] + t * t * p2[2]
  local z = u * u * p0[3] + 2.0 * u * t * p1[3] + t * t * p2[3]
  return { x, y, z }
end

function StartBikeTravel(destHubId)
  local host = getHost()
  if host ~= nil and not host.IsChapterReached("ch1") then
    logger:info("邮差单车驿站需完成第一章并找回水獭团团铃铛后解锁")
    return false, "locked_ch1"
  end
  local hub = BIKE_HUBS[destHubId] or BIKE_HUBS[TargetStationId]
  if hub == nil then return false, "invalid_hub" end
  if host ~= nil and not host.IsZoneUnlocked(hub.zone) then
    hub = BIKE_HUBS["F42_Zone0"]
  end
  activeTransition = {
    kind = "bike",
    elapsed = 0.0,
    duration = math.max(0.8, TransitionSeconds),
    dest = hub,
  }
  lastTravelLabel = "单车前往:" .. tostring(destHubId or TargetStationId)
  logger:info("薄荷单车叮铃出发 -> " .. tostring(hub.zone))
  return true
end

function StartFerryCrossing(destDockId)
  local host = getHost()
  if host ~= nil and not host.IsChapterReached("ch2") then
    logger:info("摇橹小渡船需在第二章修复造船坊与白昼号后下水")
    return false, "locked_ch2"
  end
  local fromDock = FERRY_DOCKS[StationId] or FERRY_DOCKS["F01"]
  local toDock = FERRY_DOCKS[destDockId] or FERRY_DOCKS[fromDock.nextDock] or FERRY_DOCKS["F40"]
  local midWater = {
    (fromDock.pos[1] + toDock.pos[1]) * 0.5,
    0.25,
    (fromDock.pos[3] + toDock.pos[3]) * 0.5 - 2.5,
  }
  activeTransition = {
    kind = "ferry",
    elapsed = 0.0,
    duration = 2.0,
    p0 = fromDock.pos,
    p1 = midWater,
    p2 = toDock.pos,
    yaw = toDock.yaw,
    destZone = toDock.zone,
  }
  lastTravelLabel = "摇橹渡船:" .. tostring(StationId) .. "->" .. tostring(destDockId or fromDock.nextDock)
  logger:info("摇橹渡船离岸 -> " .. tostring(toDock.zone))
  return true
end

function StartTimberSlide(slideId)
  local host = getHost()
  if host ~= nil and not host.IsChapterReached("ch3") then
    logger:info("林间快速木滑道将在第三章开启北麓溪谷后开放")
    return false, "locked_ch3"
  end
  local spline = SLIDE_SPLINES[slideId or StationId] or SLIDE_SPLINES["F35W"]
  activeTransition = {
    kind = "slide",
    elapsed = 0.0,
    duration = spline.duration,
    p0 = spline.p0,
    p1 = spline.p1,
    p2 = spline.p2,
    yaw = spline.yaw,
  }
  if host ~= nil then
    host.SetFact("yesterdayAction", "rode_slide")
    host.AddWarmFuzzies(2, "slide:" .. tostring(slideId or StationId))
  end
  lastTravelLabel = "林间木滑道:" .. tostring(slideId or StationId)
  logger:info("踏入林间木滑道（7.0 m/s 无跳跃平滑下行）")
  return true
end

function TriggerDefaultTravel()
  if cooldownTimer > 0.0 or activeTransition ~= nil then return false end
  cooldownTimer = 1.0
  if TravelMode == "BikeHub" then
    local cur = BIKE_HUBS[StationId]
    local nextId = (cur ~= nil and cur.nextHub) or TargetStationId
    return StartBikeTravel(nextId)
  elseif TravelMode == "FerryRoute" then
    local cur = FERRY_DOCKS[StationId]
    local nextId = (cur ~= nil and cur.nextDock) or TargetStationId
    return StartFerryCrossing(nextId)
  else
    return StartTimberSlide(StationId)
  end
end

function GetTravelState()
  return {
    mode = TravelMode,
    station = StationId,
    isTransitioning = activeTransition ~= nil,
    label = lastTravelLabel,
  }
end

function Start()
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "fast-travel-and-ferry 未取得 RuntimeScope", runtimeScopeReason)
  end
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.fastTravel = {
    StartBikeTravel = StartBikeTravel,
    StartFerryCrossing = StartFerryCrossing,
    StartTimberSlide = StartTimberSlide,
    GetTravelState = GetTravelState,
  }
  logger:info(string.format("快速通行点初始化: %s (%s)", TravelMode, StationId))
end

function Update()
  local dt = Time.deltaTime
  if cooldownTimer > 0.0 then
    cooldownTimer = math.max(0.0, cooldownTimer - dt)
  end

  if activeTransition ~= nil then
    activeTransition.elapsed = activeTransition.elapsed + dt
    local t = math.min(1.0, activeTransition.elapsed / activeTransition.duration)
    if activeTransition.kind == "bike" then
      if t >= 1.0 then
        teleportActorSafe(activeTransition.dest.pos, activeTransition.dest.yaw)
        local host = getHost()
        if host ~= nil then host.VisitFacility(StationId, activeTransition.dest.zone) end
        activeTransition = nil
      end
    elseif activeTransition.kind == "ferry" or activeTransition.kind == "slide" then
      local smoothT = t * t * (3.0 - 2.0 * t)
      local posNow = evalQuadraticBezier(activeTransition.p0, activeTransition.p1, activeTransition.p2, smoothT)
      teleportActorSafe(posNow, activeTransition.yaw)
      if t >= 1.0 then
        activeTransition = nil
      end
    end
    return
  end

  local interactPressed = Input.GetKey(KeyCode.E)
  local interactStarted = interactPressed and not wasInteractPressed
  wasInteractPressed = interactPressed

  local actor = getLocalActor()
  if actor ~= nil and self ~= nil and self.transform ~= nil then
    local p = actor.position
    local c = self.transform.position
    local dx = p.x - c.x
    local dz = p.z - c.z
    local dy = math.abs(p.y - c.y)
    local dist = math.sqrt(dx * dx + dz * dz)
    if dist <= InteractDistance and dy <= 3.0 then
      if TravelMode == "TimberSlide" or interactStarted then
        TriggerDefaultTravel()
      end
    end
  end
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.fastTravel = nil
  end
end
