"""Dump all level-1 nodes in shiguang-25d-windwaker/prefab.json with pos, yaw, scale, and uri."""
import json
import math
from pathlib import Path

PREFAB = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker\prefab.json"
)
URIS = Path(r"C:\Users\Administrator\Desktop\抖音\workspace\data\windwaker_asset_uris.json")
uri_to_key = {v: k for k, v in json.loads(URIS.read_text(encoding="utf-8")).items()}
d = json.loads(PREFAB.read_text(encoding="utf-8"))
for n in d["nodeTransformDatas"]:
    b = n.get("basic") or {}
    if b.get("parentId") not in (0, 1):
        continue
    pos = b.get("pos") or {}
    rot = b.get("rot") or {}
    sc = b.get("scale") or {}
    yaw = math.degrees(2 * math.atan2(rot.get("y", 0.0), rot.get("w", 1.0)))
    uri = (n.get("resource") or {}).get("glbSliceData", {}).get("sourceUri", "")
    rkey = uri_to_key.get(uri, uri[-24:] if uri else "")
    print(
        f"{n['id']:>4} | {b['nodeName']:26s} | "
        f"pos=({pos.get('x',0):+6.2f},{pos.get('y',0):+6.2f},{pos.get('z',0):+6.2f}) | "
        f"yaw={yaw:+6.1f} | sc=({sc.get('x',1):.2f},{sc.get('y',1):.2f},{sc.get('z',1):.2f}) | {rkey}"
    )
