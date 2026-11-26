const a = CS.DouyinActorService.GetLocalActor();
if (a) {
  a.Teleport(new CS.UnityEngine.Vector3(-10.5, 0.25, -6.0), CS.UnityEngine.Quaternion.Euler(0, 0, 0));
}
return a ? { x: a.position.x, y: a.position.y, z: a.position.z } : null;
