const THREE = require('three');

// 5x5x8.5m 北高台木质风车塔：+Z 为风车正面（朝南瞰海），BladesPivot 保持初始旋转 [0,0,0]
function addBox(parent, name, w, h, d, x, y, z, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y, z); parent.add(m); return m;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'WindmillRoot';
  moduleRoot.add(root);

  const stoneMat = new THREE.MeshStandardMaterial({ color: 0xc2b5a3, roughness: 0.90, metalness: 0.02, side: THREE.FrontSide });
  const bodyWood = new THREE.MeshStandardMaterial({ color: 0xe2b786, roughness: 0.76, metalness: 0.02, side: THREE.FrontSide });
  const trimWood = new THREE.MeshStandardMaterial({ color: 0x8d5634, roughness: 0.78, metalness: 0.03, side: THREE.FrontSide });
  const roofMat = new THREE.MeshStandardMaterial({ color: 0xb96a59, roughness: 0.78, metalness: 0.02, side: THREE.FrontSide });
  const sailCloth = new THREE.MeshStandardMaterial({ color: 0xfff8eb, roughness: 0.82, metalness: 0.0, side: THREE.FrontSide });
  const glowGlass = new THREE.MeshStandardMaterial({ color: 0xffd67a, emissive: 0xffb347, emissiveIntensity: 0.8, roughness: 0.35, side: THREE.FrontSide });

  // 圆石阶底座 (Y: 0..0.52m)
  const baseStep = new THREE.Mesh(new THREE.CylinderGeometry(2.25, 2.40, 0.24, 16), stoneMat);
  baseStep.name = 'WindmillPlinth'; baseStep.position.y = 0.12; root.add(baseStep);
  const stonePed = new THREE.Mesh(new THREE.CylinderGeometry(1.88, 2.02, 0.42, 12), stoneMat);
  stonePed.name = 'WindmillStoneFoundation'; stonePed.position.y = 0.44; root.add(stonePed);

  // 八角渐缩塔身 (Y: 0.64..6.10m)
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(1.18, 1.82, 5.46, 8), bodyWood);
  shaft.name = 'WindmillTowerShaft';
  shaft.rotation.y = Math.PI / 8;
  shaft.position.y = 3.37;
  root.add(shaft);

  // 腰线木环
  [2.5, 4.4, 6.0].forEach((ry, ri) => {
    const rad = 1.82 - ((ry - 0.64) / 5.46) * (1.82 - 1.18);
    const ring = new THREE.Mesh(new THREE.CylinderGeometry(rad + 0.08, rad + 0.08, 0.16, 8), trimWood);
    ring.name = 'TowerBelt_' + ri;
    ring.rotation.y = Math.PI / 8;
    ring.position.y = ry;
    root.add(ring);
  });

  // 正面 (+Z) 门框与小暖窗
  addBox(root, 'DoorFrame', 1.12, 1.85, 0.28, 0, 1.56, 1.62, trimWood);
  addBox(root, 'DoorLeaf', 0.88, 1.68, 0.32, 0, 1.50, 1.64, bodyWood);
  addBox(root, 'UpperWinFrame', 0.68, 0.72, 0.26, 0, 3.45, 1.42, trimWood);
  addBox(root, 'UpperWinGlass', 0.48, 0.52, 0.30, 0, 3.45, 1.43, glowGlass);

  // 暖陶红锥形屋顶 (Y: 6.10..8.35m)
  const coneRoof = new THREE.Mesh(new THREE.ConeGeometry(1.56, 2.15, 12), roofMat);
  coneRoof.name = 'WindmillConeRoof';
  coneRoof.position.y = 7.18;
  root.add(coneRoof);
  const topBall = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), trimWood);
  topBall.name = 'RoofFinial';
  topBall.position.y = 8.32;
  root.add(topBall);

  // 独立风叶枢轴 BladesPivot（位于正面 +Z 塔肩 Y=5.45, 旋转绕 Z 轴）
  const bladesPivot = new THREE.Group();
  bladesPivot.name = 'BladesPivot';
  bladesPivot.position.set(0, 5.45, 1.42);
  root.add(bladesPivot);

  const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.56, 10), trimWood);
  axle.name = 'BladeAxle';
  axle.rotation.x = Math.PI / 2;
  bladesPivot.add(axle);

  const hub = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), trimWood);
  hub.name = 'BladeHubCap';
  hub.position.z = 0.24;
  bladesPivot.add(hub);

  // 4 片对称风车木格帆叶（直径 ~5.2m，最低端 Y ≈ 5.45 - 2.6 = 2.85m 不挡人行）
  for (let i = 0; i < 4; i += 1) {
    const armGroup = new THREE.Group();
    armGroup.name = 'WindmillBlade_' + i;
    armGroup.rotation.z = (i * Math.PI) / 2 + Math.PI / 4;
    bladesPivot.add(armGroup);

    // 主木杆
    addBox(armGroup, 'BladeSpar_' + i, 0.12, 2.58, 0.08, 0, 1.32, 0.18, trimWood);
    // 帆布面（偏移在木杆一侧）
    addBox(armGroup, 'BladeSail_' + i, 0.68, 1.88, 0.04, 0.36, 1.60, 0.19, sailCloth);
    // 横木栅格
    for (let r = 0; r < 4; r += 1) {
      addBox(armGroup, `BladeLattice_${i}_${r}`, 0.72, 0.05, 0.06, 0.36, 0.85 + r * 0.48, 0.20, trimWood);
    }
  }

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-windmill successfully');
};
