---@id aeaf8abb-ae77-49a6-8e55-150900895e40
---@sourceScriptId ca75e61e-97e0-49f2-be2e-446fd45e9390
---@referenceName courtyard-lights.lua
---@displayName 庭院与壁炉暖光点光源
---@start
---@var HearthIntensity:number=2.6
---@name 壁炉火光强度
---@desc 室内壁炉余烬暖橙点光源基准强度
---@group 灯光
---@var PorchIntensity:number=2.2
---@name 门廊提灯强度
---@desc 南向入户木廊提灯暖黄点光源强度
---@group 灯光
---@var TerraceIntensity:number=1.9
---@name 茶歇露台光源强度
---@desc 东侧咖啡茶歇平台上方柔光强度
---@group 灯光
---@end

local UnityEngine = CS.UnityEngine
local GameObject = UnityEngine.GameObject
local Vector3 = UnityEngine.Vector3
local Color = UnityEngine.Color
local Light = UnityEngine.Light
local LightType = UnityEngine.LightType
local LightShadows = UnityEngine.LightShadows
local Time = UnityEngine.Time
local Object = UnityEngine.Object
local Logger = require("official.core.logger")

local logger = Logger.create("courtyard-lights")
local createdLights = {}
local hearthLight = nil
local flickerTime = 0

local function spawnPointLight(name, localPos, color, intensity, range)
  local go = GameObject(name)
  go.transform:SetParent(self.transform, false)
  go.transform.localPosition = localPos
  local lightComp = go:AddComponent(typeof(Light))
  lightComp.type = LightType.Point
  lightComp.shadows = LightShadows.None
  lightComp.color = color
  lightComp.intensity = intensity
  lightComp.range = range
  table.insert(createdLights, go)
  return lightComp
end

local function cleanupLights()
  for _, go in ipairs(createdLights) do
    if go ~= nil then
      Object.Destroy(go)
    end
  end
  createdLights = {}
  hearthLight = nil
end

function Start()
  cleanupLights()
  -- glTF 转 Unity 后 X 轴取反：壁炉位于模型局部 (-2.35, 0.95, -1.72)
  hearthLight = spawnPointLight(
    "LocalLight_Hearth",
    Vector3(-2.35, 0.95, -1.72),
    Color(1.0, 0.56, 0.22),
    HearthIntensity,
    8.5
  )
  -- 门廊提灯在模型局部 (-1.05, 1.98, 1.75)
  spawnPointLight(
    "LocalLight_PorchLantern",
    Vector3(-1.05, 1.98, 1.75),
    Color(1.0, 0.72, 0.36),
    PorchIntensity,
    8.0
  )
  -- 茶歇露台位于模型局部旋转 180° 后的 (-8.0, 2.5, 5.0) 即地图 (-2, 4.3, -7)
  spawnPointLight(
    "LocalLight_CoffeeTerrace",
    Vector3(-8.0, 2.5, 5.0),
    Color(1.0, 0.78, 0.46),
    TerraceIntensity,
    10.0
  )
  logger:info("已创建 3 盏庭院与室内暖光点光源（LightShadows.None）")
end

function Update()
  if hearthLight ~= nil then
    flickerTime = flickerTime + Time.deltaTime
    local wave = math.sin(flickerTime * 6.8) * 0.14 + math.sin(flickerTime * 11.3) * 0.08
    hearthLight.intensity = math.max(1.2, HearthIntensity + wave)
  end
end

function OnDestroy()
  cleanupLights()
end

function GetLightCount()
  return #createdLights
end
