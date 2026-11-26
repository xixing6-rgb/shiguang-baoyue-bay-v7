const s = CS.UnityEngine.SceneManagement.SceneManager.GetActiveScene();
const arr = s.GetRootGameObjects();
const roots = [];
for (let i = 0; i < arr.Length; i++) {
  const r = arr.GetValue ? arr.GetValue(i) : arr[i];
  if (!r) continue;
  const children = [];
  const t = r.transform;
  const maxC = Math.min(t.childCount, 25);
  for (let j = 0; j < maxC; j++) {
    const ch = t.GetChild(j);
    children.push({
      name: ch.name,
      pos: { x: ch.position.x, y: ch.position.y, z: ch.position.z }
    });
  }
  roots.push({
    name: r.name,
    active: r.activeSelf,
    pos: { x: t.position.x, y: t.position.y, z: t.position.z },
    childCount: t.childCount,
    children
  });
}
const a = CS.DouyinActorService.GetLocalActor();
return {
  actor: a ? { x: a.position.x, y: a.position.y, z: a.position.z } : null,
  rootCount: arr.Length,
  roots: roots.slice(0, 25)
};
