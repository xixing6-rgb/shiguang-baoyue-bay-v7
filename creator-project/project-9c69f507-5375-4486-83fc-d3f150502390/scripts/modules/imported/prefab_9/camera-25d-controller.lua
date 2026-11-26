---@id 886dbf47-ddbb-486d-bad5-a2bec4315b7c
---@sourceScriptId 2a039d00-17e6-483b-9400-7d56ccd9352f
---@referenceName camera-25d-controller.lua
local UnityEngine = CS.UnityEngine
local CameraService = DouyinCameraService or (CS and CS.DouyinCameraService)
local PlayerService = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local RendererType = typeof(UnityEngine.Renderer)

local NPC_DEFS = {
  NPC_Amu = { id = "C01", displayName = "阿木", rigged = true },
  NPC_Mianmian = { id = "C02", displayName = "绵绵", rigged = true },
  NPC_C03_Aju = { id = "C03", displayName = "阿橘", rigged = true },
  NPC_C04_Naibao_Unrigged = { id = "C04", displayName = "奶包", rigged = false },
  NPC_C05_Moyu = { id = "C05", displayName = "墨羽", rigged = true },
  NPC_C07_Tuantuan_Unrigged = { id = "C07", displayName = "团团", rigged = false },
  NPC_C09_Rongrong_Unrigged = { id = "C09", displayName = "绒绒", rigged = false },
}

local npcRefs = {}

local function prepareScene(root)
  local stack = { root }
  while #stack > 0 do
    local node = table.remove(stack)
    local name = node.name or ""
    local npc = NPC_DEFS[name]
    if npc ~= nil and npcRefs[npc.id] == nil then
      npcRefs[npc.id] = { def = npc, transform = node }
    end
    if string.find(name, "Invisible_Sea_Boundary", 1, true) ~= nil then
      local renderers = node.gameObject:GetComponentsInChildren(RendererType)
      for i = 0, renderers.Length - 1 do
        renderers[i].enabled = false
      end
    end
    for i = 0, node.childCount - 1 do
      stack[#stack + 1] = node:GetChild(i)
    end
  end
end

local function getLocalPlayerPosition()
  local player = PlayerService and PlayerService.GetLocalPlayer()
  local actor = player and player:GetActor()
  return actor and actor.position or nil
end

local function getNpcList()
  local result = {}
  for _, entry in pairs(npcRefs) do
    result[#result + 1] = {
      id = entry.def.id,
      displayName = entry.def.displayName,
      rigged = entry.def.rigged,
      worldPos = entry.transform.position,
    }
  end
  table.sort(result, function(a, b) return a.id < b.id end)
  return result
end

local function getCameraDebugState()
  local cam = CameraService and CameraService.GetCamera()
  local angles = cam and cam.transform.eulerAngles
  return {
    mode = "native-free",
    pitch = angles and angles.x or nil,
    yaw = angles and angles.y or nil,
  }
end

function Start()
  prepareScene(self.transform)
  _G.SHIGUANG_25D = _G.SHIGUANG_25D or {}
  local bus = _G.SHIGUANG_25D
  bus.GetLocalPlayerPosition = getLocalPlayerPosition
  bus.GetNpcList = getNpcList
  bus.GetCameraDebugState = getCameraDebugState
end

function OnDestroy()
  local bus = _G.SHIGUANG_25D
  if bus ~= nil and bus.GetNpcList == getNpcList then
    bus.GetLocalPlayerPosition = nil
    bus.GetNpcList = nil
    bus.GetCameraDebugState = nil
  end
end
