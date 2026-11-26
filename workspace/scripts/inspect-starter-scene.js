const pgr = CS.UnityEngine.GameObject.Find("previewGameRoot");
const dumpTree = (tr, depth) => {
  if (!tr || depth > 2) return null;
  const kids = [];
  for (let i = 0; i < Math.min(tr.childCount, 20); i++) {
    kids.push(dumpTree(tr.GetChild(i), depth + 1));
  }
  return {
    name: tr.name,
    active: tr.gameObject.activeSelf,
    pos: { x: Math.round(tr.position.x * 100) / 100, y: Math.round(tr.position.y * 100) / 100, z: Math.round(tr.position.z * 100) / 100 },
    kids
  };
};
return {
  env: dumpTree(pgr ? pgr.transform.Find("Env") : null, 0),
  map: dumpTree(pgr ? pgr.transform.Find("地图") : null, 0),
  spawn: dumpTree(pgr ? pgr.transform.Find("出生点") : null, 0),
  townChildrenCount: pgr && pgr.transform.Find("时光小筑海滨小镇") ? pgr.transform.Find("时光小筑海滨小镇").childCount : null
};
