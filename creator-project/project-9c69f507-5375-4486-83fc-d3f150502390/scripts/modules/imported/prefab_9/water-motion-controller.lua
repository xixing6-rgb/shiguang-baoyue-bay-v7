---@id 8675f2dc-c8df-45f9-9c82-10afcce9decb
---@sourceScriptId 3773693c-b4e6-43da-b6f1-a666317df8b8
---@referenceName water-motion-controller.lua
---@displayName 水面多层动效与涟漪特效
---@start
---@var WaterRippleEffect:UnityEngine.GameObject=nil
---@name 水面涟漪特效
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Vector2 = UnityEngine.Vector2
local Color = UnityEngine.Color
local Time = UnityEngine.Time
local RendererType = typeof(UnityEngine.Renderer)
local Effect = require("official.effect.playback")
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("water-motion")
local runtimeScope = RuntimeScope.from(self)

local lagoonTr = nil
local foamInnerTr = nil
local foamOuterTr = nil
local sparkleTr = nil
local windmillBladesTr = nil
local swingPivotTr = nil

local lagoonBasePos = nil
local foamInnerBasePos = nil
local foamInnerBaseScale = nil
local foamOuterBasePos = nil
local foamOuterBaseScale = nil
local sparkleBasePos = nil

local lagoonMat = nil
local sparkleMat = nil
local origSparkleEmission = nil
local origSparkleHadEmission = false

local ambientAnchors = {}
local ambientHandles = {}
local ambientSpawned = false
local animTime = 0.0
local stepRippleCooldown = 0.0
local stepRippleCount = 0

local function ensureSharedBus()
  if _G.SHIGUANG_25D == nil then
    _G.SHIGUANG_25D = {}
  end
  return _G.SHIGUANG_25D
end

local function findInSiblings(nameSubstr)
  local rootTr = self.transform.parent or self.transform
  local stack = { rootTr }
  while #stack > 0 do
    local tr = table.remove(stack)
    local n = tr.name or ""
    if n == nameSubstr or string.find(n, nameSubstr, 1, true) ~= nil then
      return tr
    end
    for i = 0, tr.childCount - 1 do
      table.insert(stack, tr:GetChild(i))
    end
  end
  return nil
end

local function cacheNodes()
  lagoonTr = findInSiblings("WindWaker_Lagoon_Shallows")
  foamInnerTr = findInSiblings("WW_WaveFoam_Inner")
  foamOuterTr = findInSiblings("WW_WaveFoam_Outer")
  sparkleTr = findInSiblings("WW_SeaSparkle_Layer")
  windmillBladesTr = findInSiblings("F15_BladesPivot")
  swingPivotTr = findInSiblings("F14_SwingPivot")

  if lagoonTr ~= nil then
    lagoonBasePos = lagoonTr.localPosition
    local r = lagoonTr.gameObject:GetComponent(RendererType)
    if r ~= nil then lagoonMat = r.material end
  end
  if foamInnerTr ~= nil then
    foamInnerBasePos = foamInnerTr.localPosition
    foamInnerBaseScale = foamInnerTr.localScale
  end
  if foamOuterTr ~= nil then
    foamOuterBasePos = foamOuterTr.localPosition
    foamOuterBaseScale = foamOuterTr.localScale
  end
  if sparkleTr ~= nil then
    sparkleBasePos = sparkleTr.localPosition
    local r = sparkleTr.gameObject:GetComponent(RendererType)
    if r ~= nil and r.material ~= nil then
      sparkleMat = r.material
      if sparkleMat:HasProperty("_EmissionColor") then
        origSparkleEmission = sparkleMat:GetColor("_EmissionColor")
        origSparkleHadEmission = sparkleMat:IsKeywordEnabled("_EMISSION")
      end
    end
  end

  -- Ambient water ripple locations (fountain basin, fishing pier tip, west bridge water)
  ambientAnchors = {}
  local fountainTr = findInSiblings("F09_WishFountain")
  if fountainTr ~= nil then
    table.insert(ambientAnchors, { tr = fountainTr, offset = Vector3(0, 0.55, 0), scale = 0.85 })
  end
  local pierTr = findInSiblings("F02_FishingPier")
  if pierTr ~= nil then
    table.insert(ambientAnchors, { tr = pierTr, offset = Vector3(0, -0.18, -2.8), scale = 1.15 })
  end
end

local function trySpawnAmbientRipples()
  if ambientSpawned or WaterRippleEffect == nil then return end
  if #ambientAnchors == 0 then
    ambientSpawned = true
    return
  end
  local allCreated = true
  for _, anc in ipairs(ambientAnchors) do
    local wpos = anc.tr:TransformPoint(anc.offset)
    local handle, reason = Effect.create(self.gameObject, WaterRippleEffect, wpos, {
      scale = anc.scale,
      parent = self.gameObject,
    })
    if handle ~= nil then
      handle:Play()
      table.insert(ambientHandles, handle)
    else
      allCreated = false
      if reason ~= Effect.Reason.NotReady then
        logger:warnOnce("ambient-ripple-" .. tostring(reason), "环境涟漪初始化跳过:", reason)
        allCreated = true
      end
    end
  end
  if allCreated then
    ambientSpawned = true
  end
end

function SpawnWaterStepRipple(worldPos)
  if WaterRippleEffect == nil or worldPos == nil or stepRippleCooldown > 0.0 then
    return false
  end
  stepRippleCooldown = 0.28
  local pos = Vector3(worldPos.x, worldPos.y + 0.04, worldPos.z)
  local copy = Effect.spawn(self.gameObject, WaterRippleEffect, pos, { scale = 0.65 })
  if copy ~= nil then
    stepRippleCount = stepRippleCount + 1
    return true
  end
  return false
end

function Start()
  cacheNodes()
  local bus = ensureSharedBus()
  bus.SpawnWaterStepRipple = SpawnWaterStepRipple
  bus.GetWaterMotionState = GetWaterMotionState
  trySpawnAmbientRipples()
  logger:info("水面多层动效控制器就绪")
end

function Update()
  local dt = Time.deltaTime
  animTime = animTime + dt
  if stepRippleCooldown > 0.0 then
    stepRippleCooldown = stepRippleCooldown - dt
  end

  if not ambientSpawned then
    trySpawnAmbientRipples()
  end

  -- 1. Lagoon shallows gentle tidal heave & UV drift
  if lagoonTr ~= nil and lagoonBasePos ~= nil then
    local dy = 0.030 * math.sin(animTime * 1.35)
    local dx = 0.22 * math.sin(animTime * 0.55)
    local dz = 0.18 * math.cos(animTime * 0.45)
    lagoonTr.localPosition = Vector3(lagoonBasePos.x + dx, lagoonBasePos.y + dy, lagoonBasePos.z + dz)
    if lagoonMat ~= nil then
      pcall(function()
        lagoonMat.mainTextureOffset = Vector2(animTime * 0.008, animTime * 0.005)
      end)
    end
  end

  -- 2. Double coastal foam wave surge (out-of-phase breathing along shore)
  if foamInnerTr ~= nil and foamInnerBasePos ~= nil and foamInnerBaseScale ~= nil then
    local w1 = math.sin(animTime * 1.85)
    local s1 = 1.0 + 0.007 * w1
    foamInnerTr.localPosition = Vector3(foamInnerBasePos.x, foamInnerBasePos.y + 0.025 * w1, foamInnerBasePos.z)
    foamInnerTr.localScale = Vector3(foamInnerBaseScale.x * s1, foamInnerBaseScale.y, foamInnerBaseScale.z * s1)
  end
  if foamOuterTr ~= nil and foamOuterBasePos ~= nil and foamOuterBaseScale ~= nil then
    local w2 = math.sin(animTime * 1.85 - 1.35)
    local s2 = 1.0 + 0.009 * w2
    foamOuterTr.localPosition = Vector3(foamOuterBasePos.x, foamOuterBasePos.y + 0.022 * w2, foamOuterBasePos.z)
    foamOuterTr.localScale = Vector3(foamOuterBaseScale.x * s2, foamOuterBaseScale.y, foamOuterBaseScale.z * s2)
  end

  -- 3. Sea sparkle layer shimmer & drift
  if sparkleTr ~= nil and sparkleBasePos ~= nil then
    local dx = 0.45 * math.sin(animTime * 0.72)
    local dz = 0.35 * math.cos(animTime * 0.61)
    local dy = 0.018 * math.sin(animTime * 2.1)
    sparkleTr.localPosition = Vector3(sparkleBasePos.x + dx, sparkleBasePos.y + dy, sparkleBasePos.z + dz)
    if sparkleMat ~= nil and sparkleMat:HasProperty("_EmissionColor") then
      local glow = 0.22 + 0.16 * (0.5 + 0.5 * math.sin(animTime * 2.6))
      sparkleMat:SetColor("_EmissionColor", Color(0.88 * glow, 0.98 * glow, 1.0 * glow, 1.0))
      sparkleMat:EnableKeyword("_EMISSION")
    end
  end

  -- 4. Gentle windmill rotation & pergola swing motion
  if windmillBladesTr ~= nil then
    local cur = windmillBladesTr.localEulerAngles
    windmillBladesTr.localEulerAngles = Vector3(cur.x, cur.y, (animTime * 26.0) % 360.0)
  end
  if swingPivotTr ~= nil then
    local ang = 8.0 * math.sin(animTime * 1.5)
    swingPivotTr.localEulerAngles = Vector3(ang, 0.0, 0.0)
  end
end

function OnDestroy()
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.SpawnWaterStepRipple = nil
    _G.SHIGUANG_25D.GetWaterMotionState = nil
  end
  for _, h in ipairs(ambientHandles) do
    pcall(function()
      h:Stop()
      h:Release()
    end)
  end
  ambientHandles = {}
  if sparkleMat ~= nil and origSparkleEmission ~= nil and sparkleMat:HasProperty("_EmissionColor") then
    pcall(function()
      sparkleMat:SetColor("_EmissionColor", origSparkleEmission)
      if not origSparkleHadEmission then
        sparkleMat:DisableKeyword("_EMISSION")
      end
    end)
  end
end

function GetWaterMotionState()
  return {
    hasLagoon = lagoonTr ~= nil,
    hasFoamInner = foamInnerTr ~= nil,
    hasFoamOuter = foamOuterTr ~= nil,
    hasSparkle = sparkleTr ~= nil,
    hasWindmill = windmillBladesTr ~= nil,
    hasSwing = swingPivotTr ~= nil,
    hasEffectAsset = WaterRippleEffect ~= nil,
    ambientCount = #ambientHandles,
    stepRippleCount = stepRippleCount,
    animTime = animTime,
    foamInnerPosY = foamInnerTr ~= nil and foamInnerTr.localPosition.y or nil,
    lagoonPosY = lagoonTr ~= nil and lagoonTr.localPosition.y or nil,
  }
end
