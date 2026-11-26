// 《时光小筑海滨小镇》64m x 56m 三级微高差地形与槽位入口
// SCAD Z-up [x, y, z] -> Unity [-x, z, -y]
// SCAD +y 为 Unity 南面(-Z 海湾)，SCAD -y 为 Unity 北面(+Z 高台)

use <scad/lib/shiguang_parts.scad>

world_map_bounds = [64, 56];
world_seed = 20261122;

// 1. 南侧海湾。水面抬离宿主地形，三段色带以同一条岸线拼接。
sg_shore = [[-46,30],[-37,29.2],[-32,26.4],[-25,26.8],[-18,27.3],
            [-10,27.7],[0,28.1],[10,27.5],[18,27.1],[25,26.8],
            [32,26.3],[37,29.1],[46,30]];

module sg_coastal_water(start_delta, end_delta) {
  n = len(sg_shore);
  points = concat(
    [for (p=sg_shore) [p[0],p[1]+start_delta]],
    [for (i=[n-1:-1:0]) [sg_shore[i][0],sg_shore[i][1]+end_delta]]
  );
  translate([0,0,0.27]) linear_extrude(height=0.08) polygon(points);
}

world_visual_form(id="sea-bay", importance="secondary", structure_kind="landform") {
  world_material([0.74,0.81,0.69], roughness=0.84)
    sg_coastal_water(0,0.21);
  world_material([0.34,0.62,0.61], roughness=0.74)
    sg_coastal_water(0.21,2.5);
  world_material([0.23,0.49,0.56], roughness=0.70)
    sg_coastal_water(2.5,30);
}

// 2. 三级微高差连续可行走地形与坡道（视觉与碰撞单一精准对齐）
module sg_walkable_tiers_geometry() {
  // L0: 南侧亲水沙滩层 (z = 0.20m, SCAD y: +14..+28)
  world_material([0.88, 0.77, 0.56], roughness=0.90)
    translate([-32, 14, -0.50]) cube([64, 14, 0.70]);

  // L1: 核心生活主台地 (z = 1.80m, SCAD y: -14..+14)
  world_material([0.46, 0.72, 0.36], roughness=0.88)
    translate([-32, -14, -0.50]) cube([64, 28, 2.30]);

  // L2: 北侧暖阳观景高台 (z = 3.60m, SCAD y: -28..-14)
  world_material([0.52, 0.75, 0.35], roughness=0.88)
    translate([-30, -28, -0.50]) cube([60, 14, 4.10]);

  // 南西木阶坡道 (Unity X=-6 -> SCAD x=+6, y: +19.4 -> +14.0, z: 0.20 -> 1.80, 约16.5度)
  world_material([0.62, 0.38, 0.20], roughness=0.84)
    translate([6, 0, 0])
      sg_graded_ramp_y(4.4, [[19.4, 0.20], [14.02, 1.80]], thickness=0.35);

  // 南东木阶坡道 (Unity X=+10 -> SCAD x=-10, y: +18.8 -> +14.0, z: 0.20 -> 1.80, 约18.4度)
  world_material([0.62, 0.38, 0.20], roughness=0.84)
    translate([-10, 0, 0])
      sg_graded_ramp_y(4.4, [[18.8, 0.20], [14.02, 1.80]], thickness=0.35);

  // 北西圆石缓坡 (Unity X=-16 -> SCAD x=+16, y: -8.6 -> -14.0, z: 1.80 -> 3.60, 约18.4度)
  world_material([0.68, 0.64, 0.58], roughness=0.90)
    translate([16, 0, 0])
      sg_graded_ramp_y(4.0, [[-8.6, 1.80], [-13.98, 3.60]], thickness=0.35);

  // 北东林间缓坡 (Unity X=+16 -> SCAD x=-16, y: -8.2 -> -14.0, z: 1.80 -> 3.60, 约17.2度)
  world_material([0.49, 0.73, 0.36], roughness=0.88)
    translate([-16, 0, 0])
      sg_graded_ramp_y(4.2, [[-8.2, 1.80], [-13.98, 3.60]], thickness=0.35);
}

// 碰撞几何使用简洁无材质实体，与顶面精确一致
module sg_walkable_colliders_only() {
  translate([-32, 14, -0.50]) cube([64, 14, 0.70]);
  translate([-32, -14, -0.50]) cube([64, 28, 2.30]);
  translate([-30, -28, -0.50]) cube([60, 14, 4.10]);
  translate([6, 0, 0]) sg_graded_ramp_y(4.4, [[19.4, 0.20], [14.02, 1.80]], thickness=0.35);
  translate([-10, 0, 0]) sg_graded_ramp_y(4.4, [[18.8, 0.20], [14.02, 1.80]], thickness=0.35);
  translate([16, 0, 0]) sg_graded_ramp_y(4.0, [[-8.6, 1.80], [-13.98, 3.60]], thickness=0.35);
  translate([-16, 0, 0]) sg_graded_ramp_y(4.2, [[-8.2, 1.80], [-13.98, 3.60]], thickness=0.35);
}

world_visual_form(id="town-terrain-tiers", importance="primary", structure_kind="landform")
world_surface(id="walkable-ground", tags=["walkable"])
  sg_walkable_tiers_geometry();

world_collider(id="walkable-ground-collider", tags=["walkable", "gameplay"], visual=false)
  sg_walkable_colliders_only();

// 3. 装饰镶边、石板路、木护栏、海岸鹅卵石与 L2 东翼果树背衬
world_visual_form(id="town-trim-and-foliage", importance="secondary", structure_kind="landform") {
  // L1 边缘暖木挡土装饰条（避开坡道口）
  world_material([0.54, 0.34, 0.19], roughness=0.86) {
    translate([-32, 13.7, 0.20]) cube([19.8, 0.45, 1.62]);
    translate([-7.8, 13.7, 0.20]) cube([11.6, 0.45, 1.62]);
    translate([8.2, 13.7, 0.20]) cube([23.8, 0.45, 1.62]);
  }
  // L2 边缘暖石矮坎（避开坡道口）
  world_material([0.66, 0.62, 0.56], roughness=0.90) {
    translate([-30, -14.2, 1.80]) cube([11.9, 0.45, 1.82]);
    translate([-13.9, -14.2, 1.80]) cube([27.9, 0.45, 1.82]);
    translate([18.0, -14.2, 1.80]) cube([12.0, 0.45, 1.82]);
  }

  // L1 主庭院至心愿广场及各坡道口的浅暖石板拼花小径（视觉装饰，仅高出草面 1.5cm）
  world_material([0.82, 0.77, 0.68], roughness=0.88) {
    for (px = [-10 : 2.2 : 12]) {
      translate([px, 10.8, 1.805]) cylinder(h=0.02, r=0.82, $fn=10);
    }
    for (py = [2.5 : 2.2 : 9.0]) {
      translate([4.2, py, 1.805]) cylinder(h=0.02, r=0.78, $fn=10);
    }
    // 衔接南西、南东坡道口与北侧高台石阶口的石板踏步
    translate([6, 12.6, 1.805]) cylinder(h=0.02, r=0.82, $fn=10);
    translate([-10, 12.6, 1.805]) cylinder(h=0.02, r=0.82, $fn=10);
    for (py = [-7.0 : 2.2 : 10.0]) {
      translate([16, py, 1.805]) cylinder(h=0.02, r=0.72, $fn=10);
    }
  }
  // L0 沙滩衔接南东坡道至钓鱼栈桥的暖木踩板
  world_material([0.62, 0.38, 0.20], roughness=0.84) {
    for (py = [19.4, 20.1, 20.8]) {
      translate([-10, py, 0.21]) cube([2.4, 0.45, 0.04], center=true);
    }
  }

  // 两座南侧木阶扶手栏杆
  translate([6, 0, 0]) sg_ramp_rails_y(4.4, 19.4, 0.20, 14.0, 1.80);
  translate([-10, 0, 0]) sg_ramp_rails_y(4.4, 18.8, 0.20, 14.0, 1.80);

  // 海岸鹅卵石簇
  translate([22, 23, 0.20]) sg_pebble_cluster();
  translate([-24, 24, 0.20]) rotate([0, 0, 45]) sg_pebble_cluster();

  // 秘境果林现由独立 F17 资源承载，此处仅保留背景灌木。
  for (bp = [
    [22, -22, 0.85], [24, -18, 0.70], [4, -22, 0.80],
    [24, 8, 0.72], [-26, 8, 0.75]
  ]) {
    translate([bp[0], bp[1], bp[1] < -14 ? 3.60 : 1.80]) sg_round_bush(bp[2]);
  }
}

// 4. 8 处标准独立模型逻辑槽位（代理底面居中 Z=0，正面 -Y -> 朝南向海旋转 180°）
translate([10, 2, 1.80]) rotate([0, 0, 180])
  map_asset(instance_id="cottage-main", slot="cottage", proxy_size=[8, 6, 4.8])
    sg_slot_proxy([8, 6, 4.8], [0.76, 0.48, 0.32]);

translate([-10, 23, 0.20]) rotate([0, 0, 180])
  map_asset(instance_id="fishing-pier", slot="pier", proxy_size=[4, 8, 1.4])
    sg_slot_proxy([4, 8, 1.4], [0.62, 0.40, 0.22]);

translate([2, 7, 1.80]) rotate([0, 0, 180])
  map_asset(instance_id="coffee-terrace", slot="terrace", proxy_size=[5, 4, 1.4])
    sg_slot_proxy([5, 4, 1.4], [0.68, 0.48, 0.28]);

translate([-5, 8, 1.80]) rotate([0, 0, 180])
  map_asset(instance_id="flower-bed", slot="flowerbed", proxy_size=[6, 4, 1.0])
    sg_slot_proxy([6, 4, 1.0], [0.85, 0.42, 0.56]);

translate([-1, 11, 1.80]) rotate([0, 0, 180])
  map_asset(instance_id="pixel-flag", slot="flagpole", proxy_size=[1.6, 1.6, 4.2])
    sg_slot_proxy([1.6, 1.6, 4.2], [0.85, 0.28, 0.28]);

translate([6, 10, 1.80]) rotate([0, 0, 180])
  map_asset(instance_id="chalkboard-main", slot="chalkboard", proxy_size=[2.0, 1.2, 1.8])
    sg_slot_proxy([2.0, 1.2, 1.8], [0.28, 0.30, 0.34]);

translate([-14, 1, 1.80])
  map_asset(instance_id="wish-fountain", slot="fountain", proxy_size=[6, 6, 2.2])
    sg_slot_proxy([6, 6, 2.2], [0.42, 0.72, 0.85]);

translate([12, -20, 3.60]) rotate([0, 0, 180])
  map_asset(instance_id="windmill-north", slot="windmill", proxy_size=[5, 5, 8.5])
    sg_slot_proxy([5, 5, 8.5], [0.78, 0.56, 0.38]);

// 5. 连续通行路线诊断（从 L0 沙滩经南西木坡上 L1 庭院至北西石坡上 L2 风车平台）
world_traversal_route(
  id="main-route",
  role="primary",
  points=[
    [6, 22, 0.20],
    [6, 19.4, 0.20],
    [6, 14.02, 1.80],
    [6, 10.5, 1.80],
    [16, 10.5, 1.80],
    [16, -8.6, 1.80],
    [16, -13.98, 3.60],
    [12, -16.5, 3.60]
  ],
  capsule=[0.45, 1.7],
  sample_spacing=0.45,
  max_slope_degrees=25,
  max_step_height=0.25
);
