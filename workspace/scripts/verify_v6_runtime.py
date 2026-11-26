"""Full runtime verification runner for WPrefab v6 (Checks 1-5)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
DEBUG_DIR = ROOT / "workspace" / "debug"
INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}
RUNTIME_ID = ""
CAM_BINDING = ""


def run_cli(args: list[str], allow_fail: bool = False) -> dict:
    proc = subprocess.run(
        subprocess.list2cmdline(args),
        shell=True,
        env=CLEAN_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    data = None
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{"):
            data = json.loads(s)
            break
    if (proc.returncode != 0 or not data or not data.get("ok")) and not allow_fail:
        raise RuntimeError(f"CLI failed ({' '.join(args[:4])}): {raw}")
    return data or {"ok": False, "raw": raw}


def discover_runtime():
    global RUNTIME_ID, CAM_BINDING
    st = run_cli(["douyin-world", "runtime", "status", "--instance", INSTANCE, "--json"])
    if st["data"]["status"] != "running":
        print(f"[RUNTIME] status={st['data']['status']}, starting...", flush=True)
        st = run_cli([
            "douyin-world", "runtime", "start",
            "--instance", INSTANCE, "--wait", "45", "--timeout-ms", "120000", "--json",
        ])
    RUNTIME_ID = st["data"]["runtimeId"]
    if st["data"]["status"] != "running":
        raise RuntimeError(f"Runtime not running: {st}")
    tgts = run_cli([
        "douyin-world", "runtime", "lua", "targets",
        "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
    ])["data"]
    for t in tgts:
        if t.get("referenceName") == "camera-25d-controller.lua" and "shiguang-25d-windwaker" in t.get("targetPath", ""):
            CAM_BINDING = t["bindingKey"]
            break
    if not CAM_BINDING:
        raise RuntimeError(f"Could not find shiguang-25d-windwaker camera binding in targets: {tgts[:5]}")
    print(f"[RUNTIME READY] runtimeId={RUNTIME_ID}, camBinding={CAM_BINDING}")


def js_eval(code: str, timeout_ms: int = 35000):
    tmp = ROOT / "workspace" / "scripts" / "_tmp_rt_eval.js"
    tmp.write_text(code, encoding="utf-8")
    try:
        res = run_cli([
            "douyin-world", "runtime", "js", "eval", "--file", str(tmp),
            "--instance", INSTANCE, "--runtime-id", RUNTIME_ID,
            "--timeout-ms", str(timeout_ms), "--json",
        ])
    finally:
        tmp.unlink(missing_ok=True)
    return res.get("data", {}).get("result")


def lua_eval(code: str):
    tmp = ROOT / "workspace" / "scripts" / "_tmp_rt_eval.lua"
    tmp.write_text(code, encoding="utf-8")
    try:
        res = run_cli([
            "douyin-world", "runtime", "lua", "eval", "--file", str(tmp),
            f"--binding={CAM_BINDING}",
            "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
        ])
    finally:
        tmp.unlink(missing_ok=True)
    return res.get("data", {})


def screenshot(out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return run_cli([
        "douyin-world", "runtime", "screenshot",
        "--out", str(out_path),
        "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
    ])


def teleport_player(wx: float, wy: float, wz: float):
    lua_eval(f"""
local ps = DouyinPlayerService or (CS and CS.DouyinPlayerService)
local player = ps.GetLocalPlayer()
local actor = player:GetActor()
local cc = actor.gameObject and actor.gameObject:GetComponent(typeof(CS.UnityEngine.CharacterController)) or nil
if cc ~= nil then cc.enabled = false end
actor.position = CS.UnityEngine.Vector3({wx}, {wy}, {wz})
if actor.transform ~= nil then actor.transform.position = CS.UnityEngine.Vector3({wx}, {wy}, {wz}) end
if cc ~= nil then cc.enabled = true end
return true
""")
    time.sleep(0.8)


def walk_keys(keys: str):
    return run_cli([
        "douyin-world", "runtime", "input", "keys", keys,
        "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
    ])


def phase_ab():
    print("\n=== CHECK 1: Single Root + Voxels Invisible + 45deg Centered + Lag-Follow ===")
    r_scene = js_eval(r"""
await awaitFrames(20);
const pg = CS.UnityEngine.GameObject.Find("previewGameRoot");
const pgChildren = [];
let voxelEnabledRenderers = -1;
if (pg) {
  const t = pg.transform;
  for (let i = 0; i < t.childCount; i++) {
    const c = t.GetChild(i);
    pgChildren.push({ name: c.name, id: c.gameObject.GetInstanceID() });
    const voxTr = c.Find("SurfaceMaterialVoxels");
    if (voxTr) {
      const rends = voxTr.gameObject.GetComponentsInChildren(puer.$typeof(CS.UnityEngine.Renderer));
      let cnt = 0;
      for (let r = 0; r < rends.Length; r++) {
        if (rends.get_Item(r).enabled) cnt++;
      }
      voxelEnabledRenderers = cnt;
    }
  }
}
return { pgChildren, voxelEnabledRenderers };
""")
    print("pgChildren:", json.dumps(r_scene, ensure_ascii=False))
    dup = [c for c in r_scene["pgChildren"] if "抱月湾" in c["name"]]
    if dup:
        raise RuntimeError(f"Duplicate old root still present: {dup}")
    assert r_scene["voxelEnabledRenderers"] == 0, f"Visible voxel renderers: {r_scene['voxelEnabledRenderers']}"

    st0 = lua_eval("return _G.SHIGUANG_25D.GetCameraDebugState()")["result"]
    print("Stationary cam state:", json.dumps(st0, ensure_ascii=False))
    screenshot(DEBUG_DIR / "v6-check1-45deg-centered.png")

    # Drive movement and sample camera lag cleanly via fast synchronous lua_eval calls
    probe_lua = (
        "local s=_G.SHIGUANG_25D.GetCameraDebugState(); "
        "local p=_G.SHIGUANG_25D.GetLocalPlayerPosition(); "
        "s._px=p and p.x or 0; s._pz=p and p.z or 0; return s"
    )
    p_in = subprocess.Popen(
        subprocess.list2cmdline([
            "douyin-world", "runtime", "input", "keys", "W:1200",
            "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
        ]),
        shell=True, env=CLEAN_ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    samples = []
    idx = 0
    while p_in.poll() is None and idx < 10:
        samples.append(lua_eval(probe_lua)["result"])
        idx += 1
        time.sleep(0.12)
    p_in.communicate(timeout=15)
    for _ in range(7):
        samples.append(lua_eval(probe_lua)["result"])
        time.sleep(0.22)
    for idx, s in enumerate(samples):
        vp = s["playerViewportXY"]
        print(
            f"  step={idx:2d} | pos=({s['_px']:.2f},{s['_pz']:.2f}) | lag={s['lagMagnitude']:.3f}m "
            f"| vp=({vp['x']:.3f},{vp['y']:.3f}) | lagW=({s['lagWorld']['x']:+.2f},{s['lagWorld']['z']:+.2f}) "
            f"| off=({s['appliedOffset']['x']:+.2f},{s['appliedOffset']['z']:+.2f}) | cam=({s['cameraPosition']['x']:.2f},{s['cameraPosition']['z']:.2f})"
        )


def phase_c2():
    print("\n=== CHECK 2: Northern Meadow (No Creek) & Clean Roads ===")
    teleport_player(100.0, 81.2, 112.0)  # local (-15, 1.85, 26) near former creek center
    screenshot(DEBUG_DIR / "v6-check2-no-creek-clean-roads.png")
    print("Saved v6-check2-no-creek-clean-roads.png")


def phase_c34():
    print("\n=== CHECK 3 & 4: Material Voxels + Grass/Sand/Water Audio + Coastal Waves/Ripples ===")
    spots = [
        ("grass", 93.0, 80.55, 112.0),   # local (-22, 1.2, 26) north meadow
        ("road",  115.0, 80.50, 86.0),   # local (0, 1.15, 0) plaza
        ("sand",  117.0, 79.80, 63.2),   # local (2, 0.45, -22.8) south beach sand
        ("water", 117.0, 79.35, 59.5),   # local (2, 0.0, -26.5) shallow lagoon water
    ]
    for label, wx, wy, wz in spots:
        teleport_player(wx, wy, wz)
        walk_keys("D:600")
        time.sleep(0.35)
        st = lua_eval("""
return {
  mat = _G.SHIGUANG_25D.GetMaterialState and _G.SHIGUANG_25D.GetMaterialState() or nil,
  aud = _G.SHIGUANG_25D.GetAudioDebugState and _G.SHIGUANG_25D.GetAudioDebugState() or nil,
}
""")["result"]
        print(f"  After {label:5s} walk -> aud={json.dumps(st.get('aud'), ensure_ascii=False)}")

    # Check 4: Pier / Beach overview, two spaced frames + water motion state
    teleport_player(124.0, 79.85, 62.5)  # local (9, 0.5, -23.5) right next to fishing pier & shallow waves
    wat = lua_eval("return _G.SHIGUANG_25D.GetWaterMotionState()")["result"]
    print("WaterMotionState:", json.dumps(wat, ensure_ascii=False))
    screenshot(DEBUG_DIR / "v6-check4-water-f1.png")
    time.sleep(1.5)
    screenshot(DEBUG_DIR / "v6-check4-water-f2.png")
    wat2 = lua_eval("return _G.SHIGUANG_25D.GetWaterMotionState()")["result"]
    print("WaterMotionState f2:", json.dumps(wat2, ensure_ascii=False))


def phase_c5():
    print("\n=== CHECK 5: Farm + NPC + Runtime Logs Regression ===")
    # Check 5: Farm + NPC + Runtime Logs Regression
    tgts = run_cli([
        "douyin-world", "runtime", "lua", "targets",
        "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
    ])["data"]
    farm_key = next(
        (t["bindingKey"] for t in tgts if t.get("referenceName") == "farming-plot-system.lua" and "shiguang-25d-windwaker" in t.get("targetPath", "")),
        None,
    )
    farm_info = None
    if farm_key:
        tmp_f = ROOT / "workspace" / "scripts" / "_tmp_farm_eval.lua"
        tmp_f.write_text("return { plotCount = plots and #plots or 0, selectedCrop = selectedCrop }", encoding="utf-8")
        try:
            farm_info = run_cli([
                "douyin-world", "runtime", "lua", "eval", "--file", str(tmp_f),
                f"--binding={farm_key}",
                "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
            ])["data"]
        finally:
            tmp_f.unlink(missing_ok=True)
    res = lua_eval("""
local b = _G.SHIGUANG_25D or {}
local npcs = b.GetNpcList and b.GetNpcList() or {}
local npcOut = {}
for _, n in ipairs(npcs) do
  table.insert(npcOut, { id=n.id, name=n.displayName, x=n.worldPos.x, y=n.worldPos.y, z=n.worldPos.z })
end
return { npcs=npcOut }
""")["result"]
    res["farmInfo"] = farm_info
    print("Farm & NPCs:", json.dumps(res, ensure_ascii=False))
    logs = run_cli([
        "douyin-world", "runtime", "logs", "--args", json.dumps({"after": 0, "limit": 80}),
        "--instance", INSTANCE, "--runtime-id", RUNTIME_ID, "--json",
    ])["data"]
    errs = [e for e in (logs.get("entries") or logs.get("logs") or []) if str(e.get("level", "")).lower() in ("error", "exception")]
    print(f"Runtime logs: {len(logs.get('entries') or logs.get('logs') or [])} entries, errors={len(errs)}")
    for e in errs[:10]:
        print("  ERR:", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all")
    args = ap.parse_args()
    discover_runtime()
    ph = args.phase
    if ph in ("all", "ab", "1"):
        phase_ab()
    if ph in ("all", "c2", "2"):
        phase_c2()
    if ph in ("all", "c34", "3", "4"):
        phase_c34()
    if ph in ("all", "c5", "5"):
        phase_c5()


if __name__ == "__main__":
    main()
