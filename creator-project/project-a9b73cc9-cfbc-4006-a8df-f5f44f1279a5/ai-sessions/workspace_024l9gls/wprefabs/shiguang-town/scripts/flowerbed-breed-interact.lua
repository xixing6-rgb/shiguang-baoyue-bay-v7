---@id c2bf26b4-0bf1-4901-9466-2aeb83d597e5
---@referenceName flowerbed-breed-interact.lua
---@displayName 杂交花圃色系培育
---@start
---@var InteractDistance:number=4.5
---@name 培育触发距离
---@desc 玩家靠近花圃可按 E 或首次进入自动杂交的距离
---@group 交互
---@var AutoTriggerOnFirstVisit:boolean=true
---@name 首次靠近自动触发
---@desc 玩家第一次走近花圃时自动示范一次花色杂交
---@group 交互
---@var CooldownSeconds:number=0.8
---@name 操作冷却时间
---@desc 两次杂交培育之间的最小间隔秒数
---@group 交互
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Color = UnityEngine.Color
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local Time = UnityEngine.Time
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("flowerbed-breed")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 孟德尔双基因配色表（R/Y/B 组合，兼容 URP _BaseColor 与标准 _Color）
local MENDEL_PALETTE = {
  { name = "珊瑚红(RR)", color = Color(0.95, 0.38, 0.42, 1.0) },
  { name = "暖金黄(YY)", color = Color(0.98, 0.80, 0.30, 1.0) },
  { name = "丁香紫(RY)", color = Color(0.76, 0.56, 0.94, 1.0) },
  { name = "樱桃粉(RW)", color = Color(0.98, 0.62, 0.76, 1.0) },
  { name = "晴空蓝(BB)", color = Color(0.45, 0.76, 0.96, 1.0) },
  { name = "蜜桃橙(OY)", color = Color(0.98, 0.58, 0.34, 1.0) },
  { name = "奶霜白(WW)", color = Color(0.98, 0.94, 0.86, 1.0) },
}

local blooms = {}
local breedCount = 0
local paletteCursor = 1
local bloomCursor = 1
local firstAutoDone = false
local wasInteractPressed = false
local lastTriggerAt = -10.0
local lastDistance = 999.0
local lastBreedLabel = "初始配色"

local function applyBloomColor(entry, colorVal)
  if entry == nil or entry.renderers == nil then return end
  for _, renderer in ipairs(entry.renderers) do
    if renderer ~= nil then
      local mat = renderer.material
      if mat ~= nil then
        if mat:HasProperty("_BaseColor") then
          mat:SetColor("_BaseColor", colorVal)
        elseif mat:HasProperty("_Color") then
          mat:SetColor("_Color", colorVal)
        end
      end
    end
  end
end

local function cacheBlooms()
  blooms = {}
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "花圃脚本无法取得 RuntimeScope", runtimeScopeReason)
    return
  end
  for i = 1, 12 do
    local name = string.format("FlowerBloom_%02d", i)
    local go, reason = runtimeScope:GetGameObjectByPath(name)
    if go ~= nil then
      local renderers = {}
      local arr = go:GetComponentsInChildren(typeof(UnityEngine.Renderer))
      if arr ~= nil then
        for idx = 0, arr.Length - 1 do
          local r = arr[idx]
          if r ~= nil and string.find(r.gameObject.name, "BloomPetal", 1, true) ~= nil then
            table.insert(renderers, r)
          end
        end
        if #renderers == 0 then
          for idx = 0, arr.Length - 1 do
            table.insert(renderers, arr[idx])
          end
        end
      end
      table.insert(blooms, {
        name = name,
        transform = go.transform,
        baseScale = go.transform.localScale,
        pulseTimer = 0.0,
        renderers = renderers
      })
    else
      logger:warnOnce("bloom-missing-" .. name, "未找到花朵节点: " .. name, reason)
    end
  end
end

function TriggerCrossBreed()
  if #blooms < 2 then return false end
  local now = Time.time
  if (now - lastTriggerAt) < CooldownSeconds then return false end
  lastTriggerAt = now

  local idxA = bloomCursor
  local idxB = ((bloomCursor + 5) % #blooms) + 1
  bloomCursor = (bloomCursor % #blooms) + 1

  local palA = MENDEL_PALETTE[((paletteCursor - 1) % #MENDEL_PALETTE) + 1]
  local palB = MENDEL_PALETTE[((paletteCursor + 1) % #MENDEL_PALETTE) + 1]
  paletteCursor = paletteCursor + 1

  applyBloomColor(blooms[idxA], palA.color)
  applyBloomColor(blooms[idxB], palB.color)
  blooms[idxA].pulseTimer = 0.45
  blooms[idxB].pulseTimer = 0.45

  breedCount = breedCount + 1
  lastBreedLabel = string.format("%s->%s & %s->%s", blooms[idxA].name, palA.name, blooms[idxB].name, palB.name)
  logger:info(string.format("完成第 %d 次花色杂交: %s", breedCount, lastBreedLabel))
  return true
end

local function getLocalPlayerPosition()
  if PlayerService == nil then return nil end
  local player = PlayerService.GetLocalPlayer()
  if player == nil then return nil end
  local actor = player:GetActor()
  if actor == nil then return nil end
  return actor.position
end

function Start()
  cacheBlooms()
  logger:info(string.format("杂交花圃初始化完成，缓存花株数=%d", #blooms))
end

function Update()
  local dt = Time.deltaTime
  local interactPressed = Input.GetKey(KeyCode.E)
  local interactStarted = interactPressed and not wasInteractPressed
  wasInteractPressed = interactPressed
  for _, entry in ipairs(blooms) do
    if entry.pulseTimer > 0 then
      entry.pulseTimer = math.max(0.0, entry.pulseTimer - dt)
      local boost = 1.0 + 0.30 * math.sin((entry.pulseTimer / 0.45) * math.pi)
      entry.transform.localScale = entry.baseScale * boost
    end
  end

  local playerPos = getLocalPlayerPosition()
  if playerPos ~= nil then
    local center = self.transform.position
    local dx = playerPos.x - center.x
    local dz = playerPos.z - center.z
    lastDistance = math.sqrt(dx * dx + dz * dz)

    if lastDistance <= InteractDistance then
      if AutoTriggerOnFirstVisit and not firstAutoDone then
        firstAutoDone = true
        TriggerCrossBreed()
      elseif interactStarted then
        TriggerCrossBreed()
      end
    end
  end
end

function GetBreedState()
  return {
    bloomCount = #blooms,
    breedCount = breedCount,
    distance = lastDistance,
    lastBreedLabel = lastBreedLabel
  }
end
