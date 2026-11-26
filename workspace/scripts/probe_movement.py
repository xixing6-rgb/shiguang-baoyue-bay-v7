"""Diagnose player movement input (WASD vs mouse click focus vs joystick drag) and water/road voxel coords."""
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


def get_state():
    tmp = ROOT / "workspace" / "scripts" / "_tmp_probe.lua"
    tmp.write_text(
        "local p=_G.SHIGUANG_25D.GetLocalPlayerPosition(); "
        "local c=_G.SHIGUANG_25D.GetCameraDebugState(); "
        "local a=_G.SHIGUANG_25D.GetAudioDebugState(); "
        "return {x=p.x,y=p.y,z=p.z, lag=c.lagMagnitude, vp=c.playerViewportXY, mat=a.currentMaterial, steps=a.totalSteps}",
        encoding="utf-8",
    )
    res = run_cli(["douyin-world", "runtime", "lua", "eval", "--file", str(tmp), f"--binding={cam_key}", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
    tmp.unlink(missing_ok=True)
    return res["data"]["result"]


# 1. Inspect water & wood & road voxel centers from JSON
vox = json.loads((ROOT / "workspace" / "data" / "windwaker_material_voxels.json").read_text(encoding="utf-8"))
for mat in ("water", "sand", "road", "grass", "wood"):
    nodes = [n for n in vox["nodes"] if n["material"] == mat]
    first = nodes[0]["triggers"][0] if nodes else None
    print(f"Voxel {mat:5s}: {len(nodes)} nodes, sample local center={first['center'] if first else None} size={first['size'] if first else None}")
# Find closest water box near x=2..12
water_near = [t["center"] for n in vox["nodes"] if n["material"] == "water" for t in n["triggers"] if -15 <= t["center"]["x"] <= 15]
print("Sample south water local centers (first 6):", water_near[:6])

# 2. Teleport back to main plaza road (local 0, 1.2, 0 -> world 115, 80.55, 86)
tmp = ROOT / "workspace" / "scripts" / "_tmp_tp.lua"
tmp.write_text(
    "local ps=DouyinPlayerService or CS.DouyinPlayerService; local a=ps.GetLocalPlayer():GetActor(); "
    "local cc=a.gameObject and a.gameObject:GetComponent(typeof(CS.UnityEngine.CharacterController)); "
    "if cc then cc.enabled=false end; a.position=CS.UnityEngine.Vector3(115,80.55,86); "
    "if a.transform then a.transform.position=CS.UnityEngine.Vector3(115,80.55,86) end; "
    "if cc then cc.enabled=true end; return true",
    encoding="utf-8",
)
run_cli(["douyin-world", "runtime", "lua", "eval", "--file", str(tmp), f"--binding={cam_key}", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
tmp.unlink(missing_ok=True)
time.sleep(0.5)

print("Before click/move:", get_state())
run_cli(["douyin-world", "runtime", "input", "mouse", "click:0.5,0.5", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
time.sleep(0.2)
run_cli(["douyin-world", "runtime", "input", "keys", "W:1000", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
print("After click + W:1000:", get_state())
