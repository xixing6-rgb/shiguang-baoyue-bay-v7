const THREE = require('three');

// 2.0x1.2x1.8m 庭院涂鸦留言黑板（无文字纯趣味粉笔画）
function createChalkDoodleTexture() {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 192;
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D context is required');

  ctx.fillStyle = '#2d3436';
  ctx.fillRect(0, 0, 256, 192);
  ctx.strokeStyle = 'rgba(255,255,255,0.08)';
  ctx.lineWidth = 4;
  ctx.strokeRect(8, 8, 240, 176);

  // 粉笔太阳
  ctx.strokeStyle = '#ffeaa7';
  ctx.lineWidth = 4;
  ctx.beginPath(); ctx.arc(62, 54, 20, 0, Math.PI * 2); ctx.stroke();
  for (let i = 0; i < 8; i += 1) {
    const a = (i * Math.PI) / 4;
    ctx.beginPath();
    ctx.moveTo(62 + Math.cos(a) * 26, 54 + Math.sin(a) * 26);
    ctx.lineTo(62 + Math.cos(a) * 34, 54 + Math.sin(a) * 34);
    ctx.stroke();
  }
  ctx.fillStyle = '#ffeaa7';
  ctx.beginPath(); ctx.arc(55, 50, 2.5, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(69, 50, 2.5, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(62, 56, 7, 0.2, Math.PI - 0.2); ctx.stroke();

  // 粉笔小花
  ctx.strokeStyle = '#ff9ff3';
  for (let p = 0; p < 5; p += 1) {
    const a = (p * Math.PI * 2) / 5;
    ctx.beginPath(); ctx.arc(178 + Math.cos(a) * 14, 118 + Math.sin(a) * 14, 8, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.strokeStyle = '#55efc4';
  ctx.beginPath(); ctx.moveTo(178, 134); ctx.lineTo(178, 166); ctx.stroke();

  // 粉笔小鱼
  ctx.strokeStyle = '#81ecec';
  ctx.beginPath(); ctx.ellipse(90, 138, 24, 13, 0, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(114, 138); ctx.lineTo(132, 126); ctx.lineTo(132, 150); ctx.closePath(); ctx.stroke();

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function addBox(parent, name, w, h, d, x, y, z, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.name = name; m.position.set(x, y, z); parent.add(m); return m;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'ChalkboardRoot';
  moduleRoot.add(root);

  const woodMat = new THREE.MeshStandardMaterial({ color: 0xc98a55, roughness: 0.76, metalness: 0.02, side: THREE.FrontSide });
  const darkWood = new THREE.MeshStandardMaterial({ color: 0x8d5634, roughness: 0.80, metalness: 0.02, side: THREE.FrontSide });
  const slateMat = new THREE.MeshStandardMaterial({ color: 0xffffff, map: createChalkDoodleTexture(), roughness: 0.88, metalness: 0.0, side: THREE.FrontSide });
  const chalkPink = new THREE.MeshStandardMaterial({ color: 0xffa6c1, roughness: 0.9, side: THREE.FrontSide });
  const chalkYellow = new THREE.MeshStandardMaterial({ color: 0xffe066, roughness: 0.9, side: THREE.FrontSide });

  // 前后倾 A 字形木画板结构
  const frontLeaf = new THREE.Group();
  frontLeaf.name = 'FrontBoardLeaf';
  frontLeaf.position.set(0, 0.84, 0.20);
  frontLeaf.rotation.x = -0.14;
  root.add(frontLeaf);

  addBox(frontLeaf, 'FrontLegL', 0.11, 1.72, 0.09, -0.78, 0, 0, woodMat);
  addBox(frontLeaf, 'FrontLegR', 0.11, 1.72, 0.09, 0.78, 0, 0, woodMat);
  addBox(frontLeaf, 'FrameTop', 1.66, 0.11, 0.10, 0, 0.66, 0, woodMat);
  addBox(frontLeaf, 'FrameBottom', 1.66, 0.11, 0.16, 0, -0.44, 0.03, woodMat);
  addBox(frontLeaf, 'SlateSurface', 1.46, 1.00, 0.045, 0, 0.11, 0, slateMat);

  // 粉笔槽小粉笔
  const c1 = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.12, 8), chalkPink);
  c1.name = 'ChalkStickPink'; c1.rotation.z = Math.PI / 2; c1.position.set(-0.42, -0.37, 0.08); frontLeaf.add(c1);
  const c2 = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.12, 8), chalkYellow);
  c2.name = 'ChalkStickYellow'; c2.rotation.z = Math.PI / 2; c2.position.set(-0.22, -0.37, 0.08); frontLeaf.add(c2);

  const backLeaf = new THREE.Group();
  backLeaf.name = 'BackSupportLeaf';
  backLeaf.position.set(0, 0.84, -0.20);
  backLeaf.rotation.x = 0.14;
  root.add(backLeaf);

  addBox(backLeaf, 'BackLegL', 0.10, 1.72, 0.08, -0.78, 0, 0, darkWood);
  addBox(backLeaf, 'BackLegR', 0.10, 1.72, 0.08, 0.78, 0, 0, darkWood);
  addBox(backLeaf, 'BackBrace', 1.50, 0.10, 0.06, 0, -0.30, 0, darkWood);

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-chalkboard successfully');
};
