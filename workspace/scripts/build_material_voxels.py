"""Generate invisible 3D material voxel trigger boxes from the continuous Wind-Waker terrain.

Outputs workspace/data/windwaker_material_voxels.json containing grouped box triggers
for: grass, sand, water, road, wood (bridges/piers).
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
import build_windwaker_terrain as bwt

OUT_JSON = ROOT / "workspace" / "data" / "windwaker_material_voxels.json"


def greedy_merge_2d(grid: np.ndarray, xs: np.ndarray, zs: np.ndarray, step: float) -> list[tuple[float, float, float, float]]:
    """Greedy maximal rectangle decomposition of a 2D boolean voxel grid (nz, nx)."""
    nz, nx = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    rects: list[tuple[float, float, float, float]] = []
    for j in range(nz):
        for i in range(nx):
            if not grid[j, i] or visited[j, i]:
                continue
            # Expand width along X
            w = 1
            while i + w < nx and grid[j, i + w] and not visited[j, i + w]:
                w += 1
            # Expand height along Z while full row slice is available
            h = 1
            while j + h < nz:
                if np.all(grid[j + h, i:i + w]) and not np.any(visited[j + h, i:i + w]):
                    h += 1
                else:
                    break
            visited[j:j + h, i:i + w] = True
            x0 = float(xs[i]) - step * 0.5
            x1 = float(xs[i + w - 1]) + step * 0.5
            z0 = float(zs[j]) - step * 0.5
            z1 = float(zs[j + h - 1]) + step * 0.5
            cx = 0.5 * (x0 + x1)
            cz = 0.5 * (z0 + z1)
            sx = x1 - x0
            sz = z1 - z0
            rects.append((cx, cz, sx, sz))
    return rects


def main() -> None:
    step = 2.0
    x_min, x_max = -72.0, 72.0
    z_min, z_max = -58.0, 72.0
    xs = np.arange(x_min + step * 0.5, x_max, step)
    zs = np.arange(z_min + step * 0.5, z_max, step)
    nx, nz = len(xs), len(zs)
    xx, zz = np.meshgrid(xs, zs)

    fields = bwt.compute_terrain_fields(xx, zz)
    hh = fields["h"]
    d_land = fields["d_land"]
    d_causeway = fields["d_causeway"]
    d_wbridge = fields["d_wbridge"]
    d_road = fields["d_road"]
    d_shore = np.minimum(d_land, d_causeway)

    # Bridge vector helper for west arch height
    ax, az = bwt.WEST_BRIDGE_A
    bx, bz = bwt.WEST_BRIDGE_B
    bdx, bdz = bx - ax, bz - az
    blen = math.hypot(bdx, bdz)

    buckets: dict[tuple[str, float], np.ndarray] = defaultdict(lambda: np.zeros((nz, nx), dtype=bool))
    counts = defaultdict(int)

    for j in range(nz):
        for i in range(nx):
            ux = float(xx[j, i])
            uz = float(zz[j, i])
            dl = float(d_land[j, i])
            ds = float(d_shore[j, i])
            dc = float(d_causeway[j, i])
            dw = float(d_wbridge[j, i])
            dr = float(d_road[j, i])
            hy = float(hh[j, i])

            mat = None
            y_val = hy

            # 1. Wood bridges / fishing pier
            if dw <= 0.35:
                t = ((ux - ax) * bdx + (uz - az) * bdz) / (blen * blen)
                t_clamped = max(0.0, min(1.0, t))
                mat = "wood"
                y_val = 0.23 + 0.78 * (math.sin(math.pi * t_clamped) ** 1.35)
            elif abs(ux - 10.0) <= 1.25 and -29.2 <= uz <= -22.4:
                mat = "wood"
                y_val = 0.45
            # 2. Shallow wading water around shoreline
            elif 0.10 < ds <= 4.30 and dc > 0.40:
                mat = "water"
                y_val = 0.02
            # 3. Walkable land & stone causeway
            elif dl <= 0.40 or dc <= 0.40:
                if dr <= 1.45 or dc <= 0.40:
                    mat = "road"
                elif dl > -3.80 or hy < 0.58:
                    mat = "sand"
                else:
                    mat = "grass"
                y_val = hy

            if mat is not None:
                y_band = round(round(y_val / 0.35) * 0.35, 2)
                buckets[(mat, y_band)][j, i] = True
                counts[mat] += 1

    nodes_out = []
    total_boxes = 0
    for (mat, y_band), grid in sorted(buckets.items()):
        rects = greedy_merge_2d(grid, xs, zs, step)
        if not rects:
            continue
        # Chunk at <= 100 boxes per node to keep Unity BoxCollider components tidy
        chunk_size = 100
        for ci in range(0, len(rects), chunk_size):
            chunk = rects[ci:ci + chunk_size]
            part_idx = (ci // chunk_size) + 1
            suffix = f"_{part_idx:02d}" if len(rects) > chunk_size else ""
            node_name = f"Voxel_{mat}_Y{y_band:.2f}{suffix}"
            triggers = [
                {
                    "shape": "box",
                    "enabled": True,
                    "center": {"x": round(cx, 3), "y": round(y_band + 0.90, 3), "z": round(cz, 3)},
                    "size": {"x": round(sx, 3), "y": 2.4, "z": round(sz, 3)},
                }
                for (cx, cz, sx, sz) in chunk
            ]
            nodes_out.append({
                "name": node_name,
                "material": mat,
                "yBand": y_band,
                "triggers": triggers,
            })
            total_boxes += len(triggers)

    payload = {
        "voxelStepM": step,
        "materials": dict(counts),
        "nodeCount": len(nodes_out),
        "totalBoxes": total_boxes,
        "nodes": nodes_out,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[VOXELS OK] nodes={len(nodes_out)}, totalBoxes={total_boxes}, materials={dict(counts)}")


if __name__ == "__main__":
    main()
