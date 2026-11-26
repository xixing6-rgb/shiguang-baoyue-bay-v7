# 《时光小筑》全量 62 项 AI 3D 建模特写资产清单与画风终审报告

> **审定范围**：原老镇核心 `F01–F18`（含 F13 拆分三栋 = 20 项）+ 4× 扩容新增地标 `F19–F42`（24 项）+ 全部 9 位标准正面水平 **T-Pose** 动物居民 `C01–C09` + 高频叙事微道具 `P01–P06` + 生态树木 `E01–E02` + 2D 纸片宠物 `U01`，总计 **62 项**。
> **生成方式**：本机 Codex CLI 0.167.1 内置 `image_gen` 工具 + `workspace/scripts/codex-gen-closeup.py`，以《时光小筑》美术圣经（`01/04/05/06/07` 及 `scheme-b`）为风格锚点。
> **总联络表**：
> - [sheet-1-core-town-F01-F18.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-1-core-town-F01-F18.png)
> - [sheet-2-expansion-west-east-F19-F31.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-2-expansion-west-east-F19-F31.png)
> - [sheet-3-expansion-north-south-F32-F42.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-3-expansion-north-south-F32-F42.png)
> - [sheet-4-residents-props-C01-U01.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/_contact-sheets/sheet-4-residents-props-C01-U01.png)

---

## 一、7 维终审对齐标准与实测统计

1. **纯净无影棚背景**：全 62 张四角像素实测最小 RGB 通道值 **≥ 241**（纯白/极浅暖奶白 `#FFFFFF / #FAF8F5`），无草皮、沙滩、海面、地平线、重阴影或网格水印。
2. **AI 3D 建模友好构图**：非角色类均采用单一孤立主体居中 + 3/4 清晰透视正交感 + 柔和漫射软箱白光，完整展现立面与屋脊/风叶/树冠顶端，零裁切。
3. **全部 9 位居民标准正面 T-Pose 一票否决项**：初始校准 `C01` 采用 A-Pose，经阶段指令统一重构模板后已对 `C01–C09` **全部强制重生成为双臂（含猫头鹰双翼）水平 90° 伸展、空手不遮挡躯干、左右留白充足的正面标准 T-Pose**，直接对接 `douyin-world generation start rig` 与 AI 3D 重建。
4. **绘本暖阳造型倒角质感**：全批保持 2–4cm 柔和圆角木玩与哑光软泥黏土质感（粗糙度 `0.75–0.88`），无写实脏旧噪点与黑线描边（仅 `U01` 依 `scheme-b` 契约保留 2D 白底黑线纸板立牌反差美学）。
5. **PAD 色板一致性**：严格锁定 `#E4BA8B` 浅原木、`#B96A59` 暖陶红瓦、`#FFF5E4` 奶油白、`#B7DDA8 / #93C794` 鼠尾草绿、`#7CC6E8` 薄荷浅蓝、`#FFD67A` 琥珀暖光与 `#5A587D` 紫灰暗部。
6. **题材特征零文字准确度**：黑板无字涂鸦、指路牌纯图标、邮筒无英文字母、三果实树精确 3 颗圆果、12×12 像素鱼旗与 9 种动物品种服装全对位。
7. **跨图家族一致性**：四张联络表联排审视下全员高度同源，**终审通过率 62 / 62 (100%)**。

### 校准与返工历史记录
- **Pilot #1 (`F04-main-cottage`)**：一次校准通过（`1440x1092`，纯白底无草坪、层叠红瓦与拱门窗完整）。
- **Pilot #2 (`C01-glasses-bear`)**：首版产出为 30° 下垂 A-Pose；随后按标准 T-Pose 规范升级 `codex-gen-closeup.py` 与 `manifest.json` 并强制 `--force` 重生成后（`1448x1086`），双臂水平 90° 展开、画风完美对齐，全员 `C01–C09` 一次性达成 T-Pose 终审通过。

---

## 二、62 项独立资产明细总表

| 编号 | ID | 中文名称 | 批次 | 类别 | 设计尺度 | 图幅 (px) | 参考基准 | 终审结果 | 资产特写链接 |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :--- | :---: | :--- |
| `F01` | `F01-arrival-dock` | 登岛小码头 | A | `architecture` | 6.0m x 5.0m x 2.6m | 1536x1024 | facilities, daylight | **PASS** | [F01-arrival-dock.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F01-arrival-dock.png) |
| `F02` | `F02-fishing-pier` | 木质钓鱼栈桥 | A | `architecture` | 4.0m x 8.0m x 2.2m | 1679x937 | daylight, facilities | **PASS** | [F02-fishing-pier.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F02-fishing-pier.png) |
| `F03` | `F03-beach-discovery` | 漂流瓶与海星贝壳礁石组 | A | `prop` | 2.4m x 1.8m x 0.9m | 1536x1024 | foliage, facilities | **PASS** | [F03-beach-discovery.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F03-beach-discovery.png) |
| `F04` | `F04-main-cottage` | 时光小筑主木屋 | A | `architecture` | 8.0m x 6.0m x 4.8m | 1440x1092 | daylight, interior | **PASS (校准样张)** | [F04-main-cottage.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F04-main-cottage.png) |
| `F05` | `F05-coffee-terrace` | 户外咖啡茶桌露台 | A | `architecture` | 5.0m x 4.0m x 1.4m | 1536x1024 | daylight, interior | **PASS** | [F05-coffee-terrace.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F05-coffee-terrace.png) |
| `F06` | `F06-mendel-flowerbed` | 孟德尔杂交花圃 | A | `prop` | 6.0m x 4.0m x 1.0m | 1448x1086 | daylight, foliage | **PASS** | [F06-mendel-flowerbed.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F06-mendel-flowerbed.png) |
| `F07` | `F07-pixel-flagpole` | 12x12像素小鱼旗杆 | A | `prop` | 1.6m x 1.6m x 4.2m | 1024x1536 | facilities, daylight | **PASS** | [F07-pixel-flagpole.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F07-pixel-flagpole.png) |
| `F08` | `F08-chalkboard` | 庭院涂鸦留言黑板 | A | `prop` | 2.0m x 1.2m x 1.8m | 1254x1254 | facilities, daylight | **PASS** | [F08-chalkboard.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F08-chalkboard.png) |
| `F09` | `F09-wish-fountain` | 中心心愿喷泉 | A | `architecture` | 6.0m x 6.0m x 2.2m | 1448x1086 | facilities | **PASS** | [F09-wish-fountain.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F09-wish-fountain.png) |
| `F10` | `F10-retro-vending` | 复古马卡龙自动售货机 | A | `prop` | 2.5m x 2.0m x 2.4m | 1254x1254 | facilities | **PASS** | [F10-retro-vending.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F10-retro-vending.png) |
| `F11` | `F11-plaza-benches` | 广场八卦长椅与花盆组 | A | `prop` | 5.0m x 2.5m x 1.2m | 1679x937 | facilities, daylight | **PASS** | [F11-plaza-benches.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F11-plaza-benches.png) |
| `F12` | `F12-cafe-kiosk` | 露天海风条纹咖啡小卖部 | A | `architecture` | 5.0m x 4.0m x 3.4m | 1394x1128 | facilities | **PASS** | [F12-cafe-kiosk.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F12-cafe-kiosk.png) |
| `F13a` | `F13a-house-amber` | 居民萌屋·琥珀屋 | A | `architecture` | 5.0m x 4.5m x 4.0m | 1448x1086 | daylight, facilities | **PASS** | [F13a-house-amber.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F13a-house-amber.png) |
| `F13b` | `F13b-house-sage` | 居民萌屋·鼠尾草屋 | A | `architecture` | 5.0m x 4.5m x 4.4m | 1448x1086 | daylight, foliage | **PASS** | [F13b-house-sage.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F13b-house-sage.png) |
| `F13c` | `F13c-house-blue` | 居民萌屋·海风屋 | A | `architecture` | 5.0m x 4.5m x 3.8m | 1448x1086 | facilities, daylight | **PASS** | [F13c-house-blue.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F13c-house-blue.png) |
| `F14` | `F14-swing-pavilion` | 社区秋千与小吉他亭 | A | `architecture` | 5.0m x 5.0m x 3.2m | 1448x1086 | daylight, facilities | **PASS** | [F14-swing-pavilion.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F14-swing-pavilion.png) |
| `F15` | `F15-windmill-tower` | 北高台八角木质风车塔 | A | `architecture` | 5.0m x 5.0m x 8.5m | 1086x1448 | foliage, daylight | **PASS** | [F15-windmill-tower.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F15-windmill-tower.png) |
| `F16` | `F16-sunset-overlook` | 日落观景望远镜木亭 | A | `architecture` | 5.0m x 3.0m x 3.5m | 1254x1254 | daylight, facilities | **PASS** | [F16-sunset-overlook.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F16-sunset-overlook.png) |
| `F17` | `F17-three-fruit-tree` | 三果实标志圆润果树 | A | `flora` | 3.2m x 3.2m x 4.4m | 1254x1254 | foliage | **PASS** | [F17-three-fruit-tree.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F17-three-fruit-tree.png) |
| `F18` | `F18-memory-stone-corner` | 时光石与纸片宠物打卡坪 | A | `prop` | 4.5m x 4.0m x 2.2m | 1347x1167 | facilities, paperPet | **PASS** | [F18-memory-stone-corner.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F18-memory-stone-corner.png) |
| `F19` | `F19-windchime-post-office` | 风铃旧邮局 | B | `architecture` | 9.0m x 7.0m x 5.5m | 1448x1086 | daylight, facilities | **PASS** | [F19-windchime-post-office.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F19-windchime-post-office.png) |
| `F20` | `F20-mailbox-gallery` | 阶梯复古信箱画廊与邮包棚 | B | `architecture` | 6.0m x 4.0m x 3.2m | 1448x1086 | facilities, daylight | **PASS** | [F20-mailbox-gallery.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F20-mailbox-gallery.png) |
| `F21` | `F21-windchime-corridor` | 海岬风铃长廊与信号旗台 | B | `architecture` | 8.0m x 4.0m x 3.8m | 1679x937 | daylight, facilities | **PASS** | [F21-windchime-corridor.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F21-windchime-corridor.png) |
| `F22` | `F22-west-cape-lighthouse` | 西岬旧灯塔 | B | `architecture` | 7.0m x 7.0m x 11.5m | 1168x1346 | facilities, daylight | **PASS** | [F22-west-cape-lighthouse.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F22-west-cape-lighthouse.png) |
| `F23` | `F23-cliff-cottage` | 西北山崖灰蓝尖瓦萌屋 | B | `architecture` | 5.5m x 4.5m x 4.2m | 1254x1254 | daylight, facilities | **PASS** | [F23-cliff-cottage.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F23-cliff-cottage.png) |
| `F24` | `F24-driftwood-campfire` | 西滩漂流木篝火角 | B | `prop` | 6.0m x 5.0m x 1.4m | 1536x1024 | foliage, daylight | **PASS** | [F24-driftwood-campfire.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F24-driftwood-campfire.png) |
| `F25` | `F25-bakery-kiln-stall` | 微光夜市红砖烤包窑炉与串灯木摊 | B | `architecture` | 6.0m x 5.0m x 4.0m | 1536x1024 | facilities, daylight | **PASS** | [F25-bakery-kiln-stall.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F25-bakery-kiln-stall.png) |
| `F26` | `F26-old-boatyard` | 旧造船木工坊 | B | `architecture` | 10.0m x 8.0m x 5.0m | 1254x1254 | daylight, facilities | **PASS** | [F26-old-boatyard.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F26-old-boatyard.png) |
| `F27` | `F27-daylight-lightship` | 搁浅的白昼号潮汐灯船 | B | `architecture` | 11.0m x 5.0m x 9.5m | 1460x1077 | facilities, daylight | **PASS** | [F27-daylight-lightship.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F27-daylight-lightship.png) |
| `F28` | `F28-tidepool-rocks` | 潮间带海蚀圆礁石与浅池组 | B | `prop` | 4.5m x 3.8m x 1.5m | 1536x1024 | foliage | **PASS** | [F28-tidepool-rocks.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F28-tidepool-rocks.png) |
| `F29` | `F29-kite-terrace-bench` | 茶花梯田木阶与纸风筝架 | B | `architecture` | 5.0m x 4.0m x 2.8m | 1679x937 | daylight, foliage | **PASS** | [F29-kite-terrace-bench.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F29-kite-terrace-bench.png) |
| `F30` | `F30-studio-cottage` | 东岸芥末黄工坊画室萌屋 | B | `architecture` | 5.5m x 4.5m x 4.2m | 1448x1086 | daylight, facilities | **PASS** | [F30-studio-cottage.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F30-studio-cottage.png) |
| `F31` | `F31-memory-greenhouse` | 溪谷记忆温室与森林图书馆 | B | `architecture` | 12.0m x 9.0m x 6.2m | 1536x1024 | interior, daylight, foliage | **PASS** | [F31-memory-greenhouse.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F31-memory-greenhouse.png) |
| `F32` | `F32-creek-arch-bridge` | 萤火浅溪原木拱桥 | C | `architecture` | 6.0m x 2.6m x 2.0m | 1672x941 | foliage, daylight | **PASS** | [F32-creek-arch-bridge.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F32-creek-arch-bridge.png) |
| `F33` | `F33-forest-watermill` | 森林水车磨坊与旧留声亭 | C | `architecture` | 7.0m x 6.0m x 4.8m | 1536x1024 | daylight, facilities | **PASS** | [F33-forest-watermill.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F33-forest-watermill.png) |
| `F34` | `F34-camphor-bell-pavilion` | 古樟星穹钟楼与环树观景台 | C | `architecture` | 12.0m x 10.0m x 12.5m | 1484x1060 | foliage, daylight | **PASS** | [F34-camphor-bell-pavilion.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F34-camphor-bell-pavilion.png) |
| `F35` | `F35-timber-slide` | 林间快速下行圆木滑道组件 | C | `architecture` | 2.4m x 8.0m x 3.2m | 1536x1024 | daylight, foliage | **PASS** | [F35-timber-slide.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F35-timber-slide.png) |
| `F36` | `F36-tree-hollow-postbox` | 北林秘密树洞邮筒与回忆相框 | C | `prop` | 4.5m x 4.0m x 3.5m | 1448x1086 | foliage, interior | **PASS** | [F36-tree-hollow-postbox.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F36-tree-hollow-postbox.png) |
| `F37` | `F37-sea-arch-bridge` | 弧形跨海木拱桥 | C | `architecture` | 12.0m x 2.8m x 3.0m | 1679x937 | facilities, daylight | **PASS** | [F37-sea-arch-bridge.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F37-sea-arch-bridge.png) |
| `F38` | `F38-tidal-stepping-stones` | 东潮汐玄武岩踏石与苔藓柱组 | C | `prop` | 6.0m x 2.6m x 1.2m | 1679x937 | foliage, facilities | **PASS** | [F38-tidal-stepping-stones.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F38-tidal-stepping-stones.png) |
| `F39` | `F39-echo-amphitheater-arch` | 潮汐风铃回声海风拱门 | C | `architecture` | 10.0m x 9.0m x 6.5m | 1536x1024 | facilities, daylight | **PASS** | [F39-echo-amphitheater-arch.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F39-echo-amphitheater-arch.png) |
| `F40` | `F40-wooden-rowboat` | 摇橹小渡船 | C | `prop` | 3.6m x 1.6m x 1.1m | 1536x1024 | facilities, daylight | **PASS** | [F40-wooden-rowboat.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F40-wooden-rowboat.png) |
| `F41` | `F41-mini-book-booth` | 星砂沙洲迷你漂流书屋 | C | `prop` | 2.5m x 2.0m x 2.6m | 1199x1312 | facilities, interior | **PASS** | [F41-mini-book-booth.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F41-mini-book-booth.png) |
| `F42` | `F42-postal-bike-stop` | 复古薄荷绿邮差单车驿站 | C | `prop` | 2.4m x 1.2m x 2.3m | 1679x937 | facilities | **PASS** | [F42-postal-bike-stop.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/F42-postal-bike-stop.png) |
| `C01` | `C01-glasses-bear` | 眼镜棕熊·阿木 | D | `character` | 1.5m x 0.9m x 1.65m | 1448x1086 | characters | **PASS (T-Pose 重生校准)** | [C01-glasses-bear.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C01-glasses-bear.png) |
| `C02` | `C02-lop-rabbit` | 垂耳白兔·绵绵 | D | `character` | 1.2m x 0.7m x 1.2m | 1199x1312 | characters | **PASS (T-Pose)** | [C02-lop-rabbit.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C02-lop-rabbit.png) |
| `C03` | `C03-deadpan-cat` | 面瘫橘猫·阿橘 | D | `character` | 1.25m x 0.8m x 1.3m | 1199x1312 | characters | **PASS (T-Pose)** | [C03-deadpan-cat.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C03-deadpan-cat.png) |
| `C04` | `C04-corgi-baker` | 吃包柯基·奶包 | D | `character` | 1.35m x 0.85m x 1.35m | 1254x1254 | characters | **PASS (T-Pose)** | [C04-corgi-baker.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C04-corgi-baker.png) |
| `C05` | `C05-floating-owl` | 悬浮猫头鹰·墨羽 | D | `character` | 1.25m x 0.75m x 1.05m | 1254x1254 | characters | **PASS (T-Pose)** | [C05-floating-owl.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C05-floating-owl.png) |
| `C06` | `C06-strawhat-fox` | 草帽狐狸·阿澈 | D | `character` | 1.35m x 0.85m x 1.38m | 1199x1312 | characters | **PASS (T-Pose)** | [C06-strawhat-fox.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C06-strawhat-fox.png) |
| `C07` | `C07-postman-otter` | 迷糊邮差水獭·团团 | D | `character` | 1.3m x 0.8m x 1.32m | 1312x1199 | characters | **PASS (T-Pose)** | [C07-postman-otter.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C07-postman-otter.png) |
| `C08` | `C08-carpenter-raccoon` | 强迫症木工小浣熊·咔哒 | D | `character` | 1.35m x 0.85m x 1.35m | 1536x1024 | characters | **PASS (T-Pose)** | [C08-carpenter-raccoon.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C08-carpenter-raccoon.png) |
| `C09` | `C09-artist-sheep` | 纸片画师小羊·绒绒 | D | `character` | 1.32m x 0.85m x 1.30m | 1312x1199 | characters | **PASS (T-Pose)** | [C09-artist-sheep.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/C09-artist-sheep.png) |
| `P01` | `P01-clay-street-lamp` | 暖陶木质矮路灯 | D | `prop` | 0.7m x 0.7m x 1.9m | 1199x1312 | facilities, daylight | **PASS** | [P01-clay-street-lamp.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P01-clay-street-lamp.png) |
| `P02` | `P02-vintage-mailbox` | 歪斜复古薄荷绿海风邮筒 | D | `prop` | 0.7m x 0.7m x 1.35m | 1254x1254 | facilities | **PASS** | [P02-vintage-mailbox.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P02-vintage-mailbox.png) |
| `P03` | `P03-wooden-signpost` | 手绘微倾木质指路牌 | D | `prop` | 0.9m x 0.6m x 1.75m | 1342x1172 | daylight, facilities | **PASS** | [P03-wooden-signpost.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P03-wooden-signpost.png) |
| `P04` | `P04-shell-windchime-post` | 贝壳玻璃风铃木桩 | D | `prop` | 0.8m x 0.8m x 2.1m | 1254x1254 | facilities, daylight | **PASS** | [P04-shell-windchime-post.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P04-shell-windchime-post.png) |
| `P05` | `P05-bakery-food-cart` | 海风烤包木推车 | D | `prop` | 1.8m x 1.1m x 1.9m | 1448x1086 | facilities, daylight | **PASS** | [P05-bakery-food-cart.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P05-bakery-food-cart.png) |
| `P06` | `P06-mini-armillary-sphere` | 暖铜迷你星盘观测仪 | D | `prop` | 0.9m x 0.9m x 1.5m | 1254x1254 | facilities | **PASS** | [P06-mini-armillary-sphere.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/P06-mini-armillary-sphere.png) |
| `E01` | `E01-coastal-pine-tree` | 海风歪颈三团圆蓬松树 | D | `flora` | 3.2m x 2.8m x 4.8m | 1448x1086 | foliage | **PASS** | [E01-coastal-pine-tree.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/E01-coastal-pine-tree.png) |
| `E02` | `E02-autumn-maple-tree` | 北麓柔金奶油枫树 | D | `flora` | 3.4m x 3.2m x 5.2m | 1254x1254 | foliage | **PASS** | [E02-autumn-maple-tree.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/E02-autumn-maple-tree.png) |
| `U01` | `U01-paper-pet-standee` | 2D纸片涂鸦宠物立牌 | D | `ugc` | 0.9m x 0.45m x 0.9m | 1254x1254 | paperPet | **PASS** | [U01-paper-pet-standee.png](file:///C:/Users/Administrator/Desktop/抖音/workspace/assets/3d-modeling-closeups/U01-paper-pet-standee.png) |
