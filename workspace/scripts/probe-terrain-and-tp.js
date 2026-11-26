const pgr = CS.UnityEngine.GameObject.Find("previewGameRoot");
let spawnTr = null;
if (pgr) {
  const t = pgr.transform.Find("出生点");
  if (t) {
    spawnTr = {
      name: t.name,
      active: t.gameObject.activeSelf,
      pos: { x: t.position.x, y: t.position.y, z: t.position.z },
      childCount: t.childCount
    };
  }
}
const ray = (x, z) => {
  const hits = CS.UnityEngine.Physics.RaycastAll(new CS.UnityEngine.Vector3(x, 300, z), CS.UnityEngine.Vector3.down, 400);
  const out = [];
  if (hits) {
    for (let i = 0; i < hits.Length; i++) {
      const h = hits.GetValue ? hits.GetValue(i) : hits[i];
      out.push({ y: h.point.y, col: h.collider ? h.collider.name : null });
    }
  }
  return out.sort((a, b) => b.y - a.y);
};
return {
  spawnTr,
  rayAtOrigin: ray(0, -10),
  rayAtSpawn: ray(110.76, 91.49),
  rayAtLake: ray(-100, -100)
};
