---@id 33e13146-3731-4d44-b13f-101f8380a590
---@referenceName ugc-flag-chalkboard-pet.lua
---@displayName 12×12像素旗编解码、涂鸦黑板与2D纸片宠物随行
---@start
---@var UgcMode:string="Flag"
---@name 组件模式
---@desc Flag(12x12像素旗) / Chalkboard(流行语黑板) / PaperPet(2D纸片宠物随行)
---@group 轻拼贴UGC
---@var TargetNodePath:string="FlagClothPivot"
---@name 目标子节点路径
---@desc 旗面渲染子节点路径或纸片立牌根节点路径
---@group 轻拼贴UGC
---@var DefaultFlagCode:string="PF1:000000000000002222222200022111111220021141141120021111111120021133331120021113311120022111111220002222222200000022220000000000000000000000000000"
---@name 默认12×12旗面编码
---@desc 紧凑字符串格式（~148字节，远低于 DataStore 6000B 上限）
---@group 轻拼贴UGC
---@var PetFollowDistance:number=1.65
---@name 纸片宠跟随距离
---@desc 2D纸片立牌随主角散步的舒适间距（米）
---@group 纸片宠物
---@var SquashAmplitude:number=0.18
---@name 正弦挤压拉伸幅度
---@desc 无骨骼2D立牌弹跳移动时的Y轴正弦形变幅度
---@group 纸片宠物
---@var SquashFrequency:number=6.5
---@name 正弦挤压拉伸频率
---@desc 纸片宠物随行弹跳节拍角频率（弧度/秒）
---@group 纸片宠物
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Color = UnityEngine.Color
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("ugc-collage")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 8 色低门槛高辨识 12×12 像素调色板（兼容 PAD 绘本柔色与高饱和焦点点睛）
local FLAG_PALETTE = {
  ["0"] = Color(0.996, 0.961, 0.894, 1.0), -- 奶油白底 #FFF5E4
  ["1"] = Color(0.486, 0.776, 0.910, 1.0), -- 薄荷天蓝 #7CC6E8
  ["2"] = Color(0.725, 0.416, 0.349, 1.0), -- 暖陶珊瑚 #B96A59
  ["3"] = Color(0.980, 0.800, 0.082, 1.0), -- 柠檬晴黄 #FACC15
  ["4"] = Color(0.984, 0.573, 0.235, 1.0), -- 蜜橘橙 #FB923C
  ["5"] = Color(0.576, 0.780, 0.580, 1.0), -- 鼠尾草绿 #93C794
  ["6"] = Color(0.957, 0.447, 0.714, 1.0), -- 樱花粉 #F472B6
  ["7"] = Color(0.353, 0.345, 0.490, 1.0), -- 暖石板灰 #5A587D
}

local targetTransform = nil
local baseScale = nil
local petPos = nil
local wasInteractPressed = false
local animPhase = 0.0
local activeFlagCode = DefaultFlagCode

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

-- 12×12 像素网格紧凑编解码（支持 PF1: 148B 直写与 PFR1: 游程压缩，均 <180B）
function EncodePixelFlag(grid144)
  if type(grid144) ~= "table" then return DefaultFlagCode end
  local rawChars = {}
  for i = 1, 144 do
    local ch = tostring(grid144[i] or "0")
    if FLAG_PALETTE[ch] == nil then ch = "0" end
    rawChars[i] = ch
  end
  local rawStr = "PF1:" .. table.concat(rawChars, "")

  local rleParts = { "PFR1:" }
  local idx = 1
  while idx <= 144 do
    local cur = rawChars[idx]
    local runLen = 1
    while (idx + runLen) <= 144 and rawChars[idx + runLen] == cur and runLen < 35 do
      runLen = runLen + 1
    end
    local countTag = (runLen < 10) and tostring(runLen) or string.char(55 + runLen)
    table.insert(rleParts, cur .. countTag)
    idx = idx + runLen
  end
  local rleStr = table.concat(rleParts, "")
  if #rleStr < #rawStr then
    return rleStr
  end
  return rawStr
end

function DecodePixelFlag(code)
  local grid = {}
  for i = 1, 144 do grid[i] = "0" end
  if type(code) ~= "string" then return grid end

  if string.sub(code, 1, 4) == "PF1:" then
    local body = string.sub(code, 5)
    for i = 1, math.min(144, #body) do
      local ch = string.sub(body, i, i)
      grid[i] = FLAG_PALETTE[ch] ~= nil and ch or "0"
    end
    return grid
  elseif string.sub(code, 1, 5) == "PFR1:" then
    local body = string.sub(code, 6)
    local outIdx = 1
    local p = 1
    while p + 1 <= #body and outIdx <= 144 do
      local ch = string.sub(body, p, p)
      local tag = string.sub(body, p + 1, p + 1)
      local byte = string.byte(tag)
      local count = 1
      if byte >= 48 and byte <= 57 then
        count = byte - 48
      elseif byte >= 65 and byte <= 90 then
        count = byte - 55
      end
      local safeCh = FLAG_PALETTE[ch] ~= nil and ch or "0"
      for _ = 1, count do
        if outIdx <= 144 then
          grid[outIdx] = safeCh
          outIdx = outIdx + 1
        end
      end
      p = p + 2
    end
    return grid
  end
  return grid
end

function ApplyFlagPattern(flagCode)
  local grid = DecodePixelFlag(flagCode)
  local compact = EncodePixelFlag(grid)
  activeFlagCode = compact

  local host = getHost()
  if host ~= nil then
    host.SetPixelFlag(compact)
  end

  if targetTransform ~= nil then
    pcall(function()
      local renderer = targetTransform.gameObject:GetComponent(typeof(UnityEngine.Renderer))
      if renderer == nil then
        renderer = targetTransform.gameObject:GetComponentInChildren(typeof(UnityEngine.Renderer))
      end
      if renderer ~= nil and UnityEngine.Texture2D ~= nil then
        local tex = UnityEngine.Texture2D(12, 12)
        tex.filterMode = UnityEngine.FilterMode.Point
        for y = 0, 11 do
          for x = 0, 11 do
            local idx = (11 - y) * 12 + x + 1
            local col = FLAG_PALETTE[grid[idx]] or FLAG_PALETTE["0"]
            tex:SetPixel(x, y, col)
          end
        end
        tex:Apply()
        if renderer.material ~= nil then
          renderer.material.mainTexture = tex
        end
      end
    end)
  end

  logger:info(string.format("12×12 像素旗应用完成（编码=%d 字节）", #compact))
  return compact
end

function InjectChalkboardLingo(phrase, authorNote)
  local host = getHost()
  if host == nil then return false end
  local ok = host.AddLingo(phrase)
  if ok then
    local eng = getDialogueEngine()
    local news = eng ~= nil and eng.GenerateIslandNews() or phrase
    logger:info(string.format("黑板注入流行语 [%s] -> 小报广播: %s", tostring(phrase), tostring(news)))
    return true, news
  end
  return false
end

local function updatePaperPetMotion(dt)
  if targetTransform == nil or baseScale == nil then return end
  animPhase = animPhase + dt * SquashFrequency
  local isMoving = false

  local playerPos = getLocalPlayerPosition()
  if playerPos ~= nil then
    if petPos == nil then
      petPos = Vector3(playerPos.x - PetFollowDistance, playerPos.y, playerPos.z - PetFollowDistance)
    end
    local dx = playerPos.x - petPos.x
    local dz = playerPos.z - petPos.z
    local distXZ = math.sqrt(dx * dx + dz * dz)
    if distXZ > PetFollowDistance then
      isMoving = true
      local moveSpeed = math.min(5.2, 2.6 + (distXZ - PetFollowDistance) * 1.1)
      local step = math.min(distXZ - PetFollowDistance, moveSpeed * dt)
      petPos = Vector3(
        petPos.x + (dx / distXZ) * step,
        petPos.y + (playerPos.y - petPos.y) * math.min(1.0, dt * 6.0),
        petPos.z + (dz / distXZ) * step
      )
      targetTransform.position = petPos
    end
  end

  -- 2D 纸片宠物招牌：朝向主相机 + 零骨骼 Y 轴正弦挤压拉伸
  pcall(function()
    local cam = UnityEngine.Camera.main
    if cam ~= nil then
      local lookDir = cam.transform.position - targetTransform.position
      lookDir.y = 0
      if lookDir.sqrMagnitude > 0.001 then
        targetTransform.rotation = Quaternion.LookRotation(-lookDir)
      end
    end
  end)

  local amp = isMoving and SquashAmplitude or (SquashAmplitude * 0.35)
  local wave = math.abs(math.sin(animPhase))
  local scaleY = 1.0 + amp * wave
  local scaleX = 1.0 / math.sqrt(scaleY)
  targetTransform.localScale = Vector3(baseScale.x * scaleX, baseScale.y * scaleY, baseScale.z)
end

function GetUgcState()
  return {
    mode = UgcMode,
    flagCode = activeFlagCode,
    flagBytes = #activeFlagCode,
    hasTarget = targetTransform ~= nil,
  }
end

function Start()
  if runtimeScope ~= nil then
    targetTransform = runtimeScope:GetTransformByPath(TargetNodePath)
  end
  if targetTransform == nil and self ~= nil then
    targetTransform = self.transform
  end
  if targetTransform ~= nil then
    baseScale = targetTransform.localScale
    petPos = targetTransform.position
  end

  if UgcMode == "Flag" then
    ApplyFlagPattern(DefaultFlagCode)
  end

  if _G.__SHIGUANG_SERVICES == nil then
    _G.__SHIGUANG_SERVICES = {}
  end
  _G.__SHIGUANG_SERVICES.ugcSystem = {
    EncodePixelFlag = EncodePixelFlag,
    DecodePixelFlag = DecodePixelFlag,
    ApplyFlagPattern = ApplyFlagPattern,
    InjectChalkboardLingo = InjectChalkboardLingo,
    GetUgcState = GetUgcState,
  }
  logger:info(string.format("轻拼贴 UGC 模块就绪（模式=%s, 路径=%s）", UgcMode, TargetNodePath))
end

function Update()
  local dt = Time.deltaTime
  if UgcMode == "PaperPet" then
    updatePaperPetMotion(dt)
    return
  end

  local interactPressed = Input.GetKey(KeyCode.E)
  local interactStarted = interactPressed and not wasInteractPressed
  wasInteractPressed = interactPressed

  if interactStarted and targetTransform ~= nil then
    local playerPos = getLocalPlayerPosition()
    if playerPos ~= nil then
      local c = targetTransform.position
      local dx = playerPos.x - c.x
      local dz = playerPos.z - c.z
      if (dx * dx + dz * dz) <= (3.8 * 3.8) then
        if UgcMode == "Chalkboard" then
          local samples = { "慢一点也没关系", "海风允许你发呆", "今天也来吃烤包", "纸片小宠天下第一" }
          InjectChalkboardLingo(samples[math.random(1, #samples)])
        elseif UgcMode == "Flag" then
          ApplyFlagPattern(activeFlagCode)
        end
      end
    end
  end
end

function OnDestroy()
  if _G.__SHIGUANG_SERVICES ~= nil then
    _G.__SHIGUANG_SERVICES.ugcSystem = nil
  end
end
