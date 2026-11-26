---@id 4f32bd33-448d-44f3-8e41-85327fff30eb
---@referenceName narrative-host.lua
---@displayName 时光小筑全局叙事宿主与存档状态机
---@start
---@var SaveKey:string="shiguang_town_save_v4"
---@name 存档键名
---@desc DouyinDataStore 持久化主键（严格控制单条上限 <6000 字节）
---@group 叙事宿主
---@var InitialChapter:string="prologue"
---@name 初始章节
---@desc 默认开启的叙事章回（prologue/ch1/ch2/ch3/ch4/epilogue）
---@group 叙事宿主
---@var AutoSaveInterval:number=45
---@name 自动保存间隔
---@desc 运行态周期性写入 DataStore 的秒数间隔
---@group 叙事宿主
---@var EnableDebugUnlockAll:boolean=false
---@name 全区预览模式
---@desc 开启后允许跳过软门控直接预览全 42 项设施
---@group 调试
---@end

local Time = CS.UnityEngine.Time
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("narrative-host")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local DATASTORE_MAX_BYTES = 6000
local INITIAL_AFFECTION = 25
local MAX_AFFECTION = 255
local CHAR_STAGE_MAX = 3

local CHAPTER_ORDER = { "prologue", "ch1", "ch2", "ch3", "ch4", "epilogue" }
local CHAPTER_RANK = {
  prologue = 0,
  ch1 = 1,
  ch2 = 2,
  ch3 = 3,
  ch4 = 4,
  epilogue = 5,
}

local RESIDENT_IDS = { "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09" }

local ZONE_UNLOCK_CHAPTER = {
  Zone0 = "prologue",
  ZoneW = "ch1",
  ZoneE = "ch2",
  ZoneN = "ch3",
  ZoneS = "ch4",
}

local state = {
  chapter = InitialChapter,
  warmFuzzies = 0,
  affection = {},
  charStages = {},
  visitedFacilities = {},
  collectedMemories = {},
  storyEvents = {},
  lingoPool = { "慢一点也没关系" },
  petName = "小白喵",
  flagTitle = "风铃湾小鱼旗",
  pixelFlag = "PF1:" .. string.rep("0", 144),
  weatherSeed = 20260416,
  facts = {
    chapter = InitialChapter,
    timeSlot = "afternoon",
    weather = "sunny",
    yesterdayAction = "none",
    zone = "Zone0",
    playerAbsentLong = false,
    asyncVisitMemory = false,
    directorSoftBias = false,
  },
}

local listeners = {}
local saveTimer = 0.0
local isInitialized = false

local function clampInt(val, minVal, maxVal)
  local num = math.floor(tonumber(val) or minVal)
  if num < minVal then return minVal end
  if num > maxVal then return maxVal end
  return num
end

local function ensureDefaults()
  if CHAPTER_RANK[state.chapter] == nil then
    state.chapter = "prologue"
  end
  state.facts.chapter = state.chapter
  for _, cid in ipairs(RESIDENT_IDS) do
    if state.affection[cid] == nil then
      state.affection[cid] = INITIAL_AFFECTION
    else
      state.affection[cid] = clampInt(state.affection[cid], 0, MAX_AFFECTION)
    end
    if state.charStages[cid] == nil then
      state.charStages[cid] = 0
    else
      state.charStages[cid] = clampInt(state.charStages[cid], 0, CHAR_STAGE_MAX)
    end
  end
end

local function emitSignal(signalName, payload)
  for _, cb in ipairs(listeners) do
    local ok, err = pcall(cb, signalName, payload)
    if not ok then
      logger:warn("叙事事件监听回调异常: " .. tostring(err))
    end
  end
end

function Subscribe(callback)
  if type(callback) ~= "function" then return false end
  table.insert(listeners, callback)
  return true
end

function GetChapterRank(chapterId)
  return CHAPTER_RANK[chapterId] or 0
end

function IsChapterReached(requiredChapter)
  if EnableDebugUnlockAll then return true end
  local need = CHAPTER_RANK[requiredChapter or "prologue"] or 0
  local cur = CHAPTER_RANK[state.chapter] or 0
  return cur >= need
end

function IsZoneUnlocked(zoneId)
  if EnableDebugUnlockAll then return true end
  local req = ZONE_UNLOCK_CHAPTER[zoneId or "Zone0"] or "prologue"
  return IsChapterReached(req)
end

local function countCollectedByPrefix(prefix)
  local n = 0
  for mid, got in pairs(state.collectedMemories) do
    if got and (prefix == nil or string.sub(mid, 1, #prefix) == prefix) then
      n = n + 1
    end
  end
  return n
end

local function countMapTrue(tbl)
  local n = 0
  for _, v in pairs(tbl) do
    if v == true then n = n + 1 end
  end
  return n
end

local function evaluateChapterProgression()
  local changed = true
  while changed do
    changed = false
    if state.chapter == "prologue" then
      local hasBoard = state.visitedFacilities["F08"] == true
      local hasBeach = state.visitedFacilities["F03"] == true
      local hasM01 = state.collectedMemories["M01"] == true
      local talked = (state.facts.talkCount or 0) >= 2
      if (hasBoard and hasBeach and hasM01) or (hasM01 and talked) then
        state.chapter = "ch1"
        state.facts.chapter = "ch1"
        state.storyEvents["west_alley_opened"] = true
        emitSignal("chapter_unlocked", { chapter = "ch1", zone = "ZoneW" })
        logger:info("软门控解除：进入第一章《未寄出的海风信》，ZoneW 开放")
        changed = true
      end
    elseif state.chapter == "ch1" then
      local hasPost = state.visitedFacilities["F19"] == true
      local hasLight = state.storyEvents["lighthouse_relight"] == true
      if hasPost and hasLight then
        state.chapter = "ch2"
        state.facts.chapter = "ch2"
        state.storyEvents["fast_travel_unlocked"] = true
        emitSignal("chapter_unlocked", { chapter = "ch2", zone = "ZoneE" })
        logger:info("软门控解除：点亮西岬灯塔，进入第二章《搁浅的白昼号与夏夜烤包香》")
        changed = true
      end
    elseif state.chapter == "ch2" then
      local hasNight = state.visitedFacilities["F25"] == true
      local hasShip = state.storyEvents["lightship_relight"] == true
      local hasRose = state.storyEvents["blue_rose_bred"] == true
      if hasNight and hasShip and hasRose then
        state.chapter = "ch3"
        state.facts.chapter = "ch3"
        state.storyEvents["ferry_unlocked"] = true
        emitSignal("chapter_unlocked", { chapter = "ch3", zone = "ZoneN" })
        logger:info("软门控解除：白昼号亮灯且培育出蓝玫瑰，进入第三章《玻璃顶下的四季年谱》")
        changed = true
      end
    elseif state.chapter == "ch3" then
      local hasChron = state.storyEvents["chronicle_restored"] == true
      local hasVinyl = state.storyEvents["vinyl_played"] == true
      local totalMem = countMapTrue(state.collectedMemories)
      if hasChron and (hasVinyl or totalMem >= 10) then
        state.chapter = "ch4"
        state.facts.chapter = "ch4"
        state.storyEvents["crescent_loop_closed"] = true
        emitSignal("chapter_unlocked", { chapter = "ch4", zone = "ZoneS" })
        logger:info("软门控解除：海湾大闭环合龙，进入终章《潮汐退去后的回声音乐会》")
        changed = true
      end
    elseif state.chapter == "ch4" then
      local hasBell = state.storyEvents["summit_bell_rung"] == true
      local hasStage = state.visitedFacilities["F39"] == true
      if hasBell and hasStage then
        state.chapter = "epilogue"
        state.facts.chapter = "epilogue"
        emitSignal("chapter_unlocked", { chapter = "epilogue", zone = "ALL" })
        logger:info("终章回声音乐会落幕，切入无尽疗愈沙盒阶段")
        changed = true
      end
    end
  end
end

function GetBondTier(residentId)
  local val = state.affection[residentId] or INITIAL_AFFECTION
  if val >= 150 then return 5, "琥珀星砂挚友" end
  if val >= 100 then return 4, "心照不宣的怪友" end
  if val >= 60 then return 3, "茶桌搭子" end
  if val >= 30 then return 2, "海岸点头友" end
  return 1, "陌邻初识"
end

function GetPhotoDropProbability(residentId)
  local val = state.affection[residentId] or INITIAL_AFFECTION
  if val < 150 then return 0.0 end
  return val / 25.0
end

-- 零缺席惩罚：好感度永不因时间流逝而扣减，只保留积极增幅或喜剧微调
function AddAffection(residentId, delta, reason)
  if state.affection[residentId] == nil then return nil end
  local d = tonumber(delta) or 0
  if d < 0 and reason == "absence" then
    return state.affection[residentId]
  end
  local oldVal = state.affection[residentId]
  local newVal = clampInt(oldVal + d, 0, MAX_AFFECTION)
  state.affection[residentId] = newVal
  emitSignal("affection_changed", { residentId = residentId, old = oldVal, value = newVal, reason = reason })
  return newVal
end

function GetAffection(residentId)
  return state.affection[residentId] or INITIAL_AFFECTION
end

function GetCharStage(residentId)
  return state.charStages[residentId] or 0
end

function SetCharStage(residentId, stage)
  if state.charStages[residentId] == nil then return nil end
  local nextStage = clampInt(stage, 0, CHAR_STAGE_MAX)
  state.charStages[residentId] = nextStage
  emitSignal("char_stage_changed", { residentId = residentId, stage = nextStage })
  return nextStage
end

function AdvanceCharStage(residentId)
  local cur = GetCharStage(residentId)
  return SetCharStage(residentId, math.min(CHAR_STAGE_MAX, cur + 1))
end

function AddWarmFuzzies(amount, source)
  local gain = math.max(0, math.floor(tonumber(amount) or 0))
  state.warmFuzzies = state.warmFuzzies + gain
  emitSignal("warm_fuzzies_changed", { total = state.warmFuzzies, gain = gain, source = source })
  return state.warmFuzzies
end

function CollectMemory(memoryId, facilityId)
  if type(memoryId) ~= "string" or memoryId == "" then return false end
  local firstTime = state.collectedMemories[memoryId] ~= true
  state.collectedMemories[memoryId] = true
  if facilityId then
    state.visitedFacilities[facilityId] = true
  end
  if firstTime then
    AddWarmFuzzies(10, "memory:" .. memoryId)
    emitSignal("memory_collected", { memoryId = memoryId, facilityId = facilityId, total = countCollectedByPrefix(nil) })
    evaluateChapterProgression()
  end
  return firstTime
end

function VisitFacility(facilityId, zoneId)
  if type(facilityId) == "string" and facilityId ~= "" then
    state.visitedFacilities[facilityId] = true
  end
  if type(zoneId) == "string" and zoneId ~= "" then
    state.facts.zone = zoneId
  end
  evaluateChapterProgression()
end

function TriggerStoryEvent(eventKey)
  if type(eventKey) ~= "string" or eventKey == "" then return false end
  local isNew = state.storyEvents[eventKey] ~= true
  state.storyEvents[eventKey] = true
  if isNew then
    AddWarmFuzzies(15, "event:" .. eventKey)
    emitSignal("story_event_triggered", { eventKey = eventKey })
    evaluateChapterProgression()
  end
  return isNew
end

function SetFact(key, value)
  if type(key) ~= "string" or key == "" then return end
  state.facts[key] = value
  if key == "talkCount" then
    evaluateChapterProgression()
  end
  emitSignal("fact_updated", { key = key, value = value })
end

function GetFact(key)
  return state.facts[key]
end

function GetAllFacts()
  return state.facts
end

function AddLingo(phrase)
  if type(phrase) ~= "string" then return false end
  local clean = string.gsub(phrase, "[|\n\r;]", " ")
  clean = string.sub(clean, 1, 36)
  if clean == "" then return false end
  for _, existing in ipairs(state.lingoPool) do
    if existing == clean then return true end
  end
  table.insert(state.lingoPool, 1, clean)
  while #state.lingoPool > 8 do
    table.remove(state.lingoPool)
  end
  state.storyEvents["lingo_injected"] = true
  SetFact("yesterdayAction", "changed_chalkboard")
  emitSignal("lingo_updated", { phrase = clean })
  evaluateChapterProgression()
  return true
end

function SetPixelFlag(flagCode)
  if type(flagCode) ~= "string" or #flagCode > 220 then return false end
  state.pixelFlag = flagCode
  state.storyEvents["pixel_flag_customized"] = true
  SetFact("yesterdayAction", "changed_flag")
  emitSignal("pixel_flag_updated", { code = flagCode })
  evaluateChapterProgression()
  return true
end

function GetStateSnapshot()
  return state
end

-- 紧凑编码序列化（严格保证 < 6000 B，其中 charStages 仅占 ~14 B）
local function escapeVal(s)
  local str = tostring(s or "")
  str = string.gsub(str, "[|\n\r;=,]", " ")
  return str
end

local function encodeCharStagesCompact()
  local digits = {}
  for i, cid in ipairs(RESIDENT_IDS) do
    digits[i] = tostring(clampInt(state.charStages[cid] or 0, 0, CHAR_STAGE_MAX))
  end
  return table.concat(digits, "")
end

local function decodeCharStagesCompact(raw)
  if type(raw) ~= "string" then return end
  for i, cid in ipairs(RESIDENT_IDS) do
    local ch = string.sub(raw, i, i)
    local num = tonumber(ch)
    if num ~= nil then
      state.charStages[cid] = clampInt(num, 0, CHAR_STAGE_MAX)
    end
  end
end

local function encodeAffectionCompact()
  local parts = {}
  for i, cid in ipairs(RESIDENT_IDS) do
    parts[i] = tostring(clampInt(state.affection[cid] or INITIAL_AFFECTION, 0, MAX_AFFECTION))
  end
  return table.concat(parts, ",")
end

local function decodeAffectionCompact(raw)
  if type(raw) ~= "string" then return end
  local idx = 1
  for token in string.gmatch(raw, "[^,]+") do
    local cid = RESIDENT_IDS[idx]
    if cid ~= nil then
      state.affection[cid] = clampInt(token, 0, MAX_AFFECTION)
    end
    idx = idx + 1
  end
end

local function encodeKeySet(tbl)
  local keys = {}
  for k, v in pairs(tbl) do
    if v == true then
      table.insert(keys, escapeVal(k))
    end
  end
  table.sort(keys)
  return table.concat(keys, ",")
end

local function decodeKeySet(raw, target)
  if type(raw) ~= "string" or raw == "" then return end
  for token in string.gmatch(raw, "[^,]+") do
    target[token] = true
  end
end

function EncodeSaveData()
  ensureDefaults()
  local lingoStr = ""
  do
    local tmp = {}
    for i, item in ipairs(state.lingoPool) do
      tmp[i] = escapeVal(item)
    end
    lingoStr = table.concat(tmp, ",")
  end
  local fields = {
    "v=4",
    "ch=" .. escapeVal(state.chapter),
    "wf=" .. tostring(state.warmFuzzies),
    "af=" .. encodeAffectionCompact(),
    "cs=" .. encodeCharStagesCompact(),
    "vf=" .. encodeKeySet(state.visitedFacilities),
    "cm=" .. encodeKeySet(state.collectedMemories),
    "ev=" .. encodeKeySet(state.storyEvents),
    "lg=" .. lingoStr,
    "pn=" .. escapeVal(state.petName),
    "ft=" .. escapeVal(state.flagTitle),
    "pf=" .. escapeVal(state.pixelFlag),
    "ws=" .. tostring(state.weatherSeed),
    "ya=" .. escapeVal(state.facts.yesterdayAction),
  }
  local encoded = table.concat(fields, "|")
  if #encoded >= DATASTORE_MAX_BYTES then
    logger:warn("存档接近 6000B 上限，截断次要历史流行语池以保障写入成功")
    state.lingoPool = { state.lingoPool[1] or "慢一点也没关系" }
    fields[9] = "lg=" .. escapeVal(state.lingoPool[1])
    encoded = table.concat(fields, "|")
  end
  return encoded
end

function DecodeSaveData(encoded)
  if type(encoded) ~= "string" or encoded == "" then return false end
  for pair in string.gmatch(encoded, "[^|]+") do
    local eq = string.find(pair, "=", 1, true)
    if eq ~= nil then
      local k = string.sub(pair, 1, eq - 1)
      local v = string.sub(pair, eq + 1)
      if k == "ch" and CHAPTER_RANK[v] ~= nil then
        state.chapter = v
      elseif k == "wf" then
        state.warmFuzzies = math.max(0, math.floor(tonumber(v) or 0))
      elseif k == "af" then
        decodeAffectionCompact(v)
      elseif k == "cs" then
        decodeCharStagesCompact(v)
      elseif k == "vf" then
        decodeKeySet(v, state.visitedFacilities)
      elseif k == "cm" then
        decodeKeySet(v, state.collectedMemories)
      elseif k == "ev" then
        decodeKeySet(v, state.storyEvents)
      elseif k == "lg" and v ~= "" then
        local list = {}
        for item in string.gmatch(v, "[^,]+") do
          table.insert(list, item)
        end
        if #list > 0 then state.lingoPool = list end
      elseif k == "pn" and v ~= "" then
        state.petName = v
      elseif k == "ft" and v ~= "" then
        state.flagTitle = v
      elseif k == "pf" and v ~= "" then
        state.pixelFlag = v
      elseif k == "ws" then
        state.weatherSeed = tonumber(v) or state.weatherSeed
      elseif k == "ya" and v ~= "" then
        state.facts.yesterdayAction = v
      end
    end
  end
  ensureDefaults()
  return true
end

function EstimateSaveBytes()
  local payload = EncodeSaveData()
  return #payload, #encodeCharStagesCompact()
end

function SaveToDataStore()
  local payload = EncodeSaveData()
  if #payload > DATASTORE_MAX_BYTES then
    logger:error("存档序列化超出 DataStore 6000B 限制: " .. tostring(#payload))
    return false
  end
  local ds = DouyinDataStore or (CS and CS.DouyinDataStore)
  if ds ~= nil then
    local ok, err = pcall(function()
      if type(ds.SetAsync) == "function" then
        ds.SetAsync(SaveKey, payload)
      elseif type(ds.Set) == "function" then
        ds.Set(SaveKey, payload)
      end
    end)
    if not ok then
      logger:warnOnce("ds-save-warn", "DataStore 写入回退为内存保留", err)
      return false
    end
  end
  return true
end

function LoadFromDataStore()
  local ds = DouyinDataStore or (CS and CS.DouyinDataStore)
  if ds == nil then return false end
  local ok, raw = pcall(function()
    if type(ds.GetAsync) == "function" then
      return ds.GetAsync(SaveKey)
    elseif type(ds.Get) == "function" then
      return ds.Get(SaveKey)
    end
    return nil
  end)
  if ok and type(raw) == "string" and raw ~= "" then
    DecodeSaveData(raw)
    logger:info("已从 DataStore 加载存档，章回=" .. tostring(state.chapter))
    return true
  end
  return false
end

local function registerGlobalBridge()
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.narrativeHost = {
    Subscribe = Subscribe,
    IsChapterReached = IsChapterReached,
    IsZoneUnlocked = IsZoneUnlocked,
    GetBondTier = GetBondTier,
    GetPhotoDropProbability = GetPhotoDropProbability,
    AddAffection = AddAffection,
    GetAffection = GetAffection,
    GetCharStage = GetCharStage,
    SetCharStage = SetCharStage,
    AdvanceCharStage = AdvanceCharStage,
    AddWarmFuzzies = AddWarmFuzzies,
    CollectMemory = CollectMemory,
    VisitFacility = VisitFacility,
    TriggerStoryEvent = TriggerStoryEvent,
    SetFact = SetFact,
    GetFact = GetFact,
    GetAllFacts = GetAllFacts,
    AddLingo = AddLingo,
    SetPixelFlag = SetPixelFlag,
    GetStateSnapshot = GetStateSnapshot,
    EncodeSaveData = EncodeSaveData,
    DecodeSaveData = DecodeSaveData,
    EstimateSaveBytes = EstimateSaveBytes,
    SaveToDataStore = SaveToDataStore,
  }
end

function Start()
  ensureDefaults()
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "narrative-host 未取得 RuntimeScope（使用全局桥接模式）", runtimeScopeReason)
  end
  LoadFromDataStore()
  registerGlobalBridge()
  isInitialized = true
  local totalBytes, csBytes = EstimateSaveBytes()
  logger:info(string.format("时光小筑叙事宿主就绪: 章回=%s 存档=%dB (charStages=%dB)", state.chapter, totalBytes, csBytes))
end

function Update()
  if not isInitialized then return end
  saveTimer = saveTimer + Time.deltaTime
  if saveTimer >= math.max(10.0, AutoSaveInterval) then
    saveTimer = 0.0
    SaveToDataStore()
  end
end

function OnDestroy()
  if isInitialized then
    SaveToDataStore()
  end
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.narrativeHost = nil
  end
end
