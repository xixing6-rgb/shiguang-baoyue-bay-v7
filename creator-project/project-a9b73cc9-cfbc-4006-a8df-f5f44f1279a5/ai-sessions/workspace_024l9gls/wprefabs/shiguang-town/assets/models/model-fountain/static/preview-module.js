const THREE = require('three');

// 6x6x2.2m 中心心愿喷泉（参考 #05 造型板）
module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'FountainRoot';
  moduleRoot.add(root);

  const stoneLight = new THREE.MeshStandardMaterial({ color: 0xd6d2c9, roughness: 0.88, metalness: 0.02, side: THREE.FrontSide });
  const stoneMid = new THREE.MeshStandardMaterial({ color: 0xb6b0a6, roughness: 0.90, metalness: 0.02, side: THREE.FrontSide });
  const waterMat = new THREE.MeshStandardMaterial({ color: 0x7fd8eb, roughness: 0.14, metalness: 0.05, transparent: true, opacity: 0.82, side: THREE.FrontSide });
  const coinGold = new THREE.MeshStandardMaterial({ color: 0xffd166, roughness: 0.30, metalness: 0.72, side: THREE.FrontSide });

  // 底层圆石台阶基座
  const apron = new THREE.Mesh(new THREE.CylinderGeometry(2.75, 2.90, 0.16, 20), stoneMid);
  apron.name = 'FountainApron';
  apron.position.y = 0.08;
  root.add(apron);

  // 池底衬垫
  const poolFloor = new THREE.Mesh(new THREE.CylinderGeometry(2.35, 2.35, 0.14, 20), stoneMid);
  poolFloor.name = 'PoolFloor';
  poolFloor.position.y = 0.22;
  root.add(poolFloor);

  // 16 块圆润卵石围栏（形成可爱玩具石砌感）
  const stonesCount = 16;
  for (let i = 0; i < stonesCount; i += 1) {
    const a = (i * Math.PI * 2) / stonesCount;
    const stone = new THREE.Mesh(new THREE.SphereGeometry(0.46, 10, 8), i % 2 === 0 ? stoneLight : stoneMid);
    stone.name = 'BasinStone_' + i;
    stone.scale.set(1.15, 0.68, 0.92);
    stone.position.set(Math.cos(a) * 2.28, 0.48, Math.sin(a) * 2.28);
    stone.rotation.y = -a;
    root.add(stone);
  }

  // 清澈薄荷蓝水体
  const water = new THREE.Mesh(new THREE.CylinderGeometry(2.14, 2.14, 0.16, 20), waterMat);
  water.name = 'FountainWaterPool';
  water.position.y = 0.44;
  root.add(water);

  // 几枚池底许愿金币点缀
  [[0.8, 0.6], [-0.9, 0.4], [0.2, -1.0]].forEach(([cx, cz], ci) => {
    const coin = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.03, 8), coinGold);
    coin.name = 'WishCoin_' + ci;
    coin.position.set(cx, 0.31, cz);
    root.add(coin);
  });

  // 中心双层圆石喷柱与顶盆
  const pedLow = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.56, 0.85, 14), stoneLight);
  pedLow.name = 'CenterPillarLow';
  pedLow.position.y = 0.68;
  root.add(pedLow);

  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 0.52, 0.34, 16), stoneLight);
  bowl.name = 'CenterBowl';
  bowl.position.y = 1.22;
  root.add(bowl);

  const bowlWater = new THREE.Mesh(new THREE.CylinderGeometry(0.90, 0.90, 0.08, 16), waterMat);
  bowlWater.name = 'CenterBowlWater';
  bowlWater.position.y = 1.36;
  root.add(bowlWater);

  const spout = new THREE.Mesh(new THREE.CylinderGeometry(0.20, 0.28, 0.48, 12), stoneMid);
  spout.name = 'TopSpout';
  spout.position.y = 1.60;
  root.add(spout);

  const splashCap = new THREE.Mesh(new THREE.SphereGeometry(0.24, 10, 8), waterMat);
  splashCap.name = 'WaterSplashCap';
  splashCap.position.y = 1.90;
  root.add(splashCap);

  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  logger.info('Built model-fountain successfully');
};
