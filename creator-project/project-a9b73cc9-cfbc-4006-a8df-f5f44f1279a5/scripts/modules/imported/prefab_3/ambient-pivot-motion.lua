---@id a013fde7-c59d-483f-9fb1-04147917ea9c
---@sourceScriptId 0c79838b-2318-4bcd-80d5-3e2aada3657a
---@referenceName ambient-pivot-motion.lua
---@displayName 风车与旗帜微风律动
---@start
---@var TargetNodePath:string="BladesPivot"
---@name 目标子节点路径
---@desc 相对模型根节点的旋转枢轴路径
---@group 动画
---@var Mode:string="spinZ"
---@name 运动模式
---@desc spinZ 为绕 Z 轴连续旋转，swayY 为绕 Y 轴海风摆动
---@group 动画
---@var Speed:number=22
---@name 速度参数
---@desc 旋转角速度（度/秒）或摆动频率（弧度/秒）
---@group 动画
---@var Amplitude:number=12
---@name 摆动幅度
---@desc swayY 模式的最大角度幅度（度）
---@group 动画
---@end

local UnityEngine = CS.UnityEngine
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("ambient-pivot")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

local targetTransform = nil
local baseRotation = nil
local currentAngle = 0.0
local elapsed = 0.0

function Start()
  if runtimeScope == nil then
    logger:warnOnce("scope-missing", "微风律动脚本无法取得 RuntimeScope", runtimeScopeReason)
    return
  end
  local reason = nil
  targetTransform, reason = runtimeScope:GetTransformByPath(TargetNodePath)
  if targetTransform == nil then
    logger:warnOnce("pivot-missing-" .. tostring(TargetNodePath), "未找到枢轴节点: " .. tostring(TargetNodePath), reason)
    return
  end
  baseRotation = targetTransform.localRotation
  currentAngle = 0.0
  elapsed = 0.0
  logger:info(string.format("微风律动已绑定 %s (%s)", tostring(TargetNodePath), tostring(Mode)))
end

function Update()
  if targetTransform == nil or baseRotation == nil then return end
  if Mode == "spinZ" then
    currentAngle = (currentAngle + Speed * Time.deltaTime) % 360.0
    targetTransform.localRotation = baseRotation * Quaternion.Euler(0, 0, currentAngle)
  else
    elapsed = elapsed + Time.deltaTime
    currentAngle = math.sin(elapsed * Speed) * Amplitude
    targetTransform.localRotation = baseRotation * Quaternion.Euler(0, currentAngle, 0)
  end
end

function GetMotionState()
  return {
    target = TargetNodePath,
    mode = Mode,
    hasTarget = targetTransform ~= nil,
    angle = currentAngle
  }
end
