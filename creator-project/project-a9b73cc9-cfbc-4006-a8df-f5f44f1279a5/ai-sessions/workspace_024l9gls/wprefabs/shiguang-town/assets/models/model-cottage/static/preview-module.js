const THREE = require('three');

// 《时光小筑》8x6x4.8m 单层可进入海滨温馨木屋（绘本暖阳风格化 PBR）
// +Y 向上，+Z 为南向正面入户廊台，入口底面局部 Y=0，室内完成面 Y=0.24m
const ASSET_BRIEF = {
  identity: {
    objectClass: 'cozy-seaside-cottage-enterable',
    confidence: 1,
    assumptions: [
      '8.0m x 6.0m x 4.8m 外部包络，与地图槽位 cottage-main 精确对齐',
      'DoorPivot 铰链在 (-0.73, 0.24, 1.39)，初始旋转 [0,0,0]，向室内 +Y 轴旋转开合'
    ],
  },
  orientation: { up: '+Y', front: '+Z' },
  silhouette: {
    primaryMasses: ['TimberFoundationAndPorch', 'MainWallShell', 'TiledGableRoofAndChimney'],
    proportions: '7.2x4.2m 木屋主体 + 1.15m 挑檐木廊台 + 分层暖陶瓦双坡顶',
    identityCues: ['DoorPivot', 'PorchLantern', 'StoneFireplace', 'PixelSunPainting'],
  },
  parts: [
    { id: 'FoundationAndPorch', level: 'macro', role: '地坪、双级入户台阶、木廊台与栏杆', parent: 'CottageRoot', materialRole: 'honeyWood' },
    { id: 'WallShell', level: 'macro', role: '真实门洞与四面开窗闭合实体外墙及室内奶油护墙', parent: 'CottageRoot', materialRole: 'warmTimberWall' },
    { id: 'RoofAndChimney', level: 'macro', role: '双坡屋面、五层陶瓦、檐口白边与石砌烟囱', parent: 'CottageRoot', materialRole: 'terracottaRoof' },
    { id: 'DoorPivot', level: 'meso', role: '可开合独立木门枢轴', parent: 'CottageRoot', moving: true, pivotStrategy: 'hinge-at-left-jamb' },
    { id: 'InteriorFloorAndBeams', level: 'meso', role: '人字木地板与室内屋架木梁', parent: 'CottageRoot', materialRole: 'herringboneFloor' },
    { id: 'TeaTableGroup', level: 'meso', role: '圆角茶桌、双编织坐垫、陶土茶杯与小点心盘', parent: 'CottageRoot', materialRole: 'oakFurniture' },
    { id: 'FireplaceGroup', level: 'meso', role: '转角石砌壁炉、柴火与暖橙余烬芯', parent: 'CottageRoot', materialRole: 'warmStone' },
    { id: 'BookshelfAndArt', level: 'micro', role: '西墙矮书架、彩色书、盆栽与北墙12x12像素太阳挂画', parent: 'CottageRoot', materialRole: 'creamWall' },
    { id: 'PorchProps', level: 'micro', role: '外廊花箱彩花与门口提灯', parent: 'CottageRoot', materialRole: 'lanternGlow' },
  ],
  materialRoles: {
    warmTimberWall: { baseColor: 0xe4ba8b, roughness: 0.78, metalness: 0.02 },
    creamWall: { baseColor: 0xfff3de, roughness: 0.84, metalness: 0.01 },
    honeyWood: { baseColor: 0xb97a4b, roughness: 0.74, metalness: 0.03 },
    darkWoodTrim: { baseColor: 0x8d5634, roughness: 0.72, metalness: 0.04 },
    oakFurniture: { baseColor: 0xd69f68, roughness: 0.64, metalness: 0.03 },
    terracottaRoof: { baseColor: 0xb96a59, roughness: 0.80, metalness: 0.02 },
    warmStone: { baseColor: 0xc2b5a3, roughness: 0.90, metalness: 0.02 },
    darkStone: { baseColor: 0x6e655c, roughness: 0.92, metalness: 0.02 },
    warmGlass: { baseColor: 0xffe4a8, roughness: 0.18, metalness: 0.05, opacity: 0.24 },
    lanternGlow: { baseColor: 0xffd67a, roughness: 0.35, metalness: 0.02, emissive: 0xffb347, emissiveIntensity: 0.95 },
    emberGlow: { baseColor: 0xff7b29, roughness: 0.45, metalness: 0.02, emissive: 0xff5a1f, emissiveIntensity: 1.4 },
    foliageGreen: { baseColor: 0x68b05c, roughness: 0.82, metalness: 0.01 },
    brassMetal: { baseColor: 0xe5b85c, roughness: 0.32, metalness: 0.78 },
  },
};

function createHerringboneTextures() {
  const size = 512;
  const albedoCanvas = document.createElement('canvas');
  albedoCanvas.width = size;
  albedoCanvas.height = size;
  const ctx = albedoCanvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D context is required');

  const roughCanvas = document.createElement('canvas');
  roughCanvas.width = size;
  roughCanvas.height = size;
  const rctx = roughCanvas.getContext('2d');
  if (!rctx) throw new Error('Canvas 2D context is required for roughness');

  ctx.fillStyle = '#d9ac7a';
  ctx.fillRect(0, 0, size, size);
  rctx.fillStyle = '#b4b4b4';
  rctx.fillRect(0, 0, size, size);

  const plankW = 64;
  const plankH = 32;
  const shades = ['#e3b98a', '#d7a876', '#ecc599', '#cfa06e'];
  const roughShades = ['#a8a8a8', '#bcbcbc', '#9e9e9e', '#c6c6c6'];

  let idx = 0;
  for (let y = 0; y < size; y += plankH) {
    const offset = ((y / plankH) % 2) * (plankW / 2);
    for (let x = -plankW; x < size + plankW; x += plankW) {
      const pick = (idx * 7 + (y / plankH) * 3) % shades.length;
      ctx.fillStyle = shades[pick];
      ctx.fillRect(x + offset + 1.5, y + 1.5, plankW - 3, plankH - 3);
      ctx.strokeStyle = 'rgba(135, 88, 48, 0.35)';
      ctx.lineWidth = 2;
      ctx.strokeRect(x + offset + 1, y + 1, plankW - 2, plankH - 2);

      rctx.fillStyle = roughShades[pick];
      rctx.fillRect(x + offset + 1.5, y + 1.5, plankW - 3, plankH - 3);
      idx += 1;
    }
  }

  const map = new THREE.CanvasTexture(albedoCanvas);
  map.colorSpace = THREE.SRGBColorSpace;
  map.wrapS = THREE.RepeatWrapping;
  map.wrapT = THREE.RepeatWrapping;
  map.repeat.set(3, 2);
  map.needsUpdate = true;

  const roughnessMap = new THREE.CanvasTexture(roughCanvas);
  roughnessMap.colorSpace = THREE.NoColorSpace;
  roughnessMap.wrapS = THREE.RepeatWrapping;
  roughnessMap.wrapT = THREE.RepeatWrapping;
  roughnessMap.repeat.set(3, 2);
  roughnessMap.needsUpdate = true;

  return { map, roughnessMap };
}

function createPixelSunTexture() {
  const c = document.createElement('canvas');
  c.width = 120;
  c.height = 120;
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D context is required');
  const palette = ['#fff8eb', '#ffd166', '#f77f00', '#ef476f', '#3a2e28'];
  const grid = [
    [0,0,0,0,0,1,1,0,0,0,0,0],
    [0,0,1,0,0,1,1,0,0,1,0,0],
    [0,1,0,0,1,1,1,1,0,0,1,0],
    [0,0,0,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,4,1,1,4,1,1,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,1,1,2,1,1,2,1,1,0,0],
    [0,0,1,1,1,4,4,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,0,0,0],
    [0,1,0,0,0,0,0,0,3,3,0,0],
    [0,0,0,0,0,0,0,3,3,3,3,0],
    [0,0,0,0,0,0,0,0,3,3,0,0],
  ];
  for (let r = 0; r < 12; r += 1) {
    for (let col = 0; col < 12; col += 1) {
      ctx.fillStyle = palette[grid[r][col]];
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

function createMaterials() {
  const mats = {};
  Object.entries(ASSET_BRIEF.materialRoles).forEach(([k, cfg]) => {
    const opts = {
      color: cfg.baseColor,
      roughness: cfg.roughness,
      metalness: cfg.metalness,
      side: THREE.FrontSide,
    };
    if (cfg.opacity !== undefined) {
      opts.transparent = true;
      opts.opacity = cfg.opacity;
    }
    if (cfg.emissive !== undefined) {
      opts.emissive = cfg.emissive;
      opts.emissiveIntensity = cfg.emissiveIntensity || 1;
    }
    mats[k] = new THREE.MeshStandardMaterial(opts);
    mats[k].name = k;
  });

  const floorTex = createHerringboneTextures();
  mats.herringboneFloor = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    map: floorTex.map,
    roughness: 0.72,
    roughnessMap: floorTex.roughnessMap,
    metalness: 0.02,
    side: THREE.FrontSide,
  });
  mats.herringboneFloor.name = 'herringboneFloor';

  mats.pixelPainting = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    map: createPixelSunTexture(),
    roughness: 0.65,
    metalness: 0.0,
    side: THREE.FrontSide,
  });
  mats.pixelPainting.name = 'pixelPainting';

  const accents = [0xf43f5e, 0xfb923c, 0x38bdf8, 0xfacc15, 0xa855f7];
  accents.forEach((hex, idx) => {
    const m = new THREE.MeshStandardMaterial({ color: hex, roughness: 0.58, metalness: 0.03, side: THREE.FrontSide });
    m.name = 'accent_' + idx;
    mats['accent_' + idx] = m;
  });
  return mats;
}

function addBox(parent, name, w, h, d, x, y, z, mat) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  mesh.name = name;
  mesh.position.set(x, y, z);
  parent.add(mesh);
  return mesh;
}

function addWindowFrame(parent, name, cx, cy, cz, w, h, rotY, mats) {
  const wg = new THREE.Group();
  wg.name = name;
  wg.position.set(cx, cy, cz);
  wg.rotation.y = rotY;
  parent.add(wg);

  const frameT = 0.08;
  const frameD = 0.27;
  // 四周边框（有厚度实心框）
  addBox(wg, name + '_Top', w + 0.10, frameT, frameD, 0, h / 2 + frameT / 2 - 0.02, 0, mats.darkWoodTrim);
  addBox(wg, name + '_Sill', w + 0.18, frameT + 0.02, frameD + 0.10, 0, -h / 2 - frameT / 2 + 0.02, 0.03, mats.honeyWood);
  addBox(wg, name + '_Left', frameT, h, frameD, -w / 2 - frameT / 2 + 0.02, 0, 0, mats.darkWoodTrim);
  addBox(wg, name + '_Right', frameT, h, frameD, w / 2 + frameT / 2 - 0.02, 0, 0, mats.darkWoodTrim);
  // 十字木格窗棂
  addBox(wg, name + '_MuntinV', 0.055, h - 0.04, 0.06, 0, 0, 0, mats.creamWall);
  addBox(wg, name + '_MuntinH', w - 0.04, 0.055, 0.06, 0, 0, 0, mats.creamWall);
  // 极薄透光玻璃（闭合实心片）
  addBox(wg, name + '_Glass', w - 0.06, h - 0.06, 0.02, 0, 0, 0, mats.warmGlass);
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'CottageRoot';
  root.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(root);

  const mats = createMaterials();

  // 1. 地坪、木廊台与双级入户台阶 (Y: 0 -> 0.24m)
  const gFound = new THREE.Group();
  gFound.name = 'FoundationAndPorch';
  root.add(gFound);

  addBox(gFound, 'BasePlinth', 7.36, 0.22, 5.20, 0, 0.11, -0.15, mats.warmStone);
  addBox(gFound, 'PorchDeck', 7.20, 0.06, 1.15, 0, 0.21, 1.98, mats.honeyWood);
  // 两级宽台阶连接 Y=0 到 Y=0.24m
  addBox(gFound, 'EntryStepLower', 2.20, 0.08, 0.28, 0, 0.04, 2.86, mats.honeyWood);
  addBox(gFound, 'EntryStepUpper', 2.20, 0.16, 0.28, 0, 0.08, 2.59, mats.honeyWood);

  // 廊台四根圆木柱与双侧矮栏杆
  const postXs = [-3.35, -1.05, 1.05, 3.35];
  postXs.forEach((px, idx) => {
    const post = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.115, 2.52, 10), mats.darkWoodTrim);
    post.name = 'PorchPost_' + idx;
    post.position.set(px, 1.48, 2.40);
    gFound.add(post);
  });
  // 左右栏杆（居中门前 Z=2.40 留 2.1m 净宽开口）
  [[-2.20, 2.20], [2.20, 2.20]].forEach(([rx, rlen], sideIdx) => {
    addBox(gFound, 'PorchRailTop_' + sideIdx, rlen, 0.08, 0.10, rx, 0.92, 2.40, mats.darkWoodTrim);
    for (let k = -2; k <= 2; k += 1) {
      addBox(gFound, 'PorchBaluster_' + sideIdx + '_' + (k + 2), 0.07, 0.68, 0.07, rx + k * 0.42, 0.56, 2.40, mats.honeyWood);
    }
  });

  // 2. 闭合实体外墙（真实门洞 1.50x2.25m + 4 扇真实窗洞）
  const gWalls = new THREE.Group();
  gWalls.name = 'WallShell';
  root.add(gWalls);

  // 室内人字木地板 (Y=0.22..0.24)
  addBox(gWalls, 'InteriorFloorSlab', 6.76, 0.03, 3.80, 0, 0.225, -0.58, mats.herringboneFloor);

  // 后墙（北墙 Z=-2.59, 宽7.20, 高2.50）
  addBox(gWalls, 'WallNorthOuter', 7.20, 2.50, 0.14, 0, 1.49, -2.63, mats.warmTimberWall);
  addBox(gWalls, 'WallNorthInner', 6.76, 2.50, 0.08, 0, 1.49, -2.52, mats.creamWall);

  // 前墙（南墙 Z=+1.39, 门洞 X: -0.75..+0.75, Y: 0.24..2.49）
  addBox(gWalls, 'WallSouthDoorHeader', 1.50, 0.25, 0.22, 0, 2.615, 1.39, mats.warmTimberWall);
  // 门框左右竖挺
  addBox(gWalls, 'DoorFrameLeft', 0.08, 2.25, 0.25, -0.75, 1.365, 1.39, mats.darkWoodTrim);
  addBox(gWalls, 'DoorFrameRight', 0.08, 2.25, 0.25, 0.75, 1.365, 1.39, mats.darkWoodTrim);
  addBox(gWalls, 'DoorFrameTop', 1.58, 0.09, 0.26, 0, 2.47, 1.39, mats.darkWoodTrim);

  // 南墙左段 (-3.60..-0.75) 含左窗 (-2.75..-1.55, Y:1.05..2.15)
  addBox(gWalls, 'WallSouthLeft_OuterPier', 0.85, 2.50, 0.22, -3.175, 1.49, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthLeft_InnerPier', 0.80, 2.50, 0.22, -1.15, 1.49, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthLeft_UnderWin', 1.20, 0.81, 0.22, -2.15, 0.645, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthLeft_OverWin', 1.20, 0.59, 0.22, -2.15, 2.445, 1.39, mats.warmTimberWall);
  addWindowFrame(gWalls, 'WindowSouthLeft', -2.15, 1.60, 1.39, 1.20, 1.10, 0, mats);

  // 南墙右段 (+0.75..+3.60) 含右窗 (+1.55..+2.75, Y:1.05..2.15)
  addBox(gWalls, 'WallSouthRight_OuterPier', 0.85, 2.50, 0.22, 3.175, 1.49, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthRight_InnerPier', 0.80, 2.50, 0.22, 1.15, 1.49, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthRight_UnderWin', 1.20, 0.81, 0.22, 2.15, 0.645, 1.39, mats.warmTimberWall);
  addBox(gWalls, 'WallSouthRight_OverWin', 1.20, 0.59, 0.22, 2.15, 2.445, 1.39, mats.warmTimberWall);
  addWindowFrame(gWalls, 'WindowSouthRight', 2.15, 1.60, 1.39, 1.20, 1.10, 0, mats);

  // 东西两侧墙 (X=-3.49 / +3.49, Z:-2.48..+1.28, 中央开窗 Z:-1.20..0.00, Y:1.05..2.15)
  [-3.49, 3.49].forEach((wx, side) => {
    const tag = side === 0 ? 'West' : 'East';
    addBox(gWalls, `Wall${tag}_NorthPier`, 0.22, 2.50, 1.28, wx, 1.49, -1.84, mats.warmTimberWall);
    addBox(gWalls, `Wall${tag}_SouthPier`, 0.22, 2.50, 1.28, wx, 1.49, 0.64, mats.warmTimberWall);
    addBox(gWalls, `Wall${tag}_UnderWin`, 0.22, 0.81, 1.20, wx, 0.645, -0.60, mats.warmTimberWall);
    addBox(gWalls, `Wall${tag}_OverWin`, 0.22, 0.59, 1.20, wx, 2.445, -0.60, mats.warmTimberWall);
    addWindowFrame(gWalls, `Window${tag}`, wx, 1.60, -0.60, 1.20, 1.10, side === 0 ? -Math.PI / 2 : Math.PI / 2, mats);
  });

  // 四角结构圆木柱加强立体咬合
  [[-3.55, -2.65], [3.55, -2.65], [-3.55, 1.45], [3.55, 1.45]].forEach(([cx, cz], idx) => {
    const col = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 2.54, 10), mats.darkWoodTrim);
    col.name = 'CornerLog_' + idx;
    col.position.set(cx, 1.49, cz);
    gWalls.add(col);
  });

  // 前后山墙三角封堵
  const gableShape = new THREE.Shape();
  gableShape.moveTo(-3.60, 0);
  gableShape.lineTo(3.60, 0);
  gableShape.lineTo(0, 1.56);
  gableShape.closePath();
  const gableGeo = new THREE.ExtrudeGeometry(gableShape, { depth: 0.20, bevelEnabled: false });
  [1.29, -2.69].forEach((gz, gi) => {
    const gm = new THREE.Mesh(gableGeo, mats.warmTimberWall);
    gm.name = 'GableTriangle_' + gi;
    gm.position.set(0, 2.74, gz);
    gWalls.add(gm);
  });

  // 3. 独立可开合木门 DoorPivot（初始旋转 [0,0,0]，向室内旋转开启）
  const doorPivot = new THREE.Group();
  doorPivot.name = 'DoorPivot';
  doorPivot.position.set(-0.71, 0.24, 1.39);
  root.add(doorPivot);

  addBox(doorPivot, 'DoorLeafMain', 1.42, 2.19, 0.075, 0.71, 1.095, 0, mats.oakFurniture);
  addBox(doorPivot, 'DoorPanelLower', 1.08, 0.78, 0.095, 0.71, 0.56, 0, mats.darkWoodTrim);
  addBox(doorPivot, 'DoorUpperFrame', 0.96, 0.72, 0.095, 0.71, 1.58, 0, mats.darkWoodTrim);
  addBox(doorPivot, 'DoorGlass', 0.76, 0.54, 0.105, 0.71, 1.58, 0, mats.warmGlass);
  const knobOut = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 8), mats.brassMetal);
  knobOut.name = 'DoorKnobOuter';
  knobOut.position.set(1.26, 1.02, 0.065);
  doorPivot.add(knobOut);
  const knobIn = new THREE.Mesh(new THREE.SphereGeometry(0.055, 10, 8), mats.brassMetal);
  knobIn.name = 'DoorKnobInner';
  knobIn.position.set(1.26, 1.02, -0.065);
  doorPivot.add(knobIn);

  // 4. 双坡屋顶、五层陶瓦片与石砌烟囱
  const gRoof = new THREE.Group();
  gRoof.name = 'RoofAndChimney';
  root.add(gRoof);

  const roofSlopeAngle = Math.atan2(1.56, 3.60); // ~23.4 deg
  const slopeLen = Math.hypot(3.60, 1.56) + 0.55;
  const roofDepth = 5.45; // 覆盖 Z: -2.98 ~ +2.47（含挑檐廊台）
  const roofZ = -0.25;

  [-1, 1].forEach(side => {
    const slopeGroup = new THREE.Group();
    slopeGroup.name = side < 0 ? 'RoofSlopeWest' : 'RoofSlopeEast';
    slopeGroup.position.set(side * 1.95, 3.48, roofZ);
    slopeGroup.rotation.z = -side * roofSlopeAngle;
    gRoof.add(slopeGroup);

    // 屋面板与奶油白檐口条
    addBox(slopeGroup, 'RoofDeck_' + side, slopeLen, 0.12, roofDepth, 0, 0, 0, mats.darkWoodTrim);
    addBox(slopeGroup, 'EaveTrim_' + side, 0.12, 0.18, roofDepth + 0.06, side * (slopeLen / 2 - 0.02), -0.02, 0, mats.creamWall);

    // 5 排错缝暖陶红圆角屋瓦条
    for (let row = 0; row < 5; row += 1) {
      const localX = side * (slopeLen / 2 - 0.45 - row * 0.82);
      const localY = 0.08 + row * 0.015;
      addBox(slopeGroup, `TileCourse_${side}_${row}`, 0.78, 0.075, roofDepth - 0.08, localX, localY, 0, mats.terracottaRoof);
    }
  });
  // 屋脊圆木压顶
  const ridge = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, roofDepth + 0.12, 10), mats.terracottaRoof);
  ridge.name = 'RoofRidgeCap';
  ridge.rotation.x = Math.PI / 2;
  ridge.position.set(0, 4.38, roofZ);
  gRoof.add(ridge);

  // 石砌烟囱（从北东角落直通屋顶外）
  addBox(gRoof, 'ChimneyShaft', 0.72, 2.30, 0.72, 2.35, 3.60, -1.75, mats.warmStone);
  addBox(gRoof, 'ChimneyCap', 0.88, 0.16, 0.88, 2.35, 4.72, -1.75, mats.darkStone);

  // 室内屋架横梁
  [-1.4, -0.3, 0.8].forEach((bz, idx) => {
    addBox(gRoof, 'InteriorBeam_' + idx, 6.80, 0.14, 0.16, 0, 2.76, bz, mats.darkWoodTrim);
  });

  // 5. 室内陈设（茶桌、壁炉、书架、像素画框）
  const gTea = new THREE.Group();
  gTea.name = 'TeaTableGroup';
  gTea.position.set(0.45, 0.24, -0.75);
  root.add(gTea);

  const tableTop = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.60, 0.07, 18), mats.oakFurniture);
  tableTop.name = 'TeaTableTop';
  tableTop.position.y = 0.44;
  gTea.add(tableTop);
  for (let i = 0; i < 4; i += 1) {
    const ang = (i * Math.PI) / 2 + Math.PI / 4;
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.04, 0.42, 8), mats.darkWoodTrim);
    leg.name = 'TeaTableLeg_' + i;
    leg.position.set(Math.cos(ang) * 0.38, 0.21, Math.sin(ang) * 0.38);
    gTea.add(leg);
  }
  // 2 个编织圆垫
  [-0.90, 0.90].forEach((cx, ci) => {
    const cush = new THREE.Mesh(new THREE.CylinderGeometry(0.30, 0.32, 0.11, 14), ci === 0 ? mats.creamWall : mats.accent_3);
    cush.name = 'FloorCushion_' + ci;
    cush.position.set(cx, 0.055, 0.06);
    gTea.add(cush);
  });
  // 2 只陶土茶杯 + 点心盘
  [[-0.22, 0.10], [0.22, -0.10]].forEach(([tx, tz], ti) => {
    const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.042, 0.09, 10), mats.terracottaRoof);
    cup.name = 'TeaCup_' + ti;
    cup.position.set(tx, 0.52, tz);
    gTea.add(cup);
  });
  const plate = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.12, 0.025, 12), mats.creamWall);
  plate.name = 'CookiePlate';
  plate.position.set(0, 0.488, 0.02);
  gTea.add(plate);

  // 转角石砌壁炉
  const gFire = new THREE.Group();
  gFire.name = 'FireplaceGroup';
  gFire.position.set(2.35, 0.24, -1.75);
  gFire.rotation.y = -Math.PI * 0.22;
  root.add(gFire);

  addBox(gFire, 'FireplaceHearth', 1.48, 0.12, 0.98, 0, 0.06, 0.10, mats.darkStone);
  addBox(gFire, 'FireplaceLeftPillar', 0.30, 1.15, 0.72, -0.52, 0.69, 0, mats.warmStone);
  addBox(gFire, 'FireplaceRightPillar', 0.30, 1.15, 0.72, 0.52, 0.69, 0, mats.warmStone);
  addBox(gFire, 'FireplaceBack', 0.76, 1.15, 0.22, 0, 0.69, -0.25, mats.darkStone);
  addBox(gFire, 'FireplaceMantel', 1.50, 0.16, 0.84, 0, 1.32, 0.04, mats.honeyWood);
  addBox(gFire, 'FireplaceHood', 1.10, 1.25, 0.68, 0, 2.02, -0.02, mats.warmStone);
  const ember = new THREE.Mesh(new THREE.SphereGeometry(0.20, 12, 10), mats.emberGlow);
  ember.name = 'FireplaceEmberCore';
  ember.scale.set(1.3, 0.65, 0.9);
  ember.position.set(0, 0.26, 0.04);
  gFire.add(ember);

  // 西墙矮书架 + 彩书 + 盆栽 + 北墙12x12像素画框
  const gShelf = new THREE.Group();
  gShelf.name = 'BookshelfAndArt';
  root.add(gShelf);

  const shelfRoot = new THREE.Group();
  shelfRoot.name = 'WestBookshelf';
  shelfRoot.position.set(-2.98, 0.24, -1.72);
  shelfRoot.rotation.y = Math.PI / 2;
  gShelf.add(shelfRoot);
  addBox(shelfRoot, 'ShelfBack', 1.36, 1.16, 0.06, 0, 0.58, -0.19, mats.darkWoodTrim);
  addBox(shelfRoot, 'ShelfSideL', 0.07, 1.16, 0.42, -0.645, 0.58, 0, mats.honeyWood);
  addBox(shelfRoot, 'ShelfSideR', 0.07, 1.16, 0.42, 0.645, 0.58, 0, mats.honeyWood);
  [0.06, 0.58, 1.12].forEach((sy, si) => {
    addBox(shelfRoot, 'ShelfBoard_' + si, 1.26, 0.06, 0.40, 0, sy, 0, mats.oakFurniture);
  });
  for (let b = 0; b < 10; b += 1) {
    const rowY = b < 5 ? 0.24 : 0.76;
    const colX = -0.44 + (b % 5) * 0.20;
    const bh = 0.26 + ((b * 3) % 4) * 0.03;
    addBox(shelfRoot, 'Book_' + b, 0.08, bh, 0.24, colX, rowY, 0.02, mats['accent_' + (b % 5)]);
  }
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.10, 0.18, 10), mats.terracottaRoof);
  pot.name = 'ShelfPlantPot';
  pot.position.set(0.36, 1.24, 0);
  shelfRoot.add(pot);
  const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.18, 10, 8), mats.foliageGreen);
  leaf.name = 'ShelfPlantLeaves';
  leaf.position.set(0.36, 1.44, 0);
  shelfRoot.add(leaf);

  // 北墙 12x12 像素太阳画框
  addBox(gShelf, 'PixelArtFrame', 1.24, 1.24, 0.08, 0, 1.72, -2.44, mats.honeyWood);
  addBox(gShelf, 'PixelArtCanvas', 1.06, 1.06, 0.04, 0, 1.72, -2.40, mats.pixelPainting);

  // 6. 外廊花箱与门口小提灯
  const gPorchProps = new THREE.Group();
  gPorchProps.name = 'PorchProps';
  root.add(gPorchProps);

  [-2.15, 2.15].forEach((fx, fi) => {
    addBox(gPorchProps, 'WindowFlowerBox_' + fi, 1.15, 0.26, 0.30, fx, 0.37, 1.72, mats.honeyWood);
    for (let k = 0; k < 4; k += 1) {
      const fl = new THREE.Mesh(new THREE.SphereGeometry(0.11, 8, 6), mats['accent_' + ((fi * 2 + k) % 5)]);
      fl.name = `PorchFlower_${fi}_${k}`;
      fl.position.set(fx - 0.38 + k * 0.25, 0.56, 1.72);
      gPorchProps.add(fl);
    }
  });

  // 门口小提灯
  addBox(gPorchProps, 'LanternBracket', 0.06, 0.06, 0.24, 1.05, 2.14, 1.60, mats.darkWoodTrim);
  const lanternBody = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.075, 0.22, 8), mats.lanternGlow);
  lanternBody.name = 'PorchLanternBulb';
  lanternBody.position.set(1.05, 1.98, 1.68);
  gPorchProps.add(lanternBody);

  root.traverse(obj => {
    if (!obj.isMesh) return;
    obj.castShadow = true;
    obj.receiveShadow = true;
  });

  logger.info('Built Shiguang Cottage (enterable 8x6m) successfully');
};
