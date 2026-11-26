---@id 841e3b34-d619-4808-b1f0-9be17c603723
---@sourceScriptId f75af761-295f-43cd-9736-34b34dd1b285
---@referenceName terrain-material-trigger.lua
---@displayName 地表材质体素触发
---@start
---@var MaterialId:string="grass"
---@name 地表材质类型
---@desc 隐形体素所属地表材质：grass / sand / water / road / wood
---@end

local UnityEngine = CS.UnityEngine
local Time = UnityEngine.Time
local BoxColliderType = typeof(UnityEngine.BoxCollider)
local RuntimeScope = require("official.core.runtime_scope")

local runtimeScope = RuntimeScope.from(self)

local sampleInterval = 0.08
local detectionMargin = 0.9
local boxes = {}
local actorInRange = nil
local elapsed = 0.0
local inside = false
local enters = 0
local exits = 0
local voxelKey = nil

local function ensureSharedBus()
  if _G.SHIGUANG_25D == nil then
    _G.SHIGUANG_25D = {}
  end
  return _G.SHIGUANG_25D
end

local function notifyHost(isInside)
  local bus = ensureSharedBus()
  if bus.NotifyMaterialVoxel ~= nil then
    pcall(bus.NotifyMaterialVoxel, voxelKey, MaterialId, isInside)
  end
end

local function setInside(value)
  if inside == value then return end
  inside = value
  if value then
    enters = enters + 1
  else
    exits = exits + 1
  end
  notifyHost(value)
end

local function samplePosition()
  if actorInRange == nil then return end
  local ok, pos = pcall(function()
    return actorInRange.position
  end)
  if not ok or pos == nil then
    actorInRange = nil
    setInside(false)
    return
  end

  local p = self.transform:InverseTransformPoint(pos)
  local near = false
  for _, box in ipairs(boxes) do
    if p.y >= box.minY and p.y < box.maxY then
      if p.x >= box.minX and p.x < box.maxX and p.z >= box.minZ and p.z < box.maxZ then
        setInside(true)
        return
      end
      if p.x >= box.minX - detectionMargin and p.x < box.maxX + detectionMargin
          and p.z >= box.minZ - detectionMargin and p.z < box.maxZ + detectionMargin then
        near = true
      end
    end
  end

  setInside(false)
  if not near then
    actorInRange = nil
  end
end

function Start()
  voxelKey = tostring(self.gameObject:GetInstanceID()) .. ":" .. tostring(self.gameObject.name)
  boxes = {}
  local colliders = self.gameObject:GetComponents(BoxColliderType)
  if colliders ~= nil then
    for i = 0, colliders.Length - 1 do
      local collider = colliders[i]
      if collider ~= nil and collider.isTrigger and collider.enabled then
        local c = collider.center
        local s = collider.size
        boxes[#boxes + 1] = {
          minX = c.x - s.x * 0.5, maxX = c.x + s.x * 0.5,
          minY = c.y - s.y * 0.5, maxY = c.y + s.y * 0.5,
          minZ = c.z - s.z * 0.5, maxZ = c.z + s.z * 0.5,
        }
      end
    end
  end
end

function OnActorTriggerEnter(actor)
  if actor ~= nil and actor.isLocal then
    actorInRange = actor
    elapsed = sampleInterval
  end
end

function OnActorTriggerExit(actor)
  if actor ~= nil and actor.isLocal and actorInRange ~= nil then
    elapsed = sampleInterval
  end
end

function Update()
  if actorInRange == nil then return end
  elapsed = elapsed + Time.deltaTime
  if elapsed >= sampleInterval then
    elapsed = 0.0
    samplePosition()
  end
end

function OnDisable()
  actorInRange = nil
  setInside(false)
end

function OnDestroy()
  actorInRange = nil
  setInside(false)
end

function GetMaterialState()
  return {
    material = MaterialId,
    boxCount = #boxes,
    inside = inside,
    enters = enters,
    exits = exits,
  }
end
