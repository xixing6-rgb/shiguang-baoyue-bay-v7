---@id adf277f7-e474-43ef-95c5-cd0f5a74ac88
---@referenceName ms-gentle-sway.lua
-- 让整组荷花荷叶以轻微角度随时间摆动
---@start
---@var EnableSway:boolean=true
---@name 启用晃动
---@desc 开启后荷花与荷叶会持续轻微摆动
---@group 晃动
---@var SwayAngle:number=2.2
---@name 晃动角度
---@desc 前后左右倾斜的最大角度，单位为度
---@group 晃动
---@var SwaySpeed:number=0.65
---@name 晃动速度
---@desc 摆动节奏，数值越大晃动越快
---@group 晃动
---@end

local UnityEngine = CS.UnityEngine
local Time = CS.UnityEngine.Time

local target = nil
local baseEuler = nil
local elapsed = 0
local phase = 0

local function restoreBaseRotation()
  if target == nil or baseEuler == nil then return end
  target.localEulerAngles = baseEuler
end

function Start()
  target = self.transform
  if target == nil then return end

  baseEuler = target.localEulerAngles
  local pos = target.position
  phase = math.sin(pos.x * 12.9898 + pos.z * 78.233) * 6.28318
  elapsed = phase
end

function Update()
  if target == nil or baseEuler == nil then return end

  if not EnableSway then
    restoreBaseRotation()
    return
  end

  local speed = math.max(0, SwaySpeed)
  local angle = math.max(0, SwayAngle)
  elapsed = elapsed + Time.deltaTime * speed

  local xOffset = math.sin(elapsed) * angle
  local zOffset = math.cos(elapsed * 0.73 + phase * 0.37) * angle * 0.65
  target.localEulerAngles = UnityEngine.Vector3(baseEuler.x + xOffset, baseEuler.y, baseEuler.z + zOffset)
end

function OnDisable()
  restoreBaseRotation()
end

function OnDestroy()
  restoreBaseRotation()
end