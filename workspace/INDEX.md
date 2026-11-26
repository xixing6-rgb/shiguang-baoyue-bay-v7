# 《时光小筑》本地创作项目索引（4× 叙事完整版）

> 对应机器可读索引：[project-index.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/project-index.json)

## 1. 项目绑定信息

| 字段 | 值 | 说明 |
| --- | --- | --- |
| `projectName` | 新世界项目 | 编辑器项目显示名 |
| `projectDirName` | `project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5` | 编辑器项目目录名（短 ID） |
| `worldId` | `12054206254850` | 世界 ID |
| `worldType` | `avatar` | 世界类型 |
| `workspaceId` | `workspace_024l9gls` | 时光小筑作者工作区 |
| `v1Baseline` | `方案 C · 时光小筑 (64m × 56m)` | 零改动保留于老镇核心区 `Zone 0` (`3,584 m²`，`F01–F18`) |
| `v2Expansion` | **`4× 抱月双岬 + 离岸潮汐小屿`** | **`136m × 122m` 抱月海湾（可步行陆地 ~`14,170–14,334 m²`，外海 `184m × 168m`），`L-0.5 / L0 / L1 / L2 / L3(+5.4m)` 4+1 级微高差，5 大片区 / `F01–F42`（51 实例）/ 9 位居民** |
| 机器索引 | [project-index.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/project-index.json) | 结构化项目索引与状态记录 |

---

## 2. 本地目录索引与核心文档

| 目录 | 用途说明 |
| --- | --- |
| `docs/` | 策划文档、美术对齐圣经、4× 地图研究与规划、五幕叙事总纲、角色小剧本、62 项特写审计 |
| `data/` | 离线可加载叙事数据库（`narrative-db.json/.js`）与全角色小剧本库（`character-mini-scripts.json/.js`） |
| `assets/references/art-bible/` | 方案 C《时光小筑》美术对齐基准图集（8 张专向 PNG + `scheme-a/b/c`） |
| `assets/3d-modeling-closeups/` | **62 项 AI 3D 建模级干净特写 PNG**（含全 9 位标准正面水平 **T-Pose** 居民）+ 4 张联络表（`_contact-sheets/`） |
| `assets/models/` | Blender 5.3 导出 4× 地形（`map-shiguang-town-4x.glb`）、4× 硬装（`town-hardscape-4x.glb`）及 `landmarks-4x/`（31 个 Y-up GLB） |
| `scripts/` | Blender 4× 生成脚本、Codex 生图脚本、Hamlet Lua 5.3 脚本（`scripts/lua/`）、Scene SDK 绑定与自动化校验脚本 |
| `exports/` | `.wprefab` 本地可编辑包（原版 `shiguang-town-complete.wprefab`） |
| `debug/` | 运行态与 Blender 4× 验收截图（`town-4x-*.png`）及 15 条路线连续性审计报告（`route-audit-4x.json`） |
| `../interactive-demos/` | **离线直接可玩《时光小筑》4× 叙事游戏（`shiguang-narrative-game.html`）**、**4× 数字蓝图（`town-layout-blueprint-4x.html`）** 与美术对齐看板 |

### 核心文档清单

| 文档 | 用途 | 路径 |
| --- | --- | --- |
| 4× 地图设计专题研究 | 9 款标杆游戏空间研究与抱月湾 4× 方案论证 | [map-design-research-4x.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/map-design-research-4x.md) |
| **4× 小镇规划工程总纲** | **136m×122m 坐标、4+1 高差、F01–F42 布局、坡道与雾效参数** | [town-masterplan-4x.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/town-masterplan-4x.md) |
| **五幕叙事设计圣经** | **世界观、五幕主线软门控、9 居民档案、26 记忆碎片、86 黑板台词与 Tracery 词库** | [narrative-design-and-script.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/narrative-design-and-script.md) |
| **角色阶段小剧本（Gemini 4 Neon）** | **9 位居民 × 3 阶段 = 27 幕 + 3 段偶遇（254 句），严格平台动作/存储边界** | [character-mini-scripts.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/character-mini-scripts.md) |
| **62 项特写与画风终审报告** | **62 项 AI 3D 建模级干净特写（全 T-Pose 居民）逐项尺寸与审定结果** | [asset-closeup-style-audit.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/asset-closeup-style-audit.md) |
| 原版前期规划与美术圣经 | 平台可行性审计与原版 `64m×56m` 方案规范 | [preproduction-plan.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/preproduction-plan.md) · [town-masterplan-and-art-bible.md](file:///C:/Users/Administrator/Desktop/抖音/workspace/docs/town-masterplan-and-art-bible.md) |

---

## 3. 交互式游戏原型与数字蓝图（零 CDN · 双击 `file://` 即玩）

| 文件 | 功能说明 | 链接 |
| --- | --- | --- |
| **4× 完整叙事游戏可玩版** | WASD/点击散步、五幕主线软门控、9 居民 Utility AI 与 27+3 阶段小剧本、抓起轻推、四色气泡、WebAudio Animalese/机械电音、室内剖面、渡船/滑道/单车驿站、孟德尔花圃、12×12 像素旗、黑板流行语与 62 项特写图鉴 | [shiguang-narrative-game.html](file:///C:/Users/Administrator/Desktop/抖音/interactive-demos/shiguang-narrative-game.html) |
| **4× 空间规划与 2.5D 蓝图** | 2D 平面/2.5D 轴测切换、5 大片区与 5 级高差过滤、章节演进滑块、三时段引力热力图、35° 遮挡安全层、点击即看设施 3D 特写图 | [town-layout-blueprint-4x.html](file:///C:/Users/Administrator/Desktop/抖音/interactive-demos/town-layout-blueprint-4x.html) |
| **美术对齐对照板** | 原圣经基准图 + 第五组 4 张全量 62 项特写联络表 | [art-alignment-board.md](file:///C:/Users/Administrator/Desktop/抖音/interactive-demos/art-alignment-board.md) |

---

## 4. 4× 3D 场景工程、Hamlet Lua 5.3 脚本与特写资产总览

### 4.1 4× 地图与 Blender 5.3 交付件
- **SCAD 与 Layout（保留 `*-v1` 备份）**：`scene.scad` / `layout.json` / [town-building-layout.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/town-building-layout.json)
- **Blender 5.3 产出 GLB**：
  - 4× 抱月湾地形：[map-shiguang-town-4x.glb](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/models/map-shiguang-town-4x.glb)（脚本：[build-town-terrain-4x.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/build-town-terrain-4x.py)）
  - 4× 环湾硬装与桥道：[town-hardscape-4x.glb](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/models/town-hardscape-4x.glb)（脚本：[build-town-hardscape-4x.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/build-town-hardscape-4x.py)）
  - 31 个新增地标/生态 GLB：`assets/models/landmarks-4x/*.glb`（脚本：[build-new-landmarks-4x.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/build-new-landmarks-4x.py)）
- **4× 路线连续性与渲染验收**：
  - [route-audit-4x.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/debug/route-audit-4x.json)：15 条主次路径共 `3,564` 个采样点，最大坡度 **`17.23°`**（`≤ 18.5°`），`issueCount = 0`。
  - 渲染证据：[平面图](file:///C:/Users/Administrator/Desktop/抖音/workspace/debug/town-4x-site-plan.png) · [35° 斜俯视](file:///C:/Users/Administrator/Desktop/抖音/workspace/debug/town-4x-overview.png) · [全镇 4× 51 实例总装鸟瞰](file:///C:/Users/Administrator/Desktop/抖音/workspace/debug/town-4x-full-assembly.png)

### 4.2 叙事数据库与 Hamlet Lua 5.3 正式脚本（11 脚本全量校验通过）
- **结构化数据**：[narrative-db.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/data/narrative-db.json) · [narrative-db.js](file:///C:/Users/Administrator/Desktop/抖音/workspace/data/narrative-db.js) · [character-mini-scripts.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/data/character-mini-scripts.json) · [character-mini-scripts.js](file:///C:/Users/Administrator/Desktop/抖音/workspace/data/character-mini-scripts.js)
- **7 个新 Hamlet Lua 5.3 脚本**（同步写入 `workspace/scripts/lua/` 与 `creator-project/.../wprefabs/shiguang-town/scripts/`）：
  - `narrative-host.lua`、`resident-utility-ai.lua`、`blackboard-dialogue-engine.lua`、`smart-object-broadcaster.lua`、`fast-travel-and-ferry.lua`、`time-weather-lighting.lua`、`ugc-flag-chalkboard-pet.lua`
- **Scene SDK 绑定**：[bind-scripts-4x.js](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/bind-scripts-4x.js)
- **自动化验证**：[verify-lua-scripts.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/verify-lua-scripts.py) · [verify-mini-scripts.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/verify-mini-scripts.py) · [verify-all-deliverables.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/verify-all-deliverables.py)

### 4.3 62 项 3D 建模特写与联络表
- **清单与指标**：[manifest.json](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/manifest.json) · [codex-gen-closeup.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/codex-gen-closeup.py) · [build-contact-sheets.py](file:///C:/Users/Administrator/Desktop/抖音/workspace/scripts/build-contact-sheets.py)
- **4 张对比联络表**：
  - [联络表 1（老镇 F01–F18）](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-1-core-town-F01-F18.png)
  - [联络表 2（东西翼 F19–F31）](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-2-expansion-west-east-F19-F31.png)
  - [联络表 3（北麓南屿 F32–F42）](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-3-expansion-north-south-F32-F42.png)
  - [联络表 4（9 位 T-Pose 居民与道具 C01–U01）](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-4-residents-props-C01-U01.png)

---

## 5. 原版 v1 历史归档与星光记录（保留参考）
- 原版 64×56m WPrefab：`exports/shiguang-town-complete.wprefab`（53,516 三角面，`0` 星光消耗）；原版实机验收截图保留于 `debug/p1-*.png` 与 `debug/town-full-*.png`。
- 本次 4× 扩容与 62 项特写工作全部采用本机 Blender 5.3、Hamlet Lua 5.3、HTML5 及本机 Codex `image_gen` 完成，**造世界编辑器星光消耗新增 = 0**。
