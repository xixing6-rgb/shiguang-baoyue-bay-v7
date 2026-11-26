const THREE = require('three');

// 6x4x1.0m 孟德尔杂交花圃：12 株独立命名的花冠 FlowerBloom_01..12 便于 Lua 动态变色
function addBox(parent, name, w, h, d, x, y, z, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y, z); parent.add(m); return m;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'FlowerBedRoot';
  moduleRoot.add(root);

  const frameWood = new THREE.MeshStandardMaterial({ color: 0xb97a4b, roughness: 0.78, metalness: 0.02, side: THREE.FrontSide });
  const cornerPost = new THREE.MeshStandardMaterial({ color: 0x8d5634, roughness: 0.80, metalness: 0.03, side: THREE.FrontSide });
  const soilMat = new THREE.MeshStandardMaterial({ color: 0x6f4e37, roughness: 0.94, metalness: 0.0, side: THREE.FrontSide });
  const stemMat = new THREE.MeshStandardMaterial({ color: 0x559e4d, roughness: 0.80, metalness: 0.0, side: THREE.FrontSide });

  const initialColors = [
    0xef4444, 0xf472b6, 0xfff8eb, 0xfb923c,
    0xfff8eb, 0xef4444, 0xf472b6, 0x60a5fa,
    0xfb923c, 0xc084fc, 0xef4444, 0xfff8eb,
  ];

  // 厚原木围框 (5.6 x 3.6m)
  addBox(root, 'BorderNorth', 5.60, 0.30, 0.22, 0, 0.15, -1.69, frameWood);
  addBox(root, 'BorderSouth', 5.60, 0.30, 0.22, 0, 0.15, 1.69, frameWood);
  addBox(root, 'BorderWest', 0.22, 0.30, 3.16, -2.69, 0.15, 0, frameWood);
  addBox(root, 'BorderEast', 0.22, 0.30, 3.16, 2.69, 0.15, 0, frameWood);
  [[-2.72, -1.72], [2.72, -1.72], [-2.72, 1.72], [2.72, 1.72]].forEach(([cx, cz], i) => {
    addBox(root, 'CornerPeg_' + i, 0.28, 0.36, 0.28, cx, 0.18, cz, cornerPost);
  });

  // 花土床
  addBox(root, 'SoilBed', 5.18, 0.22, 3.16, 0, 0.11, 0, soilMat);

  // 4x3 十二株杂交花朵（每株保留独立 FlowerBloom_XX 节点与独立材质）
  let idx = 1;
  for (let row = 0; row < 3; row += 1) {
    for (let col = 0; col < 4; col += 1) {
      const fx = -1.74 + col * 1.16;
      const fz = -0.95 + row * 0.95;
      const numStr = String(idx).padStart(2, '0');

      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.038, 0.32, 7), stemMat);
      stem.name = 'FlowerStem_' + numStr;
      stem.position.set(fx, 0.36, fz);
      root.add(stem);

      [-1, 1].forEach((side, li) => {
        const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.085, 8, 6), stemMat);
        leaf.name = `FlowerLeaf_${numStr}_${li}`;
        leaf.scale.set(1.4, 0.35, 0.8);
        leaf.position.set(fx + side * 0.11, 0.31, fz);
        leaf.rotation.z = side * 0.35;
        root.add(leaf);
      });

      const bloomGroup = new THREE.Group();
      bloomGroup.name = 'FlowerBloom_' + numStr;
      bloomGroup.position.set(fx, 0.56, fz);
      root.add(bloomGroup);

      const petalMat = new THREE.MeshStandardMaterial({
        color: initialColors[(idx - 1) % initialColors.length],
        roughness: 0.55,
        metalness: 0.02,
        side: THREE.FrontSide,
      });
      petalMat.name = 'PetalMat_' + numStr;

      // 清晰 3 单元花瓣冠（一中心花蕾 + 两瓣或三瓣对称）
      for (let p = 0; p < 3; p += 1) {
        const ang = (p * Math.PI * 2) / 3;
        const petal = new THREE.Mesh(new THREE.SphereGeometry(0.135, 10, 8), petalMat);
        petal.name = `BloomPetal_${numStr}_${p}`;
        petal.scale.set(1.0, 0.78, 1.0);
        petal.position.set(Math.cos(ang) * 0.085, 0, Math.sin(ang) * 0.085);
        bloomGroup.add(petal);
      }

      idx += 1;
    }
  }

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-flowerbed (12 controllable flowers) successfully');
};
