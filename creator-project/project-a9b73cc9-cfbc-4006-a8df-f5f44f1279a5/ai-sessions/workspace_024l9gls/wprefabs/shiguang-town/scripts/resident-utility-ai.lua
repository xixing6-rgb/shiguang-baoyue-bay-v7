---@id c5670c57-c276-47ed-a8f6-b71d5e9e2352
---@referenceName resident-utility-ai.lua
---@displayName 居民效用AI、65/35引力潮汐与8秒轻导演调度
---@start
---@var ResidentId:string="C01"
---@name 居民编号
---@desc 若挂载于单个居民节点则指定 C01..C09；若设为 ALL 则作为全镇调度协调器
---@group 居民AI
---@var DecisionInterval:number=4.5
---@name 决策刷新间隔
---@desc 效用AI重新评估周边智能物件的秒数周期
---@group 居民AI
---@var DirectorBiasSeconds:number=8.0
---@name 轻导演防空窗阈值
---@desc 玩家进入外围区且28m内无居民满该秒数后触发软牵引
---@group 轻导演
---@var DirectorScanRadius:number=28.0
---@name 空窗检测半径
---@desc 检测玩家周边活跃居民数的距离（米）
---@group 轻导演
---@var MaxPerScreen:number=6
---@name 同屏软上限
---@desc 保护移动端帧率与画面留白的单屏最大活跃居民数
---@group 轻导演
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("resident-utility-ai")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 平台官方动作与表现白名单校验表（严禁手指精细动作、面部嘴型动画、跳跃攀爬）
local ALLOWED_ACTIONS = {
  -- 官方动作库
  walk = true,
  run = true,
  greet = true,
  wave = true,
  sit = true,
  clap = true,
  cheer = true,
  dance = true,
  photo = true,
  water_bend = true,
  -- 程序化节点动效
  turn_to_player = true,
  hop_bounce = true,
  nod_tilt = true,
  hover_bob = true,
  door_open = true,
  pivot_spin = true,
  paper_pet_squash = true,
  -- 四色烦恼气泡
  bubble_yellow = true,
  bubble_orange = true,
  bubble_pink = true,
  bubble_purple = true,
  -- 轻量粒子特效
  fx_heart = true,
  fx_sparkle = true,
  fx_petal = true,
  fx_ripple = true,
  fx_firefly = true,
  -- 语音模式
  voice_soft = true,
  voice_mech = true,
}

local ZONE_BOUNDS = {
  Zone0 = { xMin = -32, xMax = 32, zMin = -28, zMax = 28 },
  ZoneW = { xMin = -68, xMax = -32, zMin = -44, zMax = 34 },
  ZoneE = { xMin = 32, xMax = 68, zMin = -42, zMax = 32 },
  ZoneN = { xMin = -54, xMax = 54, zMin = 28, zMax = 68 },
  ZoneS = { xMin = -38, xMax = 28, zMin = -54, zMax = -34 },
}

local TIME_GRAVITY_ANCHORS = {
  afternoon = {
    hotspotA = { F05 = true, F06 = true, F09 = true, F12 = true },
    hotspotB = { F19 = true, F26 = true },
    outer = { F31 = true, F02 = true, F28 = true, F15 = true },
  },
  dusk = {
    hotspotA = { F16 = true, F21 = true, F22 = true },
    hotspotB = { F37 = true, F39 = true },
    outer = { F25 = true, F06 = true, F27 = true },
  },
  night = {
    hotspotA = { F25 = true },
    hotspotB = { F04 = true, F05 = true },
    outer = { F34 = true, F32 = true, F22 = true, F39 = true },
  },
}

local RESIDENT_DEFS = {
  C01 = { name = "阿木", axis = "ICSG", quirk = "collector_nostalgia", unlock = "prologue", homeFacility = "F04", homePos = { -10, 1.8, -2 }, voice = "voice_soft", motives = { curiosity = 1.35, warmth = 1.25, nature = 1.15 } },
  C02 = { name = "绵绵", axis = "EDRG", quirk = "flower_whisperer", unlock = "prologue", homeFacility = "F13", homePos = { 5, 1.8, -8 }, voice = "voice_soft", motives = { nature = 1.45, social = 1.25, curiosity = 1.10 } },
  C03 = { name = "阿橘", axis = "ICSK", quirk = "deadpan_applause", unlock = "prologue", homeFacility = "F11", homePos = { 11, 1.8, 5 }, voice = "voice_mech", motives = { curiosity = 1.30, rest = 1.20, social = 0.90 } },
  C04 = { name = "奶包", axis = "ECRG", quirk = "big_stomach", unlock = "prologue", homeFacility = "F12", homePos = { 23, 1.8, -4 }, voice = "voice_soft", motives = { hunger = 1.55, social = 1.35, warmth = 1.20 } },
  C05 = { name = "墨羽", axis = "IDSK", quirk = "levitating_night_owl", unlock = "prologue", homeFacility = "F15", homePos = { -12, 3.6, 20 }, voice = "voice_mech", motives = { curiosity = 1.40, relax = 1.25, warmth = 1.10 } },
  C06 = { name = "阿澈", axis = "ICRK", quirk = "tide_watcher", unlock = "prologue", homeFacility = "F02", homePos = { 10, 0.2, -23 }, voice = "voice_soft", motives = { relax = 1.45, craft = 1.20, warmth = 1.10 } },
  C07 = { name = "团团", axis = "EDRK", quirk = "absentminded_drop", unlock = "ch1", homeFacility = "F23", homePos = { -44, 1.8, 4 }, voice = "voice_soft", motives = { social = 1.35, curiosity = 1.25, play = 1.15 } },
  C08 = { name = "咔哒", axis = "ICSG", quirk = "symmetry_ocd", unlock = "ch2", homeFacility = "F30", homePos = { 54, 1.2, -18 }, voice = "voice_mech", motives = { craft = 1.50, curiosity = 1.20, relax = 0.95 } },
  C09 = { name = "绒绒", axis = "IDRG", quirk = "shy_runway_walk", unlock = "ch3", homeFacility = "F31", homePos = { -16, 3.6, 42 }, voice = "voice_soft", motives = { play = 1.35, curiosity = 1.30, warmth = 1.20 } },
}

local agents = {}
local activeScreenResidents = {}
local emptyOuterTimer = 0.0
local lastEmptyZone = nil
local decisionTimer = 0.0
local bubbleTimer = 0.0

local function getHost()
  if runtimeScope ~= nil then
    local host = runtimeScope:GetRuntimeHostScript("narrative-host.lua")
    if host ~= nil then return host end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.narrativeHost or nil
end

local function getSmartRegistry()
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.smartObjects or {}
end

function IsActionAllowed(actionName)
  return type(actionName) == "string" and ALLOWED_ACTIONS[actionName] == true
end

function ValidateAndExecuteAction(residentId, actionName)
  if not IsActionAllowed(actionName) then
    logger:warnOnce("bad-action-" .. tostring(actionName),
      string.format("拒绝未在白名单中的动作 [%s]（居民 %s）", tostring(actionName), tostring(residentId)))
    return false, "walk"
  end
  local ag = agents[residentId]
  if ag ~= nil then
    ag.currentAction = actionName
    ag.actionTimer = 2.4
  end
  return true, actionName
end

local function resolveZoneFromPos(pos)
  if pos == nil then return "Zone0" end
  local x, z = pos.x or pos[1] or 0, pos.z or pos[3] or 0
  if z <= -34 and x >= -38 and x <= 28 then return "ZoneS" end
  if z >= 28 and x >= -54 and x <= 54 then return "ZoneN" end
  if x < -32 then return "ZoneW" end
  if x > 32 then return "ZoneE" end
  return "Zone0"
end

local function getLocalPlayerPosition()
  if PlayerService == nil then return nil end
  local ok, pos = pcall(function()
    local p = PlayerService.GetLocalPlayer()
    local actor = p ~= nil and p:GetActor() or nil
    return actor ~= nil and actor.position or nil
  end)
  if ok then return pos end
  return nil
end

-- Dave Mark IAUS 效用评分：需求 × 性格微个性权重 × 65/35三时段引力潮汐 × 轻导演偏置
local function computeUtilityScore(ag, so, timeSlot, isBiasedZone)
  local host = getHost()
  if host ~= nil and not host.IsChapterReached(so.unlockChapter or "prologue") then
    return 0.0
  end
  if (so.occupiedCount or 0) >= (so.slotCapacity or 1) then
    return 0.05
  end

  local def = RESIDENT_DEFS[ag.id]
  local baseScore = 0.25
  if so.motives ~= nil then
    for motiveKey, weight in pairs(so.motives) do
      local pref = (def.motives and def.motives[motiveKey]) or 1.0
      local need = ag.needs[motiveKey] or 0.55
      baseScore = baseScore + weight * pref * need * 0.35
    end
  end

  -- 65/35 引力潮汐权重：约三分之二居民受当前时段热区吸引
  local grav = TIME_GRAVITY_ANCHORS[timeSlot or "afternoon"]
  if grav ~= nil then
    if ag.gravityRole == "hotspot" then
      if grav.hotspotA[so.facilityId] then
        baseScore = baseScore * 2.2
      elseif grav.hotspotB[so.facilityId] then
        baseScore = baseScore * 1.7
      end
    else
      if grav.outer[so.facilityId] or so.facilityId == def.homeFacility then
        baseScore = baseScore * 1.8
      end
    end
  end

  -- 8秒轻导演偏置（仅对指定空窗目标区域 ×4.0）
  if isBiasedZone and so.zone == ag.directorTargetZone then
    baseScore = baseScore * 4.0
  end

  local dx = (ag.pos[1] - so.pos[1])
  local dz = (ag.pos[3] - so.pos[3])
  local dist = math.sqrt(dx * dx + dz * dz)
  local distFactor = 1.0 / (1.0 + dist * 0.015)

  return math.min(1.0, math.max(0.0, baseScore * distFactor * 0.65))
end

local function pickWeightedTop3(candidates)
  if #candidates == 0 then return nil end
  table.sort(candidates, function(a, b) return a.score > b.score end)
  local topN = math.min(3, #candidates)
  local sum = 0.0
  for i = 1, topN do
    sum = sum + math.max(0.01, candidates[i].score)
  end
  local roll = math.random() * sum
  local acc = 0.0
  for i = 1, topN do
    acc = acc + math.max(0.01, candidates[i].score)
    if roll <= acc then
      return candidates[i]
    end
  end
  return candidates[1]
end

local function evaluateResidentDecision(ag)
  local host = getHost()
  if host ~= nil and not host.IsChapterReached(RESIDENT_DEFS[ag.id].unlock) then
    return
  end
  local timeSlot = (host ~= nil and host.GetFact("timeSlot")) or "afternoon"
  local smartObjs = getSmartRegistry()
  local candidates = {}

  for _, so in pairs(smartObjs) do
    local score = computeUtilityScore(ag, so, timeSlot, ag.directorTargetZone ~= nil)
    if score > 0.05 then
      table.insert(candidates, { so = so, score = score })
    end
  end

  local chosen = pickWeightedTop3(candidates)
  if chosen ~= nil then
    if ag.targetFacility ~= nil and ag.targetFacility ~= chosen.so.facilityId then
      local prevSo = smartObjs[ag.targetFacility]
      if prevSo ~= nil and type(prevSo.ReleaseSlot) == "function" then
        prevSo.ReleaseSlot(ag.id)
      end
    end
    if type(chosen.so.ReserveSlot) == "function" then
      chosen.so.ReserveSlot(ag.id)
    end
    ag.targetFacility = chosen.so.facilityId
    ag.targetPos = { chosen.so.pos[1], chosen.so.pos[2], chosen.so.pos[3] }
    ag.state = "WalkToObject"
    ValidateAndExecuteAction(ag.id, "walk")
    ag.directorTargetZone = nil
  else
    ag.state = "Idle"
    ValidateAndExecuteAction(ag.id, RESIDENT_DEFS[ag.id].quirk == "levitating_night_owl" and "hover_bob" or "greet")
  end
end

-- 8秒防稀释轻导演软牵引：玩家步入外围区 8s 且 28m 内无人，从视野外 22–28m 步行引来 1 名闲置居民
local function updateSoftDirectorBias(dt)
  local playerPos = getLocalPlayerPosition()
  if playerPos == nil then return end
  local pZone = resolveZoneFromPos(playerPos)
  if pZone == "Zone0" then
    emptyOuterTimer = 0.0
    lastEmptyZone = nil
    return
  end

  local nearbyCount = 0
  local nearestOffscreen = nil
  local nearestDist = 9999.0

  for cid, ag in pairs(agents) do
    local host = getHost()
    if host == nil or host.IsChapterReached(RESIDENT_DEFS[cid].unlock) then
      local dx = ag.pos[1] - playerPos.x
      local dz = ag.pos[3] - playerPos.z
      local dist = math.sqrt(dx * dx + dz * dz)
      if dist <= DirectorScanRadius then
        nearbyCount = nearbyCount + 1
      elseif dist >= 22.0 and (ag.state == "Idle" or ag.state == "Wander" or ag.state == "WalkToObject") then
        if dist < nearestDist then
          nearestDist = dist
          nearestOffscreen = ag
        end
      end
    end
  end

  if nearbyCount == 0 then
    if lastEmptyZone ~= pZone then
      lastEmptyZone = pZone
      emptyOuterTimer = 0.0
    else
      emptyOuterTimer = emptyOuterTimer + dt
    end
    if emptyOuterTimer >= DirectorBiasSeconds and nearestOffscreen ~= nil then
      emptyOuterTimer = 0.0
      nearestOffscreen.directorTargetZone = pZone
      -- 将目标边缘微调至视野外 24m 入口拐角步行走入（严禁屏幕内凭空传送）
      local host = getHost()
      if host ~= nil then
        host.SetFact("directorSoftBias", true)
      end
      evaluateResidentDecision(nearestOffscreen)
      logger:info(string.format("轻导演软牵引触发：引导 [%s] 步行前往空窗片区 %s", nearestOffscreen.id, pZone))
    end
  else
    emptyOuterTimer = 0.0
  end
end

-- 物理轻推 つまむ 交互：抓取与轻放后保留“不配合的意外喜剧反应”
function BeginNudge(residentId)
  local ag = agents[residentId]
  if ag == nil then return false end
  ag.isGrabbed = true
  ag.state = "Nudged"
  ValidateAndExecuteAction(residentId, "hover_bob")
  return true
end

function DropNudge(residentId, worldPos)
  local ag = agents[residentId]
  if ag == nil then return false end
  ag.isGrabbed = false
  if worldPos ~= nil then
    ag.pos = { worldPos.x or worldPos[1] or ag.pos[1], worldPos.y or worldPos[2] or ag.pos[2], worldPos.z or worldPos[3] or ag.pos[3] }
  end
  local host = getHost()
  if host ~= nil then
    host.SetFact("yesterdayAction", "nudged_resident")
    host.AddWarmFuzzies(2, "nudge:" .. residentId)
  end

  -- 保留不配合的戏剧性，绝不强行命令居民服从或恋爱
  local quirk = RESIDENT_DEFS[residentId].quirk
  local reaction = "stare_silent"
  if quirk == "deadpan_applause" then
    reaction = "deadpan_applause"
    ValidateAndExecuteAction(residentId, "clap")
    ag.activeBubble = "bubble_purple"
  elseif math.random() < 0.35 then
    reaction = "walk_away_awkward"
    ValidateAndExecuteAction(residentId, "turn_to_player")
  else
    reaction = "curious_bounce"
    ValidateAndExecuteAction(residentId, "hop_bounce")
    ag.activeBubble = "bubble_orange"
  end
  ag.state = "Idle"
  logger:info(string.format("轻推放下 [%s] -> 自主意外反应: %s", residentId, reaction))
  return true, reaction
end

function TriggerWorryBubble(residentId, colorKey)
  local ag = agents[residentId]
  if ag == nil then return nil end
  local map = {
    yellow = "bubble_yellow",
    orange = "bubble_orange",
    pink = "bubble_pink",
    purple = "bubble_purple",
  }
  local bubbleAction = map[colorKey] or "bubble_yellow"
  local ok, safeAct = ValidateAndExecuteAction(residentId, bubbleAction)
  if ok then
    ag.activeBubble = safeAct
    return safeAct
  end
  return nil
end

function ResolveWorryBubble(residentId, outcomeType)
  local ag = agents[residentId]
  if ag == nil then return false end
  local prevBubble = ag.activeBubble
  ag.activeBubble = nil
  local host = getHost()
  local gain = 8
  local act = "cheer"
  if outcomeType == "super_love" then
    gain = 15
    act = "dance"
  elseif outcomeType == "soul_leave" then
    gain = 1
    act = "hover_bob"
  elseif prevBubble == "bubble_pink" then
    gain = 12
    act = "greet"
  end
  ValidateAndExecuteAction(residentId, act)
  if host ~= nil then
    host.AddAffection(residentId, gain, "worry_resolved")
    host.AddWarmFuzzies(5, "bubble:" .. tostring(prevBubble))
  end
  return true, act, gain
end

local function stepAgentMovement(ag, dt)
  if ag.isGrabbed or ag.targetPos == nil or ag.state ~= "WalkToObject" then
    if RESIDENT_DEFS[ag.id].quirk == "levitating_night_owl" then
      ag.hoverOffset = 0.25 + math.sin(Time.time * 2.2) * 0.06
    end
    return
  end
  local dx = ag.targetPos[1] - ag.pos[1]
  local dz = ag.targetPos[3] - ag.pos[3]
  local dist = math.sqrt(dx * dx + dz * dz)
  if dist < 0.85 then
    ag.pos[1] = ag.targetPos[1]
    ag.pos[2] = ag.targetPos[2]
    ag.pos[3] = ag.targetPos[3]
    ag.state = "Interact"
    local so = getSmartRegistry()[ag.targetFacility]
    local targetAct = (so ~= nil and so.allowedAction) or "greet"
    ValidateAndExecuteAction(ag.id, targetAct)
    return
  end
  local speed = (RESIDENT_DEFS[ag.id].quirk == "absentminded_drop") and 2.5 or 2.0
  local step = math.min(dist, speed * dt)
  ag.pos[1] = ag.pos[1] + (dx / dist) * step
  ag.pos[3] = ag.pos[3] + (dz / dist) * step
  ag.pos[2] = ag.pos[2] + (ag.targetPos[2] - ag.pos[2]) * math.min(1.0, dt * 3.0)

  if ag.transform ~= nil then
    local yOffset = (RESIDENT_DEFS[ag.id].quirk == "levitating_night_owl") and (0.25 + math.sin(Time.time * 2.2) * 0.06) or 0.0
    ag.transform.position = Vector3(ag.pos[1], ag.pos[2] + yOffset, ag.pos[3])
    if dist > 0.05 then
      local atanFn = math.atan2 or math.atan
      local yaw = atanFn(dx, dz) * (180.0 / math.pi)
      ag.transform.rotation = Quaternion.Euler(0, yaw, 0)
    end
  end
end

local function initAgents()
  local idx = 0
  for cid, def in pairs(RESIDENT_DEFS) do
    if ResidentId == "ALL" or ResidentId == cid then
      idx = idx + 1
      -- 严格保持 65% 热区聚拢（约 6 人） / 35% 外围据点（约 3 人）
      local role = (idx % 3 == 0) and "outer" or "hotspot"
      agents[cid] = {
        id = cid,
        state = "Idle",
        pos = { def.homePos[1], def.homePos[2], def.homePos[3] },
        targetPos = nil,
        targetFacility = nil,
        gravityRole = role,
        currentAction = def.quirk == "levitating_night_owl" and "hover_bob" or "greet",
        actionTimer = 0.0,
        activeBubble = nil,
        isGrabbed = false,
        hoverOffset = 0.0,
        directorTargetZone = nil,
        transform = (ResidentId == cid and self ~= nil) and self.transform or nil,
        needs = { social = 0.65, hunger = 0.55, curiosity = 0.70, warmth = 0.65, nature = 0.60, relax = 0.55, craft = 0.50, play = 0.55, music = 0.50, rest = 0.45 },
      }
    end
  end
end

function GetAIState()
  local count = 0
  for _ in pairs(agents) do
    count = count + 1
  end
  return {
    mode = ResidentId,
    activeCount = count,
    agents = agents,
    maxPerScreen = MaxPerScreen,
    allowedActionsCount = 29,
  }
end

function Start()
  math.randomseed(os.time())
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "resident-utility-ai 未取得 RuntimeScope", runtimeScopeReason)
  end
  initAgents()
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.residentAI = {
    BeginNudge = BeginNudge,
    DropNudge = DropNudge,
    TriggerWorryBubble = TriggerWorryBubble,
    ResolveWorryBubble = ResolveWorryBubble,
    IsActionAllowed = IsActionAllowed,
    ValidateAndExecuteAction = ValidateAndExecuteAction,
    GetAIState = GetAIState,
  }
  logger:info("居民 Utility AI 初始化完成（65/35 引力潮汐 + 8s 轻导演 + 动作白名单锁定）")
end

function Update()
  local dt = Time.deltaTime
  decisionTimer = decisionTimer + dt
  bubbleTimer = bubbleTimer + dt

  local playerPos = getLocalPlayerPosition()
  local screenCount = 0

  for cid, ag in pairs(agents) do
    stepAgentMovement(ag, dt)
    if playerPos ~= nil then
      local dx = ag.pos[1] - playerPos.x
      local dz = ag.pos[3] - playerPos.z
      if (dx * dx + dz * dz) <= (20.0 * 20.0) then
        screenCount = screenCount + 1
      end
    end
  end

  if decisionTimer >= math.max(1.5, DecisionInterval) then
    decisionTimer = 0.0
    for _, ag in pairs(agents) do
      if ag.state == "Idle" or ag.state == "Interact" then
        if screenCount <= MaxPerScreen or ag.gravityRole == "outer" then
          evaluateResidentDecision(ag)
        end
      end
    end
  end

  if bubbleTimer >= 22.0 then
    bubbleTimer = 0.0
    local colors = { "yellow", "orange", "pink", "purple" }
    for cid, ag in pairs(agents) do
      if ag.activeBubble == nil and math.random() < 0.25 then
        local c = colors[math.random(1, #colors)]
        TriggerWorryBubble(cid, c)
        break
      end
    end
  end

  updateSoftDirectorBias(dt)
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.residentAI = nil
  end
end
