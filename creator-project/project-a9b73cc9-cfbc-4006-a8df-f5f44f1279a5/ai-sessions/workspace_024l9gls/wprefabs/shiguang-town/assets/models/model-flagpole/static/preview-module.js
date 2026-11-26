const THREE = require('three');

// 1.6x1.6x4.2m 像素庭院旗杆：含独立 FlagClothPivot 供 Lua 随风摆动
function createFishFlagTexture() {
  const c = document.createElement('canvas');
  c.width = 120;
  c.height = 120;
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D context is required');
  const pal = ['#fff7e6', '#7cc6e8', '#fb923c', '#f43f5e', '#1e293b', '#facc15'];
  const grid = [
    [1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,2,2,0,0,0,0,1],
    [1,0,0,2,2,2,2,2,0,0,3,1],
    [1,0,2,4,2,5,2,2,2,3,3,1],
    [1,0,2,2,2,2,5,2,3,3,0,1],
    [1,0,2,2,2,5,2,2,2,3,3,1],
    [1,0,0,2,2,2,2,2,0,0,3,1],
    [1,0,0,0,0,2,2,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1],
  ];
  for (let r = 0; r < 12; r += 1) {
    for (let col = 0; col < 12; col += 1) {
      ctx.fillStyle = pal[grid[r][col]];
      ctx.fillRect(col * 10, r * 10, 10, 10);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.needsUpdate = true;
  return tex;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'FlagpoleRoot';
  moduleRoot.add(root);

  const stoneMat = new THREE.MeshStandardMaterial({ color: 0xc2b5a3, roughness: 0.90, metalness: 0.02, side: THREE.FrontSide });
  const poleWood = new THREE.MeshStandardMaterial({ color: 0xb97a4b, roughness: 0.74, metalness: 0.03, side: THREE.FrontSide });
  const brassMat = new THREE.MeshStandardMaterial({ color: 0xf4c44e, roughness: 0.30, metalness: 0.78, side: THREE.FrontSide });
  const flagMat = new THREE.MeshStandardMaterial({ color: 0xffffff, map: createFishFlagTexture(), roughness: 0.72, metalness: 0.0, side: THREE.FrontSide });

  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.48, 0.28, 12), stoneMat);
  base.name = 'FlagStoneBase';
  base.position.y = 0.14;
  root.add(base);

  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.16, 0.10, 12), brassMat);
  collar.name = 'FlagBaseCollar';
  collar.position.y = 0.31;
  root.add(collar);

  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.085, 3.72, 12), poleWood);
  pole.name = 'FlagPoleShaft';
  pole.position.y = 2.16;
  root.add(pole);

  const finial = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 10), brassMat);
  finial.name = 'FlagFinial';
  finial.position.y = 4.06;
  root.add(finial);

  const clothPivot = new THREE.Group();
  clothPivot.name = 'FlagClothPivot';
  clothPivot.position.set(0, 3.82, 0);
  root.add(clothPivot);

  const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1.24, 8), poleWood);
  arm.name = 'FlagCrossArm';
  arm.rotation.z = Math.PI / 2;
  arm.position.set(0.62, 0, 0);
  clothPivot.add(arm);

  const banner = new THREE.Mesh(new THREE.BoxGeometry(1.12, 0.96, 0.035), flagMat);
  banner.name = 'FlagBannerCloth';
  banner.position.set(0.62, -0.52, 0);
  clothPivot.add(banner);

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-flagpole successfully');
};
