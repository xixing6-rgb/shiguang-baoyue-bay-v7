---@id f1099544-6fa0-4303-af3e-9cc8f325ed91
---@referenceName cottage-door-interact.lua
---@displayName 木屋感应自动门
---@start
---@var DoorNodePath:string="DoorPivot"
---@name 门扇枢轴路径
---@desc 相对木屋 Model 根节点的门枢轴路径
---@group 门控
---@var TriggerDistance:number=3.4
---@name 感应触发距离
---@desc 玩家靠近门口该半径时自动平滑开门
---@group 门控
---@var OpenAngle:number=-85
---@name 开启角度
---@desc 向室内平开旋转的目标 Y 轴角度
---@group 门控
---@var LerpSpeed:number=5.5
---@name 开关平滑速度
---@desc 门扇角度插值速率
---@group 门控
---@end

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("cottage-door")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local doorPivot = nil
local baseRotation = nil
local currentAngle = 0.0
local targetAngle = 0.0
local isOpen = false
local lastDistance = 999.0

local function getDoorwayCenterWorld()
  if doorPivot == nil then
    return self.transform:TransformPoint(Vector3(0, 0.24, 1.39))
  end
  -- DoorPivot 在门框右铰链 (+0.71)，门洞中心位于其局部 (-0.71, 0.8, 0)
  return doorPivot:TransformPoint(Vector3(-0.71, 0.8, 0))
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
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "木屋门脚本无法取得 RuntimeScope", runtimeScopeReason)
    return
  end
  local reason = nil
  doorPivot, reason = runtimeScope:GetTransformByPath(DoorNodePath)
  if doorPivot == nil then
    logger:warnOnce("door-pivot-missing", "未找到门枢轴节点: " .. tostring(DoorNodePath), reason)
    return
  end
  baseRotation = doorPivot.localRotation
  currentAngle = 0.0
  targetAngle = 0.0
  isOpen = false
  logger:info("木屋自动门初始化完成: " .. tostring(DoorNodePath))
end

function Update()
  if doorPivot == nil or baseRotation == nil then return end

  local playerPos = getLocalPlayerPosition()
  if playerPos ~= nil then
    local center = getDoorwayCenterWorld()
    local dx = playerPos.x - center.x
    local dz = playerPos.z - center.z
    local dy = math.abs(playerPos.y - center.y)
    local distXZ = math.sqrt(dx * dx + dz * dz)
    lastDistance = distXZ
    local shouldOpen = (distXZ <= TriggerDistance) and (dy <= 3.0)
    if shouldOpen ~= isOpen then
      isOpen = shouldOpen
      targetAngle = isOpen and OpenAngle or 0.0
      logger:info(isOpen and "玩家靠近木屋门，自动打开" or "玩家离开木屋门，平滑关闭")
    end
  end

  if math.abs(targetAngle - currentAngle) > 0.05 then
    local alpha = math.min(1.0, Time.deltaTime * LerpSpeed)
    currentAngle = currentAngle + (targetAngle - currentAngle) * alpha
    doorPivot.localRotation = baseRotation * Quaternion.Euler(0, currentAngle, 0)
  elseif currentAngle ~= targetAngle then
    currentAngle = targetAngle
    doorPivot.localRotation = baseRotation * Quaternion.Euler(0, currentAngle, 0)
  end
end

function SetDoorOpen(open)
  isOpen = (open == true)
  targetAngle = isOpen and OpenAngle or 0.0
end

function GetDoorState()
  return {
    hasPivot = doorPivot ~= nil,
    isOpen = isOpen,
    currentAngle = currentAngle,
    targetAngle = targetAngle,
    distance = lastDistance
  }
end
