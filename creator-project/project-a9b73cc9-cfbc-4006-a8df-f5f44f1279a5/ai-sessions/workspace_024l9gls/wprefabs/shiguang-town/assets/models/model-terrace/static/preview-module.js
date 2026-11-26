const THREE = require('three');

// 5x4x1.4m 户外咖啡茶桌露台
function addBox(parent, name, w, h, d, x, y, z, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y, z); parent.add(m); return m;
}

function buildChair(name, x, z, rotY, woodMat, cushionMat) {
  const g = new THREE.Group();
  g.name = name;
  g.position.set(x, 0.16, z);
  g.rotation.y = rotY;
  // 4 legs
  [[-0.20, -0.20], [0.20, -0.20], [-0.20, 0.20], [0.20, 0.20]].forEach(([lx, lz], i) => {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.03, 0.36, 8), woodMat);
    leg.name = name + '_Leg_' + i;
    leg.position.set(lx, 0.18, lz);
    g.add(leg);
  });
  addBox(g, name + '_Seat', 0.54, 0.06, 0.52, 0, 0.38, 0, woodMat);
  const pad = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.23, 0.05, 12), cushionMat);
  pad.name = name + '_Cushion';
  pad.position.set(0, 0.43, 0.01);
  g.add(pad);
  // 背靠
  [[-0.20, -0.22], [0.20, -0.22]].forEach(([bx, bz], bi) => {
    addBox(g, name + '_BackPost_' + bi, 0.06, 0.52, 0.06, bx, 0.64, bz, woodMat);
  });
  addBox(g, name + '_BackRail', 0.48, 0.22, 0.055, 0, 0.78, -0.22, woodMat);
  return g;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'TerraceRoot';
  moduleRoot.add(root);

  const deckWood = new THREE.MeshStandardMaterial({ color: 0xe2b786, roughness: 0.78, metalness: 0.02, side: THREE.FrontSide });
  const trimWood = new THREE.MeshStandardMaterial({ color: 0x9b623c, roughness: 0.76, metalness: 0.03, side: THREE.FrontSide });
  const oakTable = new THREE.MeshStandardMaterial({ color: 0xd39962, roughness: 0.65, metalness: 0.03, side: THREE.FrontSide });
  const creamMat = new THREE.MeshStandardMaterial({ color: 0xfff5e4, roughness: 0.62, metalness: 0.01, side: THREE.FrontSide });
  const sageMat = new THREE.MeshStandardMaterial({ color: 0x96c997, roughness: 0.75, metalness: 0.01, side: THREE.FrontSide });
  const pastryMat = new THREE.MeshStandardMaterial({ color: 0xf4a261, roughness: 0.60, metalness: 0.02, side: THREE.FrontSide });

  // 双层木露台底座 (Y: 0 -> 0.16m)
  addBox(root, 'TerraceStepRim', 4.70, 0.08, 3.70, 0, 0.04, 0, trimWood);
  for (let i = 0; i < 10; i += 1) {
    addBox(root, 'TerracePlank_' + i, 4.36, 0.08, 0.30, 0, 0.12, -1.53 + i * 0.34, i % 2 === 0 ? deckWood : oakTable);
  }

  // 圆角咖啡桌
  const tGroup = new THREE.Group();
  tGroup.name = 'CoffeeTable';
  tGroup.position.set(0, 0.16, 0);
  root.add(tGroup);

  const tTop = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.70, 0.075, 20), oakTable);
  tTop.name = 'TableTop';
  tTop.position.y = 0.68;
  tGroup.add(tTop);
  const tCol = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.14, 0.64, 10), trimWood);
  tCol.name = 'TablePillar';
  tCol.position.y = 0.34;
  tGroup.add(tCol);
  const tBase = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.42, 0.07, 14), trimWood);
  tBase.name = 'TableFoot';
  tBase.position.y = 0.035;
  tGroup.add(tBase);

  // 两只咖啡杯与点心盘
  [[-0.28, 0.14], [0.28, -0.14]].forEach(([cx, cz], ci) => {
    const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.046, 0.10, 10), creamMat);
    cup.name = 'CoffeeCup_' + ci;
    cup.position.set(cx, 0.77, cz);
    tGroup.add(cup);
  });
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.14, 0.025, 14), creamMat);
  plate.name = 'PastryPlate';
  plate.position.set(0, 0.73, 0);
  tGroup.add(plate);
  const cake = new THREE.Mesh(new THREE.SphereGeometry(0.065, 10, 8), pastryMat);
  cake.name = 'PastryBun';
  cake.scale.set(1.2, 0.7, 1.2);
  cake.position.set(0, 0.77, 0);
  tGroup.add(cake);

  // 两把朝向圆桌的木椅
  root.add(buildChair('TerraceChair_West', -1.25, 0.05, Math.PI / 2, trimWood, sageMat));
  root.add(buildChair('TerraceChair_East', 1.25, -0.05, -Math.PI / 2, trimWood, sageMat));

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-terrace successfully');
};
