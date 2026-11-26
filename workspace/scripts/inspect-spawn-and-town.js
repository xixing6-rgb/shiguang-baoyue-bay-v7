const find = (p) => CS.UnityEngine.GameObject.Find(p);
const info = (go) => {
  if (!go) return null;
  const t = go.transform;
  return {
    name: go.name,
    active: go.activeInHierarchy,
    pos: { x: t.position.x, y: t.position.y, z: t.position.z },
    euler: { x: t.eulerAngles.x, y: t.eulerAngles.y, z: t.eulerAngles.z }
  };
};
const a = CS.DouyinActorService.GetLocalActor();
return {
  spawn: info(find("previewGameRoot/出生点")),
  terrain0: info(find("previewGameRoot/地图/地形")),
  terrainBlock: info(find("previewGameRoot/地图/地形/地形块(0,0)/地形块")),
  lake: info(find("previewGameRoot/地图/地形/湖泊")),
  town: info(find("previewGameRoot/时光小筑海滨小镇")),
  cottage: info(find("previewGameRoot/时光小筑海滨小镇/cottage-main")),
  flowerbed: info(find("previewGameRoot/时光小筑海滨小镇/flower-bed")),
  pier: info(find("previewGameRoot/时光小筑海滨小镇/fishing-pier")),
  windmill: info(find("previewGameRoot/时光小筑海滨小镇/windmill-north")),
  actorPos: a ? { x: a.position.x, y: a.position.y, z: a.position.z } : null,
  hasTeleport: a ? typeof a.Teleport : null,
  hasSetPos: a ? typeof a.SetPosition : null
};
