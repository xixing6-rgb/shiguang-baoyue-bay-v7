// Small editable examples, not host APIs. Units: meters; local base z=0.
use <kit_layout.scad>
use <kit_terrain.scad>

module env_terrain(t) {
    // Terrain contains material patches and a query surface, not one closed
    // Mesh per material. Do not label every patch as a solid structural part.
    world_visual_form(id="terrain", importance="secondary",
        technique="canonical-terrain", topology_class="continuous-terrain")
    world_surface(id="terrain", tags=["walkable"]) world_terrain(t);
    world_collider(id="terrain-collider", tags=["walkable"], visual=false)
        world_terrain_collider(t);
}

// The visible road is TERR's road feature, not a floating straight slab.
// Densely sampled foot points follow the same field used by its only collider.
function env_route_points(t, pts, spacing=0.5) = concat(
    [for (s=[0:len(pts)-2])
        for (k=[0:max(1,ceil(norm(pts[s+1]-pts[s])/spacing))-1])
            let(n=max(1,ceil(norm(pts[s+1]-pts[s])/spacing)),
                p=pts[s]+(pts[s+1]-pts[s])*k/n)
                [p[0],p[1],world_terrain_height(t,p[0],p[1])]],
    [[pts[len(pts)-1][0],pts[len(pts)-1][1],
      world_terrain_height(t,pts[len(pts)-1][0],pts[len(pts)-1][1])]]);
module env_route(t, pts) {
    world_traversal_route(id="main-route", role="primary", points=env_route_points(t,pts),
        capsule=[0.5,1.8], sample_spacing=0.5, max_slope_degrees=35, max_step_height=0.25);
}

module env_pine(seed=0, h=6) {
    world_material([0.30,0.22,0.15],roughness=0.96)
        cylinder(h=h*0.65,r1=h*0.065,r2=h*0.035,$fn=7);
    for(i=[0:2])
        world_material([0.14+i*0.035,0.30+i*0.045,0.22+i*0.025],roughness=0.9)
        translate([0,0,h*(0.25+i*0.19)])
        rotate([0,0,lay_randr(seed,i,0,45)])
        cylinder(h=h*(0.55-i*0.08),r1=h*(0.30-i*0.055),r2=0,$fn=7);
}

module env_rock(seed=0, r=2) {
    world_material([0.42,0.46,0.43],roughness=0.96)
    rotate([0,0,lay_randr(seed,0,0,360)])
    scale([r,r*0.72,r*0.9]) translate([0,0,0.5]) sphere(r=1,$fn=7);
}

// A compact fixed garden canopy; do not duplicate a GDD-assigned Module.
module env_pergola(width=8,depth=4,height=4) {
    world_material([0.85,0.82,0.70],roughness=0.82) {
        for(x=[-width/2,width/2], y=[-depth/2,depth/2])
            translate([x,y,0]) cylinder(h=height,r=0.20,$fn=8);
        for(y=[-depth/2,depth/2])
            translate([-width/2-0.4,y-0.14,height-0.25]) cube([width+0.8,0.28,0.35]);
        for(x=[-width/2:0.8:width/2])
            translate([x-0.10,-depth/2-0.45,height]) cube([0.2,depth+0.9,0.18]);
    }
}
