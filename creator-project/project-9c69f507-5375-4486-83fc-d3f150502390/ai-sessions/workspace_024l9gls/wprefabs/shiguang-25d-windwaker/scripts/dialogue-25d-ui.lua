---@id d47edcaf-2866-48be-80c6-a19bf23f04d0
---@referenceName dialogue-25d-ui.lua
local UnityEngine = CS.UnityEngine
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local Time = UnityEngine.Time
local ButtonType = typeof(CS.UnityEngine.UI.Button)
local TextType = typeof(CS.UnityEngine.UI.Text)
local TMPTextType = CS.TMPro ~= nil and typeof(CS.TMPro.TMP_Text) or nil
local UIService = DouyinUIService or (CS and CS.DouyinUIService)
local RuntimeScope = require("official.core.runtime_scope")

local runtimeScope = RuntimeScope.from(self)

local NPC_DIALOGUES = {
  C01 = {
    speaker = "阿木",
    title = "木工棕熊 · 抱月湾守望",
    frames = {
      "dialogueRoot/portraitCardPanel/amuFrame01",
      "dialogueRoot/portraitCardPanel/amuFrame02",
      "dialogueRoot/portraitCardPanel/amuFrame03",
      "dialogueRoot/portraitCardPanel/amuFrame04",
      "dialogueRoot/portraitCardPanel/amuFrame05",
      "dialogueRoot/portraitCardPanel/amuFrame06",
    },
    lines = {
      { who = "阿木：", text = "早呀，刚把木屋屋檐的螺钉敲紧，海风今天比昨天轻了半拍。" },
      { who = "我：", text = "对面那几格小菜圃翻过土啦，想先种点红萝卜试试手气。" },
      { who = "阿木：", text = "好主意，浇点水长起来能快一半，熟了也会稳稳留在土里等着你。" },
      { who = "我：", text = "那我去菜地看看，待会儿顺便绕去西岬老灯塔那头吹吹风。" },
    },
    gifts = {
      radish = "阿木把圆眼镜推了推，接过红萝卜认真闻了闻：‘脆生生的带点海风味，今夜煮奶油蔬菜汤正好！’（+12 贝壳币）",
      berry = "阿木有点惊喜地接过草莓：‘甜度刚合适，我拿两颗分给绵绵放在奶油包上。’（+18 贝壳币）",
      sunflower = "阿木笑着把向日葵插在木屋窗沿的陶罐里：‘这下阴天也有小太阳陪着看海啦。’（+25 贝壳币）",
    },
  },
  C02 = {
    speaker = "绵绵",
    title = "垂耳甜点兔 · 菜园邻居",
    frames = {
      "dialogueRoot/portraitCardPanel/mianmianFrame01",
      "dialogueRoot/portraitCardPanel/mianmianFrame02",
      "dialogueRoot/portraitCardPanel/mianmianFrame03",
      "dialogueRoot/portraitCardPanel/mianmianFrame04",
    },
    lines = {
      { who = "绵绵：", text = "呀！你过来的时候，我刚好听见喷泉的水声和远处的浪花在合拍子。" },
      { who = "我：", text = "这片海一望不到头，站在小桥边感觉整个人都慢下来了。" },
      { who = "绵绵：", text = "要是园子里收了新鲜的小萝卜或草莓，顺手带一颗给我做茶点呀~" },
      { who = "我：", text = "好呀，回头收了新鲜作物就第一个拿来给你挑~" },
    },
    gifts = {
      radish = "绵绵耳朵轻轻晃了晃：‘哇，好圆的小红萝卜！切薄片夹在海盐烤包里一定超棒。’（+12 贝壳币）",
      berry = "绵绵眼睛弯成月牙：‘是抱月湾刚熟的甜草莓！谢谢你，今日限定草莓塔预定一份给你的份！’（+18 贝壳币）",
      sunflower = "绵绵抱住暖金色的向日葵：‘好像连围裙口袋都被阳光晒得暖烘烘的~’（+25 贝壳币）",
    },
  },
}

NPC_DIALOGUES.C03 = {
  speaker = "阿橘",
  title = "未寄信件收藏家",
  frames = { "dialogueRoot/portraitCardPanel/ajuPortrait" },
  lines = {
    { who = "阿橘：", text = "信箱里又多了一封没写收件人的信。我先替它晒晒太阳。" },
    { who = "阿橘：", text = "有些话写下来就够了。过几天再读，说不定会想寄出去。" },
  },
}
NPC_DIALOGUES.C04 = {
  speaker = "奶包",
  title = "夜市烘焙师",
  frames = { "dialogueRoot/portraitCardPanel/naibaoPortrait" },
  lines = {
    { who = "奶包：", text = "第一炉海盐面包刚出炉。闻得到吗？晚点我就推车去夜市。" },
    { who = "奶包：", text = "有多的草莓就带给我吧。我想试试把果酱烤在面包里。" },
  },
}
NPC_DIALOGUES.C05 = {
  speaker = "墨羽",
  title = "夜行星象信使",
  frames = { "dialogueRoot/portraitCardPanel/moyuPortrait" },
  lines = {
    { who = "墨羽：", text = "今天云很薄。傍晚来山坡，能看见第一颗星从海面上升起来。" },
    { who = "墨羽：", text = "以前我靠星星认路。现在我会先认一认灯塔的光。" },
  },
}
NPC_DIALOGUES.C07 = {
  speaker = "团团",
  title = "单车驿站长",
  frames = { "dialogueRoot/portraitCardPanel/tuantuanPortrait" },
  lines = {
    { who = "团团：", text = "哎，信还在包里！我刚才一直以为落在车篮了。" },
    { who = "团团：", text = "去海边的话，沿着大路走就好。沙地骑车容易陷进去。" },
  },
}
NPC_DIALOGUES.C09 = {
  speaker = "绒绒",
  title = "纸片画师",
  frames = { "dialogueRoot/portraitCardPanel/rongrongPortrait" },
  lines = {
    { who = "绒绒：", text = "我想画一张抱月湾的明信片。你觉得该从喷泉边画起，还是从灯塔边？" },
    { who = "绒绒：", text = "先把光画下来吧。刚刚风一吹，水面上的颜色又变了。" },
  },
}

local uiCache = {}
local listeners = {}
local officialUiHandle = nil
local isDialogueOpen = false
local activeNpcId = nil
local activeLineIdx = 1
local portraitFrameIdx = 1
local visiblePortraitPath = nil
local portraitTimer = 0.0
local toastTimer = 0.0
local hudRefreshTimer = 0.0
local nearbyTarget = nil -- { kind = "npc"|"plot", id = ..., label = ..., actionable = bool }
local bondCounts = {}
for npcId in pairs(NPC_DIALOGUES) do bondCounts[npcId] = 0 end

local function getNodeGo(nodePath)
  if uiCache[nodePath] ~= nil then return uiCache[nodePath] end
  local go = nil
  if runtimeScope ~= nil then
    go = runtimeScope:GetGameObjectByPath(nodePath)
  end
  if go == nil and self ~= nil and self.transform ~= nil then
    local tr = self.transform:Find(nodePath)
    if tr ~= nil then go = tr.gameObject end
  end
  if go ~= nil then
    uiCache[nodePath] = go
  end
  return go
end

local function setNodeActive(nodePath, active)
  local go = getNodeGo(nodePath)
  if go ~= nil then
    pcall(function()
      if go.activeSelf ~= active then
        go:SetActive(active)
      end
    end)
  end
end

local function setText(nodePath, value)
  local go = getNodeGo(nodePath)
  if go == nil then return end
  local txt = go:GetComponent(TextType)
  if txt ~= nil then
    txt.text = tostring(value)
    return
  end
  if TMPTextType ~= nil then
    local tmp = go:GetComponent(TMPTextType)
    if tmp ~= nil then
      tmp.text = tostring(value)
    end
  end
end

local function bindButton(nodePath, handler)
  local go = getNodeGo(nodePath)
  if go == nil then return end
  local btn = go:GetComponent(ButtonType)
  if btn == nil then return end
  btn.onClick:AddListener(handler)
  table.insert(listeners, { btn = btn, handler = handler })
end

local function showToast(msg, seconds)
  setText("toastPanel/toastText", msg)
  setNodeActive("toastPanel", true)
  toastTimer = tonumber(seconds) or 2.8
end

local function refreshHud()
  local bus = _G.SHIGUANG_25D
  if bus ~= nil and bus.farm ~= nil then
    setText("farmHudPanel/hudBagText", bus.farm.GetBagSummary())
    setText("farmHudPanel/seedSwitchBtn/seedBtnLabel", "切换种子：" .. tostring(bus.farm.GetSelectedSeedLabel()))
  end
end

local function applyPortraitFrame()
  if not isDialogueOpen or activeNpcId == nil then return end
  local cfg = NPC_DIALOGUES[activeNpcId]
  if cfg == nil then return end
  local frames = cfg.frames
  local activePath = frames[((portraitFrameIdx - 1) % #frames) + 1]
  if activePath ~= visiblePortraitPath then
    if visiblePortraitPath ~= nil then setNodeActive(visiblePortraitPath, false) end
    setNodeActive(activePath, true)
    visiblePortraitPath = activePath
  end
end

local function renderDialogueContent(customBody)
  local cfg = NPC_DIALOGUES[activeNpcId]
  if cfg == nil then return end
  local bond = bondCounts[activeNpcId] or 0
  local bondLabel = bond >= 2 and "默契邻友" or (bond >= 1 and "海风熟人" or "初识邻里")
  setText("dialogueRoot/dialogueBoxPanel/bondBadgeText", string.format("%s · %s", cfg.title, bondLabel))
  if customBody ~= nil then
    setText("dialogueRoot/dialogueBoxPanel/speakerText", cfg.speaker .. "：")
    setText("dialogueRoot/dialogueBoxPanel/bodyText", customBody)
  else
    local line = cfg.lines[activeLineIdx] or cfg.lines[1]
    setText("dialogueRoot/dialogueBoxPanel/speakerText", line.who)
    setText("dialogueRoot/dialogueBoxPanel/bodyText", line.text)
  end

  local bus = _G.SHIGUANG_25D
  local cropCount = (bus ~= nil and bus.farm ~= nil) and bus.farm.GetTotalCrops() or 0
  setText("dialogueRoot/dialogueBoxPanel/giftBtn/giftBtnLabel",
    cropCount > 0 and string.format("送出作物(%d)", cropCount) or "送出作物")
end

local function hideSystemGameUI()
  if officialUiHandle ~= nil or UIService == nil then return end
  local ok, handle = pcall(function()
    if UIService.HideUI ~= nil then
      return UIService.HideUI()
    end
    return nil
  end)
  if ok then
    officialUiHandle = handle
  end
end

local function restoreSystemGameUI()
  if officialUiHandle == nil or UIService == nil then return end
  local h = officialUiHandle
  officialUiHandle = nil
  pcall(function()
    if UIService.ShowUI ~= nil then
      UIService.ShowUI(h)
    end
  end)
end

local function OpenDialogue(npcId)
  local cfg = NPC_DIALOGUES[npcId]
  if cfg == nil then return false end
  activeNpcId = npcId
  activeLineIdx = 1
  portraitFrameIdx = 1
  portraitTimer = 0.0
  isDialogueOpen = true

  hideSystemGameUI()
  setNodeActive("interactPanel", false)
  setNodeActive("dialogueRoot", true)
  applyPortraitFrame()
  renderDialogueContent(nil)
  refreshHud()
  return true
end

local function CloseDialogue()
  if not isDialogueOpen then return false end
  isDialogueOpen = false
  activeNpcId = nil
  setNodeActive("dialogueRoot", false)
  if visiblePortraitPath ~= nil then
    setNodeActive(visiblePortraitPath, false)
    visiblePortraitPath = nil
  end
  restoreSystemGameUI()
  return true
end

local function OnNextClick()
  if not isDialogueOpen or activeNpcId == nil then return end
  local cfg = NPC_DIALOGUES[activeNpcId]
  activeLineIdx = activeLineIdx + 1
  if activeLineIdx > #cfg.lines then
    activeLineIdx = 1
  end
  renderDialogueContent(nil)
end

local function OnGiftClick()
  if not isDialogueOpen or activeNpcId == nil then return end
  local bus = _G.SHIGUANG_25D
  if bus == nil or bus.farm == nil then return end
  local cropId, cropLabel = bus.farm.ConsumeCropForGift()
  if cropId == nil then
    renderDialogueContent("（随身小篮子还是空的呀，去旁边菜园收成一颗萝卜或草莓再来送礼吧~）")
    return
  end
  bondCounts[activeNpcId] = (bondCounts[activeNpcId] or 0) + 1
  local cfg = NPC_DIALOGUES[activeNpcId]
  local story = (cfg.gifts and cfg.gifts[cropId]) or string.format("%s开心地收下了你的%s！", cfg.speaker, cropLabel)
  renderDialogueContent(story)
  refreshHud()
  showToast(string.format("把%s送给了%s", cropLabel, cfg.speaker), 3.0)
end

local function OnSeedSwitchClick()
  local bus = _G.SHIGUANG_25D
  if bus ~= nil and bus.farm ~= nil then
    local lbl = bus.farm.CycleSeed()
    refreshHud()
    showToast("已切换种子为：" .. tostring(lbl), 1.8)
  end
end

local function updateProximityTarget()
  local bus = _G.SHIGUANG_25D
  if bus == nil or bus.GetLocalPlayerPosition == nil then
    nearbyTarget = nil
    setNodeActive("interactPanel", false)
    return
  end
  local playerPos = bus.GetLocalPlayerPosition()
  if playerPos == nil then
    nearbyTarget = nil
    setNodeActive("interactPanel", false)
    return
  end

  local bestNpc = nil
  local bestNpcDist = 3.55
  if bus.GetNpcList ~= nil then
    local list = bus.GetNpcList()
    for _, npc in ipairs(list) do
      local wp = npc.worldPos
      if wp ~= nil then
        local dx = playerPos.x - wp.x
        local dz = playerPos.z - wp.z
        local dy = math.abs(playerPos.y - wp.y)
        local dist = math.sqrt(dx * dx + dz * dz)
        if dist <= bestNpcDist and dy <= 2.6 then
          bestNpcDist = dist
          bestNpc = npc
        end
      end
    end
  end

  local bestPlotIdx, bestPlotDist, plotLabel, plotActionable = nil, 999.0, nil, false
  if bus.farm ~= nil then
    bestPlotIdx, bestPlotDist, plotLabel, plotActionable = bus.farm.GetNearestPlotInfo(playerPos)
  end

  if bestNpc ~= nil and (bestPlotIdx == nil or bestNpcDist <= bestPlotDist + 0.35) then
    nearbyTarget = {
      kind = "npc",
      id = bestNpc.id,
      label = string.format("[E] 和%s聊聊", bestNpc.displayName),
      actionable = true,
    }
    setText("interactPanel/interactBtn/interactBtnLabel", nearbyTarget.label)
    setNodeActive("interactPanel", true)
  elseif bestPlotIdx ~= nil then
    nearbyTarget = {
      kind = "plot",
      id = bestPlotIdx,
      label = plotLabel or "[E] 打理菜地",
      actionable = plotActionable,
    }
    setText("interactPanel/interactBtn/interactBtnLabel", nearbyTarget.label)
    setNodeActive("interactPanel", true)
  else
    nearbyTarget = nil
    setNodeActive("interactPanel", false)
  end
end

local function TriggerNearbyInteract()
  if isDialogueOpen then return false end
  updateProximityTarget()
  if nearbyTarget == nil then return false end

  if nearbyTarget.kind == "npc" then
    return OpenDialogue(nearbyTarget.id)
  elseif nearbyTarget.kind == "plot" then
    local bus = _G.SHIGUANG_25D
    if bus ~= nil and bus.farm ~= nil then
      local _, msg = bus.farm.InteractPlotByIndex(nearbyTarget.id)
      refreshHud()
      updateProximityTarget()
      if msg ~= nil and msg ~= "" then
        showToast(msg, 2.4)
      end
      return true
    end
  end
  return false
end

function Start()
  setNodeActive("dialogueRoot", false)
  setNodeActive("interactPanel", false)
  setNodeActive("toastPanel", false)
  for _, npc in pairs(NPC_DIALOGUES) do
    for _, path in ipairs(npc.frames) do setNodeActive(path, false) end
  end

  bindButton("farmHudPanel/seedSwitchBtn", OnSeedSwitchClick)
  bindButton("interactPanel/interactBtn", TriggerNearbyInteract)
  bindButton("dialogueRoot/dialogueBoxPanel/nextBtn", OnNextClick)
  bindButton("dialogueRoot/dialogueBoxPanel/giftBtn", OnGiftClick)
  bindButton("dialogueRoot/dialogueBoxPanel/closeBtn", CloseDialogue)

  refreshHud()
  if _G.SHIGUANG_25D == nil then _G.SHIGUANG_25D = {} end
  _G.SHIGUANG_25D.ui = {
    OpenDialogue = OpenDialogue,
    CloseDialogue = CloseDialogue,
    NextLine = OnNextClick,
    GiftCrop = OnGiftClick,
    TriggerInteract = TriggerNearbyInteract,
    GetUiState = function()
      return {
        isDialogueOpen = isDialogueOpen,
        activeNpcId = activeNpcId,
        activeLineIdx = activeLineIdx,
        portraitFrameIdx = portraitFrameIdx,
        nearbyKind = nearbyTarget ~= nil and nearbyTarget.kind or nil,
        nearbyId = nearbyTarget ~= nil and nearbyTarget.id or nil,
        bondCounts = bondCounts,
      }
    end,
  }
  print("[dialogue-ui-25d] Ready!")
end

function Update()
  local dt = Time.unscaledDeltaTime

  if toastTimer > 0 then
    toastTimer = toastTimer - dt
    if toastTimer <= 0 then
      setNodeActive("toastPanel", false)
    end
  end

  if isDialogueOpen then
    if #NPC_DIALOGUES[activeNpcId].frames > 1 then
      portraitTimer = portraitTimer + dt
      if portraitTimer >= 0.125 then
        portraitTimer = portraitTimer - 0.125
        portraitFrameIdx = portraitFrameIdx + 1
        applyPortraitFrame()
      end
    end
    if Input ~= nil and KeyCode ~= nil and Input.GetKeyDown(KeyCode.Escape) then
      CloseDialogue()
    end
    return
  end

  hudRefreshTimer = hudRefreshTimer + dt
  if hudRefreshTimer >= 0.2 then
    hudRefreshTimer = 0.0
    refreshHud()
    updateProximityTarget()
  end

  if Input ~= nil and KeyCode ~= nil and Input.GetKeyDown(KeyCode.E) then
    TriggerNearbyInteract()
  end
end

function OnDestroy()
  restoreSystemGameUI()
  for _, item in ipairs(listeners) do
    if item.btn ~= nil and item.handler ~= nil then
      pcall(function()
        item.btn.onClick:RemoveListener(item.handler)
      end)
    end
  end
  listeners = {}
  if _G.SHIGUANG_25D ~= nil then
    _G.SHIGUANG_25D.ui = nil
  end
end
