---@id fd65ee8f-9f00-4bbf-961a-6704233ef8c4
---@sourceScriptId adc4a58b-54ea-4a1d-88a3-15694e99917a
---@referenceName terrain-material-trigger.lua
---@displayName 地表材质触发
---@start
---@var MaterialId:string="meadow"
---@name 地表材质
---@end

local UnityEngine = CS.UnityEngine
local sampleInterval = 0.08
local detectionMargin = 0.9
local boxes = {}
local actorInRange
local elapsed = 0
local inside = false
local enters = 0
local exits = 0

function Start()
  local colliders = self.gameObject:GetComponents(typeof(UnityEngine.BoxCollider))
  for i = 0, colliders.Length - 1 do
    local collider = colliders[i]
    if collider.isTrigger and collider.enabled then
      local c, s = collider.center, collider.size
      boxes[#boxes + 1] = {
        minX = c.x - s.x / 2, maxX = c.x + s.x / 2,
        minY = c.y - s.y / 2, maxY = c.y + s.y / 2,
        minZ = c.z - s.z / 2, maxZ = c.z + s.z / 2,
      }
    end
  end
end

local function setInside(value)
  if inside == value then return end
  inside = value
  if value then enters = enters + 1 else exits = exits + 1 end
end

local function samplePosition()
  if actorInRange == nil then return end

  local p = self.transform:InverseTransformPoint(actorInRange.position)
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
  if not near then actorInRange = nil end
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
  elapsed = elapsed + UnityEngine.Time.deltaTime
  if elapsed >= sampleInterval then
    elapsed = 0
    samplePosition()
  end
end

function OnDisable()
  actorInRange = nil
  setInside(false)
end

function GetMaterialState()
  return { material = MaterialId, inside = inside, enters = enters, exits = exits }
end
