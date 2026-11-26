// 《时光小筑海滨小镇》4x 抱月双岬 + 离岸潮汐小屿（136m x 122m 陆地 / 184m x 168m 外海）
// 4+1 级微高差地形（L-0.5 / L0 / L0.5 / S-L1 / L1 / L2 / L2.5 / L3）与 F01-F42 槽位入口
// SCAD Z-up [x, y, z] -> Unity [-x, z, -y]
// SCAD +y 为 Unity 南面(-Z 海湾)，SCAD -y 为 Unity 北面(+Z 高台)

use <scad/lib/shiguang_parts.scad>

world_map_bounds = [136, 122];
world_outer_sea_bounds = [184, 168];
world_seed = 20261123;

// 沿局部 X 方向展开的连续坡道断面生成：section = [x_pos, z_top]
module sg_graded_ramp_x(width, sections, thickness=0.35) {
  n = len(sections);
  hw = width / 2;
  vertices = [for (q = sections) each [
    [q[0], -hw, q[1] - thickness],
    [q[0],  hw, q[1] - thickness],
    [q[0],  hw, q[1]],
    [q[0], -hw, q[1]]
  ]];
  faces = concat(
    [[0, 3, 2], [0, 2, 1]],
    [for (i = [0 : n - 2]) for (j = [0 : 3]) each
      let(a = 4 * i + j, b = 4 * i + (j + 1) % 4, c = b + 4, d = a + 4)
      [[a, b, c], [a, c, d]]],
    [[4 * (n - 1), 4 * (n - 1) + 1, 4 * (n - 1) + 2],
     [4 * (n - 1), 4 * (n - 1) + 2, 4 * (n - 1) + 3]]
  );
  polyhedron(points=vertices, faces=faces);
}

// 拱桥/栈桥连续弧面碰撞与桥面：从 p0 到 p1（SCAD 2D 坐标）
module sg_arch_span_xy(p0, p1, width, z_base, rise=0.95, steps=12, thickness=0.28) {
  d = [p1[0] - p0[0], p1[1] - p0[1]];
  L = sqrt(d[0]*d[0] + d[1]*d[1]);
  ang = atan2(d[1], d[0]);
  translate([p0[0], p0[1], 0])
    rotate([0, 0, ang])
      sg_graded_ramp_x(width, [
        for (i = [0 : steps])
          let(t = i / steps, u = 2 * t - 1)
          [t * L, z_base + rise * (1 - u * u)]
      ], thickness=thickness);
}

// 统一抱月主岛与南屿外轮廓（SCAD 坐标：X_s = -X_u, Y_s = -Z_u）
sg_main_coast_poly = [
  // 南湾内岸（由西岬角 -> 老镇弧岸 -> 东岬角）
  [64, 43], [50, 44.5], [40, 39.5], [36, 33.5],
  [32, 28.0], [25, 27.5], [18, 27.7], [10, 27.9], [0, 28.0],
  [-10, 27.8], [-18, 27.6], [-25, 27.4], [-32, 28.0],
  [-30.5, 33.5], [-41, 39.5], [-54, 42.0], [-64, 41.0],
  // 东外岸 -> 北山脊 -> 西外岸
  [-68, 32], [-68, 4], [-68, -28], [-62, -38],
  [-56, -52], [-52, -63], [-42, -67.5], [-24, -68],
  [0, -68], [24, -68], [42, -67.5], [52, -63],
  [56, -52], [62, -38], [68, -28], [68, 4], [68, 32]
];

sg_south_islet_poly = [
  [28, 40.5], [20, 36.5], [11, 35.2], [5, 35.8], [-4, 35.8],
  [-13.5, 38.5], [-24, 41.5], [-28, 48.0], [-22, 53.0], [-8, 54.0],
  [14, 54.0], [28, 52.5], [34, 46.5]
];

// 1. 184m x 168m 三段色带抱月外海与远景礁石
module sg_sea_band_ring(offset_r, z_pos, thickness) {
  translate([0, 0, z_pos])
    linear_extrude(height=thickness)
      difference() {
        square([184, 168], center=true);
        offset(r=offset_r) {
          polygon(sg_main_coast_poly);
          polygon(sg_south_islet_poly);
        }
      }
}

world_visual_form(id="sea-bay-4x", importance="secondary", structure_kind="landform") {
  // 近岸浅沫带 (0..1.4m)
  world_material([0.74, 0.85, 0.78], roughness=0.82)
    difference() {
      translate([0, 0, -0.04]) linear_extrude(height=0.04)
        offset(r=1.4) { polygon(sg_main_coast_poly); polygon(sg_south_islet_poly); }
      translate([0, 0, -0.06]) linear_extrude(height=0.10)
        { polygon(sg_main_coast_poly); polygon(sg_south_islet_poly); }
    }
  // 内湾薄荷浅海 (1.4..6.0m)
  world_material([0.48, 0.78, 0.91], roughness=0.72)
    difference() {
      translate([0, 0, -0.06]) linear_extrude(height=0.04)
        offset(r=6.0) { polygon(sg_main_coast_poly); polygon(sg_south_islet_poly); }
      translate([0, 0, -0.08]) linear_extrude(height=0.10)
        offset(r=1.4) { polygon(sg_main_coast_poly); polygon(sg_south_islet_poly); }
    }
  // 远海深青带 (6.0m..184x168m)
  world_material([0.30, 0.60, 0.72], roughness=0.70)
    translate([0, -4, 0]) sg_sea_band_ring(6.0, -0.08, 0.04);

  // 东湾潮间带 F28 浅池水面 (Y = +0.02m)
  world_material([0.48, 0.78, 0.91], roughness=0.45)
    translate([-36, 26, -0.02]) cylinder(h=0.04, r=4.6, $fn=24);

  // 北麓萤火浅溪 F32 水面 (Y = +3.32m)
  world_material([0.48, 0.78, 0.91], roughness=0.40) {
    hull() { translate([-32, -43, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); translate([-24, -36, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); }
    hull() { translate([-24, -36, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); translate([-18, -34.8, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); }
    hull() { translate([-18, -34.8, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); translate([-4, -35.6, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); }
    hull() { translate([-4, -35.6, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); translate([12, -34.5, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); }
    hull() { translate([12, -34.5, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); translate([28, -36.0, 3.30]) cylinder(h=0.04, r=1.1, $fn=12); }
  }
}

// 2. 4+1 级微高差连续可行走地形与全部 18 处坡道/桥梁（视觉与碰撞精准一致）
module sg_walkable_tiers_geometry(is_collider=false) {
  // === Zone 0 核心老镇（零改动原地保留，仅SE/NW/NE坡道延展0.2m确保<=18.5度）===
  // L0: 老镇南沙滩 (z = 0.20m)
  world_material([0.96, 0.90, 0.78], roughness=0.90)
    translate([-32, 14, -0.50]) cube([64, 14, 0.70]);
  // L1: 老镇生活主层 (z = 1.80m)
  world_material([0.72, 0.87, 0.66], roughness=0.88)
    translate([-32, -14, -0.50]) cube([64, 28, 2.30]);
  // L2: 老镇北高台 (z = 3.60m)
  world_material([0.58, 0.78, 0.58], roughness=0.88)
    translate([-30, -28, -0.50]) cube([60, 14, 4.10]);

  // === Zone W / E / S L0 亲水海滨层 (+0.20m) ===
  world_material([0.96, 0.90, 0.78], roughness=0.90) {
    // 全岛外缘沙滩底座 (+0.20m)
    difference() {
      translate([0, 0, -0.50]) linear_extrude(height=0.70) {
        polygon(sg_main_coast_poly);
        polygon(sg_south_islet_poly);
      }
      // 挖空东湾 L-0.5 潮间带深池凹槽（F28 at Unity +36, -26 -> SCAD -36, +26）
      translate([-36, 26, -0.30]) scale([5.6, 4.4, 1.0]) cylinder(h=0.80, r=1.0, $fn=24);
    }
    // L-0.5 东湾潮间带池底 (-0.15m) 与南北平缓斜坡
    translate([-36, 26, -0.50]) scale([6.2, 4.8, 1.0]) cylinder(h=0.35, r=1.0, $fn=24);
  }
  // R16a/b 潮间带 L0(+0.20)->L-0.5(-0.15) 6.7度平缓砾石坡
  world_material([0.78, 0.73, 0.64], roughness=0.90) {
    translate([-36, 0, 0]) sg_graded_ramp_y(3.4, [[21.6, 0.20], [24.6, -0.15]], thickness=0.30);
    translate([0, 26, 0]) sg_graded_ramp_x(3.4, [[-41.8, 0.20], [-38.8, -0.15]], thickness=0.30);
  }

  // === Zone E L0.5 旧造船木工坊船台 (+1.00m) ===
  world_material([0.89, 0.73, 0.55], roughness=0.86)
    translate([-62, 12.5, -0.50]) cube([16, 10, 1.50]); // Unity X:+46..+62, Z:-22.5..-12.5

  // === Zone S 南屿 S-L1 回声剧场台地 (+1.40m) ===
  world_material([0.72, 0.87, 0.66], roughness=0.88)
    translate([-6.5, 40.5, -0.50]) cube([18, 9.0, 1.90]); // Unity X:-11.5..+6.5, Z:-49.5..-40.5

  // === Zone W & Zone E L1 生活延展台地 (+1.80m) ===
  world_material([0.72, 0.87, 0.66], roughness=0.88) {
    // 西翼 L1：Unity X:-65..-32, Z:-19..+12（留出西南角 L2/L3 区域）
    translate([32, -12, -0.50]) cube([12.5, 31, 2.30]);   // X_u:-44.5..-32, Z_u:-19..+12
    translate([44.5, -12, -0.50]) cube([20.5, 22, 2.30]); // X_u:-65..-44.5, Z_u:-10..+12
    // 东翼 L1：Unity X:+32..+65, Z:-11..+11.5
    translate([-65, -11.5, -0.50]) cube([33, 22.5, 2.30]);
  }

  // === Zone W / E / N L2 暖阳台地与溪谷 (+3.60m) ===
  world_material([0.62, 0.81, 0.58], roughness=0.88) {
    // 西翼南 L2 (F21 风铃长廊台地 + Ramp 07 东入口落脚平台)：Unity X:-54..-42.5
    translate([44.5, 10, -0.50]) cube([9.5, 16, 4.10]);
    translate([42.5, 20.5, -0.50]) cube([2.0, 6.0, 4.10]);
    // 西北 L2 (F23a/b 崖居)：Unity X:-64..-30, Z:+12..+32
    translate([30, -32, -0.50]) cube([34, 20, 4.10]);
    // 东翼 L2 (F29 茶花梯田 / F30a)：Unity X:+30..+61, Z:+11.5..+32
    translate([-61, -32, -0.50]) cube([31, 20.5, 4.10]);
    // 北麓溪谷 L2 南岸带（Z_u: +28..+32.5）与北岸带（Z_u: +37..+62），中留溪床通道
    translate([-52, -32.5, -0.50]) cube([104, 4.5, 4.10]);
    difference() {
      translate([-52, -62, -0.50]) cube([104, 25, 4.10]);
      // 水车东侧流道微切口
      translate([-31, -43, 3.05]) cube([4.0, 6.0, 0.80]);
    }
    // 溪谷中央涉浅溪床底座 (+3.10m，双拱桥下可连续)
    translate([-34, -37.2, -0.50]) cube([68, 4.8, 3.60]);
  }

  // === Zone N L2.5 西北秘密树洞台地 (+4.20m) ===
  world_material([0.59, 0.79, 0.55], roughness=0.88)
    translate([31, -51, -0.50]) cube([11, 10, 4.70]); // Unity X:-42..-31, Z:+41..+51

  // === L3 双制高观景崖 (+5.40m) ===
  world_material([0.60, 0.80, 0.56], roughness=0.88) {
    // 西岬灯塔崖 F22：Unity X:-63..-51, Z:-31.5..-19.5
    translate([51, 19.5, -0.50]) cube([12, 12, 5.90]);
    // 北麓古樟星穹台 F34：Unity X:-10..+10, Z:+51..+65
    translate([-10, -65, -0.50]) cube([20, 14, 5.90]);
  }

  // === 全部 18 处跨层缓坡（均 <= 18.5度） ===
  // R01-R02 老镇南木坡
  world_material([0.62, 0.38, 0.20], roughness=0.84) {
    translate([6, 0, 0]) sg_graded_ramp_y(4.4, [[19.4, 0.20], [14.0, 1.80]], thickness=0.35);
    translate([-10, 0, 0]) sg_graded_ramp_y(4.4, [[19.4, 0.20], [14.0, 1.80]], thickness=0.35);
  }
  // R03-R04 老镇北石/草坡
  world_material([0.68, 0.64, 0.58], roughness=0.90)
    translate([16, 0, 0]) sg_graded_ramp_y(4.0, [[-8.1, 1.80], [-14.0, 3.60]], thickness=0.35);
  world_material([0.62, 0.81, 0.58], roughness=0.88)
    translate([-16, 0, 0]) sg_graded_ramp_y(4.2, [[-8.1, 1.80], [-14.0, 3.60]], thickness=0.35);

  // R05-R09 西翼坡道
  world_material([0.62, 0.38, 0.20], roughness=0.84)
    translate([35.5, 0, 0]) sg_graded_ramp_y(3.6, [[24.5, 0.20], [19.0, 1.80]], thickness=0.35);
  world_material([0.68, 0.64, 0.58], roughness=0.90) {
    translate([0, 14.0, 0]) sg_graded_ramp_x(3.4, [[38.5, 1.80], [44.5, 3.60]], thickness=0.35);
    translate([0, 24.0, 0]) sg_graded_ramp_x(3.4, [[44.5, 3.60], [51.0, 5.40]], thickness=0.35);
    translate([35.5, 0, 0]) sg_graded_ramp_y(3.4, [[-5.5, 1.80], [-12.0, 3.60]], thickness=0.35);
    translate([53.5, 0, 0]) sg_graded_ramp_y(3.0, [[-5.5, 1.80], [-12.0, 3.60]], thickness=0.35);
  }

  // R10-R12 东翼坡道
  world_material([0.62, 0.38, 0.20], roughness=0.84) {
    translate([-36.0, 0, 0]) sg_graded_ramp_y(3.6, [[17.0, 0.20], [11.0, 1.80]], thickness=0.35);
    translate([0, 21.5, 0]) sg_graded_ramp_x(3.2, [[-43.0, 0.20], [-46.0, 1.00]], thickness=0.35);
    translate([-49.0, 0, 0]) sg_graded_ramp_y(3.2, [[14.0, 1.00], [11.0, 1.80]], thickness=0.35);
  }
  world_material([0.62, 0.81, 0.58], roughness=0.88)
    translate([-40.0, 0, 0]) sg_graded_ramp_y(3.4, [[-5.5, 1.80], [-11.5, 3.60]], thickness=0.35);

  // R13-R15 北麓坡道
  world_material([0.68, 0.64, 0.58], roughness=0.90) {
    translate([0, -54.5, 0]) sg_graded_ramp_x(3.4, [[17.0, 3.60], [10.0, 5.40]], thickness=0.35);
    translate([0, -54.5, 0]) sg_graded_ramp_x(3.4, [[-17.0, 3.60], [-10.0, 5.40]], thickness=0.35);
  }
  world_material([0.59, 0.79, 0.55], roughness=0.88)
    translate([0, -44.0, 0]) sg_graded_ramp_x(2.8, [[27.2, 3.60], [31.50, 4.20]], thickness=0.35);

  // R17a/b/c 南屿剧场三向草坡
  world_material([0.72, 0.87, 0.66], roughness=0.88) {
    translate([5.0, 0, 0]) sg_graded_ramp_y(3.0, [[35.8, 0.20], [40.5, 1.40]], thickness=0.35);
    translate([0, 44.5, 0]) sg_graded_ramp_x(3.0, [[16.5, 0.20], [11.5, 1.40]], thickness=0.35);
    translate([0, 44.5, 0]) sg_graded_ramp_x(3.0, [[-11.5, 0.20], [-6.5, 1.40]], thickness=0.35);
  }

  // F32a/b 北溪双木拱桥 + F37 西跨海拱桥 + F38 东潮汐踏石连续通道
  world_material([0.62, 0.38, 0.20], roughness=0.84) {
    sg_arch_span_xy([12.0, -31.8], [12.0, -37.2], 2.8, 3.60, rise=0.38, steps=8);
    sg_arch_span_xy([-18.0, -32.1], [-18.0, -37.5], 2.8, 3.60, rise=0.38, steps=8);
    sg_arch_span_xy([36.0, 33.5], [20.0, 36.5], 2.8, 0.20, rise=0.95, steps=14);
  }
  world_material([0.48, 0.46, 0.44], roughness=0.90)
    sg_arch_span_xy([-30.5, 33.5], [-13.5, 38.5], 2.6, 0.20, rise=0.04, steps=8);
}

world_visual_form(id="town-terrain-tiers-4x", importance="primary", structure_kind="landform")
world_surface(id="walkable-ground", tags=["walkable"])
  sg_walkable_tiers_geometry(is_collider=false);

world_collider(id="walkable-ground-collider", tags=["walkable", "gameplay"], visual=false)
  sg_walkable_tiers_geometry(is_collider=true);

// 3. 装饰镶边、崖壁护坎、生态植被背衬与远景礁石
world_visual_form(id="town-trim-and-foliage-4x", importance="secondary", structure_kind="landform") {
  // 老镇保留木挡土与石坎
  world_material([0.54, 0.34, 0.19], roughness=0.86) {
    translate([-32, 13.7, 0.20]) cube([19.8, 0.45, 1.62]);
    translate([-7.8, 13.7, 0.20]) cube([11.6, 0.45, 1.62]);
    translate([8.2, 13.7, 0.20]) cube([23.8, 0.45, 1.62]);
  }
  world_material([0.66, 0.62, 0.56], roughness=0.90) {
    translate([-30, -14.2, 1.80]) cube([11.9, 0.45, 1.82]);
    translate([-13.9, -14.2, 1.80]) cube([27.9, 0.45, 1.82]);
    translate([18.0, -14.2, 1.80]) cube([12.0, 0.45, 1.82]);
  }

  // 外海远景礁石圈 (184m x 168m)
  for (rk = [
    [74, 38, 2.2], [-74, 38, 2.4], [38, 62, 1.8], [-34, 60, 1.9],
    [58, -74, 2.5], [-56, -74, 2.3], [78, -10, 2.0], [-78, -8, 2.1]
  ]) {
    translate([rk[0], rk[1], 0.05]) scale([rk[2], rk[2]*0.8, rk[2]*0.65]) sg_pebble_cluster();
  }

  // 分区树种点缀（海风歪颈松/金枫）
  for (tp = [
    [56, 11, 3.60], [61, 18, 3.60], [28, 48, 0.20], [-25, 48, 0.20],
    [-60, -25, 3.60], [45, -52, 3.60], [-42, -52, 3.60]
  ]) {
    translate([tp[0], tp[1], tp[2]]) sg_fruit_tree(0.95);
  }
}

// 4. 全岛 F01-F42 标准模型逻辑槽位（SCAD [-X_u, -Z_u, Y_u], rotate(-yaw)）
// --- Zone 0 原老镇 F01-F18（零改动保留）---
translate([6, 22, 0.20]) map_asset(instance_id="model-arrival-dock", slot="arrival-dock", proxy_size=[6, 5, 3.1]) sg_slot_proxy([6, 5, 3.1], [0.76, 0.56, 0.34]);
translate([-10, 23, 0.20]) rotate([0, 0, 180]) map_asset(instance_id="fishing-pier", slot="pier", proxy_size=[4, 8, 1.4]) sg_slot_proxy([4, 8, 1.4], [0.62, 0.40, 0.22]);
translate([18, 19, 0.20]) map_asset(instance_id="model-beach-discovery", slot="beach-discovery", proxy_size=[11.4, 4.6, 0.8]) sg_slot_proxy([11.4, 4.6, 0.8], [0.85, 0.72, 0.56]);
translate([10, 2, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="cottage-main", slot="cottage", proxy_size=[8, 6, 4.8]) sg_slot_proxy([8, 6, 4.8], [0.76, 0.48, 0.32]);
translate([2, 7, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="coffee-terrace", slot="terrace", proxy_size=[5, 4, 1.4]) sg_slot_proxy([5, 4, 1.4], [0.68, 0.48, 0.28]);
translate([-5, 8, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="flower-bed", slot="flowerbed", proxy_size=[6, 4, 1.0]) sg_slot_proxy([6, 4, 1.0], [0.85, 0.42, 0.56]);
translate([-1, 11, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="pixel-flag", slot="flagpole", proxy_size=[1.6, 1.6, 4.2]) sg_slot_proxy([1.6, 1.6, 4.2], [0.85, 0.28, 0.28]);
translate([6, 10, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="chalkboard-main", slot="chalkboard", proxy_size=[2.0, 1.2, 1.8]) sg_slot_proxy([2.0, 1.2, 1.8], [0.28, 0.30, 0.34]);
translate([-14, 1, 1.80]) map_asset(instance_id="wish-fountain", slot="fountain", proxy_size=[6, 6, 2.2]) sg_slot_proxy([6, 6, 2.2], [0.42, 0.72, 0.85]);
translate([-19, -5, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="model-vending", slot="vending", proxy_size=[2.5, 2.0, 2.4]) sg_slot_proxy([2.5, 2.0, 2.4], [0.82, 0.65, 0.72]);
translate([-11, -5, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="model-plaza-benches", slot="plaza-benches", proxy_size=[5.0, 2.5, 1.2]) sg_slot_proxy([5.0, 2.5, 1.2], [0.70, 0.52, 0.34]);
translate([-23, 4, 1.80]) rotate([0, 0, 90]) map_asset(instance_id="model-cafe-kiosk", slot="cafe-kiosk", proxy_size=[5.0, 4.0, 3.5]) sg_slot_proxy([5.0, 4.0, 3.5], [0.48, 0.78, 0.90]);
translate([24, -4, 1.80]) rotate([0, 0, -90]) map_asset(instance_id="model-resident-amber", slot="resident-amber", proxy_size=[5.0, 4.5, 4.5]) sg_slot_proxy([5.0, 4.5, 4.5], [0.90, 0.75, 0.56]);
translate([23, -11, 1.80]) rotate([0, 0, -90]) map_asset(instance_id="model-resident-sage", slot="resident-sage", proxy_size=[5.0, 4.5, 4.5]) sg_slot_proxy([5.0, 4.5, 4.5], [0.65, 0.76, 0.60]);
translate([-24, -8, 1.80]) rotate([0, 0, 90]) map_asset(instance_id="model-resident-blue", slot="resident-blue", proxy_size=[5.0, 4.5, 3.8]) sg_slot_proxy([5.0, 4.5, 3.8], [0.55, 0.70, 0.80]);
translate([22, 6, 1.80]) rotate([0, 0, -90]) map_asset(instance_id="model-community-pavilion", slot="community-pavilion", proxy_size=[5.0, 5.0, 3.2]) sg_slot_proxy([5.0, 5.0, 3.2], [0.72, 0.50, 0.30]);
translate([12, -20, 3.60]) rotate([0, 0, 180]) map_asset(instance_id="windmill-north", slot="windmill", proxy_size=[5, 5, 8.5]) sg_slot_proxy([5, 5, 8.5], [0.78, 0.56, 0.38]);
translate([2, -18, 3.60]) rotate([0, 0, 180]) map_asset(instance_id="model-sunset-overlook", slot="sunset-overlook", proxy_size=[5.3, 3.9, 3.6]) sg_slot_proxy([5.3, 3.9, 3.6], [0.52, 0.68, 0.72]);
translate([-14, -19, 3.60]) map_asset(instance_id="model-fruit-orchard", slot="fruit-orchard", proxy_size=[13.4, 5.4, 3.8]) sg_slot_proxy([13.4, 5.4, 3.8], [0.46, 0.72, 0.42]);
translate([-23, -17, 3.60]) rotate([0, 0, 90]) map_asset(instance_id="model-memory-corner", slot="memory-corner", proxy_size=[5.8, 5.2, 2.0]) sg_slot_proxy([5.8, 5.2, 2.0], [0.68, 0.64, 0.76]);

// --- Zone W / E / N / S 新增 F19-F42 槽位 ---
translate([44, -4, 1.80]) rotate([0, 0, -180]) map_asset(instance_id="F19-windchime-post-office", slot="windchime-post-office", proxy_size=[9, 7, 5.5]) sg_slot_proxy([9, 7, 5.5], [0.72, 0.48, 0.42]);
translate([38, 8, 1.80]) rotate([0, 0, -165]) map_asset(instance_id="F20-mailbox-gallery", slot="mailbox-gallery", proxy_size=[6, 4, 3.2]) sg_slot_proxy([6, 4, 3.2], [0.80, 0.60, 0.44]);
translate([49.5, 14, 3.60]) rotate([0, 0, -160]) map_asset(instance_id="F21-windchime-corridor", slot="windchime-corridor", proxy_size=[6.4, 3.8, 3.8]) sg_slot_proxy([6.4, 3.8, 3.8], [0.56, 0.78, 0.85]);
translate([56, 24, 5.40]) rotate([0, 0, -145]) map_asset(instance_id="F22-west-cape-lighthouse", slot="west-cape-lighthouse", proxy_size=[7, 7, 11.5]) sg_slot_proxy([7, 7, 11.5], [0.86, 0.45, 0.36]);
translate([48, -20, 3.60]) rotate([0, 0, -180]) map_asset(instance_id="F23a-cliff-cottage", slot="cliff-cottage", proxy_size=[5.5, 4.5, 4.2]) sg_slot_proxy([5.5, 4.5, 4.2], [0.56, 0.66, 0.76]);
translate([58, -14, 3.60]) rotate([0, 0, -145]) map_asset(instance_id="F23b-cliff-cottage", slot="cliff-cottage", proxy_size=[5.5, 4.5, 4.2]) sg_slot_proxy([5.5, 4.5, 4.2], [0.56, 0.66, 0.76]);
translate([42, 30, 0.20]) rotate([0, 0, -135]) map_asset(instance_id="F24-driftwood-campfire", slot="driftwood-campfire", proxy_size=[6, 5, 1.4]) sg_slot_proxy([6, 5, 1.4], [0.88, 0.56, 0.30]);

translate([-44, 4, 1.80]) rotate([0, 0, 150]) map_asset(instance_id="F25-bakery-kiln-stall", slot="bakery-kiln-stall", proxy_size=[12, 9.5, 4.2]) sg_slot_proxy([12, 9.5, 4.2], [0.84, 0.48, 0.34]);
translate([-54, 18, 1.00]) rotate([0, 0, 120]) map_asset(instance_id="F26-old-boatyard", slot="old-boatyard", proxy_size=[10, 8, 5.0]) sg_slot_proxy([10, 8, 5.0], [0.76, 0.56, 0.36]);
translate([-52, 32, 0.20]) rotate([0, 0, 115]) map_asset(instance_id="F27-daylight-lightship", slot="daylight-lightship", proxy_size=[11, 5, 9.5]) sg_slot_proxy([11, 5, 9.5], [0.48, 0.76, 0.88]);
translate([-36, 26, -0.15]) map_asset(instance_id="F28-tidepool-rocks", slot="tidepool-rocks", proxy_size=[11, 8.5, 1.5]) sg_slot_proxy([11, 8.5, 1.5], [0.58, 0.72, 0.76]);
translate([-48, -14, 3.60]) rotate([0, 0, 180]) map_asset(instance_id="F29-kite-terrace-bench", slot="kite-terrace-bench", proxy_size=[9, 7, 2.8]) sg_slot_proxy([9, 7, 2.8], [0.86, 0.58, 0.62]);
translate([-42, -24, 3.60]) rotate([0, 0, 180]) map_asset(instance_id="F30a-studio-cottage", slot="studio-cottage", proxy_size=[5.5, 4.5, 4.2]) sg_slot_proxy([5.5, 4.5, 4.2], [0.92, 0.80, 0.48]);
translate([-56, -4, 1.80]) rotate([0, 0, 90]) map_asset(instance_id="F30b-studio-cottage", slot="studio-cottage", proxy_size=[5.5, 4.5, 4.2]) sg_slot_proxy([5.5, 4.5, 4.2], [0.64, 0.84, 0.74]);

translate([16, -42, 3.60]) rotate([0, 0, -180]) map_asset(instance_id="F31-memory-greenhouse", slot="memory-greenhouse", proxy_size=[12, 9, 6.2]) sg_slot_proxy([12, 9, 6.2], [0.68, 0.88, 0.78]);
translate([12, -34.5, 3.60]) map_asset(instance_id="F32a-creek-arch-bridge", slot="creek-arch-bridge", proxy_size=[2.8, 5.6, 2.0]) sg_slot_proxy([2.8, 5.6, 2.0], [0.76, 0.54, 0.34]);
translate([-18, -34.8, 3.60]) map_asset(instance_id="F32b-creek-arch-bridge", slot="creek-arch-bridge", proxy_size=[2.8, 5.6, 2.0]) sg_slot_proxy([2.8, 5.6, 2.0], [0.76, 0.54, 0.34]);
translate([-26, -42, 3.60]) rotate([0, 0, -180]) map_asset(instance_id="F33-forest-watermill", slot="forest-watermill", proxy_size=[7, 6, 4.8]) sg_slot_proxy([7, 6, 4.8], [0.72, 0.58, 0.46]);
translate([0, -58, 5.40]) rotate([0, 0, -180]) map_asset(instance_id="F34-camphor-bell-pavilion", slot="camphor-bell-pavilion", proxy_size=[12, 10, 12.5]) sg_slot_proxy([12, 10, 12.5], [0.54, 0.78, 0.52]);
translate([26.5, -35, 3.60]) map_asset(instance_id="F35W-timber-slide", slot="timber-slide", proxy_size=[2.4, 45.0, 3.8]) sg_slot_proxy([2.4, 12.0, 3.8], [0.80, 0.56, 0.32]);
translate([-27, -35.5, 3.60]) map_asset(instance_id="F35E-timber-slide", slot="timber-slide", proxy_size=[2.4, 45.0, 3.8]) sg_slot_proxy([2.4, 12.0, 3.8], [0.80, 0.56, 0.32]);
translate([36, -46, 4.20]) rotate([0, 0, -150]) map_asset(instance_id="F36-tree-hollow-postbox", slot="tree-hollow-postbox", proxy_size=[5, 4.5, 3.5]) sg_slot_proxy([5, 4.5, 3.5], [0.64, 0.42, 0.26]);

translate([28, 35, 0.20]) rotate([0, 0, -100.6]) map_asset(instance_id="F37-sea-arch-bridge", slot="sea-arch-bridge", proxy_size=[2.8, 16.5, 3.0]) sg_slot_proxy([2.8, 16.5, 3.0], [0.74, 0.50, 0.28]);
translate([-22, 36, 0.20]) rotate([0, 0, 106.4]) map_asset(instance_id="F38-tidal-stepping-stones", slot="tidal-stepping-stones", proxy_size=[2.6, 17.8, 1.2]) sg_slot_proxy([2.6, 17.8, 1.2], [0.54, 0.52, 0.56]);
translate([2, 45, 1.40]) map_asset(instance_id="F39-echo-amphitheater-arch", slot="echo-amphitheater-arch", proxy_size=[10, 9, 6.5]) sg_slot_proxy([10, 9, 6.5], [0.86, 0.74, 0.58]);
translate([5, 36, 0.20]) map_asset(instance_id="F40-ferry-dock-rowboat", slot="ferry-dock-rowboat", proxy_size=[5, 4.5, 2.2]) sg_slot_proxy([5, 4.5, 2.2], [0.56, 0.78, 0.80]);
translate([-10, 47, 0.20]) rotate([0, 0, 25]) map_asset(instance_id="F41-mini-book-booth", slot="mini-book-booth", proxy_size=[2.5, 2.0, 2.6]) sg_slot_proxy([2.5, 2.0, 2.6], [0.60, 0.84, 0.74]);

translate([-6, -4.5, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="F42a-postal-bike-stop", slot="postal-bike-stop", proxy_size=[2.4, 1.2, 2.3]) sg_slot_proxy([2.4, 1.2, 2.3], [0.54, 0.82, 0.72]);
translate([34, 3.5, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="F42b-postal-bike-stop", slot="postal-bike-stop", proxy_size=[2.4, 1.2, 2.3]) sg_slot_proxy([2.4, 1.2, 2.3], [0.54, 0.82, 0.72]);
translate([-40, -5, 1.80]) rotate([0, 0, 180]) map_asset(instance_id="F42c-postal-bike-stop", slot="postal-bike-stop", proxy_size=[2.4, 1.2, 2.3]) sg_slot_proxy([2.4, 1.2, 2.3], [0.54, 0.82, 0.72]);
translate([12, -31.5, 3.60]) rotate([0, 0, 180]) map_asset(instance_id="F42d-postal-bike-stop", slot="postal-bike-stop", proxy_size=[2.4, 1.2, 2.3]) sg_slot_proxy([2.4, 1.2, 2.3], [0.54, 0.82, 0.72]);

// 5. 多条连续通行路线诊断（全部 <= 18.5度，覆盖内环、大外环与四片区次环）
world_traversal_route(id="main-route", role="primary",
  points=[[6,22,0.20],[6,19.4,0.20],[6,14.0,1.80],[6,10.5,1.80],[16,10.5,1.80],[16,-8.4,1.80],[16,-14.0,3.60],[12,-16.5,3.60]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="outer-coastal-loop", role="primary",
  points=[
    [51,24,5.40],[44.5,24,3.60],[44.5,14,3.60],[38.5,14,1.80],[35.5,19.0,1.80],[35.5,24.5,0.20],[36,33.5,0.20],
    [20,36.5,0.20],[16.5,44.5,0.20],[11.5,44.5,1.40],[-6.5,44.5,1.40],[-11.5,44.5,0.20],[-13.5,38.5,0.20],
    [-30.5,33.5,0.20],[-36,24,0.20],[-36,16.5,0.20],[-36,10.5,1.80],[-40,-5.5,1.80],[-40,-11.5,3.60],
    [-18,-32.1,3.60],[-18,-37.5,3.60],[-10,-54.5,5.40],[10,-54.5,5.40],[17,-54.5,3.60],
    [12,-37.2,3.60],[12,-31.8,3.60],[35.5,-12.0,3.60],[35.5,-5.5,1.80],[44,0,1.80],[38.5,14,1.80]
  ],
  capsule=[0.45,1.7], sample_spacing=0.45, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="west-cape-loop", role="secondary",
  points=[[34,3.5,1.80],[35.5,-5.5,1.80],[35.5,-12.0,3.60],[48,-16,3.60],[53.5,-12.0,3.60],[53.5,-5.5,1.80],[44,0,1.80],[38,8,1.80],[35.5,19.0,1.80],[35.5,24.5,0.20],[42,30,0.20]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="east-bay-loop", role="secondary",
  points=[[-40,4,1.80],[-49,10.3,1.80],[-49,13.5,1.00],[-46.2,21.5,1.00],[-43.0,21.5,0.20],[-48,29,0.20],[-36,26,-0.15],[-36,20.5,0.20],[-36,16.5,0.20],[-36,10.5,1.80],[-40,4,1.80]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="north-valley-loop", role="secondary",
  points=[[12,-31.8,3.60],[12,-37.2,3.60],[17,-54.5,3.60],[10,-54.5,5.40],[-10,-54.5,5.40],[-17,-54.5,3.60],[-18,-37.5,3.60],[-18,-32.1,3.60],[12,-31.8,3.60]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="south-islet-loop", role="secondary",
  points=[[20,36.5,0.20],[5,36.5,0.20],[5,41.5,1.40],[-6.5,44.5,1.40],[-11.5,44.5,0.20],[-13.5,38.5,0.20],[-10,47,0.20],[16.5,44.5,0.20],[20,36.5,0.20]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="east-west-promenade", role="primary",
  points=[[44,0,1.80],[34,3.5,1.80],[20,-2.5,1.80],[10,-2.5,1.80],[-14,-1.0,1.80],[-23,4.0,1.80],[-40,4.0,1.80],[-52,-4.0,1.80]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);

world_traversal_route(id="knoll-secret-route", role="secondary",
  points=[[22,-44.0,3.60],[27.5,-44.0,3.60],[31.0,-44.0,4.20],[36,-46,4.20]],
  capsule=[0.45,1.7], sample_spacing=0.40, max_slope_degrees=18.5, max_step_height=0.20);
