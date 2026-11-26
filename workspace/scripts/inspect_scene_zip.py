"""Read ZIP entries inside project scene.data to list top-level scene node IDs & names."""
import json
import zipfile
from pathlib import Path

SD = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390\scene.data"
)
with zipfile.ZipFile(SD, "r") as zf:
    print("ZIP entries:", [(i.filename, i.file_size) for i in zf.infolist()])
    for info in zf.infolist():
        if info.filename.endswith(".json") or info.file_size < 2_000_000:
            raw = zf.read(info.filename)
            try:
                d = json.loads(raw.decode("utf-8"))
                if isinstance(d, dict) and "nodeTransformDatas" in d:
                    for n in d["nodeTransformDatas"]:
                        b = n.get("basic") or {}
                        if b.get("parentId") in (0, None):
                            print("  ROOT:", n.get("id"), "|", b.get("nodeName"), "| pos=", b.get("pos"))
                else:
                    txt = raw.decode("utf-8", errors="ignore")
                    if "抱月湾" in txt or "windwaker" in txt or "WindWaker" in txt:
                        print("  MATCH in", info.filename, txt[:400])
            except Exception:
                pass
