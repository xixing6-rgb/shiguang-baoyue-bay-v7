---@id adc4a58b-54ea-4a1d-88a3-15694e99917a
---@referenceName terrain-material-trigger.lua
---@displayName 地表材质触发
---@start
---@var MaterialId:string="meadow"
---@name 地表材质
---@end

local contacts = 0
local enters = 0
local exits = 0

function OnActorTriggerEnter(actor)
  if actor == nil or not actor.isLocal then return end
  contacts = contacts + 1
  enters = enters + 1
end

function OnActorTriggerExit(actor)
  if actor == nil or not actor.isLocal then return end
  contacts = math.max(0, contacts - 1)
  exits = exits + 1
end

function OnDisable()
  contacts = 0
end

function GetMaterialState()
  return { material = MaterialId, inside = contacts > 0, enters = enters, exits = exits }
end
