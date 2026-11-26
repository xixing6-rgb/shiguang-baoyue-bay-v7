# 《时光小筑》项目完整打包清单与还原说明

- 打包时间：2026-11-22 22:34:26
- 工程代号：`project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5`（新世界项目 / `shiguang-town`）

## 1. 归档内容统计

| 压缩包目录 / 文件 | 来源说明 | 文件数 | 原始体积 (字节) |
| --- | --- | ---: | ---: |
| `动森.txt` | 桌面原始需求与灵感文本 | 1 | 65,293 |
| `workspace/` | 本地创作工作区（策划文档、美术参考、脚本、导出 WPrefab、实机截图等） | 75 | 30,740,797 |
| `creator-project/project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5/` | 抖音造世界编辑器工程根目录（`scene.data`、`project.json`、`ai-sessions/workspace_024l9gls/` 源码与构建包等） | 201 | 19,776,129 |
| `interactive-demos/` | 前期交互式网页原型与美术对齐看板（HTML / MD） | 3 | 106,096 |
| `PACKAGE_MANIFEST.md` | 本清册与还原说明 | 1 | — |

## 2. 跨机还原说明

### 方式一：还原完整造世界编辑器工程
1. 先完全关闭「抖音造世界」客户端。
2. 将 `creator-project/project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5/` 完整解压复制到目标电脑的：
   `%APPDATA%\AI World Creator\projects\project-a9b73cc9-cfbc-4006-a8df-f5f44f1279a5\`
3. 可选：将 `workspace/` 解压到任意工作目录（如桌面 `抖音\`），打开客户端即可看到并编辑「新世界项目」。

### 方式二：仅导入小镇 WPrefab 资源
1. 在已有造世界工程中导入 `workspace/exports/shiguang-town-complete.wprefab`（或 `shiguang-town-ensemble.wprefab`）。
2. 场景落点参数与配套源码说明见 `workspace/INDEX.md` 及 `workspace/project-index.json`。
