"""Export 7 character FBX models (C01-C05, C07, C09) to GLB, preserve rigs on C01/C02/C03/C05,
create marker-unrigged-badge.glb, render audit sheet, and write character_rig_audit.json.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
SRC_BASE = ROOT / "图片" / "模型"
OUT_CHAR_DIR = ROOT / "workspace" / "assets" / "models" / "characters"
OUT_MARKER = ROOT / "workspace" / "assets" / "models" / "marker-unrigged-badge.glb"
OUT_AUDIT = ROOT / "workspace" / "data" / "character_rig_audit.json"
OUT_SHEET = ROOT / "workspace" / "debug" / "characters-rig-audit-sheet.png"

CHARS = [
    {"id": "C01", "name": "阿木", "species": "眼镜棕熊", "role": "镇史年谱守护者", "folder": "C01-眼镜棕熊·阿木", "out": "C01-glasses-bear.glb", "targetH": 1.55},
    {"id": "C02", "name": "绵绵", "species": "垂耳白兔", "role": "杂交花圃引路人", "folder": "C02-垂耳白兔·绵绵", "out": "C02-lop-rabbit.glb", "targetH": 1.28},
    {"id": "C03", "name": "阿橘", "species": "面瘫橘猫", "role": "未寄信件收藏家", "folder": "C03-面瘫橘猫·阿橘", "out": "C03-deadpan-cat.glb", "targetH": 1.30},
    {"id": "C04", "name": "奶包", "species": "吃包柯基", "role": "微光夜市烘焙大厨", "folder": "C04-吃包柯基·奶包", "out": "C04-corgi-baker-unrigged.glb", "targetH": 1.28},
    {"id": "C05", "name": "墨羽", "species": "悬浮猫头鹰", "role": "昔日夜行星象信使", "folder": "C05-悬浮猫头鹰·墨羽", "out": "C05-floating-owl.glb", "targetH": 1.15},
    {"id": "C07", "name": "团团", "species": "水獭邮差", "role": "迷糊邮差与单车驿站长", "folder": "C07-迷糊邮差水獭·团团", "out": "C07-postman-otter-unrigged.glb", "targetH": 1.30},
    {"id": "C09", "name": "绒绒", "species": "社恐小羊", "role": "纸片画师与流行语策划", "folder": "C09-纸片画师小羊·绒绒", "out": "C09-artist-sheep-unrigged.glb", "targetH": 1.28},
]

MISSING_CHARS = [
    {"id": "C06", "name": "阿澈", "species": "草帽狐狸", "role": "退休的白昼号船长", "rigged": False, "status": "missing_3d_fbx", "note": "仅概念特写图 C06-strawhat-fox.png，缺少 3D FBX/GLB 源文件"},
    {"id": "C08", "name": "咔哒", "species": "木工小浣熊", "role": "直角强迫症首席木匠", "rigged": False, "status": "missing_3d_fbx", "note": "仅概念特写图 C08-carpenter-raccoon.png，缺少 3D FBX/GLB 源文件"},
]


def wire_fbm_textures(folder: Path):
    texs = list(folder.rglob("*.jpg")) + list(folder.rglob("*.png"))
    img = bpy.data.images.load(str(texs[0])) if texs else None
    for mat in bpy.data.materials:
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.84
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        # Ensure Base Color is linked to loaded texture if missing
        bc_in = bsdf.inputs.get("Base Color")
        if bc_in and not bc_in.is_linked and img is not None:
            tex_node = nt.nodes.new("ShaderNodeTexImage")
            tex_node.image = img
            nt.links.new(tex_node.outputs["Color"], bc_in)


def world_mesh_bounds(meshes):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def inspect_glb_json(glb_path: Path):
    b = glb_path.read_bytes()
    clen = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20 : 20 + clen].decode("utf-8"))
    has_joints = any(
        "JOINTS_0" in prim.get("attributes", {})
        for m in g.get("meshes", [])
        for prim in m.get("primitives", [])
    )
    return {
        "skins": len(g.get("skins", [])),
        "hasJointsAttr": has_joints,
        "images": len(g.get("images", [])),
        "nodes": len(g.get("nodes", [])),
    }


def export_one_char(cfg: dict) -> dict:
    folder = SRC_BASE / cfg["folder"]
    fbx_files = list(folder.glob("*.fbx"))
    if not fbx_files:
        raise FileNotFoundError(f"No FBX in {folder}")
    fbx = fbx_files[0]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
    wire_fbm_textures(folder)

    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    # Remove unused lights/cameras if any
    for o in list(bpy.data.objects):
        if o.type not in ("ARMATURE", "MESH", "EMPTY"):
            bpy.data.objects.remove(o, do_unlink=True)

    bones = sum(len(a.data.bones) for a in arms)
    vgroups = sum(len(m.vertex_groups) for m in meshes)
    skinned = any(any(mod.type == "ARMATURE" for mod in m.modifiers) for m in meshes)
    tris = sum(len(m.data.polygons) for m in meshes)
    is_rigged = bool(arms and bones > 0 and skinned)

    x0, x1, y0, y1, z0, z1 = world_mesh_bounds(meshes)
    h = max(1e-4, z1 - z0)
    sc = cfg["targetH"] / h
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)

    roots = [o for o in bpy.data.objects if o.parent is None]
    for r in roots:
        r.scale = (r.scale.x * sc, r.scale.y * sc, r.scale.z * sc)
    bpy.context.view_layer.update()

    # Re-measure after scaling cleanly
    x0, x1, y0, y1, z0, z1 = world_mesh_bounds(meshes)
    shift = Vector((-0.5 * (x0 + x1), -0.5 * (y0 + y1), -z0))
    for r in roots:
        r.location += shift
    bpy.context.view_layer.update()

    # For unrigged static meshes, bake transform cleanly into vertices so root node has identity transform
    if not is_rigged:
        bpy.ops.object.select_all(action="DESELECT")
        for m in meshes:
            m.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.context.view_layer.update()

    fx0, fx1, fy0, fy1, fz0, fz1 = world_mesh_bounds(meshes)

    OUT_CHAR_DIR.mkdir(parents=True, exist_ok=True)
    out_glb = OUT_CHAR_DIR / cfg["out"]
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(out_glb),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_skins=True,
        export_morph=False,
        export_animations=False,
        export_materials="EXPORT",
    )
    glb_info = inspect_glb_json(out_glb)
    # Unity coords from Blender: ux=-bx, uy=bz, uz=-by
    ux_w = round(fx1 - fx0, 3)
    uy_h = round(fz1 - fz0, 3)
    uz_d = round(fy1 - fy0, 3)

    rec = {
        "id": cfg["id"],
        "name": cfg["name"],
        "species": cfg["species"],
        "role": cfg["role"],
        "fbxPath": str(fbx.relative_to(ROOT)),
        "glbPath": str(out_glb.relative_to(ROOT)),
        "glbBytes": out_glb.stat().st_size,
        "rigged": is_rigged,
        "rigLabel": f"已绑骨 ({bones} 骨)" if is_rigged else "未绑骨 (静态网格)",
        "armatures": len(arms),
        "bones": bones,
        "skinned": skinned,
        "vertexGroups": vgroups,
        "tris": tris,
        "gltfSkins": glb_info["skins"],
        "hasJointsAttr": glb_info["hasJointsAttr"],
        "images": glb_info["images"],
        "unitySize": [ux_w, uy_h, uz_d],
        "blenderMinZ": round(fz0, 4),
    }
    print(f"[CHAR GLB] {cfg['id']} {cfg['name']:4s} | rigged={str(is_rigged):5s} | bones={bones:2d} | gltfSkins={glb_info['skins']} | size={rec['unitySize']} | minZ={fz0:+.4f} | {out_glb.stat().st_size//1024} KB")
    return rec


def build_unrigged_marker_glb():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    def make_mat(name, rgba, em=0.45):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = 0.55
        bsdf.inputs["Emission Color"].default_value = rgba
        bsdf.inputs["Emission Strength"].default_value = em
        return m

    mat_orange = make_mat("UnriggedOrange", (0.90, 0.57, 0.40, 1.0), 0.55)
    mat_cream = make_mat("UnriggedCream", (0.97, 0.96, 0.90, 1.0), 0.35)

    # 8-segment ground dashed warning ring at Y=0.02m (radius ~0.62m)
    for i in range(8):
        a0 = i * (2 * math.pi / 8)
        cx = 0.62 * math.cos(a0)
        cy = 0.62 * math.sin(a0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, 0.025))
        seg = bpy.context.object
        seg.scale = (0.08, 0.24, 0.022)
        seg.rotation_euler = (0.0, 0.0, a0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        seg.data.materials.append(mat_orange if i % 2 == 0 else mat_cream)

    # Floating overhead octahedron marker at Y_unity = 1.72m
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.11)
    mesh = bpy.data.meshes.new("OverheadDiamond")
    bm.to_mesh(mesh)
    bm.free()
    dia = bpy.data.objects.new("UnriggedDiamond", mesh)
    bpy.context.collection.objects.link(dia)
    dia.scale = (1.0, 1.0, 1.45)
    dia.location = (0.0, 0.0, 1.72)
    bpy.context.view_layer.objects.active = dia
    dia.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    dia.data.materials.append(mat_orange)

    OUT_MARKER.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(OUT_MARKER),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_materials="EXPORT",
    )
    print(f"[MARKER OK] {OUT_MARKER} ({OUT_MARKER.stat().st_size // 1024} KB)")


def render_audit_sheet(records):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 900

    world = bpy.data.worlds.new("AuditWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.93, 0.94, 0.90, 1.0)
    bg.inputs[1].default_value = 1.1

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 30))
    sun = bpy.context.object
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(38), math.radians(15), math.radians(-28))

    def mat(name, rgba):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Emission Color"].default_value = rgba
        b.inputs["Emission Strength"].default_value = 0.45
        return m

    mat_rig = mat("PadRigged", (0.54, 0.78, 0.54, 1.0))
    mat_unrig = mat("PadUnrigged", (0.90, 0.57, 0.40, 1.0))
    mat_red = mat("AxX", (0.92, 0.2, 0.2, 1.0))
    mat_blue = mat("AxZ", (0.2, 0.45, 0.92, 1.0))
    mat_yel = mat("AxNegZ", (0.95, 0.85, 0.15, 1.0))

    def u2b(ux, uy, uz):
        return Vector((-ux, -uz, uy))

    spacing = 2.6
    for idx, rec in enumerate(records):
        ux = (idx - (len(records) - 1) * 0.5) * spacing
        cb = u2b(ux, 0.0, 0.0)
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(ROOT / rec["glbPath"]))
        for o in bpy.context.scene.objects:
            if o not in before and o.parent is None:
                o.location += cb

        if not rec["rigged"]:
            before2 = set(bpy.context.scene.objects)
            bpy.ops.import_scene.gltf(filepath=str(OUT_MARKER))
            for o in bpy.context.scene.objects:
                if o not in before2 and o.parent is None:
                    o.location += cb

        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.92, depth=0.03, location=cb + Vector((0, 0, -0.02)))
        bpy.context.object.data.materials.append(mat_rig if rec["rigged"] else mat_unrig)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=cb + u2b(0.65, 0.03, 0.0))
        bx = bpy.context.object
        bx.dimensions = (0.7, 0.08, 0.04)
        bx.data.materials.append(mat_red)

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=cb + u2b(0.0, 0.03, 0.65))
        bz = bpy.context.object
        bz.dimensions = (0.08, 0.7, 0.04)
        bz.data.materials.append(mat_blue)

        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=cb + u2b(0.0, 0.06, -0.85))
        bpy.context.object.data.materials.append(mat_yel)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 17.5
    cam = bpy.data.objects.new("Cam", cam_d)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    tgt = u2b(0.0, 0.65, 0.0)
    eye = u2b(-10.0, 10.5, -12.0)
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
    OUT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(OUT_SHEET)
    bpy.ops.render.render(write_still=True)
    print(f"[SHEET OK] {OUT_SHEET}")


def main():
    records = [export_one_char(c) for c in CHARS]
    build_unrigged_marker_glb()
    render_audit_sheet(records)
    audit = {
        "summary": {
            "totalDesignResidents": 9,
            "fbxAvailable": len(records),
            "riggedCount": sum(1 for r in records if r["rigged"]),
            "unriggedCount": sum(1 for r in records if not r["rigged"]),
            "missing3dCount": len(MISSING_CHARS),
            "riggedIds": [r["id"] for r in records if r["rigged"]],
            "unriggedIds": [r["id"] for r in records if not r["rigged"]],
            "missingIds": [m["id"] for m in MISSING_CHARS],
        },
        "characters": records,
        "missing": MISSING_CHARS,
    }
    OUT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[AUDIT WRITTEN] {OUT_AUDIT}")


if __name__ == "__main__":
    main()
