"""Test SetCameraOffsetMode('camera') lag-follow + verify all 5 surface voxels (grass/road/sand/water/wood) & north meadow."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
import build_windwaker_terrain as terrain  # noqa: E402

INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}
DEBUG_DIR = ROOT / "workspace" / "debug"
ORIGIN = (115.0, 79.35, 86.0)


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


def lua_eval(code):
    tmp = ROOT / "workspace" / "scripts" / "_tmp_pc.lua"
    tmp.write_text(code, encoding="utf-8")
    res = run_cli(["douyin-world", "runtime", "lua", "eval", "--file", str(tmp), f"--binding={cam_key}", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
    tmp.unlink(missing_ok=True)
    return res["data"]["result"]


def tp_local(lx, lz, dy=0.6):
    f = terrain.compute_terrain_fields(np.array([lx], dtype=np.float64), np.array([lz], dtype=np.float64))
    hy = float(f["h"][0])
    wx, wy, wz = ORIGIN[0] + lx, ORIGIN[1] + max(0.0, hy) + dy, ORIGIN[2] + lz
    lua_eval(f"""
local ps=DouyinPlayerService or CS.DouyinPlayerService
local a=ps.GetLocalPlayer():GetActor()
local cc=a.gameObject and a.gameObject:GetComponent(typeof(CS.UnityEngine.CharacterController))
if cc then cc.enabled=false end
a.position=CS.UnityEngine.Vector3({wx},{wy},{wz})
if a.transform then a.transform.position=CS.UnityEngine.Vector3({wx},{wy},{wz}) end
if cc then cc.enabled=true end
return true
""")
    time.sleep(0.8)
    return wx, wy, wz


def walk(keys):
    run_cli(["douyin-world", "runtime", "input", "mouse", "click:0.5,0.5", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
    run_cli(["douyin-world", "runtime", "input", "keys", keys, "--instance", INSTANCE, "--runtime-id", RID, "--json"])
    time.sleep(0.25)


# 1. Switch to camera offset mode & test W/D movement cleanly without Popen focus conflict
print("Offset mode set:", lua_eval("return _G.SHIGUANG_25D.SetCameraOffsetMode('camera')"))
tp_local(0.0, 0.0, 0.4)
pre = lua_eval("local s=_G.SHIGUANG_25D.GetCameraDebugState(); local p=_G.SHIGUANG_25D.GetLocalPlayerPosition(); s._px=p.x; s._pz=p.z; return s")
print(f"Pre-move : pos=({pre['_px']:.2f},{pre['_pz']:.2f}) lag={pre['lagMagnitude']:.3f} vp=({pre['playerViewportXY']['x']:.3f},{pre['playerViewportXY']['y']:.3f}) cam=({pre['cameraPosition']['x']:.2f},{pre['cameraPosition']['z']:.2f})")

run_cli(["douyin-world", "runtime", "input", "mouse", "click:0.5,0.5", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
run_cli(["douyin-world", "runtime", "input", "keys", "W:1000", "--instance", INSTANCE, "--runtime-id", RID, "--json"])
for k in range(6):
    s = lua_eval("local s=_G.SHIGUANG_25D.GetCameraDebugState(); local p=_G.SHIGUANG_25D.GetLocalPlayerPosition(); s._px=p.x; s._pz=p.z; return s")
    print(f"Post {k}   : pos=({s['_px']:.2f},{s['_pz']:.2f}) lag={s['lagMagnitude']:.3f} vp=({s['playerViewportXY']['x']:.3f},{s['playerViewportXY']['y']:.3f}) lagW=({s['lagWorld']['x']:+.2f},{s['lagWorld']['z']:+.2f}) cam=({s['cameraPosition']['x']:.2f},{s['cameraPosition']['z']:.2f})")
    time.sleep(0.22)

# 2. Teleport to Northern Meadow (-18, 26) where creek used to be -> Check 2 screenshot
tp_local(-18.0, 26.0, 0.5)
walk("D:400")
pos2 = lua_eval("local p=_G.SHIGUANG_25D.GetLocalPlayerPosition(); return {x=p.x,y=p.y,z=p.z}")
print("Check 2 player pos:", pos2)
run_cli(["douyin-world", "runtime", "screenshot", "--out", str(DEBUG_DIR / "v6-check2-no-creek-clean-roads.png"), "--instance", INSTANCE, "--runtime-id", RID, "--json"])

# 3. Walk across grass, road, sand, water & check audio + ripple counts
for name, lx, lz in [("grass", -22.0, 24.0), ("road", 0.0, 0.0), ("sand", -2.0, -25.0), ("water", -5.0, -31.5)]:
    tp_local(lx, lz, 0.3)
    walk("D:700")
    st_aw = lua_eval("return {aud=_G.SHIGUANG_25D.GetAudioDebugState(), wat=_G.SHIGUANG_25D.GetWaterMotionState()}")
    aud = st_aw["aud"] or {}
    wat = st_aw["wat"] or {}
    print(f"Surface {name:5s}: mat={str(aud.get('currentMaterial','none')):5s} totalSteps={aud.get('totalSteps')} steps={aud.get('stepCounts')} enters={aud.get('voxelEnterCounts')} wave={aud.get('waveIsPlaying')} ripples={wat.get('stepRippleCount')}")

# 4. Water motion + South Bay lagoon + foam view from South Islet edge (-6, -42) looking NE across lagoon & pier!
tp_local(-6.0, -42.0, 0.6)
walk("W:300")
wat1 = lua_eval("return _G.SHIGUANG_25D.GetWaterMotionState()")
print("Water f1:", json.dumps(wat1, ensure_ascii=False))
run_cli(["douyin-world", "runtime", "screenshot", "--out", str(DEBUG_DIR / "v6-check4-water-f1.png"), "--instance", INSTANCE, "--runtime-id", RID, "--json"])
time.sleep(1.5)
wat2 = lua_eval("return _G.SHIGUANG_25D.GetWaterMotionState()")
print("Water f2:", json.dumps(wat2, ensure_ascii=False))
run_cli(["douyin-world", "runtime", "screenshot", "--out", str(DEBUG_DIR / "v6-check4-water-f2.png"), "--instance", INSTANCE, "--runtime-id", RID, "--json"])
