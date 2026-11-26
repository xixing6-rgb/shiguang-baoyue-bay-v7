const ray = (x, z) => {
  const hits = CS.UnityEngine.Physics.RaycastAll(new CS.UnityEngine.Vector3(x, 300, z), CS.UnityEngine.Vector3.down, 400);
  const out = [];
  if (hits) {
    for (let i = 0; i < hits.Length; i++) {
      const h = hits.GetValue ? hits.GetValue(i) : hits[i];
      out.push({ y: Math.round(h.point.y * 100) / 100, col: h.collider ? h.collider.name : null });
    }
  }
  return out.sort((a, b) => b.y - a.y);
};

const a = CS.DouyinActorService.GetLocalActor();
let tpErr = null;
if (a) {
  try {
    a.Teleport(new CS.UnityEngine.Vector3(-4, 0.3, -12), CS.UnityEngine.Quaternion.Euler(0, -30, 0));
  } catch (e) {
    tpErr = String(e);
  }
}
return {
  tpErr,
  posNow: a ? { x: a.position.x, y: a.position.y, z: a.position.z, g: a.IsGrounded() } : null,
  rayCottage: ray(-10, -6),
  rayWindmill: ray(-12, 16),
  rayNE: ray(20, 20),
  rayCenter: ray(0, 0)
};
