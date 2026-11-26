---@id e61d5806-bc55-4463-8873-191b97209e4e
---@referenceName time-weather-lighting.lua
---@displayName 三时段雾效光影、确定性气象与灯塔夜市萤火控制
---@start
---@var TimeMode:string="auto"
---@name 时段模式
---@desc auto(按RTC时刻切换) / afternoon(14:00) / dusk(17:30) / night(21:00)
---@group 环境光影
---@var LighthouseBeamPath:string="F22_WestLighthouse/BeamPivot"
---@name 西岬灯塔光束节点路径
---@desc 相对作用域根的灯塔旋转光束节点路径
---@group 地标灯光
---@var NightMarketPath:string="F25_NightMarketKiln/StringLights"
---@name 夜市灯串节点路径
---@desc 相对作用域根的东湾夜市暖灯串节点路径
---@group 地标灯光
---@var FirefliesPath:string="F32_FireflyCreek/FireflyParticles"
---@name 溪谷萤火粒子路径
---@desc 相对作用域根的北麓溪谷萤火粒子根节点路径
---@group 地标灯光
---@var LighthouseSweepSpeed:number=30
---@name 灯塔旋转角速度
---@desc 度/秒（默认30度/秒对应12秒横扫整座月牙湾一圈）
---@group 地标灯光
---@end

local UnityEngine = CS.UnityEngine
local RenderSettings = UnityEngine.RenderSettings
local Color = UnityEngine.Color
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("time-weather-lighting")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 4× 地图适配雾效与环境参数（防止 80-120m 外地标被远雾吞没）
local ENV_PRESETS = {
  afternoon = {
    startFog = 45.0,
    endFog = 300.0,
    fogColor = Color(0.796, 0.918, 0.969, 1.0),    -- #CBEAF7
    ambientColor = Color(0.906, 0.941, 0.863, 1.0), -- #E7F0DC
    lighthouseActive = false,
    nightMarketActive = false,
    firefliesActive = false,
  },
  dusk = {
    startFog = 38.0,
    endFog = 260.0,
    fogColor = Color(0.961, 0.722, 0.620, 1.0),    -- #F5B89E
    ambientColor = Color(0.851, 0.655, 0.631, 1.0), -- #D9A7A1
    lighthouseActive = true,
    nightMarketActive = true,
    firefliesActive = false,
  },
  night = {
    startFog = 32.0,
    endFog = 230.0,
    fogColor = Color(0.165, 0.227, 0.361, 1.0),    -- #2A3A5C
    ambientColor = Color(0.435, 0.471, 0.659, 1.0), -- #6F78A8
    lighthouseActive = true,
    nightMarketActive = true,
    firefliesActive = true,
  },
}

local currentSlot = "afternoon"
local currentWeather = "sunny"
local lighthouseBeam = nil
local lighthouseBaseRot = nil
local beamAngle = 0.0
local nightMarketObj = nil
local firefliesObj = nil
local syncTimer = 0.0

local function getHost()
  if runtimeScope ~= nil then
    local host = runtimeScope:GetRuntimeHostScript("narrative-host.lua")
    if host ~= nil then return host end
  end
  return _G.__SHIGUANG_SERVICES and _G.__SHIGUANG_SERVICES.narrativeHost or nil
end

local function computeTimeSlot()
  if ENV_PRESETS[TimeMode] ~= nil then
    return TimeMode
  end
  local dt = os.date("*t")
  local hour = (dt ~= nil and dt.hour) or 14
  if hour >= 16 and hour < 19 then
    return "dusk"
  elseif hour >= 19 or hour < 6 then
    return "night"
  end
  return "afternoon"
end

-- 确定性气象种子：修改本地时钟不洗牌长期气象序列
local function computeDeterministicWeather(seed, slot)
  if slot == "night" then
    return "starlight"
  end
  local dt = os.date("*t")
  local dayHash = ((dt and dt.yday or 100) * 131 + (seed or 20260416)) % 100
  if dayHash < 52 then return "sunny" end
  if dayHash < 82 then return "breeze" end
  return "rain"
end

local function setActiveSafe(go, active)
  if go == nil then return end
  pcall(function()
    if go.activeSelf ~= active then
      go:SetActive(active)
    end
  end)
end

local function applyEnvironment(slot)
  local preset = ENV_PRESETS[slot] or ENV_PRESETS.afternoon
  pcall(function()
    RenderSettings.fog = true
    RenderSettings.fogStartDistance = preset.startFog
    RenderSettings.fogEndDistance = preset.endFog
    RenderSettings.fogColor = preset.fogColor
    RenderSettings.ambientLight = preset.ambientColor
  end)

  local host = getHost()
  local snap = host ~= nil and host.GetStateSnapshot() or nil
  local events = snap ~= nil and snap.storyEvents or {}
  local lighthouseLit = events["lighthouse_relight"] == true or (host ~= nil and host.IsChapterReached("ch2"))
  local marketLit = events["lightship_relight"] == true or (host ~= nil and host.IsChapterReached("ch2"))
  local creekLit = host ~= nil and host.IsChapterReached("ch3")

  if lighthouseBeam ~= nil then
    setActiveSafe(lighthouseBeam.gameObject, preset.lighthouseActive and lighthouseLit)
  end
  setActiveSafe(nightMarketObj, preset.nightMarketActive and marketLit)
  setActiveSafe(firefliesObj, preset.firefliesActive and creekLit)
end

function SetTimeSlotOverride(slot)
  if ENV_PRESETS[slot] ~= nil or slot == "auto" then
    TimeMode = slot
    currentSlot = computeTimeSlot()
    local host = getHost()
    local seed = (host ~= nil and host.GetStateSnapshot().weatherSeed) or 20260416
    currentWeather = computeDeterministicWeather(seed, currentSlot)
    if host ~= nil then
      host.SetFact("timeSlot", currentSlot)
      host.SetFact("weather", currentWeather)
    end
    applyEnvironment(currentSlot)
    logger:info(string.format("环境光影切换: %s (fog %.0f/%.0fm, 天气=%s)",
      currentSlot, ENV_PRESETS[currentSlot].startFog, ENV_PRESETS[currentSlot].endFog, currentWeather))
    return true
  end
  return false
end

function GetEnvironmentState()
  local preset = ENV_PRESETS[currentSlot] or ENV_PRESETS.afternoon
  return {
    timeSlot = currentSlot,
    weather = currentWeather,
    startFog = preset.startFog,
    endFog = preset.endFog,
    beamAngle = beamAngle,
  }
end

local function cacheNodes()
  if runtimeScope == nil then return end
  lighthouseBeam = runtimeScope:GetTransformByPath(LighthouseBeamPath)
  if lighthouseBeam ~= nil then
    lighthouseBaseRot = lighthouseBeam.localRotation
  end
  nightMarketObj = runtimeScope:GetGameObjectByPath(NightMarketPath)
  firefliesObj = runtimeScope:GetGameObjectByPath(FirefliesPath)
end

function Start()
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "time-weather-lighting 未取得 RuntimeScope", runtimeScopeReason)
  end
  cacheNodes()
  SetTimeSlotOverride(TimeMode)
  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.environment = {
    SetTimeSlotOverride = SetTimeSlotOverride,
    GetEnvironmentState = GetEnvironmentState,
  }
end

function Update()
  local dt = Time.deltaTime
  syncTimer = syncTimer + dt
  if syncTimer >= 10.0 then
    syncTimer = 0.0
    local nextSlot = computeTimeSlot()
    if nextSlot ~= currentSlot then
      SetTimeSlotOverride(TimeMode)
    end
  end

  local preset = ENV_PRESETS[currentSlot] or ENV_PRESETS.afternoon
  if lighthouseBeam ~= nil and lighthouseBaseRot ~= nil and preset.lighthouseActive then
    beamAngle = (beamAngle + LighthouseSweepSpeed * dt) % 360.0
    lighthouseBeam.localRotation = lighthouseBaseRot * Quaternion.Euler(0, beamAngle, 0)
  end
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.environment = nil
  end
end
