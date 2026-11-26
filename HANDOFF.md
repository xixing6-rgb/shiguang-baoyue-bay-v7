# 阶段交接手册（HANDOFF）— 《时光小筑 · 抱月湾 2.5D》

> **交接日期**：2026-11-25  
> **当前状态**：**v3 WPrefab 已导入并保存，Check C 成熟与收获、Check D 对话与赠礼均已通过。** 预览已停止，四张验收截图已归档到 `workspace/debug/`。

---

## 一、暂停边界与验收矩阵

| 检查项 | 当前状态 | 实测结论与依据 |
| :--- | :--- | :--- |
| **地形与海景法线修复 + 资产入库** | **已完成** | 修复 `WindWaker_Bay_Terrain`、`F37_West_Arch_Bridge`、`Firefly_Creek_Water`、`WindWaker_Lagoon_Shallows`、`WindWaker_Endless_Ocean` 在 Blender→glTF 中的 `-Y` 倒置绕序并加入 `+Z` 构建断言；重新导入归档并更新 WPrefab。 |
| **Check A：出生点与 2.5D 俯视全景（v2）** | **已通过** | v2 实机 `playerPos = [119.742, 80.502, 88.641]`，向下射线命中 `WindWaker_Bay_Terrain`（`y = 80.50`），`camPitch = 36`、`camYaw = 0`，`foundPlots = 8`，`Invisible_Sea_Boundary` 不可见。 |
| **Check B：坡道与跨海拱桥连续通行（v2）** | **已通过** | 8 个地标射线探针全部命中真实地形/桥面碰撞体（`F37_West_Arch_Bridge` 局部高 `+0.818m`），真机 `W:700` 移动停在 `[84.353, 80.215, 52.017]` 桥面无穿模、无阻断（[ww-runtime-slope-and-bridge.png](workspace/debug/ww-runtime-slope-and-bridge.png)）。 |
| **UI 与对白设计术语清理（v3）** | **已修改并归档 WPrefab** | 已移除 `1920x1080.html`、`hudCapsuleSkin.svg` 与 `dialogue-25d-ui.lua` 中的 `"抱月湾慢生活 · 无任务压迫"`、`"轻偶遇"`、`"打卡表"` 等开发期描述；`ui check` 零错通过，`ui-dialogue-25d` 与 `shiguang-25d-windwaker` 已重新构建、校验（`items: [], warnings: []`）并归档至 **v3** URI。 |
| **v3 导入实景与 HUD** | **已通过** | 移除旧根 `-1522262027`，导入得到新根 `-1577082918`。出生点复拍中，背包与种子按钮排版清晰，显示赠礼后的 `壳 12`，未见开发期术语或与系统控件重叠。[最终 HUD](workspace/debug/ww-runtime-spawn-25d.png) |
| **Check C：8 格种菜循环** | **已通过** | v2 实测播种后浇水，湿土激活，剩余时间减半至 `12.57s`。v3 识别 `8/8` 格，接续采样时已播种的 `Plot_1` 萝卜，实测自然成熟于 `25s`，`P1_Stage3_Radish` 激活。按 `E` 后地块回到空地，成熟节点关闭，`bag.radish` 从 `0` 变为 `1`。[成熟萝卜](workspace/debug/ww-runtime-farming.png) |
| **Check D：对话、8fps 立绘与赠礼** | **已通过** | 靠近 `NPC_Amu` 按 `E` 打开对话，NPC 坐标始终为 `[112.500, 80.480, 89.600]`。系统摇杆和右侧操作键随对话隐藏，告别后恢复。跨帧观测记录 21 次切换用时约 `2.64s`。点击继续对话使行号 `1 → 2`，点击送出作物使萝卜 `1 → 0`、贝壳币 `0 → 12`、阿木好感 `0 → 1`。[第 1 帧](workspace/debug/ww-runtime-dialogue-f1.png) · [第 2 帧](workspace/debug/ww-runtime-dialogue-f2.png) |
| **收尾与保存** | **已完成** | `verifyNoTempHooks` 返回 `residues: []`，预览状态回到 `not_started`，`scene save` 返回 `committed`、`hasUnsavedChanges: false`。本轮星光消耗 `0`。 |

---

## 二、造世界工程与云端归档标识清单

### 1. 编辑器与作者工作区路径
- **实景项目根目录（本地造世界数据盘）**：  
  `C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390`
- **作者工作区 ID**：`workspace_024l9gls`
- **2.5D WPrefab ID**：`shiguang-25d-windwaker`
- **推荐场景导入世界坐标**：`115,79.35,86`（场景自带 `出生点` 位于 `[119.74, 80.8, 88.64]`，正对应 `WindWaker_Bay_Terrain` 庭院高程 `80.50m` 上方）
- **主场景磁盘现状**：`scene.data` 已于 `2026-11-25` 保存。写盘回读确认根 `-1577082918`（`时光小筑2.5D风之杖抱月湾`）位于 `[115, 79.35, 86]`，旧根 `-1522262027` 已移除。后续换包时以交付回执的 `lastRootId` 为准，先核对当前主场景。

### 2. 最新云端归档 URI 凭据（v3）
- **最新 WPrefab URI（含 cleaned UI + Lua + 修复法线地形，已 `validate` & `build`）**：  
  `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/eitflflegg6eihqv.wprefab`  
  （同时保存在 [windwaker_delivery_receipt.json](workspace/data/windwaker_delivery_receipt.json)）
- **最新 `ui-dialogue-25d` UI URI**：  
  `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/fmg4yxf8td7ocif0.glb`
- **最新地形 & 海洋模型 URI**（12 项完整模型 URI 见 [windwaker_asset_uris.json](workspace/data/windwaker_asset_uris.json)）：
  - `model-windwaker-bay`: `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/8xcujhw7q815ab3v.glb`
  - `model-windwaker-sea-horizon`: `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/pl9keay60uotvp9v.glb`
  - 其余已减面归档：8 个 Tripo 资产（`F22`, `F09`, `E01`, `E02`, `P01`, `P02`, `P03`, `P05`）、`model-farm-garden`、`model-npc-placeholder`、`ui-dialogue-25d`（均已写入清单与 [windwaker_scene_manifest.json](workspace/data/windwaker_scene_manifest.json)）。

---

## 三、已踩通的平台坑点记录（复工避坑必看）

1. **Blender(`-ux, -uz, uy`) → glTF → Unity 顶点绕序反转**：
   - 开放单面网片若按 `(j,i)→(j+1,i)→(j+1,i+1)→(j,i+1)` 建面会导致法线朝 `-Y`，Unity 背面剔除使其完全透明且向下射线穿透（玩家直接跌落至 `77.9m` 的底座 `地形块`）。
   - 已改为 `(j,i)→(j,i+1)→(j+1,i+1)→(j+1,i)` 并封闭桥梁两端执行 `recalc_face_normals`，同时在 [build_windwaker_terrain.py](workspace/scripts/build_windwaker_terrain.py) 内加入构建期 `+Z` 法线强制断言。
2. **`nodeMergeBlacklist` 必须写 GLB 相对层级路径**：
   - `model-farm-garden/meta.json` 必须列出 `Plot_{i}` 及完整相对路径 `Plot_{i}/P{i}_SoilDry` 等 64 项，仅写子节点裸名会被编辑器网格合并导致作物无法单独显隐。
3. **隐形海岸空气墙不可只依赖 Lua 关闭 `Renderer`**：
   - 造世界切片网格走引擎内部渲染通道，`GetComponent(Renderer)` 可能返回空；必须在 WPrefab 上显式配置 `appearanceData: { transparency: 0, castShadows: false }`，配合 `physicsColliderData.enableCollision = true`。
4. **UI HTML 编译硬约束**：
   - 禁止 `right`/`bottom`/`margin`/`border`/`border-radius`；根容器必须带 `background-color: rgba(0, 0, 0, 0)`；按钮文字相对皮肤边界保留内边距；皮肤修改后必须同步 `wprefabs/.../assets/uis/ui-dialogue-25d/` 并重新 `resource ui check` → `resource archive`。
5. **`scene import` CLI 180s 超时恢复规范**：
   - 大尺寸 WPrefab 导入主场景时，CLI 可能报 `TIMEOUT` 而编辑器仍在提交。**严禁更换 `--request-id` 盲目重提**，应运行 `douyin-world scene cancel <原requestId> --instance <ID> --timeout-ms 60000 --json` 找回 `committed` 回执（或使用 `--request-id` 重试确认）；若遇 `"自动化会话暂停清理尚未完成"`，等待 `instance status` 中 `backgroundTasks.active == false` 后再查询。
6. **Windows PowerShell 5.1 UTF-8 规则 & PuerTS 探针限制**：
   - CLI 含中文或 JSON 参数一律通过 `--file` / `--args-file` 或 UTF-8 `.py` 脚本使用 `subprocess.list2cmdline` 调用，切勿在 PS 5.1 管道或 `python -c` 中内联中文；运行期 JS `runtime js eval` 中避免多参数 `GetComponentsInChildren` 与 `FindObjectsOfType`。

---

## 四、验收回执与后续工作

### 已完成的 v3 实景验收

- 本轮复用前台实例 `993d993d-fe6a-44b0-87f9-9c6d2f95ef69`。前台被覆盖时，`runtime start` 曾停在 `loading`。切回编辑器后，同一代次恢复为 `running`。
- 移除请求 `shiguang-25d-v4-remove-old` 和导入请求 `shiguang-25d-v4-import` 均为 `committed`。环境补丁返回 `appliedToScene: true`。
- C/D 与最终 HUD 使用 Runtime `55c3921a-707c-4595-9c62-8cbfc3b77522`。探针用于观测和摆放玩家，收获、开对话、翻页、赠礼及告别均经键鼠输入。两张立绘截图分别拍于赠礼前后，对应 `amuFrame01`、`amuFrame02`。
- 最终 HUD 在 `[119.742, 80.502, 88.641]`、相机俯角 `36°` 时采集。最终保存请求 `shiguang-25d-v4-final-save` 返回 `committed`、`hasUnsavedChanges: false`，操作 ID 为 `44f9cc0973482476847ddb37e121b8bbeeee9aec408be7343198f0f7154c6d7a`。

### v3 原复工步骤（已执行，供查阅）
1. **启动或连接造世界实例**（若无前台窗口，可直接起无头实例，并在结尾关闭）：
   ```powershell
   douyin-world instance start --project "C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390" --mode offscreen --idle 15 --startup-timeout 120 --json
   ```
2. **环境补丁 + 清理旧根 + 导入 v3 WPrefab**：
   - 执行 `douyin-world scene environment set --file workspace\data\windwaker_env_patch.json --instance <ID> --json`
   - 尝试 `douyin-world scene remove -1522262027 --instance <ID> --json`（若未找到旧根则跳过）
   - 执行 `douyin-world scene import` 导入 `eitflflegg6eihqv.wprefab`，坐标 `--position 115,79.35,86`，名称 `--name 时光小筑2.5D风之杖抱月湾`，新 `--request-id shiguang-25d-v4-import --timeout-ms 240000`；若超时则调用一次 `douyin-world scene cancel shiguang-25d-v4-import` 检查是否已 `committed`。
3. **启动运行态预览并完成未闭环验收**：
   ```powershell
   douyin-world runtime start --wait 60 --instance <ID> --timeout-ms 120000 --json
   ```
   - **HUD v3 复核**：截取 [ww-runtime-spawn-25d.png](workspace/debug/ww-runtime-spawn-25d.png) 并核验左上角胶囊无设计术语、位置不遮挡摇杆或系统按键。
   - **Check C（8 格种菜完整流程）**：移至 `Plot_1` → 播种 `radish` → 浇水确认湿土与减半倒计时 → 等待 ~15s 成熟 → 验证 `P1_Stage3_Radish` 激活并截图 `workspace/debug/ww-runtime-farming.png` → 收获确认背包 `萝卜 1`。
   - **Check D（对话与左侧 8fps 动画）**：移至 `NPC_Amu` 旁记录初始坐标 → 打开对话 → 验证 NPC 未移动且 `HideUI()` 隐藏系统摇杆 → 间隔 ~26 帧截取 `ww-runtime-dialogue-f1.png` 与 `ww-runtime-dialogue-f2.png` 验证底部对话盒 + 左侧立绘切帧变化 → 验证 `NextLine`、`GiftCrop`（萝卜 `1→0`、贝壳币 `+12`）与 `CloseDialogue` 恢复 UI。
4. **净场检查与保存**：
   - `douyin-world runtime verifyNoTempHooks --instance <ID> --runtime-id <RID> --json`
   - `douyin-world runtime stop --instance <ID> --runtime-id <RID> --json`
   - `douyin-world scene save --request-id shiguang-25d-v4-save --instance <ID> --timeout-ms 120000 --json`（核对 `hasUnsavedChanges: false`）
   - 若本轮新起了 `offscreen` 实例，收尾执行 `douyin-world instance stop --instance <ID> --json`。

### 阶段 2：内容替换（待外部资产就绪后）
1. **替换 NPC 3D 占位**：待所有角色骨骼绑定完成后，仅在 [windwaker_scene_manifest.json](workspace/data/windwaker_scene_manifest.json) / WPrefab 中替换 `NPC_Amu` 与 `NPC_Mianmian` 模型，并按需接入轻量移动/待机动作（仅站桩互动，对话不位移）。
2. **接入真实绿幕人物动画**：用 [greenscreen_to_frames.py](workspace/scripts/greenscreen_to_frames.py) 将生成好的绿幕人物视频导出透明 PNG 帧序列覆盖 `amuFrame01..08.png` / `mianmianFrame01..08.png`，执行 `resource ui check` → `archive` 更新 UI 节点即可生效。
3. **补齐剩余 2.5D 微交互与文档收口**：验收完成后同步更新 [项目理解与总览.md](项目理解与总览.md)。

---

## 五、v4.1 接续进展与当前断点（2026-11-25 下午）

### 1. 已完成的本地工程与云端归档
- **本地 Tripo FBX 零积分优化与入库（v4.1）**：
  - 使用 [prepare_fbx_tripo.py](workspace/scripts/prepare_fbx_tripo.py) 转换 `P06` 星盘观测仪（196 万 → `8,000` 面，[P06-mini-armillary-sphere.glb](workspace/assets/models/tripo-optimized/P06-mini-armillary-sphere.glb)）与 `U01` 纸片宠物立牌（197 万 → `3,000` 面，[U01-paper-pet-standee.glb](workspace/assets/models/tripo-optimized/U01-paper-pet-standee.glb)）。
  - 均已通过 `resource model check` 并归档至作者区（URI 已更新至 [windwaker_asset_uris.json](workspace/data/windwaker_asset_uris.json)）：
    - `model-p06-tripo`: `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/y2v6iyx5ibejl7bd.glb`
    - `model-u01-tripo`: `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/rav6btlz747bpaa9.glb`
- **v4.1 WPrefab 已校验、构建并归档**：
  - 通过 [add_p06_u01_to_prefab.js](workspace/scripts/add_p06_u01_to_prefab.js) 在保留 Codex v4 成果（Tripo 萝卜 `FarmGarden`、`F03_BeachDiscovery`、`F23a/b_CliffCottage`）基础上新增 `P06_Armillary_West`、`P06_Armillary_North`、`U01_PaperPet_Courtyard`；`prefab validate` 零报错零警告，已归档为：
    `hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/y7gbk41sh5cgq9ti.wprefab`
- **分部件建模参考图（15 张纯白底 PNG 已就绪）**：
  - 存放于 [workspace/assets/3d-modeling-closeups/parts/](workspace/assets/3d-modeling-closeups/parts/)（四角最小 RGB ≥ 242，零文字）：`F15_part_tower.png`、`F15_part_blades.png`、`F14_part_pergola.png`、`F14_part_swing.png`、`F17_part_tree_bare.png`、`F17_part_fruit_peach.png`、`F06_part_planter_empty.png`、`F06_part_flower_bloom.png`、`F07_part_pole_only.png`、`F16_part_gazebo.png`、`F16_part_telescope.png`、`Part_windchime_strand.png`、`P04_part_post.png`、`F42_part_signpost.png`、`F42_part_bicycle.png`。
- **多部件拼装、GLB 校验与批量入库流水线已备妥并完成冒烟验证**：
  - [verify_multipart_glbs.py](workspace/scripts/verify_multipart_glbs.py)：二进制解析 GLB 节点树并生成 `nodeMergeBlacklist` 路径表（已在 `farm-garden-v4.glb` 64 项子节点上验证）。
  - [assemble_multipart_models.py](workspace/scripts/assemble_multipart_models.py)：Blender 5.3 分部件归零轴心拼装脚本，覆盖 `F15/F14/F17/F06/F07/F16/P04/F42`（含程序化 `[0,1]×[0,1]` UV 的 `FlagClothPivot` 旗面，已通过 `--test-flag-only` 实测）。
  - [tripo_batch_manifest.json](workspace/data/tripo_batch_manifest.json) & [batch_import_tripo_assets.py](workspace/scripts/batch_import_tripo_assets.py)：待 Batch 1（10 件）与分部件模型下载至 `Downloads` 后即可一键减面、写入 `nodeMergeBlacklist`、按真实地形高程批量置入并重打包。

### 2. 当前阻塞点（需用户回到电脑旁处理）
1. **Tripo Studio 账号登录态隔离**：
   - Antigravity 内置浏览器访问 `https://studio.tripo3d.com/workspace/generate` 时显示未登录（右上角为「注册/登录」、积分 `?`、资产列表为空）。
   - 会话中新安装的 `Chrome DevTools` MCP 插件工具在当前运行会话中尚未启用（报错 `tool list_pages is not enabled for server chrome_devtools`），无法直接接管桌面端已登录的 Chrome。
   - **恢复方式**：在内置浏览器中登录 Tripo Studio，或重启对话后启用 `chrome_devtools` 连接到原 Chrome，批量导出 12:48 已提交的 Batch 1（10 件）至 `Downloads`，并用剩余 `1,060` 积分提交 `parts/` 下的 15 张分部件图 + `F12/F13a/b/c/C06/C08`。
2. **造世界前台窗口被遮挡导致 `v4.1` 主场景导入挂起**：
   - 实例 `993d993d-fe6a-44b0-87f9-9c6d2f95ef69` 上已完成 `scene remove -1577082918`，但 `scene import`（请求 ID：`shiguang-25d-v41-import`）触发编辑器 `LogicApiMono.ImportNodeDataFromUriAsync` 时因 `suspendReasons: ["hidden-runtime-canvas"]` 导致 Unity 主循环降频至约 1 帧/分钟而挂起；磁盘 `scene.data` 尚未覆盖保存，仍安全保留 v3。
   - **恢复方式**：将桌面上的「造世界编辑器」窗口点回前台让导入完成，然后执行 `douyin-world scene operation shiguang-25d-v41-import --instance 993d993d-fe6a-44b0-87f9-9c6d2f95ef69 --json` 核验 `committed` 并执行 `scene save`。
