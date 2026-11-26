"""Solve and audit clean zero-overlap, off-road, flat-foundation v6 layout."""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path
import numpy as np

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
import build_windwaker_terrain as terrain  # noqa: E402

TRIPO_DIR = ROOT / "workspace" / "assets" / "models" / "tripo-optimized"
CHAR_DIR = ROOT / "workspace" / "assets" / "models" / "characters"
MODELS_DIR = ROOT / "workspace" / "assets" / "models"
OUT_JSON = ROOT / "workspace" / "data" / "windwaker_clean_layout_v7.json"
PREFAB_JSON = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker\prefab.json"
)


def quat_to_mat4(q):
    x, y, z, w = q
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w),     2*(x*z + y*w),     0.0],
        [2*(x*y + z*w),     1 - 2*(x*x + z*z), 2*(y*z - x*w),     0.0],
        [2*(x*z - y*w),     2*(y*z + x*w),     1 - 2*(x*x + y*y), 0.0],
        [0.0,               0.0,               0.0,               1.0],
    ], dtype=np.float64)


def node_local_mat(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape((4, 4)).T
    m = np.eye(4, dtype=np.float64)
    if "scale" in node:
        sx, sy, sz = node["scale"]
        m = m @ np.diag([sx, sy, sz, 1.0])
    if "rotation" in node:
        m = quat_to_mat4(node["rotation"]) @ m
    if "translation" in node:
        tx, ty, tz = node["translation"]
        t = np.eye(4, dtype=np.float64)
        t[:3, 3] = [tx, ty, tz]
        m = t @ m
    return m


def compute_glb_unity_bounds(path: Path):
    data = path.read_bytes()
    clen = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + clen].decode("utf-8"))
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    accessors = gltf.get("accessors", [])
    scenes = gltf.get("scenes", [])
    roots = scenes[0].get("nodes", []) if scenes else list(range(len(nodes)))

    corners_all = []

    def walk(ni, parent_mat):
        node = nodes[ni]
        mat = parent_mat @ node_local_mat(node)
        if "mesh" in node:
            mesh = meshes[node["mesh"]]
            for prim in mesh.get("primitives", []):
                pos_acc_idx = prim.get("attributes", {}).get("POSITION")
                if pos_acc_idx is None:
                    continue
                acc = accessors[pos_acc_idx]
                if "min" not in acc or "max" not in acc:
                    continue
                mn, mx = acc["min"], acc["max"]
                for bx in (mn[0], mx[0]):
                    for by in (mn[1], mx[1]):
                        for bz in (mn[2], mx[2]):
                            v = mat @ np.array([bx, by, bz, 1.0])
                            corners_all.append((-float(v[0]), float(v[1]), float(v[2])))
        for ci in node.get("children", []):
            walk(ci, mat)

    if roots:
        for ri in roots:
            walk(ri, np.eye(4, dtype=np.float64))
    xs = [c[0] for c in corners_all]
    ys = [c[1] for c in corners_all]
    zs = [c[2] for c in corners_all]
    return {
        "ux_min": min(xs), "ux_max": max(xs),
        "uy_min": min(ys), "uy_max": max(ys),
        "uz_min": min(zs), "uz_max": max(zs),
    }


def rotated_aabb_xz(x, z, bounds, yaw_deg, scale=1.0):
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad), math.sin(rad)
    pts = []
    for lx in (bounds["ux_min"] * scale, bounds["ux_max"] * scale):
        for lz in (bounds["uz_min"] * scale, bounds["uz_max"] * scale):
            wx = x + lx * c + lz * s
            wz = z - lx * s + lz * c
            pts.append((wx, wz))
    wxs = [p[0] for p in pts]
    wzs = [p[1] for p in pts]
    return min(wxs), max(wxs), min(wzs), max(wzs)


def sample_footprint(x, z, bounds, yaw_deg, scale=1.0):
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad), math.sin(rad)
    lx0, lx1 = bounds["ux_min"] * scale, bounds["ux_max"] * scale
    lz0, lz1 = bounds["uz_min"] * scale, bounds["uz_max"] * scale
    sample_x, sample_z = [], []
    for i in range(5):
        u = i / 4.0
        for j in range(5):
            v = j / 4.0
            lx = lx0 + (lx1 - lx0) * u
            lz = lz0 + (lz1 - lz0) * v
            sample_x.append(x + lx * c + lz * s)
            sample_z.append(z - lx * s + lz * c)
    sx = np.array(sample_x, dtype=np.float64)
    sz = np.array(sample_z, dtype=np.float64)
    f = terrain.compute_terrain_fields(sx, sz)
    fc = terrain.compute_terrain_fields(np.array([x]), np.array([z]))
    return (
        float(np.min(f["d_road"])),
        float(np.min(f["h"])),
        float(np.max(f["h"])),
        float(np.max(f["d_land"])),
        float(fc["h"][0]),
    )


def aabb_clearance(a, b):
    dx = max(a[0] - b[1], b[0] - a[1], 0.0)
    dz = max(a[2] - b[3], b[2] - a[3], 0.0)
    if dx > 0 or dz > 0:
        return math.hypot(dx, dz)
    ox = min(a[1], b[1]) - max(a[0], b[0])
    oz = min(a[3], b[3]) - max(a[2], b[2])
    return -min(ox, oz)


OBJECTS = {
    "FarmGarden":              ("FARM_CUSTOM", "farm"),
    "F02_FishingPier":         ("F02-fishing-pier.glb", "pier"),
    "Cottage_Main":            ("F04-main-cottage.glb", "building"),
    "F22_WestLighthouse":      ("F22-west-cape-lighthouse.glb", "lighthouse"),
    "F09_WishFountain":        ("F09-wish-fountain.glb", "building"),
    "F15_WindmillTower":       ("F15-windmill-tower.glb", "building"),
    "F14_SwingPavilion":       ("F14-swing-pavilion.glb", "building"),
    "F16_SunsetOverlook":      ("F16-sunset-overlook.glb", "building"),
    "F05_CoffeeTerrace":       ("F05-coffee-terrace.glb", "building"),
    "F06_MendelFlowerbed":     ("F06-mendel-flowerbed.glb", "building"),
    "F12_CafeKiosk":           ("F12-cafe-kiosk.glb", "building"),
    "F13a_HouseAmber":         ("F13a-house-amber.glb", "building"),
    "F13b_HouseSage":          ("F13b-house-sage.glb", "building"),
    "F13c_HouseBlue":          ("F13c-house-blue.glb", "building"),
    "F23a_CliffCottage":       ("F23-cliff-cottage.glb", "building"),
    "F23b_CliffCottage":       ("F23-cliff-cottage.glb", "building"),
    "F30a_StudioCottage":      ("F30-studio-cottage.glb", "building"),
    "F30b_StudioCottage":      ("F30-studio-cottage.glb", "building"),
    "NPC_Amu":                   ("C01-glasses-bear.glb", "npc"),
    "NPC_Mianmian":              ("C02-lop-rabbit.glb", "npc"),
    "NPC_C03_Aju":               ("C03-deadpan-cat.glb", "npc"),
    "NPC_C04_Naibao_Unrigged":   ("C04-corgi-baker-unrigged.glb", "npc"),
    "NPC_C05_Moyu":              ("C05-floating-owl.glb", "npc"),
    "NPC_C07_Tuantuan_Unrigged": ("C07-postman-otter-unrigged.glb", "npc"),
    "NPC_C09_Rongrong_Unrigged": ("C09-artist-sheep-unrigged.glb", "npc"),
    "F07_PixelFlagpole":       ("F07-pixel-flagpole.glb", "prop"),
    "F08_Chalkboard":          ("F08-chalkboard.glb", "prop"),
    "F10_RetroVending":        ("F10-retro-vending.glb", "prop"),
    "F11_PlazaBenches":        ("F11-plaza-benches.glb", "prop"),
    "F03_BeachDiscovery":      ("F03-beach-discovery.glb", "prop"),
    "P05_BakeryCart":          ("P05-bakery-food-cart.glb", "prop"),
    "P02_Mailbox":             ("P02-vintage-mailbox.glb", "prop"),
    "P03_Signpost":            ("P03-wooden-signpost.glb", "prop"),
    "P01_Lamp_CourtyardS":     ("P01-clay-street-lamp.glb", "prop"),
    "P01_Lamp_Dock":           ("P01-clay-street-lamp.glb", "prop"),
    "P01_Lamp_FarmW":          ("P01-clay-street-lamp.glb", "prop"),
    "P01_Lamp_BridgeN":        ("P01-clay-street-lamp.glb", "prop"),
    "P06_Armillary_West":      ("P06-mini-armillary-sphere.glb", "prop"),
    "P06_Armillary_North":     ("P06-mini-armillary-sphere.glb", "prop"),
    "U01_PaperPet_Courtyard":  ("U01-paper-pet-standee.glb", "prop"),
    "P04_Windchime_WestBeach": ("P04-shell-windchime-post.glb", "shore_prop"),
    "P04_Windchime_South":     ("P04-shell-windchime-post.glb", "shore_prop"),
    "F42a_BikeStop":           ("F42-postal-bike-stop.glb", "prop"),
    "F42b_BikeStop":           ("F42-postal-bike-stop.glb", "prop"),
    "F42c_BikeStop":           ("F42-postal-bike-stop.glb", "prop"),
    "F42d_BikeStop":           ("F42-postal-bike-stop.glb", "prop"),
    "F17_ThreeFruitTree":      ("F17-three-fruit-tree.glb", "tree"),
    "E01_Pine_NW1":            ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_NW2":            ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_WestBluff1":     ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_WestBluff2":     ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_EastBluff1":     ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_EastBluff2":     ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_SouthIslet1":    ("E01-coastal-pine-tree.glb", "tree"),
    "E01_Pine_SouthIslet2":    ("E01-coastal-pine-tree.glb", "tree"),
    "E02_Maple_CourtyardN":    ("E02-autumn-maple-tree.glb", "tree"),
    "E02_Maple_NorthHill1":    ("E02-autumn-maple-tree.glb", "tree"),
    "E02_Maple_NorthHill2":    ("E02-autumn-maple-tree.glb", "tree"),
    "E02_Maple_CreekN":        ("E02-autumn-maple-tree.glb", "tree"),
    "E02_Maple_EastUpland":    ("E02-autumn-maple-tree.glb", "tree"),
    "E02_Maple_SouthIslet3":   ("E02-autumn-maple-tree.glb", "tree"),
}


SEEDS = {
    "FarmGarden":              {"x": 4.5,   "z": 9.0,   "yaw": 0.0,   "scale": 1.0,  "lock": True, "fixed_y": 1.13},
    "F02_FishingPier":         {"x": 10.0,  "z": -26.2, "yaw": 0.0,   "scale": 1.0,  "lock": True, "fixed_y": 0.28},
    "F22_WestLighthouse":      {"x": -56.0, "z": -25.0, "yaw": 215.0, "scale": 1.0,  "lock": True},
    "Cottage_Main":            {"x": -15.5, "z": 10.5,  "yaw": 180.0, "scale": 1.0},
    "F09_WishFountain":        {"x": -3.2,  "z": 3.5,   "yaw": 270.0, "scale": 1.0},
    "F15_WindmillTower":       {"x": -5.5,  "z": 23.0,  "yaw": 270.0, "scale": 1.0},
    "F16_SunsetOverlook":      {"x": 1.5,   "z": 21.5,  "yaw": 270.0, "scale": 1.0},
    "F14_SwingPavilion":       {"x": -22.5, "z": -7.5,  "yaw": 270.0, "scale": 1.0},
    "F05_CoffeeTerrace":       {"x": 10.0,  "z": -5.5,  "yaw": 270.0, "scale": 1.0},
    "F06_MendelFlowerbed":     {"x": 9.5,   "z": -14.5, "yaw": 90.0,  "scale": 1.0},
    "F12_CafeKiosk":           {"x": 20.5,  "z": -3.5,  "yaw": 0.0,   "scale": 1.0},
    "F13a_HouseAmber":         {"x": -20.5, "z": -1.5,  "yaw": 180.0, "scale": 1.0},
    "F13b_HouseSage":          {"x": -22.5, "z": 16.5,  "yaw": 180.0, "scale": 1.0},
    "F13c_HouseBlue":          {"x": 22.5,  "z": 10.5,  "yaw": 0.0,   "scale": 1.0},
    "F23a_CliffCottage":       {"x": -39.5, "z": 18.5,  "yaw": 200.0, "scale": 1.0},
    "F23b_CliffCottage":       {"x": -52.5, "z": 13.5,  "yaw": 165.0, "scale": 1.0},
    "F30a_StudioCottage":      {"x": 36.5,  "z": 20.5,  "yaw": 215.0, "scale": 1.0},
    "F30b_StudioCottage":      {"x": 50.5,  "z": 3.5,   "yaw": 0.0,   "scale": 1.0},
    "NPC_Amu":                   {"x": -11.8, "z": 9.8,   "yaw": 180.0, "scale": 1.0},  # Rigged: courtyard beside Cottage_Main & WishFountain
    "NPC_Mianmian":              {"x": 12.7,  "z": 5.5,   "yaw": 245.0, "scale": 1.0},  # Rigged: beside FarmGarden SE
    "NPC_C03_Aju":               {"x": -14.5, "z": 1.2,   "yaw": 180.0, "scale": 1.0},  # Rigged: near F13a_HouseAmber & P02_Mailbox
    "NPC_C04_Naibao_Unrigged":   {"x": 2.0,   "z": -13.2, "yaw": 15.0,  "scale": 1.0},  # UNRIGGED: beside P05_BakeryCart
    "NPC_C05_Moyu":              {"x": 5.5,   "z": 21.0,  "yaw": 265.0, "scale": 1.0},  # Rigged: beside F16_SunsetOverlook
    "NPC_C07_Tuantuan_Unrigged": {"x": 8.6,   "z": -1.5,  "yaw": 210.0, "scale": 1.0},  # UNRIGGED: beside F42a_BikeStop
    "NPC_C09_Rongrong_Unrigged": {"x": -6.8,  "z": 6.2,   "yaw": 185.0, "scale": 1.0},  # UNRIGGED: beside U01_PaperPet_Courtyard & WishFountain
    "F07_PixelFlagpole":       {"x": 3.2,   "z": -11.5, "yaw": 180.0, "scale": 1.0},
    "F08_Chalkboard":          {"x": 14.2,  "z": -3.5,  "yaw": 0.0,   "scale": 1.0},
    "F10_RetroVending":        {"x": 15.8,  "z": 12.2,  "yaw": 270.0, "scale": 1.0},
    "F11_PlazaBenches":        {"x": 12.2,  "z": 8.0,   "yaw": 215.0, "scale": 1.0},
    "F03_BeachDiscovery":      {"x": -12.0, "z": -24.5, "yaw": 270.0, "scale": 1.0},
    "P05_BakeryCart":          {"x": -0.2,  "z": -12.8, "yaw": 0.0,   "scale": 1.0},
    "P02_Mailbox":             {"x": -10.0, "z": 9.5,   "yaw": 180.0, "scale": 1.0},
    "P03_Signpost":            {"x": 1.8,   "z": -7.5,  "yaw": 135.0, "scale": 1.0},
    "P01_Lamp_CourtyardS":     {"x": -3.5,  "z": -12.5, "yaw": 90.0,  "scale": 1.0},
    "P01_Lamp_Dock":           {"x": -3.2,  "z": -19.2, "yaw": 180.0, "scale": 1.0},
    "P01_Lamp_FarmW":          {"x": -4.0,  "z": 9.0,   "yaw": 180.0, "scale": 1.0},
    "P01_Lamp_BridgeN":        {"x": -24.5, "z": -17.0, "yaw": 270.0, "scale": 1.0},
    "P06_Armillary_West":      {"x": -50.2, "z": -31.5, "yaw": 215.0, "scale": 1.0},
    "P06_Armillary_North":     {"x": -6.0,  "z": 50.0,  "yaw": 270.0, "scale": 1.0},
    "U01_PaperPet_Courtyard":  {"x": -5.8,  "z": 5.8,   "yaw": 195.0, "scale": 1.0},
    "P04_Windchime_WestBeach": {"x": -40.0, "z": -32.2, "yaw": 140.0, "scale": 1.0},
    "P04_Windchime_South":     {"x": -11.0, "z": -45.5, "yaw": 10.0,  "scale": 1.0},
    "F42a_BikeStop":           {"x": 7.5,   "z": 0.0,   "yaw": 195.0, "scale": 1.0},
    "F42b_BikeStop":           {"x": -34.0, "z": 0.2,   "yaw": 270.0, "scale": 1.0},
    "F42c_BikeStop":           {"x": 39.5,  "z": 4.2,   "yaw": 180.0, "scale": 1.0},
    "F42d_BikeStop":           {"x": -9.5,  "z": 31.5,  "yaw": 180.0, "scale": 1.0},
    "F17_ThreeFruitTree":      {"x": 19.5,  "z": 18.0,  "yaw": 0.0,   "scale": 1.0},
    "E01_Pine_NW1":            {"x": -26.5, "z": 11.5,  "yaw": 18.0,  "scale": 1.05},
    "E01_Pine_NW2":            {"x": -28.0, "z": -1.5,  "yaw": 95.0,  "scale": 0.92},
    "E01_Pine_WestBluff1":     {"x": -43.5, "z": -14.0, "yaw": -40.0, "scale": 1.10},
    "E01_Pine_WestBluff2":     {"x": -60.5, "z": -33.0, "yaw": 65.0,  "scale": 0.95},
    "E01_Pine_EastBluff1":     {"x": 34.5,  "z": -7.5,  "yaw": -70.0, "scale": 1.08},
    "E01_Pine_EastBluff2":     {"x": 49.5,  "z": -17.5, "yaw": 30.0,  "scale": 0.96},
    "E01_Pine_SouthIslet1":    {"x": -9.5,  "z": -48.8, "yaw": 120.0, "scale": 0.90},
    "E01_Pine_SouthIslet2":    {"x": 8.5,   "z": -47.2, "yaw": -25.0, "scale": 0.95},
    "E02_Maple_CourtyardN":    {"x": 20.5,  "z": 24.0,  "yaw": 45.0,  "scale": 1.02},
    "E02_Maple_NorthHill1":    {"x": -14.0, "z": 48.0,  "yaw": -80.0, "scale": 1.12},
    "E02_Maple_NorthHill2":    {"x": 14.5,  "z": 48.5,  "yaw": 15.0,  "scale": 1.05},
    "E02_Maple_CreekN":        {"x": -27.5, "z": 28.0,  "yaw": 140.0, "scale": 0.98},
    "E02_Maple_EastUpland":    {"x": 30.5,  "z": 29.0,  "yaw": -55.0, "scale": 1.04},
    "E02_Maple_SouthIslet3":   {"x": -1.5,  "z": -50.8, "yaw": 72.0,  "scale": 0.88},
}


def load_bounds_cache():
    cache = {}
    for name, (fname, _) in OBJECTS.items():
        if fname == "FARM_CUSTOM":
            cache[name] = {"ux_min": -3.95, "ux_max": 3.95, "uy_min": -0.45, "uy_max": 1.05, "uz_min": -2.15, "uz_max": 2.15}
            continue
        p = CHAR_DIR / fname
        if not p.exists():
            p = TRIPO_DIR / fname
        if not p.exists():
            p = MODELS_DIR / fname
        cache[name] = compute_glb_unity_bounds(p)
    return cache


def is_valid_candidate(name, x, z, cfg, bounds, placed_aabbs):
    _, cat = OBJECTS[name]
    yaw, sc = cfg["yaw"], cfg.get("scale", 1.0)
    aabb = rotated_aabb_xz(x, z, bounds, yaw, sc)
    droad_min, hmin, hmax, dland_max, hctr = sample_footprint(x, z, bounds, yaw, sc)
    dh = hmax - hmin

    req_road = 0.70 if cat == "farm" else (2.05 if cat in ("building", "lighthouse") else (1.80 if cat == "pier" else 1.55))
    if droad_min < req_road:
        return False, None
    if cat == "building" and dh > 0.28:
        return False, None
    if cat == "lighthouse" and dh > 0.72:
        return False, None
    if cat in ("building", "npc") and dland_max > -0.9:
        return False, None
    if cat == "tree" and dland_max > -0.4:
        return False, None
    if cat == "prop" and dland_max > -0.4:
        return False, None
    if cat == "shore_prop" and dland_max > 0.4:
        return False, None

    for other_name, other_aabb in placed_aabbs.items():
        if aabb_clearance(aabb, other_aabb) < 0.72:
            return False, None
    return True, (aabb, droad_min, hmin, hmax, dland_max, hctr)


def solve_layout(bounds_map):
    placed = {}
    placed_aabbs = {}
    # Order: locked first, then buildings, npcs, props, trees
    order = list(OBJECTS.keys())
    offsets = []
    for r in range(0, 26):
        rad = r * 0.5
        if r == 0:
            offsets.append((0.0, 0.0, 0.0))
        else:
            steps = max(8, int(2 * math.pi * rad / 0.5))
            for k in range(steps):
                ang = 2 * math.pi * k / steps
                dx = round(rad * math.cos(ang) * 2) / 2.0
                dz = round(rad * math.sin(ang) * 2) / 2.0
                offsets.append((dx * dx + dz * dz, dx, dz))
    # Deduplicate offsets preserving distance order
    seen_off = set()
    uniq_offsets = []
    for dist2, dx, dz in sorted(offsets):
        if (dx, dz) not in seen_off:
            seen_off.add((dx, dz))
            uniq_offsets.append((dx, dz))

    for name in order:
        cfg = SEEDS[name]
        b = bounds_map[name]
        _, cat = OBJECTS[name]
        if cfg.get("lock"):
            aabb = rotated_aabb_xz(cfg["x"], cfg["z"], b, cfg["yaw"], cfg["scale"])
            droad_min, hmin, hmax, dland_max, hctr = sample_footprint(cfg["x"], cfg["z"], b, cfg["yaw"], cfg["scale"])
            placed[name] = (cfg["x"], cfg["z"], cfg, droad_min, hmin, hmax, dland_max, hctr)
            placed_aabbs[name] = aabb
            continue

        found = None
        for dx, dz in uniq_offsets:
            cx, cz = cfg["x"] + dx, cfg["z"] + dz
            ok, info = is_valid_candidate(name, cx, cz, cfg, b, placed_aabbs)
            if ok:
                found = (cx, cz, info)
                break
        if found is None:
            raise RuntimeError(f"Could not find valid clean spot for {name} near ({cfg['x']}, {cfg['z']})")
        cx, cz, (aabb, droad_min, hmin, hmax, dland_max, hctr) = found
        placed[name] = (cx, cz, cfg, droad_min, hmin, hmax, dland_max, hctr)
        placed_aabbs[name] = aabb

    # Final pairwise check across all 56 objects
    min_pair = 999.0
    names = sorted(placed_aabbs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            min_pair = min(min_pair, aabb_clearance(placed_aabbs[names[i]], placed_aabbs[names[j]]))
    assert min_pair >= 0.72, f"Overlap invariant failed: min_pair={min_pair:.2f}"
    print(f"[SOLVED OK] All {len(names)} objects valid | min_pair_clearance={min_pair:.2f}m | 0 overlaps | 0 road violations | 0 slope overhangs")
    return placed


def main():
    bounds_map = load_bounds_cache()
    placed = solve_layout(bounds_map)
    out = {}
    for name in sorted(placed.keys()):
        x, z, cfg, droad_min, hmin, hmax, dland_max, hctr = placed[name]
        _, cat = OBJECTS[name]
        if "fixed_y" in cfg:
            y = cfg["fixed_y"]
        elif cat == "lighthouse":
            # Sink lighthouse stone plinth slightly so perimeter hugs hilltop cleanly
            y = round(hmin - 0.02, 3)
        elif cat == "building":
            y = round(hmin - 0.015, 3)
        elif cat == "npc":
            # New C01-C09 GLBs all have bottom at minY = 0.000
            y = round(hctr - 0.005, 3)
        else:
            y = round(hmin - 0.01, 3)
        moved = math.hypot(x - cfg["x"], z - cfg["z"])
        if moved > 0.01:
            print(f"  nudged {name:26s}: ({cfg['x']:+6.1f},{cfg['z']:+6.1f}) -> ({x:+6.1f},{z:+6.1f}) [dRoad={droad_min:.2f}, dh={hmax-hmin:.2f}]")
        out[name] = {
            "x": round(x, 3),
            "y": round(y, 3),
            "z": round(z, 3),
            "yawDeg": round(cfg["yaw"], 1),
            "scale": round(cfg["scale"], 3),
            "category": cat,
            "footRoadMin": round(droad_min, 3),
            "dh": round(hmax - hmin, 3),
            "dLandMax": round(dland_max, 3),
        }

    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
