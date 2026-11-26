const THREE = require('three');

// 4x8x1.4m 木质钓鱼栈桥：-Z 端衔接 L0 沙滩(Y=0)，+Z 端伸向海湾
const ASSET_BRIEF = {
  identity: { objectClass: 'wooden-fishing-pier', confidence: 1, assumptions: [] },
  orientation: { up: '+Y', front: '+Z' },
  parts: [
    { id: 'Pilings', level: 'macro', role: '入水支撑木桩与防撞柱', parent: 'PierRoot' },
    { id: 'DeckPlanks', level: 'macro', role: '错缝铺装木板与入桥斜坡', parent: 'PierRoot' },
    { id: 'LanternAndBollards', level: 'meso', role: '系船木桩、绳栏与暖黄提灯柱', parent: 'PierRoot' },
  ],
};

function addBox(parent, name, w, h, d, x, y, z, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name;
  m.position.set(x, y, z);
  parent.add(m);
  return m;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'PierRoot';
  root.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(root);

  const woodLight = new THREE.MeshStandardMaterial({ color: 0xdfb27e, roughness: 0.78, metalness: 0.02, side: THREE.FrontSide });
  const woodMid = new THREE.MeshStandardMaterial({ color: 0xc9925d, roughness: 0.80, metalness: 0.02, side: THREE.FrontSide });
  const woodDark = new THREE.MeshStandardMaterial({ color: 0x8d5735, roughness: 0.84, metalness: 0.03, side: THREE.FrontSide });
  const ropeMat = new THREE.MeshStandardMaterial({ color: 0xe6d3ad, roughness: 0.90, metalness: 0.0, side: THREE.FrontSide });
  const glowMat = new THREE.MeshStandardMaterial({ color: 0xffd67a, emissive: 0xffb347, emissiveIntensity: 1.0, roughness: 0.35, side: THREE.FrontSide });

  const gPilings = new THREE.Group(); gPilings.name = 'Pilings'; root.add(gPilings);
  const gDeck = new THREE.Group(); gDeck.name = 'DeckPlanks'; root.add(gDeck);
  const gProps = new THREE.Group(); gProps.name = 'LanternAndBollards'; root.add(gProps);

  // 纵梁承托
  [-1.08, 0, 1.08].forEach((bx, bi) => {
    addBox(gPilings, 'PierBeam_' + bi, 0.16, 0.18, 7.10, bx, 0.09, 0.30, woodDark);
  });

  // 10 根入水支撑木桩（沿 Z 排布，突出甲板形成系船矮桩）
  [-3.0, -1.2, 0.6, 2.4, 3.7].forEach((pz, row) => {
    [-1.24, 1.24].forEach((px, side) => {
      const topH = row === 4 && side === 1 ? 1.55 : 0.68;
      const depthBelow = 0.75;
      const totalH = topH + depthBelow;
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.145, totalH, 10), woodDark);
      post.name = `PierPiling_${row}_${side}`;
      post.position.set(px, (topH - depthBelow) / 2, pz);
      gPilings.add(post);

      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.145, 0.145, 0.05, 10), woodMid);
      cap.name = `PilingCap_${row}_${side}`;
      cap.position.set(px, topH + 0.025, pz);
      gPilings.add(cap);
    });
  });

  // 入桥斜坡板（-Z = -3.95.. -3.20 衔接地面 Y=0 到甲板 Y=0.22）
  const ramp = new THREE.Mesh(new THREE.BoxGeometry(2.68, 0.08, 0.82), woodMid);
  ramp.name = 'PierEntryRamp';
  ramp.position.set(0, 0.11, -3.55);
  ramp.rotation.x = -Math.atan2(0.20, 0.78);
  gDeck.add(ramp);

  // 24 根错缝原木栈道板 (Z: -3.15 .. +3.85)
  for (let i = 0; i < 23; i += 1) {
    const pz = -3.05 + i * 0.305;
    const mat = i % 3 === 0 ? woodMid : woodLight;
    addBox(gDeck, 'PierPlank_' + i, 2.74, 0.07, 0.27, (i % 2 === 0 ? -0.02 : 0.02), 0.215, pz, mat);
  }
  // 两侧护边木条
  [-1.32, 1.32].forEach((kx, ki) => {
    addBox(gDeck, 'DeckCurb_' + ki, 0.12, 0.08, 7.05, kx, 0.28, 0.35, woodDark);
  });

  // 端头挂灯横臂与暖黄提灯
  addBox(gProps, 'LanternArm', 0.42, 0.09, 0.09, 1.04, 1.46, 3.70, woodDark);
  const lantern = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.08, 0.22, 8), glowMat);
  lantern.name = 'PierEndLantern';
  lantern.position.set(0.88, 1.28, 3.70);
  gProps.add(lantern);
  const lanternHat = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.10, 8), woodDark);
  lanternHat.name = 'PierLanternCap';
  lanternHat.position.set(0.88, 1.42, 3.70);
  gProps.add(lanternHat);

  // 绳索护栏横向连接
  [-1.24, 1.24].forEach((rx, si) => {
    for (let seg = 0; seg < 4; seg += 1) {
      const zMid = -2.1 + seg * 1.8;
      const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.032, 0.032, 1.8, 6), ropeMat);
      rope.name = `PierRope_${si}_${seg}`;
      rope.rotation.x = Math.PI / 2;
      rope.position.set(rx, 0.56, zMid);
      gProps.add(rope);
    }
  });

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-pier successfully');
};
