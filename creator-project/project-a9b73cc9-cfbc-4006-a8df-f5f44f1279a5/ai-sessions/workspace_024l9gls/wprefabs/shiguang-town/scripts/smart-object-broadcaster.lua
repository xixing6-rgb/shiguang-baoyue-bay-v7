---@id 132b6356-c42c-45d9-a2f3-34f02a940885
---@referenceName smart-object-broadcaster.lua
---@displayName 智能物件动机广播与叙事交互触发器
---@start
---@var FacilityId:string="F09"
---@name 设施编号
---@desc 对应 F01..F42 的全图标准设施编码
---@group 智能物件
---@var ZoneId:string="Zone0"
---@name 所属片区
---@desc Zone0 / ZoneW / ZoneE / ZoneN / ZoneS
---@group 智能物件
---@var UnlockChapter:string="prologue"
---@name 软门控解锁章节
---@desc prologue / ch1 / ch2 / ch3 / ch4
---@group 叙事联动
---@var MotivePrimary:string="social"
---@name 主广播动机维度
---@desc social / curiosity / hunger / nature / warmth / relax / craft / play / music / rest
---@group 智能物件
---@var MotiveWeight:number=0.85
---@name 动机广播权重
---@desc 对居民效用AI的基础吸引强度（0.0-1.0）
---@group 智能物件
---@var SlotCapacity:number=3
---@name 交互槽位上限
---@desc 允许同时聚集围观或交互的居民最大人数
---@group 智能物件
---@var AllowedAction:string="greet"
---@name 对应白名单动作
---@desc 必须在官方白名单内（greet/wave/sit/clap/cheer/dance/photo/water_bend 等）
---@group 智能物件
---@var CollectibleId:string=""
---@name 关联记忆碎片
---@desc 首次按E或靠近拾取的 M01..M26 记忆碎片ID，留空表示无
---@group 叙事联动
---@var StoryEventKey:string=""
---@name 触发剧情事件键
---@desc 如 lighthouse_relight / lightship_relight / blue_rose_bred / summit_bell_rung
---@group 叙事联动
---@var InteractDistance:number=4.0
---@name 交互触发半径
---@desc 玩家按E键触发该设施叙事交互的距离（米）
---@group 交互
---@var AutoTriggerOnFirstVisit:boolean=false
---@name 首次到达自动触发
---@desc 关键地标首次走近时自动触发一次柔和叙事反馈
---@group 交互
---@end

local UnityEngine = CS.UnityEngine
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local Time = UnityEngine.Time
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("smart-object")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local COOLDOWN_SECONDS = 1.2
local occupiedResidents = {}
local occupiedCount = 0
local wasInteractPressed = false
local lastTriggerAt = -10.0
local firstVisitDone = false
local lastDistance = 999.0
local isPlayerNearby = false

local function getHost()
  if runtimeScope ~= nil then
    local host = runtimeScope:GetRuntimeHostScript("narrative-host.lua")
    if host ~= nil then return host end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.narrativeHost or nil
end

local function getDialogueEngine()
  if runtimeScope ~= nil then
    local eng = runtimeScope:GetScript("blackboard-dialogue-engine.lua")
    if eng ~= nil then return eng end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.dialogueEngine or nil
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

local function getSelfPosTable()
  if self ~= nil and self.transform ~= nil then
    local p = self.transform.position
    return { p.x, p.y, p.z }
  end
  return { 0.0, 0.0, 0.0 }
end

function ReserveSlot(residentId)
  if occupiedResidents[residentId] == true then return true end
  if occupiedCount >= math.max(1, math.floor(SlotCapacity)) then
    return false
  end
  occupiedResidents[residentId] = true
  occupiedCount = occupiedCount + 1
  return true
end

function ReleaseSlot(residentId)
  if occupiedResidents[residentId] == true then
    occupiedResidents[residentId] = nil
    occupiedCount = math.max(0, occupiedCount - 1)
  end
end

local FACILITY_YESTERDAY_MAP = {
  F02 = "fished_at_pier",
  F06 = "watered_flower",
  F07 = "changed_flag",
  F08 = "changed_chalkboard",
  F12 = "fed_bun",
  F25 = "fed_bun",
}

local FACILITY_DEFAULT_SPEAKER = {
  F01 = "C02", F02 = "C06", F03 = "C02", F04 = "C01", F05 = "C01", F06 = "C02",
  F07 = "C03", F08 = "C03", F09 = "C02", F10 = "C04", F11 = "C03", F12 = "C04",
  F13 = "C01", F14 = "C02", F15 = "C05", F16 = "C01", F17 = "C04", F18 = "C09",
  F19 = "C07", F20 = "C07", F21 = "C05", F22 = "C05", F23 = "C07", F24 = "C02",
  F25 = "C04", F26 = "C08", F27 = "C06", F28 = "C06", F29 = "C09", F30 = "C08",
  F31 = "C01", F32 = "C05", F33 = "C01", F34 = "C05", F35 = "C09", F36 = "C01",
  F37 = "C08", F38 = "C08", F39 = "C03", F40 = "C06", F41 = "C09", F42 = "C07",
}

function TriggerInteraction(residentSpeakerId)
  local now = Time.time or 0.0
  if (now - lastTriggerAt) < COOLDOWN_SECONDS then return false end
  lastTriggerAt = now

  local speaker = residentSpeakerId or FACILITY_DEFAULT_SPEAKER[FacilityId] or "C01"
  local host = getHost()
  if host ~= nil and not host.IsChapterReached(UnlockChapter) then
    logger:info(string.format("[%s] 尚在软门控等待期（需完成前置章节 %s），温柔提示玩家先逛老镇线索", FacilityId, UnlockChapter))
    return false, "soft_gated"
  end

  if host ~= nil then
    host.VisitFacility(FacilityId, ZoneId)
    if CollectibleId ~= "" then
      host.CollectMemory(CollectibleId, FacilityId)
    end
    if StoryEventKey ~= "" then
      host.TriggerStoryEvent(StoryEventKey)
    end
    local actFact = FACILITY_YESTERDAY_MAP[FacilityId]
    if actFact ~= nil then
      host.SetFact("yesterdayAction", actFact)
    end
    local prevTalks = host.GetFact("talkCount") or 0
    host.SetFact("talkCount", prevTalks + 1)
    host.AddWarmFuzzies(3, "interact:" .. FacilityId)
  end

  local eng = getDialogueEngine()
  local line = nil
  if eng ~= nil then
    line = eng.QueryDialogue(speaker, { facilityId = FacilityId, zone = ZoneId }, "happy")
    if line ~= nil then
      logger:info(string.format("[%s][%s] 交互回应(%s): %s", FacilityId, speaker, line.ruleId, line.text))
    end
  end
  return true, line
end

local function registerSmartObject()
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  if _G.__SHIGUANG_SERVICES.smartObjects == nil then
    _G.__SHIGUANG_SERVICES.smartObjects = {}
  end
  local motives = {}
  motives[MotivePrimary] = math.min(1.0, math.max(0.1, MotiveWeight))
  motives["curiosity"] = motives["curiosity"] or 0.45

  _G.__SHIGUANG_SERVICES.smartObjects[FacilityId] = {
    facilityId = FacilityId,
    zone = ZoneId,
    unlockChapter = UnlockChapter,
    pos = getSelfPosTable(),
    slotCapacity = math.max(1, math.floor(SlotCapacity)),
    occupiedCount = occupiedCount,
    motives = motives,
    allowedAction = AllowedAction,
    ReserveSlot = ReserveSlot,
    ReleaseSlot = ReleaseSlot,
    TriggerInteraction = TriggerInteraction,
  }
end

function Start()
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "smart-object-broadcaster 未取得 RuntimeScope", runtimeScopeReason)
  end
  registerSmartObject()
  logger:info(string.format("智能物件广播上线: %s (%s / %s, 槽位=%d)", FacilityId, ZoneId, MotivePrimary, math.floor(SlotCapacity)))
end

function Update()
  local entry = _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.smartObjects and _G.__SHIGUANG_SERVICES.smartObjects[FacilityId]
  if entry ~= nil then
    entry.occupiedCount = occupiedCount
  end

  local interactPressed = Input.GetKey(KeyCode.E)
  local interactStarted = interactPressed and not wasInteractPressed
  wasInteractPressed = interactPressed

  local playerPos = getLocalPlayerPosition()
  if playerPos ~= nil and self ~= nil and self.transform ~= nil then
    local center = self.transform.position
    local dx = playerPos.x - center.x
    local dz = playerPos.z - center.z
    local dy = math.abs(playerPos.y - center.y)
    lastDistance = math.sqrt(dx * dx + dz * dz)
    isPlayerNearby = (lastDistance <= InteractDistance) and (dy <= 3.5)

    if isPlayerNearby then
      if AutoTriggerOnFirstVisit and not firstVisitDone then
        firstVisitDone = true
        TriggerInteraction(nil)
      elseif interactStarted then
        TriggerInteraction(nil)
      end
    end
  end
end

function GetSmartObjectState()
  return {
    facilityId = FacilityId,
    zone = ZoneId,
    occupiedCount = occupiedCount,
    slotCapacity = SlotCapacity,
    distance = lastDistance,
    nearby = isPlayerNearby,
  }
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil and _G.__SHIGUANG_SERVICES.smartObjects ~= nil then
    _G.__SHIGUANG_SERVICES.smartObjects[FacilityId] = nil
  end
end
