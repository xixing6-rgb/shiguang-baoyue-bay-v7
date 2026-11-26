"""Inspect exact Unity-space bounding boxes of all Tripo & environment GLBs."""
import glob
import json
import struct
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
DIRS = [
    ROOT / "workspace" / "assets" / "models" / "tripo-optimized",
    ROOT / "workspace" / "assets" / "models",
]


def glb_bounds(path: Path):
    data = path.read_bytes()
    clen = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + clen].decode("utf-8"))
    mins = [a["min"] for a in gltf.get("accessors", []) if "min" in a and len(a["min"]) >= 3]
    maxs = [a["max"] for a in gltf.get("accessors", []) if "max" in a and len(a["max"]) >= 3]
    if not mins:
        return None
    # glTF (xg, yg, zg) -> Unity (-xg, yg, zg)
    gmin = [min(m[i] for m in mins) for i in range(3)]
    gmax = [max(m[i] for m in maxs) for i in range(3)]
    ux_min, ux_max = -gmax[0], -gmin[0]
    uy_min, uy_max = gmin[1], gmax[1]
    uz_min, uz_max = gmin[2], gmax[2]
    return {
        "ux_min": round(ux_min, 4),
        "ux_max": round(ux_max, 4),
        "uy_min": round(uy_min, 4),
        "uy_max": round(uy_max, 4),
        "uz_min": round(uz_min, 4),
        "uz_max": round(uz_max, 4),
        "sx": round(ux_max - ux_min, 3),
        "sy": round(uy_max - uy_min, 3),
        "sz": round(uz_max - uz_min, 3),
    }


def main():
    seen = set()
    files = sorted(glob.glob(str(ROOT / "workspace/assets/models/tripo-optimized/*.glb")))
    files += sorted(glob.glob(str(ROOT / "workspace/assets/models/*.glb")))
    for f in files:
        p = Path(f)
        if p.name in seen:
            continue
        seen.add(p.name)
        b = glb_bounds(p)
        if b:
            print(
                f"{p.name:30s} | Y=[{b['uy_min']:+.4f},{b['uy_max']:+.4f}] "
                f"| size=({b['sx']:.2f}, {b['sy']:.2f}, {b['sz']:.2f}) "
                f"| X=[{b['ux_min']:+.2f},{b['ux_max']:+.2f}] Z=[{b['uz_min']:+.2f},{b['uz_max']:+.2f}]"
            )


if __name__ == "__main__":
    main()
