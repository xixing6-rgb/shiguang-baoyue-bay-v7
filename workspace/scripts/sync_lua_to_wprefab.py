"""Copy 3 authored Lua bodies into shiguang-25d-windwaker/scripts preserving SDK-generated ---@id & ---@referenceName."""

from __future__ import annotations

from pathlib import Path

SRC_DIR = Path(r"c:\Users\Administrator\Desktop\抖音\workspace\scripts\lua-25d")
DST_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker\scripts"
)

FILES = [
    "camera-25d-controller.lua",
    "farming-plot-system.lua",
    "dialogue-25d-ui.lua",
]


def main():
    for fname in FILES:
        src = SRC_DIR / fname
        dst = DST_DIR / fname
        assert src.exists(), f"Missing authored source: {src}"
        assert dst.exists(), f"Missing SDK-registered target: {dst} (run prefab execute create first!)"

        header_lines = []
        for line in dst.read_text(encoding="utf-8").splitlines():
            if line.startswith("---@id ") or line.startswith("---@referenceName ") or line.startswith("---@displayName "):
                header_lines.append(line)
        assert any(l.startswith("---@id ") for l in header_lines), f"No ---@id header found in {dst}"
        assert any(l.startswith("---@referenceName ") for l in header_lines), f"No ---@referenceName found in {dst}"

        body_lines = [
            l
            for l in src.read_text(encoding="utf-8").splitlines()
            if not (l.startswith("---@id ") or l.startswith("---@referenceName "))
        ]
        merged = "\n".join(header_lines) + "\n" + "\n".join(body_lines) + "\n"
        dst.write_text(merged, encoding="utf-8")
        print(f"[LUA SYNC OK] {fname} ({len(merged)} chars) -> preserved {len(header_lines)} header annotations")


if __name__ == "__main__":
    main()
