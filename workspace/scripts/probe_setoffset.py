"""Probe DouyinCameraService.SetOffset axis convention & check south water/north meadow positions."""
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}


def run_cli(args):
    p = subprocess.run(subprocess.list2cmdline(args), shell=True, env=CLEAN_ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    raw = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    for ln in raw.splitlines():
        if ln.strip().startswith("{"):
            return json.loads(ln.strip())
    raise RuntimeError(raw)


st = run_cli(["douyin-world", "runtime", "status", "--instance", INSTANCE, "--json"])["data"]
RID = st["runtimeId"]
tgts = run_cli(["douyin-world", "runtime", "lua", "targets", "--instance", INSTANCE, "--runtime-id", RID, "--json"])["data"]
cam_key = next(t["bindingKey"] for t in tgts if t["referenceName"] == "camera-25d-controller.lua" and "shiguang-25d-windwaker" in t["targetPath"])


def js_probe(code):
    tmp = ROOT / "workspace" / "scripts" / "_tmp_sp.js"
    tmp.write_text(code, encoding="utf-8")
    res = run_cli(["douyin-world", "runtime", "js", "eval", "--file", str(tmp), "--instance", INSTANCE, "--runtime-id", RID, "--json"])
    tmp.unlink(missing_ok=True)
    if "data" not in res:
        raise RuntimeError(f"js_probe failed: {res}")
    return res["data"]["result"]


# Temporarily set cameraOverride so camera-25d-controller doesn't fight our 1-frame SetOffset probe, then restore!
res = js_probe(f"""
const key = {json.dumps(cam_key)};
const CS_Cam = CS.DouyinCameraService;
const Vec3 = CS.UnityEngine.Vector3;
await lua.eval(key, "_G.SHIGUANG_25D.cameraOverride = true; return true");
const snap = async (ox, oy, oz) => {{
  CS_Cam.SetPitch(45);
  CS_Cam.SetYaw(45);
  CS_Cam.SetDistance(22.5);
  CS_Cam.SetOffset(new Vec3(ox, oy, oz));
  await awaitFrames(2);
  const c = CS_Cam.GetCamera();
  const p = c.transform.position;
  return {{ ox, oy, oz, cx: p.x, cy: p.y, cz: p.z }};
}};
const base = await snap(0, 0, 0);
const px = await snap(2, 0, 0);
const pz = await snap(0, 0, 2);
await lua.eval(key, "_G.SHIGUANG_25D.cameraOverride = false; return true");
return {{ base, px, pz, dx_on_px: px.cx - base.cx, dz_on_px: px.cz - base.cz, dx_on_pz: pz.cx - base.cx, dz_on_pz: pz.cz - base.cz }};
""")
print("SetOffset axis probe:", json.dumps(res, indent=2))

# Also list water voxel boxes near -25 > z > -36
vox = json.loads((ROOT / "workspace" / "data" / "windwaker_material_voxels.json").read_text(encoding="utf-8"))
boxes = [
    {"c": t["center"], "s": t["size"]}
    for n in vox["nodes"] if n["material"] == "water"
    for t in n["triggers"] if -36 <= t["center"]["z"] <= -24
]
print("South beach water boxes:", json.dumps(boxes[:8], ensure_ascii=False))
