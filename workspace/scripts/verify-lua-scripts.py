#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《时光小筑》4x 叙事系统与 Hamlet Lua 5.3 脚本全量验证器."""

import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS_LUA_DIR = ROOT / "workspace" / "scripts" / "lua"
CREATOR_LUA_DIR = (
    ROOT
    / "creator-project"
    / "project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5"
    / "ai-sessions"
    / "workspace_024l9gls"
    / "wprefabs"
    / "shiguang-town"
    / "scripts"
)
DB_JSON_PATH = ROOT / "workspace" / "data" / "narrative-db.json"
DB_JS_PATH = ROOT / "workspace" / "data" / "narrative-db.js"
BIND_4X_PATH = ROOT / "workspace" / "scripts" / "bind-scripts-4x.js"
NARRATIVE_DOC_PATH = ROOT / "workspace" / "docs" / "narrative-design-and-script.md"

ORIGINAL_4 = [
    "ambient-pivot-motion.lua",
    "cottage-door-interact.lua",
    "courtyard-lights.lua",
    "flowerbed-breed-interact.lua",
]

NEW_7 = [
    "narrative-host.lua",
    "resident-utility-ai.lua",
    "blackboard-dialogue-engine.lua",
    "smart-object-broadcaster.lua",
    "fast-travel-and-ferry.lua",
    "time-weather-lighting.lua",
    "ugc-flag-chalkboard-pet.lua",
]

BUILTIN_KNOWN_UUIDS = {
    "d6f83b17-d36c-4840-ae2a-b896be27b101",
    "b6d250a0-6116-4346-a07d-0aed07d610bc",
}

FORBIDDEN_PATTERNS = [
    (r"\bUnityWebRequest\b", "UnityWebRequest"),
    (r"\bio\.", "io.*"),
    (r"\bos\.execute\b", "os.execute"),
    (r"\bxlua\.load_assembly\b", "xlua.load_assembly"),
    (r"\bloadstring\b", "loadstring"),
    (r"\bdofile\b", "dofile"),
    (r"\bloadfile\b", "loadfile"),
    (r"\bCS\.System\.IO\b", "CS.System.IO"),
    (r"\bCS\.System\.Net\b", "CS.System.Net"),
]


def assert_utf8_nobom(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise AssertionError(f"{path} 包含 UTF-8 BOM，违反无 BOM 规范")
    return raw.decode("utf-8")


def tokenize_lua_strip_comments_and_strings(src: str):
    """返回 (去除注释与字符串后的纯代码, 去除注释但保留字符串的代码)."""
    code_no_str = []
    code_with_str = []
    i = 0
    n = len(src)

    def match_long_bracket(pos: int):
        if pos >= n or src[pos] != "[":
            return -1
        j = pos + 1
        while j < n and src[j] == "=":
            j += 1
        if j < n and src[j] == "[":
            return j - pos - 1
        return -1

    while i < n:
        # 注释
        if src[i : i + 2] == "--":
            eq = match_long_bracket(i + 2)
            if eq >= 0:
                close_tag = "]" + ("=" * eq) + "]"
                end_pos = src.find(close_tag, i + 4 + eq)
                if end_pos == -1:
                    i = n
                else:
                    newlines = src[i : end_pos + len(close_tag)].count("\n")
                    code_no_str.append("\n" * newlines)
                    code_with_str.append("\n" * newlines)
                    i = end_pos + len(close_tag)
            else:
                nl = src.find("\n", i)
                if nl == -1:
                    i = n
                else:
                    code_no_str.append("\n")
                    code_with_str.append("\n")
                    i = nl + 1
            continue

        # 长字符串 [[ ... ]]
        eq = match_long_bracket(i)
        if eq >= 0:
            close_tag = "]" + ("=" * eq) + "]"
            end_pos = src.find(close_tag, i + 2 + eq)
            if end_pos == -1:
                raise AssertionError("存在未闭合的 Lua 长字符串 [[...]]")
            seg = src[i : end_pos + len(close_tag)]
            code_with_str.append(seg)
            code_no_str.append(" " + ("\n" * seg.count("\n")))
            i = end_pos + len(close_tag)
            continue

        # 单双引号字符串
        if src[i] in ('"', "'"):
            quote = src[i]
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == quote:
                    j += 1
                    break
                if src[j] == "\n":
                    raise AssertionError(f"存在未闭合的引号字符串（位于字符索引 {i}）")
                j += 1
            else:
                raise AssertionError(f"存在未闭合的引号字符串（位于字符索引 {i}）")
            seg = src[i:j]
            code_with_str.append(seg)
            code_no_str.append(" __STR__ ")
            i = j
            continue

        code_no_str.append(src[i])
        code_with_str.append(src[i])
        i += 1

    return "".join(code_no_str), "".join(code_with_str)


def check_lua_block_balance(code_no_str: str, filename: str):
    # 剥离表字段访问（例如 a.end / a:do），避免误判字段名
    cleaned = re.sub(r"[.:]\s*[A-Za-z_][A-Za-z0-9_]*", "", code_no_str)
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[(){}\[\]]", cleaned)

    block_stack = []
    paren_stack = []
    expecting_loop_do = False

    for tok in tokens:
        if tok in ("(", "{", "["):
            paren_stack.append(tok)
        elif tok in (")", "}", "]"):
            expected = {"(": ")", "{": "}", "[": "]"}[paren_stack.pop()] if paren_stack else None
            if tok != expected:
                raise AssertionError(f"{filename}: 括号不匹配，遇到 {tok}（期望 {expected}）")
        elif tok in ("for", "while"):
            block_stack.append(tok)
            expecting_loop_do = True
        elif tok == "do":
            if expecting_loop_do:
                expecting_loop_do = False
            else:
                block_stack.append("do")
        elif tok in ("function", "if", "repeat"):
            block_stack.append(tok)
            expecting_loop_do = False
        elif tok == "until":
            if not block_stack or block_stack[-1] != "repeat":
                raise AssertionError(f"{filename}: until 缺少对应的 repeat")
            block_stack.pop()
        elif tok == "end":
            if not block_stack:
                raise AssertionError(f"{filename}: 多余的 end 关键字")
            opener = block_stack.pop()
            if opener == "repeat":
                raise AssertionError(f"{filename}: repeat 必须由 until 闭合而非 end")

    if block_stack:
        raise AssertionError(f"{filename}: 未闭合的 Lua 代码块: {block_stack}")
    if paren_stack:
        raise AssertionError(f"{filename}: 未闭合的括号: {paren_stack}")


def parse_and_validate_metadata(src: str, filename: str) -> str:
    lines = src.splitlines()
    if len(lines) < 5:
        raise AssertionError(f"{filename}: 文件行数过少，缺少元数据头")

    id_m = re.match(r"^---@id\s+([0-9a-fA-F-]{36})\s*$", lines[0])
    if not id_m:
        raise AssertionError(f"{filename}: 第 1 行必须为 ---@id <uuid>")
    script_uuid = id_m.group(1).lower()
    uuid.UUID(script_uuid)  # 校验合法 UUID

    ref_m = re.match(r"^---@referenceName\s+([^\s]+)\s*$", lines[1])
    if not ref_m or ref_m.group(1) != filename:
        raise AssertionError(f"{filename}: 第 2 行 ---@referenceName 必须匹配文件名 {filename}")

    if not re.match(r"^---@displayName\s+.+$", lines[2]):
        raise AssertionError(f"{filename}: 第 3 行缺少合法 ---@displayName")

    start_idx = next((idx for idx, ln in enumerate(lines) if ln.strip() == "---@start"), None)
    end_idx = next((idx for idx, ln in enumerate(lines) if ln.strip() == "---@end"), None)
    if start_idx is None or end_idx is None or end_idx <= start_idx:
        raise AssertionError(f"{filename}: 缺少合法的 ---@start ... ---@end 参数注释块")

    var_count = 0
    for ln in lines[start_idx + 1 : end_idx]:
        s = ln.strip()
        if s.startswith("---@var "):
            if not re.match(r"^---@var\s+[A-Za-z_][A-Za-z0-9_]*:(string|number|boolean)=.+$", s):
                raise AssertionError(f"{filename}: 非法 ---@var 声明: {s}")
            var_count += 1
        elif not re.match(r"^---@(name|desc|group)\s+.+$", s):
            raise AssertionError(f"{filename}: ---@start/---@end 内存在非规范注释行: {s}")

    if var_count == 0:
        raise AssertionError(f"{filename}: 元数据块中至少应声明 1 个 ---@var 参数")
    return script_uuid


def validate_lua_file(path: Path, filename: str, is_new: bool, seen_uuids: dict):
    src = assert_utf8_nobom(path)
    script_uuid = parse_and_validate_metadata(src, filename)

    if script_uuid in BUILTIN_KNOWN_UUIDS:
        raise AssertionError(f"{filename}: UUID {script_uuid} 与内置脚本冲突")
    if script_uuid in seen_uuids:
        raise AssertionError(f"{filename}: UUID {script_uuid} 与 {seen_uuids[script_uuid]} 重复")
    seen_uuids[script_uuid] = filename

    code_no_str, code_with_str = tokenize_lua_strip_comments_and_strings(src)
    check_lua_block_balance(code_no_str, filename)

    # 校验 require 白名单
    for req in re.findall(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', code_with_str):
        if not req.startswith("official."):
            raise AssertionError(f"{filename}: 禁止非 official.* 的 require: {req}")

    # 校验违禁 API
    for pat, label in FORBIDDEN_PATTERNS:
        if re.search(pat, code_with_str):
            raise AssertionError(f"{filename}: 检测到违禁 API 或符号: {label}")

    if is_new:
        if "Logger.create(" not in code_with_str:
            raise AssertionError(f"{filename}: 必须使用 Logger.create(...)")
        if "RuntimeScope.from(self)" not in code_with_str:
            raise AssertionError(f"{filename}: 必须使用 RuntimeScope.from(self)")

    return script_uuid, src


def main():
    print("== 1. 检查 11 个 Hamlet Lua 5.3 脚本（原 4 + 新 7） ==")
    seen_uuids = {}
    lua_uuids = {}

    for fname in ORIGINAL_4:
        p = CREATOR_LUA_DIR / fname
        if not p.exists():
            raise AssertionError(f"缺失原版脚本: {p}")
        uid, _ = validate_lua_file(p, fname, is_new=False, seen_uuids=seen_uuids)
        lua_uuids[fname] = uid
        print(f"  [PASS][ORIG] {fname} (UUID={uid})")

    for fname in NEW_7:
        p_ws = WS_LUA_DIR / fname
        p_cr = CREATOR_LUA_DIR / fname
        if not p_ws.exists() or not p_cr.exists():
            raise AssertionError(f"新脚本双目录缺失: {p_ws} / {p_cr}")

        b_ws = p_ws.read_bytes()
        b_cr = p_cr.read_bytes()
        if hashlib.sha256(b_ws).hexdigest() != hashlib.sha256(b_cr).hexdigest():
            raise AssertionError(f"双目录字节不一致: {fname}")

        uid, src = validate_lua_file(p_ws, fname, is_new=True, seen_uuids=seen_uuids)
        lua_uuids[fname] = uid

        # 协作新增专项校验
        if fname == "narrative-host.lua":
            assert "charStages" in src and "DATASTORE_MAX_BYTES = 6000" in src, "narrative-host.lua 缺少 charStages 或 6000B 限制"
        if fname in ("resident-utility-ai.lua", "blackboard-dialogue-engine.lua"):
            assert "ALLOWED_ACTIONS" in src, f"{fname} 缺少官方动作白名单表 ALLOWED_ACTIONS"
            for req_act in ("water_bend", "paper_pet_squash", "bubble_yellow", "fx_firefly", "voice_soft", "voice_mech"):
                assert req_act in src, f"{fname} ALLOWED_ACTIONS 缺少 {req_act}"
        if fname == "blackboard-dialogue-engine.lua":
            bb_ids = re.findall(r'id\s*=\s*"(BB\d+)"', src)
            assert len(bb_ids) >= 60, f"blackboard-dialogue-engine.lua 内置规则应 >=60，实际 {len(bb_ids)}"
        if fname == "ugc-flag-chalkboard-pet.lua":
            m_flag = re.search(r'DefaultFlagCode:string="([^"]+)"', src)
            assert m_flag and len(m_flag.group(1)) <= 220, "DefaultFlagCode 编码必须 <=220 字节"

        print(f"  [PASS][NEW ] {fname} (UUID={uid}, SHA256 双目录一致)")

    print("\n== 2. 检查 narrative-db.json 与 narrative-db.js ==")
    db_json_raw = assert_utf8_nobom(DB_JSON_PATH)
    db = json.loads(db_json_raw)

    db_js_raw = assert_utf8_nobom(DB_JS_PATH)
    node_check_db = (
        "const fs = require('fs'); const vm = require('vm');"
        "const code = fs.readFileSync(process.argv[1], 'utf8');"
        "const jsonRaw = fs.readFileSync(process.argv[2], 'utf8');"
        "const ctx = { window: {} }; vm.createContext(ctx); vm.runInContext(code, ctx);"
        "const db = ctx.window.SHIGUANG_DB;"
        "if (!db || JSON.stringify(db) !== JSON.stringify(JSON.parse(jsonRaw))) process.exit(3);"
        "if (!Array.isArray(db.facilities) || db.facilities.length !== 42) process.exit(2);"
        "console.log('NODE_DB_OK', db.facilities.length, db.residents.length, db.collectibles.length, db.blackboardLines.length);"
    )
    res_db = subprocess.run(["node", "-e", node_check_db, str(DB_JS_PATH), str(DB_JSON_PATH)], capture_output=True, text=True, encoding="utf-8")
    if res_db.returncode != 0:
        raise AssertionError(f"Node.js 解析 narrative-db.js 失败: {res_db.stderr}")

    f_ids = [f["id"] for f in db["facilities"]]
    expected_f = [f"F{i:02d}" for i in range(1, 43)]
    assert f_ids == expected_f, f"设施列表不完整: {f_ids}"
    for f in db["facilities"]:
        assert isinstance(f["pos"], list) and len(f["pos"]) == 3, f"设施 {f['id']} 坐标无效"

    c_ids = [r["id"] for r in db["residents"]]
    expected_c = [f"C{i:02d}" for i in range(1, 10)]
    assert c_ids == expected_c, f"居民列表不完整: {c_ids}"
    for r in db["residents"]:
        assert r.get("charStageMax") == 3, f"居民 {r['id']} 缺少 charStageMax=3"
        assert set(r["gravityWeights"].keys()) == {"afternoon", "dusk", "night"}

    ch_ids = [c["id"] for c in db["chapters"]]
    assert ch_ids == ["prologue", "ch1", "ch2", "ch3", "ch4", "epilogue"], f"章节状态机错误: {ch_ids}"
    assert len(db["collectibles"]) == 26, f"收集品数量应为26，实际 {len(db['collectibles'])}"
    assert len(db["blackboardLines"]) >= 60, f"黑板台词应 >=60，实际 {len(db['blackboardLines'])}"
    assert db["saveSchema"]["maxBytes"] == 6000
    assert "charStages" in db["saveSchema"]["fields"]
    assert "actionWhitelist" in db["meta"]
    print(f"  [PASS] {res_db.stdout.strip()}")

    print("\n== 3. 检查 bind-scripts-4x.js 语法与 11 个脚本 UUID 覆盖 ==")
    bind_src = assert_utf8_nobom(BIND_4X_PATH)
    node_check_bind = (
        "const fs = require('fs'); const vm = require('vm');"
        "const code = fs.readFileSync(process.argv[1], 'utf8');"
        "new vm.Script('async function __wrap(scene) {\\n' + code + '\\n}');"
        "console.log('NODE_BIND_SYNTAX_OK');"
    )
    res_bind = subprocess.run(["node", "-e", node_check_bind, str(BIND_4X_PATH)], capture_output=True, text=True, encoding="utf-8")
    if res_bind.returncode != 0:
        raise AssertionError(f"bind-scripts-4x.js 语法错误: {res_bind.stderr}")
    for fname, uid in lua_uuids.items():
        assert uid in bind_src, f"bind-scripts-4x.js 未引用脚本 {fname} ({uid})"
    for fid in expected_f:
        assert f'"{fid}"' in bind_src, f"bind-scripts-4x.js 缺少设施绑定 {fid}"
    for cid in expected_c:
        assert f'"{cid}"' in bind_src, f"bind-scripts-4x.js 缺少居民绑定 {cid}"
    print(f"  [PASS] {res_bind.stdout.strip()}（覆盖全部 11 脚本、42 设施、9 居民）")

    print("\n== 4. 检查叙事设计文档 UTF-8 无 BOM ==")
    doc_src = assert_utf8_nobom(NARRATIVE_DOC_PATH)
    assert len(doc_src) > 5000, "narrative-design-and-script.md 内容过短"
    print(f"  [PASS] narrative-design-and-script.md ({len(doc_src)} chars)")

    print("\nALL CHECKS PASSED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"\n[FAIL] 验证未通过: {exc}", file=sys.stderr)
        sys.exit(1)
