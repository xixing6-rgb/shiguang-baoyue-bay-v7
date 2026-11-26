// 《时光小筑海滨小镇》SCAD 地形与背景构件库 (Units: meters, Z-up)

// 连续坡道断面生成：section = [y_pos, z_top]（沿局部 Y 方向展开）
module sg_graded_ramp_y(width, sections, thickness=0.32) {
  n = len(sections);
  hw = width / 2;
  vertices = [for (q = sections) each [
    [-hw, q[0], q[1] - thickness],
    [ hw, q[0], q[1] - thickness],
    [ hw, q[0], q[1]],
    [-hw, q[0], q[1]]
  ]];
  faces = concat(
    [[0, 1, 2], [0, 2, 3]],
    [for (i = [0 : n - 2]) for (j = [0 : 3]) each
      let(a = 4 * i + j, b = 4 * i + (j + 1) % 4, c = b + 4, d = a + 4)
      [[a, d, c], [a, c, b]]],
    [[4 * (n - 1), 4 * (n - 1) + 3, 4 * (n - 1) + 2],
     [4 * (n - 1), 4 * (n - 1) + 2, 4 * (n - 1) + 1]]
  );
  polyhedron(points=vertices, faces=faces);
}

// 坡道两侧矮木护栏
module sg_ramp_rails_y(width, y_start, z_start, y_end, z_end) {
  hw = width / 2 + 0.12;
  dy = y_end - y_start;
  dz = z_end - z_start;
  len_slope = sqrt(dy * dy + dz * dz);
  pitch = atan2(dz, abs(dy));
  sign_y = dy >= 0 ? 1 : -1;

  world_material([0.52, 0.30, 0.16], roughness=0.82) {
    for (sx = [-hw, hw]) {
      for (t = [0.1, 0.5, 0.9]) {
        translate([sx, y_start + dy * t, z_start + dz * t - 0.05])
          cylinder(h=0.58, r=0.075, $fn=8);
      }
      translate([sx, (y_start + y_end) / 2, (z_start + z_end) / 2 + 0.45])
        rotate([sign_y * pitch, 0, 0])
          cube([0.11, len_slope, 0.09], center=true);
    }
  }
}

// 海岸鹅卵石簇
module sg_pebble_cluster(seed_offset=0) {
  world_material([0.56, 0.52, 0.47], roughness=0.92) {
    scale([0.75, 0.58, 0.36]) sphere(r=1.0, $fn=10);
    translate([0.85, 0.35, -0.05]) scale([0.45, 0.42, 0.28]) sphere(r=1.0, $fn=9);
    translate([-0.68, 0.48, -0.06]) scale([0.36, 0.32, 0.24]) sphere(r=1.0, $fn=8);
  }
}

// 标志性 3 果实圆润果树（L2 东翼秘境果林背衬）
module sg_fruit_tree(scale_f=1.0) {
  // 树干
  world_material([0.44, 0.25, 0.13], roughness=0.88)
    cylinder(h=2.0 * scale_f, r1=0.30 * scale_f, r2=0.22 * scale_f, $fn=10);
  // 3 团柔和圆润树冠
  world_material([0.34, 0.62, 0.28], roughness=0.84) {
    translate([0, 0, 2.75 * scale_f]) sphere(r=1.18 * scale_f, $fn=12);
    translate([-0.55 * scale_f, 0.35 * scale_f, 2.35 * scale_f]) sphere(r=0.85 * scale_f, $fn=10);
    translate([0.58 * scale_f, -0.30 * scale_f, 2.40 * scale_f]) sphere(r=0.86 * scale_f, $fn=10);
  }
  // 3 颗高辨识度圆润果实（正反均清晰可见）
  world_material([0.86, 0.26, 0.22], roughness=0.45) {
    translate([-0.52 * scale_f, 0.92 * scale_f, 2.55 * scale_f]) sphere(r=0.20 * scale_f, $fn=8);
    translate([0.56 * scale_f, 0.85 * scale_f, 2.85 * scale_f]) sphere(r=0.20 * scale_f, $fn=8);
    translate([0.05 * scale_f, -0.96 * scale_f, 2.65 * scale_f]) sphere(r=0.20 * scale_f, $fn=8);
  }
}

// 圆润灌木点缀
module sg_round_bush(r=0.75) {
  world_material([0.30, 0.56, 0.26], roughness=0.88) {
    translate([0, 0, r * 0.65]) scale([1.15, 1.05, 0.85]) sphere(r=r, $fn=10);
    translate([r * 0.5, r * 0.2, r * 0.48]) scale([0.9, 0.9, 0.78]) sphere(r=r * 0.65, $fn=8);
  }
}

// 槽位占位代理体（不烘入 map.glb，仅用于布局与预览参考）
module sg_slot_proxy(size_vec, col=[0.75, 0.62, 0.45]) {
  world_material(col, roughness=0.7)
    translate([-size_vec[0] / 2, -size_vec[1] / 2, 0])
      cube(size_vec);
}
