---@id aa688053-4c66-4453-aa10-f308cdbe31d7
---@sourceScriptId a6f0e648-8ca8-4b14-89fa-df5b01c9d55a
---@referenceName farming-plot-system.lua
---@start
---@var InteractRangeMeters:number=2.45
---@name 田地交互距离
---@desc 玩家靠近菜地格可播种/浇水/收获的最大水平距离
---@group 轻种菜
---@var SaveKey:string="shiguang_25d_farm_v1"
---@name 存档主键
---@desc DouyinDataStore 轻存档 Key
---@group 轻种菜
---@end

local UnityEngine = CS.UnityEngine
local Time = UnityEngine.Time
local DataStore = DouyinDataStore or (CS and CS.DouyinDataStore)

local CROPS = {
  { id = "radish", label = "小红萝卜", growSec = 25.0, value = 12, nodeSuffix = "Stage3_Radish" },
  { id = "berry", label = "甜草莓", growSec = 35.0, value = 18, nodeSuffix = "Stage3_Berry" },
  { id = "sunflower", label = "向日葵", growSec = 45.0, value = 25, nodeSuffix = "Stage3_Sunflower" },
}

local CROP_BY_ID = {}
for _, c in ipairs(CROPS) do
  CROP_BY_ID[c.id] = c
end

local PART_SUFFIXES = {
  "SoilDry",
  "SoilWet",
  "Stage1_Sprout",
  "Stage2_Growing",
  "Stage3_Radish",
  "Stage3_Berry",
  "Stage3_Sunflower",
}

local plots = {}
local bag = { radish = 0, berry = 0, sunflower = 0 }
local coins = 0
local selectedSeedIdx = 1
local initialized = false
local autosaveTimer = 0.0
local lastStageCheck = {}

local function ensureSharedBus()
  if _G.SHIGUANG_25D == nil then
    _G.SHIGUANG_25D = {}
  end
  return _G.SHIGUANG_25D
end

local function setGoActive(go, active)
  if go ~= nil then
    pcall(function()
      if go.activeSelf ~= active then
        go:SetActive(active)
      end
    end)
  end
end

local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local HumanBodyBones = UnityEngine.HumanBodyBones
local ActorService = DouyinActorService or CS.DouyinActorService
local cropProps = {}
local HARVEST_PROPS = {
  radish = { node = "Harvest_Radish_Prop", scale = 0.50, liftScale = 0.06, gripDrop = 0.060, yaw = 0, roll = -20 },
  berry = { node = "Harvest_Strawberry_Prop", scale = 0.63, liftScale = 0.07, gripDrop = 0.065, yaw = 25, roll = -15 },
  sunflower = { node = "Harvest_Sunflower_Prop", scale = 0.39, liftScale = 0.04, gripDrop = 0.105, yaw = -20, roll = -24 },
}
local celebration
local warnedAboutCelebration = false
local HARVEST_DURATION = 2.05
local TAKEOFF_AT = 0.46
local FLIGHT_TIME = 0.58
local ARM_BONES = {
  { "LeftUpperArm", "LeftLowerArm", "LeftHand", -1 },
  { "RightUpperArm", "RightLowerArm", "RightHand", 1 },
}

local LEG_BONES = {
  { "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", -1 },
  { "RightUpperLeg", "RightLowerLeg", "RightFoot", 1 },
}

local function alive(object)
  return object ~= nil and not object:Equals(nil)
end

local function smoothStep(from, to, time)
  local t = math.max(0, math.min(1, (time - from) / (to - from)))
  return t * t * (3 - 2 * t)
end

local function restoreHarvestPose()
  if celebration == nil or celebration.pose == nil then return end
  for _, original in ipairs(celebration.pose) do
    if alive(original.bone) then
      original.bone.localPosition = original.position
      original.bone.localRotation = original.rotation
    end
  end
  celebration.pose = nil
end

local function finishHarvestCelebration()
  restoreHarvestPose()
  local action = celebration
  celebration = nil
  if action ~= nil and alive(action.prop) then setGoActive(action.prop.gameObject, false) end
end

local function startHarvestCelebration(cropId, plotTransform)
  local prop = cropProps[cropId]
  local grip = HARVEST_PROPS[cropId]
  if not alive(prop) or not alive(plotTransform) or ActorService == nil then return end
  local actor = ActorService.GetLocalActor()
  if actor == nil or not alive(actor.gameObject) or not actor:IsGrounded() then return end
  local hips = actor:GetBoneTransform(HumanBodyBones.Hips)
  local chest = actor:GetBoneTransform(HumanBodyBones.Chest)
  local head = actor:GetBoneTransform(HumanBodyBones.Head)
  if not alive(hips) or not alive(hips.parent) or not alive(chest) or not alive(head) then return end
  local avatar = hips:GetComponentInParent(typeof(UnityEngine.Animator))
  if not alive(avatar) or hips.parent == actor.gameObject.transform then return end

  local arms = {}
  for _, names in ipairs(ARM_BONES) do
    local upper = actor:GetBoneTransform(HumanBodyBones[names[1]])
    local lower = actor:GetBoneTransform(HumanBodyBones[names[2]])
    local hand = actor:GetBoneTransform(HumanBodyBones[names[3]])
    if not alive(upper) or not alive(lower) or not alive(hand) then return end
    arms[#arms + 1] = { upper = upper, lower = lower, hand = hand, side = names[4] }
  end

  local legs = {}
  for _, names in ipairs(LEG_BONES) do
    local upper = actor:GetBoneTransform(HumanBodyBones[names[1]])
    local lower = actor:GetBoneTransform(HumanBodyBones[names[2]])
    local foot = actor:GetBoneTransform(HumanBodyBones[names[3]])
    if not alive(upper) or not alive(lower) or not alive(foot) then return end
    legs[#legs + 1] = { upper = upper, lower = lower, hand = foot, side = names[4] }
  end

  finishHarvestCelebration()
  local player = actor.gameObject.transform
  local planted = plotTransform.position
  local delta = planted - player.position
  local flat = Vector3(delta.x, 0, delta.z)
  local direction = flat.sqrMagnitude > 0.01 and flat.normalized or avatar.transform.forward
  celebration = {
    root = hips.parent, avatar = avatar.transform, actor = actor, player = player,
    direction = direction, chest = chest, head = head, arms = arms, legs = legs,
    started = Time.time, bodyWeight = 1, prop = prop, grip = grip,
  }
end

local function aimBone(bone, child, target)
  local from = child.position - bone.position
  local to = target - bone.position
  if from.sqrMagnitude > 0.000001 and to.sqrMagnitude > 0.000001 then
    bone.rotation = Quaternion.FromToRotation(from, to) * bone.rotation
  end
end

local function poseLimb(arm, target, pole)
  local shoulder = arm.upper.position
  local offset = target - shoulder
  if offset.sqrMagnitude < 0.000001 then return end
  local axis = offset.normalized
  local upper = Vector3.Distance(shoulder, arm.lower.position)
  local lower = Vector3.Distance(arm.lower.position, arm.hand.position)
  if upper < 0.001 or lower < 0.001 then return end
  local distance = math.max(math.abs(upper - lower) + 0.0005,
    math.min(offset.magnitude, upper + lower - 0.0005))
  local along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
  local bend = math.sqrt(math.max(0, upper * upper - along * along))
  local normal = (pole - axis * Vector3.Dot(pole, axis)).normalized
  aimBone(arm.upper, arm.lower, shoulder + axis * along + normal * bend)
  aimBone(arm.lower, arm.hand, shoulder + axis * distance)
end

local function animateHarvest()
  local action = celebration
  local time = Time.time - action.started
  if time >= HARVEST_DURATION or not alive(action.player) or not alive(action.root)
      or not alive(action.prop) then
    finishHarvestCelebration()
    return
  end
  local grounded = action.actor:IsGrounded()
  -- A player-initiated jump can provide the takeoff; there is only one automatic request.
  if not grounded and action.tookOff == nil then
    action.tookOff = time
  elseif grounded and action.tookOff ~= nil and action.landed == nil then
    action.landed = time
  end
  if grounded and time >= TAKEOFF_AT and not action.jumpRequested and action.tookOff == nil then
    action.jumpRequested = true
    action.actor:Jump()
  end

  local velocity = action.actor.velocity
  local moving = velocity.x * velocity.x + velocity.z * velocity.z > 0.18
  local goal = (moving or (action.landed ~= nil and not grounded)) and 0 or 1
  action.bodyWeight = UnityEngine.Mathf.MoveTowards(action.bodyWeight, goal, Time.deltaTime * 12)

  action.pose = {}
  local function remember(bone)
    action.pose[#action.pose + 1] = { bone = bone, position = bone.localPosition, rotation = bone.localRotation }
  end
  remember(action.root)
  remember(action.chest)
  remember(action.head)
  for _, arm in ipairs(action.arms) do
    remember(arm.upper)
    remember(arm.lower)
  end
  for _, leg in ipairs(action.legs) do
    remember(leg.upper)
    remember(leg.lower)
  end

  local release = smoothStep(1.86, HARVEST_DURATION, time)
  local face = smoothStep(0.0, 0.20, time) * (1 - release) * action.bodyWeight
  local direction = Vector3.Slerp(action.avatar.forward, action.direction, face)
  local jumpStart = action.tookOff or TAKEOFF_AT
  local jumpEnd = action.landed or (jumpStart + FLIGHT_TIME)
  local phase = math.max(0, math.min(1, (time - jumpStart) / math.max(0.15, jumpEnd - jumpStart)))
  -- Fade the shortest remaining yaw so a running player keeps a forward-facing gait.
  local turn = 360 * smoothStep(0, 1, phase)
  local spin = (turn > 180 and turn - 360 or turn) * action.bodyWeight
  local spinRotation = Quaternion.AngleAxis(spin, Vector3.up)
  local forward = spinRotation * direction
  local right = Vector3.Cross(Vector3.up, forward).normalized
  local angle = Vector3.SignedAngle(action.avatar.forward, direction, Vector3.up)
  local air = math.sin(math.pi * phase)
  local landingStart = action.landed or (TAKEOFF_AT + FLIGHT_TIME)
  local land = smoothStep(landingStart - 0.025, landingStart + 0.085, time)
    - smoothStep(landingStart + 0.085, landingStart + 0.25, time)
  local pickupDip = smoothStep(0.0, 0.23, time) - smoothStep(0.25, 0.39, time)
  local launchDip = smoothStep(0.32, 0.40, time) - smoothStep(0.40, TAKEOFF_AT + 0.025, time)
  local crouch = (0.080 * pickupDip + 0.083 * launchDip + 0.076 * land) * action.bodyWeight
  local fallbackLift = action.tookOff == nil and air * 0.20 * action.bodyWeight or 0
  action.root.position = action.root.position + Vector3.up * (fallbackLift - crouch)
  action.root.rotation = Quaternion.AngleAxis(spin + angle, Vector3.up) * action.root.rotation

  for _, leg in ipairs(action.legs) do
    local tuck = air * (leg.side == 1 and 0.067 or 0.045) * action.bodyWeight
    local target = leg.hand.position + Vector3.up * (crouch + tuck) - forward * (tuck * 0.60)
    if action.bodyWeight > 0.01 and (crouch > 0.001 or tuck > 0.001) then
      poseLimb(leg, target, forward + right * (leg.side * 0.08))
    end
  end

  local show = smoothStep(landingStart + 0.04, landingStart + 0.34, time) * (1 - release)
  local reach = smoothStep(0, 0.22, time) * (1 - release)
  local lift = smoothStep(0.23, 0.43, time)
  action.chest.rotation = Quaternion.AngleAxis(crouch * 160 - show * 9, right) * action.chest.rotation
  action.head.rotation = Quaternion.AngleAxis(-air * 10 - show * 10, right) * action.head.rotation

  local chest = action.chest.position
  local carry = chest + forward * 0.12 + Vector3.up * -0.03
  local raised = action.arms[2].upper.position + forward * 0.105 + right * 0.103 + Vector3.up * 0.155
  local display = Vector3.Lerp(carry, raised, show)
  local pickup = chest + forward * 0.15 + Vector3.up * -0.105
  local hands = Vector3.Lerp(pickup, display, lift)
  for _, arm in ipairs(action.arms) do
    local grip = hands + right * (0.037 * arm.side)
    if arm.side == -1 then
      local outstretched = arm.upper.position - right * 0.16 + forward * 0.03 + Vector3.up * 0.026
      grip = Vector3.Lerp(grip, outstretched, show)
    end
    poseLimb(arm, Vector3.Lerp(arm.hand.position, grip, reach), right * arm.side - Vector3.up)
  end

  local carried = Vector3.Lerp(
    (action.arms[1].hand.position + action.arms[2].hand.position) * 0.5,
    action.arms[2].hand.position, show
  )
  local entry = smoothStep(0.16, 0.43, time)
  local plantReach = action.player.position + forward * 0.23 - Vector3.up * 0.25
  local grip = action.grip
  local held = carried + forward * 0.048 - Vector3.up * grip.gripDrop
  action.prop.position = Vector3.Lerp(plantReach, held, entry)
  action.prop.rotation = Quaternion.LookRotation(forward, Vector3.up) * Quaternion.Euler(0, grip.yaw, show * grip.roll)
  local scale = (grip.scale + grip.liftScale * show) * (1 - 0.9 * release)
  action.prop.localScale = Vector3(scale, scale, scale)
  setGoActive(action.prop.gameObject, true)
end

local function reportCelebrationError(err)
  if warnedAboutCelebration then return end
  warnedAboutCelebration = true
  print("[farming-25d] Harvest animation: " .. tostring(err))
end


local function findAllTransformsByPrefixOrExact()
  local byName = {}
  local stack = { self.transform }
  while #stack > 0 do
    local tr = table.remove(stack)
    local n = tr.name or ""
    if byName[n] == nil then
      byName[n] = tr
    end
    local cnt = tr.childCount
    for i = 0, cnt - 1 do
      table.insert(stack, tr:GetChild(i))
    end
  end
  return byName
end

local function findPlotPart(byName, plotTransform, plotIdx, suffix)
  local expected = string.format("P%d_%s", plotIdx, suffix)
  if byName[expected] ~= nil then
    return byName[expected].gameObject
  end
  -- Fallback: check Plot_i direct/descendant children matching suffix or expected prefix
  if plotTransform ~= nil then
    local stack = { plotTransform }
    while #stack > 0 do
      local tr = table.remove(stack)
      local n = tr.name or ""
      if string.find(n, expected, 1, true) ~= nil or string.find(n, suffix, 1, true) ~= nil then
        return tr.gameObject
      end
      local cnt = tr.childCount
      for i = 0, cnt - 1 do
        table.insert(stack, tr:GetChild(i))
      end
    end
  end
  return nil
end

local function syncPlotVisuals(plotIdx, force)
  local p = plots[plotIdx]
  if p == nil or p.nodes == nil then return end

  local visKey = "empty"
  if p.stage == 1 then
    local ratio = (p.duration > 0) and (p.elapsed / p.duration) or 0.0
    if ratio < 0.48 then
      visKey = "s1_" .. (p.watered and "w" or "d")
    else
      visKey = "s2_" .. (p.watered and "w" or "d")
    end
  elseif p.stage == 2 then
    visKey = "s3_" .. tostring(p.cropId) .. "_" .. (p.watered and "w" or "d")
  end

  if not force and lastStageCheck[plotIdx] == visKey then
    return
  end
  lastStageCheck[plotIdx] = visKey

  local isWet = (p.stage > 0) and (p.watered == true)
  setGoActive(p.nodes.SoilDry, not isWet)
  setGoActive(p.nodes.SoilWet, isWet)

  local showS1 = false
  local showS2 = false
  local showS3 = nil
  if p.stage == 1 then
    local ratio = (p.duration > 0) and (p.elapsed / p.duration) or 0.0
    if ratio < 0.48 then
      showS1 = true
    else
      showS2 = true
    end
  elseif p.stage == 2 then
    local def = CROP_BY_ID[p.cropId]
    showS3 = def ~= nil and def.nodeSuffix or "Stage3_Radish"
  end

  setGoActive(p.nodes.Stage1_Sprout, showS1)
  setGoActive(p.nodes.Stage2_Growing, showS2)
  setGoActive(p.nodes.Stage3_Radish, showS3 == "Stage3_Radish")
  setGoActive(p.nodes.Stage3_Berry, showS3 == "Stage3_Berry")
  setGoActive(p.nodes.Stage3_Sunflower, showS3 == "Stage3_Sunflower")
end

local function serializeState()
  local parts = {
    "v1",
    tostring(coins),
    string.format("%d,%d,%d", bag.radish or 0, bag.berry or 0, bag.sunflower or 0),
    tostring(selectedSeedIdx),
  }
  local plotTokens = {}
  for i = 1, 8 do
    local p = plots[i]
    if p == nil or p.stage == 0 then
      table.insert(plotTokens, "0")
    else
      local cropIdx = (p.cropId == "berry" and 2) or (p.cropId == "sunflower" and 3) or 1
      local rem = math.max(0, math.floor((p.duration - p.elapsed) + 0.5))
      table.insert(plotTokens, string.format("%d:%d:%d:%d", p.stage, cropIdx, p.watered and 1 or 0, rem))
    end
  end
  table.insert(parts, table.concat(plotTokens, ";"))
  return table.concat(parts, "|")
end

local function deserializeState(raw)
  if type(raw) ~= "string" or string.sub(raw, 1, 3) ~= "v1|" then return false end
  local cols = {}
  for seg in string.gmatch(raw, "([^|]+)") do
    table.insert(cols, seg)
  end
  if #cols < 5 then return false end
  coins = math.max(0, tonumber(cols[2]) or 0)
  local r, b, s = string.match(cols[3], "^(%d+),(%d+),(%d+)$")
  if r ~= nil then
    bag.radish = tonumber(r) or 0
    bag.berry = tonumber(b) or 0
    bag.sunflower = tonumber(s) or 0
  end
  selectedSeedIdx = math.max(1, math.min(#CROPS, tonumber(cols[4]) or 1))
  local idx = 1
  for tok in string.gmatch(cols[5], "([^;]+)") do
    if idx <= 8 and plots[idx] ~= nil then
      if tok == "0" then
        plots[idx].stage = 0
        plots[idx].cropId = nil
        plots[idx].watered = false
        plots[idx].elapsed = 0
        plots[idx].duration = 0
      else
        local st, ci, wt, rem = string.match(tok, "^(%d+):(%d+):(%d+):(%d+)$")
        local cDef = CROPS[tonumber(ci) or 1] or CROPS[1]
        local stageNum = tonumber(st) or 0
        if stageNum > 0 then
          plots[idx].cropId = cDef.id
          plots[idx].watered = (tonumber(wt) == 1)
          plots[idx].duration = cDef.growSec
          if stageNum >= 2 then
            plots[idx].stage = 2
            plots[idx].elapsed = cDef.growSec
          else
            plots[idx].stage = 1
            local remSec = math.max(1, math.min(cDef.growSec, tonumber(rem) or cDef.growSec))
            plots[idx].elapsed = math.max(0, cDef.growSec - remSec)
          end
        end
      end
    end
    idx = idx + 1
  end
  return true
end

local function saveState()
  if DataStore == nil then return end
  local payload = serializeState()
  pcall(function()
    if type(DataStore.SetAsync) == "function" then
      DataStore.SetAsync(SaveKey, payload)
    elseif type(DataStore.Set) == "function" then
      DataStore.Set(SaveKey, payload)
    end
  end)
end

local function loadState()
  if DataStore == nil then return end
  local ok, raw = pcall(function()
    if type(DataStore.GetAsync) == "function" then
      return DataStore.GetAsync(SaveKey)
    elseif type(DataStore.Get) == "function" then
      return DataStore.Get(SaveKey)
    end
    return nil
  end)
  if ok and type(raw) == "string" and raw ~= "" then
    deserializeState(raw)
  end
end

local function findNearestPlot(playerPos)
  if playerPos == nil then return nil, 999.0 end
  local bestIdx = nil
  local bestDist = 999.0
  local maxRange = tonumber(InteractRangeMeters) or 2.45
  for i = 1, 8 do
    local p = plots[i]
    if p ~= nil and p.transform ~= nil then
      local wp = p.transform.position
      local dx = playerPos.x - wp.x
      local dz = playerPos.z - wp.z
      local dy = math.abs(playerPos.y - wp.y)
      local dist = math.sqrt(dx * dx + dz * dz)
      if dist <= maxRange and dy <= 2.6 and dist < bestDist then
        bestDist = dist
        bestIdx = i
      end
    end
  end
  return bestIdx, bestDist
end

local function describePlotAction(i)
  local p = plots[i]
  if p == nil then return nil, false end
  if p.stage == 0 then
    local seed = CROPS[selectedSeedIdx]
    return string.format("[E] 种下%s", seed.label), true
  elseif p.stage == 1 then
    local def = CROP_BY_ID[p.cropId] or CROPS[1]
    if not p.watered then
      return string.format("[E] 浇水加速（%s）", def.label), true
    else
      local rem = math.max(1, math.ceil(p.duration - p.elapsed))
      return string.format("%s 成长中（%ds）", def.label, rem), false
    end
  else
    local def = CROP_BY_ID[p.cropId] or CROPS[1]
    return string.format("[E] 收获%s", def.label), true
  end
end

local function interactPlot(i)
  if celebration ~= nil then return false, "庆祝完这次收获再继续吧～" end
  local p = plots[i]
  if p == nil then return false, "没有选中的菜地" end

  if p.stage == 0 then
    local seed = CROPS[selectedSeedIdx]
    p.stage = 1
    p.cropId = seed.id
    p.watered = false
    p.elapsed = 0.0
    p.duration = seed.growSec
    syncPlotVisuals(i, true)
    saveState()
    return true, string.format("种下了一格%s，浇水可以长得更快哦～", seed.label)
  elseif p.stage == 1 then
    local def = CROP_BY_ID[p.cropId] or CROPS[1]
    if not p.watered then
      local rem = math.max(1.0, p.duration - p.elapsed)
      p.watered = true
      p.duration = p.elapsed + rem * 0.5
      syncPlotVisuals(i, true)
      saveState()
      return true, string.format("给%s浇了清凉水，成熟时间减半啦！", def.label)
    else
      local rem = math.max(1, math.ceil(p.duration - p.elapsed))
      return false, string.format("%s已经在喝水长大啦，还剩约 %d 秒", def.label, rem)
    end
  else
    local def = CROP_BY_ID[p.cropId] or CROPS[1]
    bag[def.id] = (bag[def.id] or 0) + 1
    p.stage = 0
    p.cropId = nil
    p.watered = false
    p.elapsed = 0.0
    p.duration = 0.0
    syncPlotVisuals(i, true)
    saveState()
    local ok, err = pcall(startHarvestCelebration, def.id, p.transform)
    if not ok then
      finishHarvestCelebration()
      reportCelebrationError(err)
    end
    return true, string.format("收获了新鲜的%s！已放进小篮子", def.label)
  end
end

function Start()
  local byName = findAllTransformsByPrefixOrExact()
  cropProps = {}
  for id, grip in pairs(HARVEST_PROPS) do
    cropProps[id] = byName[grip.node]
  end
  plots = {}
  local foundPlots = 0
  for i = 1, 8 do
    local pTr = byName["Plot_" .. tostring(i)]
    local nodes = {}
    if pTr ~= nil then
      foundPlots = foundPlots + 1
      for _, suf in ipairs(PART_SUFFIXES) do
        nodes[suf] = findPlotPart(byName, pTr, i, suf)
      end
    end
    plots[i] = {
      index = i,
      transform = pTr,
      nodes = nodes,
      stage = 0,
      cropId = nil,
      watered = false,
      elapsed = 0.0,
      duration = 0.0,
    }
  end

  loadState()
  for i = 1, 8 do
    syncPlotVisuals(i, true)
  end

  local bus = ensureSharedBus()
  bus.farm = {
    CycleSeed = function()
      selectedSeedIdx = (selectedSeedIdx % #CROPS) + 1
      return CROPS[selectedSeedIdx].label
    end,
    GetSelectedSeedLabel = function()
      return CROPS[selectedSeedIdx].label
    end,
    GetBagSummary = function()
      return string.format("萝卜 %d · 草莓 %d · 葵 %d · 壳 %d",
        bag.radish or 0, bag.berry or 0, bag.sunflower or 0, coins or 0)
    end,
    GetTotalCrops = function()
      return (bag.radish or 0) + (bag.berry or 0) + (bag.sunflower or 0)
    end,
    ConsumeCropForGift = function()
      for _, c in ipairs(CROPS) do
        if (bag[c.id] or 0) > 0 then
          bag[c.id] = bag[c.id] - 1
          coins = coins + c.value
          saveState()
          return c.id, c.label, c.value
        end
      end
      return nil, nil, 0
    end,
    AddCoins = function(delta)
      coins = math.max(0, coins + (tonumber(delta) or 0))
      saveState()
      return coins
    end,
    GetNearestPlotInfo = function(playerPos)
      local idx, dist = findNearestPlot(playerPos)
      if idx == nil then return nil, 999.0, nil, false end
      local txt, actionable = describePlotAction(idx)
      return idx, dist, txt, actionable
    end,
    InteractPlotByIndex = function(idx)
      return interactPlot(idx)
    end,
    InteractNearestPlot = function(playerPos)
      local idx = findNearestPlot(playerPos)
      if idx == nil then return false, "请走到菜地格旁边再试试" end
      return interactPlot(idx)
    end,
    GetStateSnapshot = function()
      local list = {}
      for i = 1, 8 do
        local p = plots[i]
        table.insert(list, {
          index = i,
          hasTransform = p.transform ~= nil,
          stage = p.stage,
          cropId = p.cropId,
          watered = p.watered,
          elapsed = p.elapsed,
          duration = p.duration,
        })
      end
      return {
        foundPlots = foundPlots,
        coins = coins,
        bag = { radish = bag.radish or 0, berry = bag.berry or 0, sunflower = bag.sunflower or 0 },
        selectedSeed = CROPS[selectedSeedIdx].id,
        plots = list,
      }
    end,
  }

  initialized = true
  print(string.format("[farming-25d] Ready! Found %d/8 plots", foundPlots))
end

function Update()
  restoreHarvestPose()
  if not initialized then return end
  local dt = Time.deltaTime
  for i = 1, 8 do
    local p = plots[i]
    if p ~= nil and p.stage == 1 then
      p.elapsed = p.elapsed + dt
      if p.elapsed >= p.duration then
        p.elapsed = p.duration
        p.stage = 2
      end
      syncPlotVisuals(i, false)
    end
  end

  autosaveTimer = autosaveTimer + dt
  if autosaveTimer >= 30.0 then
    autosaveTimer = 0.0
    saveState()
  end
end

function LateUpdate()
  if celebration == nil then return end
  local ok, err = pcall(animateHarvest)
  if not ok then
    finishHarvestCelebration()
    reportCelebrationError(err)
  end
end

function OnDisable()
  finishHarvestCelebration()
end

function OnDestroy()
  finishHarvestCelebration()
  if initialized then
    saveState()
  end
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.farm = nil
  end
end
