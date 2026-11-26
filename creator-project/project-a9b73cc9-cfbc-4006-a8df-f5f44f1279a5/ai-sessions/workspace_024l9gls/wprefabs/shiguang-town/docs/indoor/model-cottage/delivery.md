# 《时光小筑主木屋》交付说明（Stage 4: Delivery）

- **资产路径**：
  - 源码：`wprefabs/shiguang-town/assets/models/model-cottage/static/preview-module.js`
  - 元数据：`wprefabs/shiguang-town/assets/models/model-cottage/meta.json`（已设置 `nodeMergeBlacklist: ["CottageRoot/DoorPivot"]`）
  - 归档包：`wprefabs/shiguang-town/assets/models/model-cottage/package/model.glb`
  - 正式 URI：`hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/ptytoyd68l8ke9hv.glb`
- **局部边界与接口**：
  - 包络尺寸：宽 `8.0m` × 深 `6.0m` × 高 `4.8m`，局部 `+Y` 向上、`+Z` 为正面朝向庭院与南侧海湾。
  - 入户基准面：台阶底部落在局部 `Y = 0`，室内完成面 `Y = 0.24m`。
  - 独立门扇节点：`CottageRoot/DoorPivot`（铰链在 `(-0.71, 0.24, 1.39)`，初始旋转 `[0,0,0]`，向室内 `-Z` 旋转 `+86°` 开启）。
- **已验证与待验证边界**：
  - 已通过 `model check`、`resource archive` 与 `inspect-model` 三向正交图（`exterior.png`）检查。
  - 室内行走碰撞、DoorPivot 自动开门交互与室内视角实景留待 Runtime 启动后验证。
