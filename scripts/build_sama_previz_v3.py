"""
Blender 5.2 LTS 3D White-Model Pre-Viz (v3 — Director's Cut: Hard-Cut 3-Shot Cinema Montage)
Target Screen: 先马 ZW360 Ultra 6.8" Curved OLED (Native 2320 x 1080, 2.15:1)

Implements ALL user directorial notes:
  1. Sheathed Odachi repositioned to Heroine's RIGHT HIP/WAIST:
     - Scabbard extending BACKWARD along her right hip/ledge, Hilt + circular gold halo ring IN FRONT,
       resting slightly diagonally across her outer right thigh (natural ready-to-draw posture!).
  2. Lively, higher-frequency, larger-amplitude ALTERNATING double-leg swing (playful daydreaming bounce!).
  3. Hard-Cut 3-Shot Cinema Rhythm (12.0s @ 24fps = 288 frames, background blurred throughout with f/1.0–1.2 telephoto DOF!):
     - Shot 1 (0.0s–3.5s,  f=1..84)   : Oblique (~32 deg) Full-Leg Close-Up (whole legs + loafers + right-hip hilt-forward odachi + brisk alternating leg swing)
     - [HARD CUT]
     - Shot 2 (3.5s–7.5s,  f=85..180) : Telephoto Full-Body Medium Shot (head-to-loafers right safe plane, gazing afar daydreaming, lively leg swing, creamy blurred wasteland)
     - [HARD CUT]
     - Shot 3 (7.5s–12.0s, f=181..288): Ultra-Close Side-Profile Daydreaming (7.5s–9.7s) -> Sudden Turn to Camera + Sweet Smile (9.7s–12.0s)!
"""

import json
import math
import sys
import time
from pathlib import Path

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "previz"
FRAMES_DIR = OUT_DIR / "frames_24fps"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

W_FULL, H_FULL = 2320, 1080
W_ANIM, H_ANIM = 960, 448
TOTAL_FRAMES = 288  # 12.0s @ 24fps


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    return scene


def configure_render_engine(scene, samples=36):
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons.get('cycles')
    used_gpu = False
    if prefs:
        cprefs = prefs.preferences
        for dev_type in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
            try:
                cprefs.compute_device_type = dev_type
                cprefs.get_devices()
                devs = [d for d in cprefs.devices if d.type == dev_type]
                if devs:
                    for d in cprefs.devices:
                        d.use = (d.type == dev_type)
                    scene.cycles.device = 'GPU'
                    used_gpu = True
                    print(f"[RENDER] Cycles GPU enabled: {dev_type} ({[d.name for d in devs]})")
                    break
            except Exception:
                continue
    if not used_gpu:
        scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2

    scene.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in scene.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    try:
        scene.view_settings.look = 'AgX - Low Contrast'
    except Exception:
        pass
    scene.view_settings.exposure = 0.18
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'


def make_mat(name, color, roughness=0.55, metallic=0.0, coat=0.0, subsurface=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat
        if "Subsurface Weight" in bsdf.inputs and subsurface > 0:
            bsdf.inputs["Subsurface Weight"].default_value = subsurface
        if emission is not None and emission_strength > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def set_smooth(obj):
    if obj.type != 'MESH':
        return
    if hasattr(obj.data, "polygons"):
        obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.data.update()


def add_subsurf(obj, level=1):
    mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    mod.levels = level
    mod.render_levels = level


def create_loft_mesh(name, rings, cap_start=True, cap_end=True, mat=None, parent=None, smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vert_rings = []
    n_segs = 22
    for center, rx, ry, rot in rings:
        c = Vector(center)
        rmat = rot.to_matrix() if rot is not None else Matrix.Identity(3)
        ring_v = []
        for i in range(n_segs):
            ang = 2.0 * math.pi * i / n_segs
            local = Vector((rx * math.cos(ang), ry * math.sin(ang), 0.0))
            ring_v.append(bm.verts.new(c + rmat @ local))
        vert_rings.append(ring_v)

    bm.verts.ensure_lookup_table()
    for r in range(len(vert_rings) - 1):
        r0, r1 = vert_rings[r], vert_rings[r + 1]
        for i in range(n_segs):
            j = (i + 1) % n_segs
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cap_start:
        c0 = bm.verts.new(Vector(rings[0][0]))
        for i in range(n_segs):
            j = (i + 1) % n_segs
            bm.faces.new((c0, vert_rings[0][j], vert_rings[0][i]))
    if cap_end:
        c1 = bm.verts.new(Vector(rings[-1][0]))
        for i in range(n_segs):
            j = (i + 1) % n_segs
            bm.faces.new((c1, vert_rings[-1][i], vert_rings[-1][j]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    if smooth:
        set_smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def create_box(name, loc, scale, rot=(0, 0, 0), bevel=0.015, mat=None, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    if mat:
        obj.data.materials.append(mat)
    set_smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def create_cyl(name, loc, radius, depth, rot=(0, 0, 0), verts=24, mat=None, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    set_smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def create_empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    emp = bpy.data.objects.new(name, None)
    emp.location = Vector(loc)
    emp.rotation_euler = Euler(rot, 'XYZ')
    bpy.context.collection.objects.link(emp)
    if parent:
        emp.parent = parent
    return emp


# ==============================================================================
# ENVIRONMENT: LIGHT-TONED SUN-BLEACHED WASTELAND (PUSHED DEEP FOR CREAMY BOKEH!)
# ==============================================================================
def build_wasteland_environment(mats):
    env_root = create_empty("Env_Wasteland_Root")

    bpy.ops.mesh.primitive_plane_add(size=90.0, location=(0.0, 18.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "Wasteland_Ground"
    ground.data.materials.append(mats["ground"])
    ground.parent = env_root

    # Elevated weathered concrete ruin seat ledge (higher seat z=0.66m so BOTH swinging legs dangle freely with ample room!)
    create_box("Ledge_MainSlab", (0.28, 0.42, 0.33), (2.25, 0.84, 0.66), bevel=0.025, mat=mats["concrete_light"], parent=env_root)
    create_box("Ledge_LeftStep", (-1.15, 0.65, 0.18), (0.95, 0.90, 0.36), rot=(0.0, 0.04, 0.08), bevel=0.02, mat=mats["concrete_mid"], parent=env_root)
    create_box("Ledge_RightRubble", (1.65, 0.95, 0.25), (0.85, 0.65, 0.50), rot=(0.04, -0.08, -0.15), bevel=0.02, mat=mats["concrete_mid"], parent=env_root)

    # Collapsed sunlit pale overpass viaduct pushed deeper (y = 8..28m) so f/1.0–1.2 turns background into rich dreamy bokeh in ALL 3 SHOTS!
    viaduct_specs = [
        ("Viaduct_Pillar_1", -3.0,  9.5, 2.4, 0.75, 0.75, 5.0, 0.0,  0.07,  0.14),
        ("Viaduct_Pillar_2", -6.2, 12.8, 2.8, 0.85, 0.85, 5.8, 0.02, -0.04, 0.14),
        ("Viaduct_Pillar_3", -9.8, 16.5, 3.2, 0.95, 0.95, 6.6, -0.02, 0.03, 0.14),
        ("Viaduct_Deck_1",   -4.6, 11.2, 4.7, 4.4, 1.50, 0.48, 0.04, -0.09, -0.68),
        ("Viaduct_Deck_2",   -8.0, 14.6, 5.5, 5.0, 1.60, 0.50, -0.02, 0.03, -0.68),
        ("Viaduct_Ramp_Fall", -1.6, 8.2, 2.0, 3.4, 1.25, 0.38, 0.10, 0.38, -0.58),
        ("Far_Arch_PostL",   -0.8, 18.0, 3.6, 0.95, 0.95, 7.6, 0.0, 0.04, 0.08),
        ("Far_Arch_PostR",    3.2, 18.5, 4.0, 1.00, 1.00, 8.4, 0.0, -0.03, 0.08),
        ("Far_Arch_Beam",     1.2, 18.2, 7.2, 5.2,  1.05, 0.72, 0.0, 0.05, 0.08),
        ("Far_Tower_L",      -9.5, 25.0, 5.8, 2.6,  2.4, 12.0, 0.0, 0.05, 0.24),
        ("Far_Tower_R",       6.8, 24.0, 5.2, 2.4,  2.2, 10.6, 0.0, -0.06, -0.22),
    ]
    for nm, x, y, z, sx, sy, sz, rx, ry, rz in viaduct_specs:
        create_box(nm, (x, y, z), (sx, sy, sz), rot=(rx, ry, rz), bevel=0.05, mat=mats["ruin_far"], parent=env_root)

    # Sparse bleached grass blades on concrete cracks
    grass_blades = []
    for ci, (gx, gy, gz, count) in enumerate([(-0.85, 0.14, 0.36, 7), (-0.65, 0.08, 0.66, 5), (1.12, 0.12, 0.66, 6)]):
        for bi in range(count):
            ang = bi * 1.15 + ci * 0.7
            h = 0.22 + 0.14 * ((bi * 37) % 10) / 10.0
            lean = 0.16 + 0.10 * math.sin(ang)
            blade = create_loft_mesh(
                f"Grass_{ci}_{bi}",
                [
                    ((0, 0, 0.0),          0.008, 0.003, None),
                    ((lean*0.3, 0, h*0.4), 0.006, 0.002, None),
                    ((lean*0.8, 0, h*0.8), 0.003, 0.001, None),
                    ((lean*1.2, 0, h),     0.001, 0.001, None),
                ],
                cap_start=False, cap_end=True, mat=mats["grass"], parent=env_root
            )
            blade.location = Vector((gx + 0.08 * math.cos(ang), gy + 0.06 * math.sin(ang), gz))
            blade.rotation_euler = Euler((0.0, 0.0, ang * 0.5), 'XYZ')
            grass_blades.append((blade, ang))

    # Multi-depth luminous dandelion/crystal bokeh particles
    particles = []
    p_defs = [
        (-0.95, -1.60, 0.98, 0.017, 1.0),
        (-0.42, -1.45, 0.48, 0.019, 1.2),
        ( 0.78, -1.50, 1.28, 0.015, 0.9),
        ( 0.14, -1.35, 0.88, 0.014, 1.1),
        (-0.62, -1.20, 1.42, 0.016, 0.8),
        (-0.72, -0.35, 1.25, 0.010, 0.7),
        (-0.22, -0.45, 0.54, 0.009, 0.8),
        ( 0.72, -0.25, 1.45, 0.010, 0.6),
        ( 0.08, -0.52, 1.06, 0.008, 0.9),
        (-1.10,  0.15, 0.95, 0.011, 0.7),
        (-2.40,  3.50, 1.95, 0.028, 0.5),
        (-1.20,  4.00, 1.50, 0.025, 0.6),
        ( 0.45,  3.20, 1.85, 0.026, 0.55),
        (-3.60,  5.50, 2.35, 0.032, 0.45),
    ]
    for idx, (px, py, pz, rad, spd) in enumerate(p_defs):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rad, location=(px, py, pz))
        po = bpy.context.active_object
        po.name = f"Particle_{idx:02d}"
        po.data.materials.append(mats["particle_gold"] if idx % 3 == 0 else mats["particle_white"])
        po.parent = env_root
        particles.append((po, Vector((px, py, pz)), spd, idx))

    return env_root, grass_blades, particles


# ==============================================================================
# BUILD HEROINE + RIGHT-HIP READY-TO-DRAW SHEATHED ODACHI (刀鞘在后、刀把在前、略斜搭右腿)
# ==============================================================================
def build_heroine_and_sword(mats):
    # Seated atop z = 0.66m concrete slab, turned ~12 deg left so right hip & legs sit naturally!
    root = create_empty("Heroine_Root", loc=(0.34, 0.16, 0.66), rot=(0.0, 0.0, math.radians(-12.0)))
    pelvis = create_empty("Heroine_Pelvis", loc=(0.0, 0.0, 0.09), parent=root)

    create_loft_mesh("Body_Hips", [
        ((0.0, 0.0, -0.06), 0.145, 0.115, None),
        ((0.0, 0.0,  0.00), 0.152, 0.122, None),
        ((0.0, 0.0,  0.08), 0.128, 0.102, None),
    ], mat=mats["skirt_dark"], parent=pelvis)

    # Dark-Grey Pleated Micro-Skirt (18 radial pleats)
    skirt_pivot = create_empty("Skirt_Pivot", loc=(0.0, 0.0, 0.10), rot=(math.radians(16.0), 0.0, 0.0), parent=pelvis)
    for i in range(18):
        ang = 2.0 * math.pi * i / 18
        front_lift = 0.045 * max(0.0, -math.sin(ang))
        create_box(
            f"Skirt_Pleat_{i:02d}",
            loc=(0.158 * math.cos(ang), 0.135 * math.sin(ang) - front_lift * 0.4, -0.065 + front_lift * 0.35),
            scale=(0.056, 0.016, 0.195),
            rot=(math.radians(-18.0 * math.sin(ang) - front_lift * 160), math.radians(16.0 * math.cos(ang)), ang + math.pi/2),
            bevel=0.003, mat=mats["skirt_dark"], parent=skirt_pivot
        )

    # Torso & Cozy Oversized Cream Rib-Knit Sweater
    torso_pivot = create_empty("Heroine_Torso_Pivot", loc=(0.0, 0.02, 0.11), rot=(math.radians(-6.0), math.radians(-2.0), math.radians(4.0)), parent=pelvis)
    sweater_body = create_loft_mesh("Sweater_Torso", [
        ((0.0,  0.00, 0.00), 0.140, 0.112, None),
        ((0.0,  0.00, 0.06), 0.122, 0.098, None),
        ((0.0, -0.01, 0.14), 0.132, 0.105, None),
        ((0.0, -0.025, 0.24), 0.146, 0.126, None),
        ((0.0, -0.01, 0.34), 0.156, 0.108, None),
        ((0.0,  0.00, 0.40), 0.092, 0.078, None),
    ], mat=mats["sweater_cream"], parent=torso_pivot)
    add_subsurf(sweater_body, 1)

    for s_nm, sx in (("ShoulderCap_L", 0.145), ("ShoulderCap_R", -0.145)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.064, location=(sx, -0.005, 0.335))
        sc = bpy.context.active_object
        sc.name = s_nm
        sc.data.materials.append(mats["sweater_cream"])
        set_smooth(sc)
        sc.parent = torso_pivot

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.068, minor_radius=0.018,
        location=(0.0, -0.005, 0.405), rotation=(math.radians(10.0), 0.0, 0.0)
    )
    collar = bpy.context.active_object
    collar.name = "Sweater_Collar"
    collar.data.materials.append(mats["sweater_cream"])
    set_smooth(collar)
    collar.parent = torso_pivot

    # Neck & Expressive Anime-CG Head (with animated turn-to-camera + sweet smile!)
    create_loft_mesh("Heroine_Neck", [
        ((0.0, 0.0, 0.40), 0.044, 0.044, None),
        ((0.0, -0.008, 0.49), 0.039, 0.041, None),
    ], mat=mats["skin_porcelain"], parent=torso_pivot)

    head_pivot = create_empty("Heroine_Head_Pivot", loc=(0.0, -0.012, 0.51), parent=torso_pivot)
    head_mesh = create_loft_mesh("Heroine_Head", [
        ((0.0, -0.015, 0.00), 0.020, 0.022, None),
        ((0.0, -0.008, 0.03), 0.056, 0.066, None),
        ((0.0,  0.000, 0.08), 0.082, 0.092, None),
        ((0.0,  0.006, 0.14), 0.086, 0.098, None),
        ((0.0,  0.010, 0.195), 0.072, 0.082, None),
        ((0.0,  0.010, 0.220), 0.030, 0.034, None),
    ], mat=mats["skin_porcelain"], parent=head_pivot)
    add_subsurf(head_mesh, 1)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.010, location=(0.0, -0.089, 0.075))
    nose = bpy.context.active_object
    nose.name = "Face_Nose"
    nose.scale = (0.58, 1.25, 0.90)
    nose.data.materials.append(mats["skin_porcelain"])
    set_smooth(nose)
    nose.parent = head_pivot

    # Neutral daydream lips + separate curved sweet-smile arc (animated cross-scale in Shot 3!)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.011, location=(0.0, -0.079, 0.044))
    lips_neutral = bpy.context.active_object
    lips_neutral.name = "Face_Lips_Neutral"
    lips_neutral.scale = (1.15, 0.40, 0.32)
    lips_neutral.data.materials.append(mats["lip_blush"])
    set_smooth(lips_neutral)
    lips_neutral.parent = head_pivot

    # Curved happy smile crescent (built from torus segment rotated upward like a sweet U smile!)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.022, minor_radius=0.0042,
        location=(0.0, -0.078, 0.058), rotation=(math.radians(90.0), 0.0, 0.0)
    )
    smile_arc = bpy.context.active_object
    smile_arc.name = "Face_Smile_Arc"
    # Keep only the bottom smiling arc (z < 0.054 in local head coords -> local torus y < -0.004)
    bpy.ops.object.mode_set(mode='EDIT')
    bm_s = bmesh.from_edit_mesh(smile_arc.data)
    for v in list(bm_s.verts):
        if v.co.y > -0.008:
            bm_s.verts.remove(v)
    bmesh.update_edit_mesh(smile_arc.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    smile_arc.data.materials.append(mats["lip_smile"])
    set_smooth(smile_arc)
    smile_arc.parent = head_pivot

    # Rosy cheek blushes (intensify subtly on smile!)
    cheeks = []
    for side, sx in (("L", -0.048), ("R", 0.048)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.017, location=(sx, -0.072, 0.070))
        ch = bpy.context.active_object
        ch.name = f"Face_Cheek_{side}"
        ch.scale = (1.2, 0.35, 0.65)
        ch.data.materials.append(mats["cheek_blush"])
        set_smooth(ch)
        ch.parent = head_pivot
        cheeks.append(ch)

    eyes = []
    for side, sx in (("L", -0.032), ("R", 0.032)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(sx, -0.082, 0.098))
        eye = bpy.context.active_object
        eye.name = f"Face_Eye_{side}"
        eye.scale = (1.18, 0.42, 0.95)
        eye.rotation_euler = Euler((0.0, 0.0, math.radians(-14.0 if sx < 0 else 14.0)), 'XYZ')
        eye.data.materials.append(mats["eye_iris"])
        set_smooth(eye)
        eye.parent = head_pivot
        eyes.append(eye)
        create_box(f"Face_Brow_{side}", (sx, -0.084, 0.123), (0.026, 0.005, 0.004), rot=(0, 0, math.radians(-10 if sx < 0 else 10)), bevel=0.001, mat=mats["eye_iris"], parent=head_pivot)

    # Rainbow-Silver Inverted Blunt Bob Hair
    hair_pivot = create_empty("Hair_Pivot", loc=(0.0, 0.008, 0.12), parent=head_pivot)
    bob_shell = create_loft_mesh("Hair_Bob_Crown", [
        ((0.0,  0.020, -0.145), 0.114, 0.098, None),
        ((0.0,  0.015, -0.060), 0.106, 0.106, None),
        ((0.0,  0.008,  0.030), 0.098, 0.110, None),
        ((0.0,  0.006,  0.095), 0.078, 0.088, None),
        ((0.0,  0.006,  0.118), 0.028, 0.032, None),
    ], mat=mats["hair_silver"], parent=hair_pivot)
    bob_shell.location = Vector((0.0, 0.022, 0.0))
    add_subsurf(bob_shell, 1)

    hair_locks = []
    for nm, lx, ly, lz, lw, ll, rx, ry, rz, amp in [
        ("Hair_Bang_C1",  0.000, -0.092,  0.058, 0.014, 0.082,  0.12,  0.00,  0.00, 0.05),
        ("Hair_Bang_L1", -0.034, -0.086,  0.055, 0.016, 0.086,  0.14,  0.12, -0.15, 0.06),
        ("Hair_Bang_R1",  0.034, -0.086,  0.055, 0.016, 0.086,  0.14, -0.12,  0.15, 0.06),
        ("Hair_Side_L1", -0.084, -0.045,  0.032, 0.024, 0.185,  0.08,  0.16, -0.25, 0.14),
        ("Hair_Side_L2", -0.094,  0.010,  0.025, 0.028, 0.205,  0.05,  0.22, -0.10, 0.18),
        ("Hair_Side_R1",  0.084, -0.045,  0.032, 0.024, 0.185,  0.08, -0.18,  0.25, 0.16),
        ("Hair_Side_R2",  0.098,  0.012,  0.022, 0.030, 0.215,  0.06, -0.28,  0.12, 0.22),
        ("Hair_Wind_R3",  0.105,  0.045, -0.010, 0.022, 0.220,  0.10, -0.45,  0.18, 0.28),
        ("Hair_Wind_L3", -0.096,  0.055, -0.010, 0.024, 0.195,  0.05,  0.20, -0.10, 0.15),
    ]:
        lp = create_empty(f"{nm}_Piv", loc=(lx, ly, lz), rot=(rx, ry, rz), parent=hair_pivot)
        create_loft_mesh(nm, [
            ((0.0, 0.0,  0.00),      lw*0.9, lw*0.35, None),
            ((0.0, -0.008, -ll*0.45), lw*1.0, lw*0.32, None),
            ((0.0, -0.004, -ll*0.82), lw*0.65, lw*0.22, None),
            ((0.0,  0.006, -ll),      lw*0.18, lw*0.10, None),
        ], mat=mats["hair_silver"], parent=lp)
        hair_locks.append((lp, Euler((rx, ry, rz), 'XYZ'), amp))

    # ==========================================================================
    # LONG SCULPTED 180D PEARLESCENT WHITE PANTYHOSE LEGS + PLAYFUL LOAFERS!
    # ==========================================================================
    def build_loafer(name, parent, loc, rot):
        shoe_piv = create_empty(f"{name}_Piv", loc=loc, rot=rot, parent=parent)
        create_loft_mesh(f"{name}_Body", [
            ((0.0,  0.045,  0.00), 0.028, 0.026, Euler((math.radians(90), 0, 0))),
            ((0.0,  0.000, -0.004), 0.032, 0.028, Euler((math.radians(90), 0, 0))),
            ((0.0, -0.075, -0.008), 0.034, 0.022, Euler((math.radians(90), 0, 0))),
            ((0.0, -0.138, -0.010), 0.024, 0.013, Euler((math.radians(90), 0, 0))),
        ], mat=mats["loafer_brown"], parent=shoe_piv)
        create_box(f"{name}_Heel", (0.0, 0.028, -0.030), (0.048, 0.052, 0.024), bevel=0.004, mat=mats["loafer_brown"], parent=shoe_piv)
        create_box(f"{name}_Strap", (0.0, -0.045, 0.014), (0.068, 0.024, 0.008), bevel=0.002, mat=mats["loafer_brown"], parent=shoe_piv)
        return shoe_piv

    # Right Leg (-X in heroine local space — her RIGHT side!)
    hip_r = create_empty("Leg_R_Hip", loc=(-0.078, -0.02, 0.01), rot=(math.radians(-6.0), 0.0, math.radians(-6.0)), parent=pelvis)
    create_loft_mesh("Leg_R_Thigh", [
        ((0.0,  0.00,  0.00), 0.076, 0.078, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.15, -0.01), 0.072, 0.074, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.31, -0.03), 0.058, 0.060, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.42, -0.04), 0.046, 0.048, Euler((math.radians(90), 0, 0))),
    ], mat=mats["pantyhose_white"], parent=hip_r)
    knee_r = create_empty("Leg_R_Knee", loc=(0.0, -0.42, -0.04), parent=hip_r)
    create_loft_mesh("Leg_R_Calf", [
        ((0.0, 0.0,  0.00), 0.045, 0.047, None),
        ((0.0, 0.008, -0.15), 0.049, 0.053, None),
        ((0.0, 0.004, -0.31), 0.035, 0.038, None),
        ((0.0, 0.000, -0.44), 0.027, 0.030, None),
    ], mat=mats["pantyhose_white"], parent=knee_r)
    shoe_r = build_loafer("Loafer_R", knee_r, loc=(0.0, -0.015, -0.465), rot=(math.radians(-18.0), 0.0, 0.0))

    # Left Leg (+X in heroine local space — her LEFT side!)
    hip_l = create_empty("Leg_L_Hip", loc=(0.080, -0.02, 0.01), rot=(math.radians(-6.0), 0.0, math.radians(4.0)), parent=pelvis)
    create_loft_mesh("Leg_L_Thigh", [
        ((0.0,  0.00,  0.00), 0.076, 0.078, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.15, -0.01), 0.072, 0.074, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.31, -0.03), 0.058, 0.060, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.42, -0.04), 0.046, 0.048, Euler((math.radians(90), 0, 0))),
    ], mat=mats["pantyhose_white"], parent=hip_l)
    knee_l = create_empty("Leg_L_Knee", loc=(0.0, -0.42, -0.04), parent=hip_l)
    create_loft_mesh("Leg_L_Calf", [
        ((0.0, 0.0,  0.00), 0.045, 0.047, None),
        ((0.0, 0.008, -0.15), 0.049, 0.053, None),
        ((0.0, 0.004, -0.31), 0.035, 0.038, None),
        ((0.0, 0.000, -0.44), 0.027, 0.030, None),
    ], mat=mats["pantyhose_white"], parent=knee_l)
    shoe_l = build_loafer("Loafer_L", knee_l, loc=(0.0, -0.015, -0.465), rot=(math.radians(-18.0), 0.0, 0.0))

    for kn_nm, kn_piv in (("KneeCap_R", knee_r), ("KneeCap_L", knee_l)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.047, location=(0.0, 0.0, 0.0))
        kc = bpy.context.active_object
        kc.name = kn_nm
        kc.data.materials.append(mats["pantyhose_white"])
        set_smooth(kc)
        kc.parent = kn_piv

    # ==========================================================================
    # SHEATHED CYBER-ODACHI AT RIGHT HIP/WAIST:
    #   SCABBARD IN BACK -> RESTING SLIGHTLY DIAGONALLY ACROSS OUTER RIGHT THIGH -> HILT IN FRONT (READY TO DRAW!)
    # ==========================================================================
    # In pelvis local coords:
    #   Heroine's right side is -X; backward (behind hip onto concrete ledge) is +Y; forward (over outer right thigh) is -Y!
    p_tip_local  = Vector((-0.26,  0.64, -0.05))  # Scabbard tail resting cleanly back on the concrete slab behind her right hip!
    p_hilt_local = Vector((-0.09, -0.52,  0.14))  # Ceramic-white hilt + circular gold ring in FRONT, resting slightly diagonally across her right thigh!
    axis = p_hilt_local - p_tip_local             # Length ~ 1.19m!
    rot_q = Vector((0, 0, 1)).rotation_difference(axis.normalized())
    sword_root = create_empty("Odachi_RightHip_ReadyToDraw", loc=p_tip_local, rot=rot_q.to_euler('XYZ'), parent=pelvis)

    # Scabbard (z = 0.00 .. 0.88m along sword axis, extending backward!)
    create_box("Odachi_Scabbard", (0.0, 0.0, 0.44), (0.022, 0.044, 0.88), bevel=0.005, mat=mats["ceramic_white"], parent=sword_root)
    create_box("Odachi_TipCap",   (0.0, 0.0, 0.03), (0.025, 0.048, 0.075), bevel=0.004, mat=mats["champagne_gold"], parent=sword_root)
    create_box("Odachi_SideClip", (-0.015, 0.0, 0.72), (0.012, 0.016, 0.16), bevel=0.003, mat=mats["champagne_gold"], parent=sword_root)
    create_box("Odachi_GoldSeam", (-0.012, 0.0, 0.44), (0.004, 0.008, 0.70), bevel=0.001, mat=mats["champagne_gold"], parent=sword_root)

    # Circular Champagne-Gold Halo Ring Collar (Tsuba) right near her front-outer right thigh!
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.046, minor_radius=0.0075,
        location=(0.0, 0.0, 0.885), rotation=(0.0, 0.0, 0.0)
    )
    halo_ring = bpy.context.active_object
    halo_ring.name = "Odachi_HaloRing"
    halo_ring.data.materials.append(mats["champagne_gold"])
    set_smooth(halo_ring)
    halo_ring.parent = sword_root

    # Slim Ceramic-White CNC Hilt IN FRONT (z = 0.89 .. 1.19m) + subtle warm gold breath!
    create_box("Odachi_Hilt_Shell", (0.0, 0.0, 1.04), (0.020, 0.034, 0.29), bevel=0.005, mat=mats["ceramic_white"], parent=sword_root)
    create_box("Odachi_Hilt_GoldBreath", (0.0, 0.0, 1.04), (0.022, 0.012, 0.23), bevel=0.002, mat=mats["hilt_glow"], parent=sword_root)
    create_cyl("Odachi_Pommel", (0.0, 0.0, 1.19), 0.016, 0.022, mat=mats["champagne_gold"], parent=sword_root)

    # ==========================================================================
    # ARMS:
    #   - LEFT HAND (+X): Planted FIRMLY & FLAT ON TOP of the concrete seat surface beside her left hip (supporting seated posture!)
    #   - RIGHT HAND (-X): Resting gently ON TOP of the ceramic-white SCABBARD behind the gold halo ring (NOT on the hilt!)
    # ==========================================================================
    def build_limb_seg(name, p0, p1, r0, r_mid, r1, mat, parent):
        vec = p1 - p0
        L = vec.length
        q = Vector((0, 0, -1)).rotation_difference(vec.normalized())
        piv = create_empty(f"{name}_Piv", loc=p0, rot=q.to_euler('XYZ'), parent=parent)
        create_loft_mesh(name, [
            ((0.0, 0.0,  0.00),     r0,    r0,    None),
            ((0.0, 0.0, -L * 0.50), r_mid, r_mid, None),
            ((0.0, 0.0, -L * 0.88), r_mid * 0.96, r_mid * 0.96, None),
            ((0.0, 0.0, -L),        r1,    r1,    None),
        ], mat=mat, parent=piv)
        return piv

    # Left Arm (+X): Propping palm FLAT on top of concrete slab (slab top = z=-0.09 in pelvis local coords!)
    p_sh_l   = Vector((0.155, -0.015,  0.445))
    p_elb_l  = Vector((0.255,  0.055,  0.195))
    p_hand_l = Vector((0.300,  0.035, -0.068))  # Wrist landing cleanly onto concrete surface z=-0.09!
    build_limb_seg("Arm_L_Upper", p_sh_l, p_elb_l, 0.055, 0.058, 0.054, mats["sweater_cream"], pelvis)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.054, location=p_elb_l)
    elb_l_cap = bpy.context.active_object
    elb_l_cap.name = "Arm_L_ElbowCap"
    elb_l_cap.data.materials.append(mats["sweater_cream"])
    set_smooth(elb_l_cap)
    elb_l_cap.parent = pelvis
    build_limb_seg("Arm_L_Forearm", p_elb_l, p_hand_l, 0.054, 0.060, 0.035, mats["sweater_cream"], pelvis)
    # Flat palm & fingers planted directly on top of the concrete slab (pointing gently outward-forward!)
    hand_l_piv = create_empty("Hand_L_OnLedge_Piv", loc=(0.300, 0.035, -0.078), rot=(0.0, 0.0, math.radians(32.0)), parent=pelvis)
    create_loft_mesh("Hand_L_FlatPalm", [
        ((0.0,  0.01,  0.004), 0.024, 0.013, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.035, 0.000), 0.032, 0.011, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.082,-0.004), 0.028, 0.008, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.108,-0.006), 0.018, 0.006, Euler((math.radians(90), 0, 0))),
    ], mat=mats["skin_porcelain"], parent=hand_l_piv)

    # Right Arm (-X): Exact analytical 2-bone placement so her right hand rests PHYSICALLY ON THE SCABBARD (behind the gold halo ring, NOT on the hilt!)
    # Sword axis in pelvis space: p_tip=(-0.26, 0.64, -0.05) -> p_hilt=(-0.09, -0.52, 0.14); gold halo ring at t=0.745 (-0.133, -0.224, 0.091)
    # Target palm contact point on TOP surface of SCABBARD body/side-clip at t=0.60 (cleanly behind halo ring, leaving hilt & ring 100% exposed in front!):
    p_sh_pelvis   = Vector((-0.155, -0.015, 0.445))  # Right shoulder in pelvis space
    p_elb_pelvis  = Vector((-0.255,  0.045, 0.245))  # Relaxed slightly-back elbow
    p_hand_pelvis = Vector((-0.158, -0.056, 0.094))  # Resting naturally ON TOP of ceramic-white SCABBARD behind gold halo ring!

    build_limb_seg("Arm_R_Upper", p_sh_pelvis, p_elb_pelvis, 0.055, 0.058, 0.055, mats["sweater_cream"], pelvis)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, location=p_elb_pelvis)
    elb_cap = bpy.context.active_object
    elb_cap.name = "Arm_R_ElbowCap"
    elb_cap.data.materials.append(mats["sweater_cream"])
    set_smooth(elb_cap)
    elb_cap.parent = pelvis

    arm_r_el = build_limb_seg("Arm_R_Forearm", p_elb_pelvis, p_hand_pelvis, 0.055, 0.062, 0.036, mats["sweater_cream"], pelvis)

    # Sculpted relaxed palm + fingers resting gently OVER the ceramic-white SCABBARD behind the halo ring!
    hand_r_piv = create_empty("Hand_R_OnScabbard_Piv", loc=p_hand_pelvis, rot=(math.radians(10.0), math.radians(-18.0), math.radians(-12.0)), parent=pelvis)
    create_loft_mesh("Hand_R_Palm", [
        ((0.0,  0.00,  0.00),  0.024, 0.015, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.04, -0.004), 0.030, 0.014, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.08, -0.014), 0.026, 0.010, Euler((math.radians(90), 0, 0))),
        ((0.0, -0.105,-0.026), 0.016, 0.007, Euler((math.radians(90), 0, 0))),  # Fingers resting softly over scabbard!
    ], mat=mats["skin_porcelain"], parent=hand_r_piv)

    return {
        "root": root,
        "pelvis": pelvis,
        "torso": torso_pivot,
        "head": head_pivot,
        "eyes": eyes,
        "lips_neutral": lips_neutral,
        "smile_arc": smile_arc,
        "cheeks": cheeks,
        "hair_locks": hair_locks,
        "knee_r": knee_r,
        "knee_l": knee_l,
        "shoe_r": shoe_r,
        "shoe_l": shoe_l,
        "arm_r_el": arm_r_el,
        "sword_root": sword_root,
    }


def build_cinema_lighting(scene):
    world = bpy.data.worlds.new("Wasteland_Cinema_World")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.44, 0.52, 0.60, 1.0)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (0.72, 0.80, 0.88, 1.0)
    bg.inputs["Strength"].default_value = 0.95
    nt.links.new(tex_coord.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # Strong Milky Backlight Sun + Rim Panel (BV1UHs56DEr2 look!)
    sun_data = bpy.data.lights.new("Sun_MilkyBacklight", type='SUN')
    sun_data.energy = 5.8
    sun_data.color = (1.0, 0.96, 0.90)
    sun_data.angle = math.radians(3.5)
    sun_obj = bpy.data.objects.new("Sun_MilkyBacklight", sun_data)
    sun_obj.rotation_euler = Euler((math.radians(64.0), math.radians(-10.0), math.radians(156.0)), 'XYZ')
    bpy.context.collection.objects.link(sun_obj)

    rim_data = bpy.data.lights.new("Area_BacklightVeil", type='AREA')
    rim_data.shape = 'RECTANGLE'
    rim_data.size = 4.6
    rim_data.size_y = 2.8
    rim_data.energy = 720.0
    rim_data.color = (1.0, 0.97, 0.93)
    rim_obj = bpy.data.objects.new("Area_BacklightVeil", rim_data)
    rim_obj.location = Vector((-0.6, 4.0, 2.1))
    rim_obj.rotation_euler = Euler((math.radians(-78.0), 0.0, math.radians(168.0)), 'XYZ')
    bpy.context.collection.objects.link(rim_obj)

    # Soft Cool Ambient Fill on Front (low contrast shadowed cinema face)
    fill_data = bpy.data.lights.new("Area_CoolBounceFill", type='AREA')
    fill_data.shape = 'RECTANGLE'
    fill_data.size = 3.8
    fill_data.size_y = 2.2
    fill_data.energy = 62.0
    fill_data.color = (0.78, 0.88, 1.0)
    fill_obj = bpy.data.objects.new("Area_CoolBounceFill", fill_data)
    fill_obj.location = Vector((1.6, -2.8, 1.45))
    fill_obj.rotation_euler = Euler((math.radians(78.0), 0.0, math.radians(24.0)), 'XYZ')
    bpy.context.collection.objects.link(fill_obj)

    hilt_light_data = bpy.data.lights.new("Point_HiltGoldBreath", type='POINT')
    hilt_light_data.energy = 5.0
    hilt_light_data.shadow_soft_size = 0.08
    hilt_light_data.color = (1.0, 0.78, 0.42)
    hilt_light = bpy.data.objects.new("Point_HiltGoldBreath", hilt_light_data)
    hilt_light.location = Vector((0.20, -0.32, 0.92))
    bpy.context.collection.objects.link(hilt_light)
    return hilt_light


def ease_in_out_quint(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 16.0 * t * t * t * t * t
    return 1.0 - pow(-2.0 * t + 2.0, 5) / 2.0


# ==============================================================================
# HARD-CUT 3-SHOT CHOREOGRAPHY + LIVELY LEG SWING + SIDE-PROFILE -> TURN & SMILE!
# ==============================================================================
def build_cameras_and_animate(scene, rig, grass_blades, particles, hilt_light, hilt_mat):
    cam_data = bpy.data.cameras.new("Cam_Master_HardCut")
    cam_data.sensor_width = 36.0
    cam_data.dof.use_dof = True
    cam_obj = bpy.data.objects.new("Cam_Master_HardCut", cam_data)
    bpy.context.collection.objects.link(cam_obj)

    target_emp = create_empty("Cam_Target_Focus", loc=(0.0, 0.0, 0.8))
    cam_data.dof.focus_object = target_emp
    scene.camera = cam_obj

    # 3 HARD-CUT TELEPHOTO SHALLOW-DOF CAMERAS (Background blurred throughout with f/1.0–1.2!):
    #   Heroine seated at ~(0.34, 0.16, 0.66):
    #     Head center : ~(0.34, 0.14, 1.42)
    #     Skirt/Hips  : ~(0.34, 0.14, 0.78)
    #     Legs/Loafers: ~(0.22..0.46, -0.58..-0.05, 0.12..0.72)
    #     Right-hip Forward Hilt: ~(0.24, -0.34, 0.88)
    shots = {
        # SHOT 1 (0.0s–3.5s, f=1..84): Oblique (~32 deg front-left) FULL-LEG CLOSE-UP!
        # Full framing from sweater hem + pleated skirt + COMPLETE right-hip forward hilt & gold halo ring down to BOTH swinging loafers!
        "S1": {
            "pos":    Vector((-1.42, -2.65, 0.62)),
            "target": Vector(( 0.00, -0.08, 0.56)),
            "lens":   56.0,
            "fstop":  1.3,
            "focus":  Vector(( 0.28, -0.26, 0.50)),
        },
        # SHOT 2 (3.5s–7.5s, f=85..180): Telephoto FULL-BODY MEDIUM SHOT (58mm f/1.2 creamy blurred wasteland!)
        # Head-to-loafers cleanly framed in right flat plane x=56%..86%, daydreaming gaze left-afar!
        "S2": {
            "pos":    Vector((-0.64, -5.25, 1.02)),
            "target": Vector((-0.26,  0.10, 0.85)),
            "lens":   58.0,
            "fstop":  1.2,
            "focus":  Vector(( 0.32, -0.05, 0.86)),
        },
        # SHOT 3 (7.5s–12.0s, f=181..288): ULTRA-CLOSE SIDE PROFILE (82mm f/1.5!) -> TURN TO CAMERA & SWEET SMILE!
        # Sharp focus locked cleanly on her eyes/nose while wasteland background melts into pure creamy bokeh!
        "S3": {
            "pos":    Vector(( 0.06, -1.66, 1.46)),
            "target": Vector(( 0.20,  0.14, 1.43)),
            "lens":   82.0,
            "fstop":  1.5,
            "focus":  Vector(( 0.31,  0.04, 1.44)),
        },
    }

    # Save 3 static inspectable cameras inside the .blend
    for k, cfg in shots.items():
        cd = bpy.data.cameras.new(f"Cam_{k}")
        cd.sensor_width = 36.0
        cd.lens = cfg["lens"]
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = cfg["fstop"]
        cd.dof.focus_distance = (cfg["focus"] - cfg["pos"]).length
        co = bpy.data.objects.new(f"Cam_{k}", cd)
        co.location = cfg["pos"]
        co.rotation_euler = (cfg["target"] - cfg["pos"]).to_track_quat('-Z', 'Y').to_euler('XYZ')
        bpy.context.collection.objects.link(co)

    hilt_bsdf = next((n for n in hilt_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

    for f in range(1, TOTAL_FRAMES + 1):
        u = (f - 1) / float(TOTAL_FRAMES - 1)
        phi = 2.0 * math.pi * u

        # 1. HARD CUT Camera Selection (subtle handheld breathing drift within each shot, crisp cut at f=85 & f=181!)
        if f <= 84:
            s_u = (f - 1) / 83.0
            cfg = shots["S1"]
            drift = Vector((0.04 * math.sin(math.pi * s_u), 0.03 * math.sin(math.pi * s_u), 0.01 * math.sin(math.pi * s_u)))
        elif f <= 180:
            s_u = (f - 85) / 95.0
            cfg = shots["S2"]
            drift = Vector((0.06 * math.sin(math.pi * s_u), 0.05 * math.sin(math.pi * s_u), 0.015 * math.sin(math.pi * s_u)))
        else:
            s_u = (f - 181) / 107.0
            cfg = shots["S3"]
            # Ultra-subtle gentle push-in toward her sweet smile!
            drift = Vector((0.015 * s_u, 0.06 * s_u, 0.005 * math.sin(math.pi * s_u)))

        pos = cfg["pos"] + drift
        cam_obj.location = pos
        cam_obj.rotation_euler = (cfg["target"] - pos).to_track_quat('-Z', 'Y').to_euler('XYZ')
        cam_data.lens = cfg["lens"]
        cam_data.dof.aperture_fstop = cfg["fstop"]
        target_emp.location = cfg["focus"]

        cam_obj.keyframe_insert("location", frame=f)
        cam_obj.keyframe_insert("rotation_euler", frame=f)
        cam_data.keyframe_insert("lens", frame=f)
        cam_data.dof.keyframe_insert("aperture_fstop", frame=f)
        target_emp.keyframe_insert("location", frame=f)

        # 2. LIVELY, HIGH-FREQUENCY, LARGE-AMPLITUDE ALTERNATING DOUBLE-LEG SWING!
        # 7 full alternating cycles across 12s (~1.17 kicks/sec), wide cute range [-26 deg .. +38 deg]!
        leg_phase = 7.0 * phi
        ang_r = math.radians(6.0 + 31.0 * math.sin(leg_phase) + 4.0 * math.sin(2.0 * leg_phase))
        ang_l = math.radians(6.0 + 31.0 * math.sin(leg_phase + math.pi) + 4.0 * math.sin(2.0 * (leg_phase + math.pi)))
        rig["knee_r"].rotation_euler = Euler((ang_r, math.radians(-3.0), 0.0), 'XYZ')
        rig["knee_l"].rotation_euler = Euler((ang_l, math.radians( 3.0), 0.0), 'XYZ')
        rig["knee_r"].keyframe_insert("rotation_euler", frame=f)
        rig["knee_l"].keyframe_insert("rotation_euler", frame=f)

        # Secondary playful ankle/loafer inertia follow-through!
        rig["shoe_r"].rotation_euler = Euler((math.radians(-18.0 - 11.0 * math.cos(leg_phase)), 0.0, 0.0), 'XYZ')
        rig["shoe_l"].rotation_euler = Euler((math.radians(-18.0 - 11.0 * math.cos(leg_phase + math.pi)), 0.0, 0.0), 'XYZ')
        rig["shoe_r"].keyframe_insert("rotation_euler", frame=f)
        rig["shoe_l"].keyframe_insert("rotation_euler", frame=f)

        # 3. EMOTIONAL GAZE ARC:
        #    Shot 1 & Shot 2 & Shot 3 First Half (f=1..232): GAZING LEFT-AFAR DAYDREAMING (head yaw = -46 deg!)
        #    Shot 3 Finale (f=233..288): SUDDENLY TURNS HEAD DIRECTLY TO CAMERA (yaw -> +18 deg) + SWEET SMILE!
        if f < 232:
            turn_k = 0.0
        elif f <= 258:
            turn_k = ease_in_out_quint((f - 232) / 26.0)
        else:
            turn_k = 1.0

        if f < 248:
            smile_k = 0.0
        elif f <= 264:
            smile_k = ease_in_out_quint((f - 248) / 16.0)
        else:
            smile_k = 1.0

        # Head yaw: -46 deg (daydreaming left-afar, giving clean ~62 deg profile in Shot 3!) -> +16 deg (facing straight into S3 camera!)
        head_yaw   = math.radians(-46.0 + 62.0 * turn_k + 1.8 * math.sin(2.0 * phi))
        head_pitch = math.radians(  3.0 -  6.5 * turn_k + 1.4 * math.sin(2.0 * phi))
        head_roll  = math.radians( -3.0 + 11.0 * smile_k + 1.2 * math.sin(phi))  # Cute playful tilt on smile!
        rig["head"].rotation_euler = Euler((head_pitch, head_roll, head_yaw), 'XYZ')
        rig["head"].keyframe_insert("rotation_euler", frame=f)

        # Subtle torso turn accompanying head turn + gentle breathing
        rig["torso"].rotation_euler = Euler((
            math.radians(-6.0 + 1.2 * math.sin(2.0 * phi)),
            math.radians(-2.0 + 2.0 * smile_k),
            math.radians(-6.0 + 14.0 * turn_k)
        ), 'XYZ')
        rig["torso"].keyframe_insert("rotation_euler", frame=f)

        # Sweet smile expression animation (visible smiling crescent + happy curved eyes + warm cheek blush!)
        rig["lips_neutral"].scale = (1.15 * (1.0 - smile_k) + 0.01, 0.40 * (1.0 - smile_k) + 0.01, 0.32 * (1.0 - smile_k) + 0.01)
        rig["lips_neutral"].keyframe_insert("scale", frame=f)
        rig["smile_arc"].scale = (0.01 + 1.05 * smile_k, 0.01 + 1.05 * smile_k, 0.01 + 1.05 * smile_k)
        rig["smile_arc"].keyframe_insert("scale", frame=f)
        for eye in rig["eyes"]:
            # Eyes gently narrow vertically into cute smiling crescents!
            eye.scale = (1.18 + 0.08 * smile_k, 0.42, 0.95 - 0.32 * smile_k)
            eye.keyframe_insert("scale", frame=f)

        # Brisk natural wind sweeping bob hair locks
        for li, (lp, base_rot, amp) in enumerate(rig["hair_locks"]):
            w_val = amp * (0.65 * math.sin(5.0 * phi + li * 0.55) + 0.35 * math.sin(9.0 * phi + li * 0.9))
            lp.rotation_euler = Euler((base_rot.x + w_val * 0.45, base_rot.y - abs(w_val) * 0.5 - w_val * 0.55, base_rot.z), 'XYZ')
            lp.keyframe_insert("rotation_euler", frame=f)

        for gb, gang in grass_blades:
            gb.rotation_euler = Euler((0.09 * math.sin(4.0 * phi + gang), 0.11 * math.cos(4.0 * phi + gang), gang * 0.5), 'XYZ')
            gb.keyframe_insert("rotation_euler", frame=f)

        for po, base_p, spd, idx in particles:
            po.location = base_p + Vector((
                0.18 * spd * math.sin(phi + idx * 0.7),
                0.06 * spd * math.cos(2.0 * phi + idx * 0.5),
                0.08 * spd * math.sin(2.0 * phi + idx * 1.1)
            ))
            po.keyframe_insert("location", frame=f)

        breath = 2.5 + 4.5 * (0.5 - 0.5 * math.cos(2.0 * phi))
        hilt_light.data.energy = breath
        hilt_light.data.keyframe_insert("energy", frame=f)
        if hilt_bsdf and "Emission Strength" in hilt_bsdf.inputs:
            hilt_bsdf.inputs["Emission Strength"].default_value = 2.0 + 2.5 * (0.5 - 0.5 * math.cos(2.0 * phi))
            hilt_bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

    return cam_obj


def main():
    scene = reset_scene()
    configure_render_engine(scene, samples=36)

    mats = {
        "ground":         make_mat("Mat_Ground_PaleDust",   (0.58, 0.62, 0.66), roughness=0.92),
        "concrete_light": make_mat("Mat_Concrete_Light",    (0.62, 0.65, 0.69), roughness=0.84),
        "concrete_mid":   make_mat("Mat_Concrete_Mid",      (0.50, 0.54, 0.59), roughness=0.86),
        "ruin_far":       make_mat("Mat_Ruin_Far",          (0.66, 0.71, 0.76), roughness=0.88),
        "grass":          make_mat("Mat_Grass_Bleached",    (0.68, 0.70, 0.64), roughness=0.78),
        "skin_porcelain": make_mat("Mat_Skin_Clay",         (0.94, 0.86, 0.83), roughness=0.45, subsurface=0.12),
        "lip_blush":      make_mat("Mat_Lip_Blush",         (0.84, 0.55, 0.57), roughness=0.35),
        "lip_smile":      make_mat("Mat_Lip_Smile",         (0.86, 0.44, 0.48), roughness=0.30),
        "cheek_blush":    make_mat("Mat_Cheek_Blush",       (0.95, 0.74, 0.76), roughness=0.65),
        "eye_iris":       make_mat("Mat_Eye_ClayLavender",  (0.30, 0.27, 0.46), roughness=0.15, coat=0.6),
        "hair_silver":    make_mat("Mat_Hair_SilverClay",   (0.95, 0.96, 1.00), roughness=0.26, coat=0.40),
        "sweater_cream":  make_mat("Mat_Sweater_CreamClay", (0.90, 0.87, 0.80), roughness=0.88),
        "skirt_dark":     make_mat("Mat_Skirt_DarkSlate",   (0.16, 0.18, 0.23), roughness=0.78),
        "pantyhose_white":make_mat("Mat_Pantyhose_180D",    (0.98, 0.98, 1.00), roughness=0.22, coat=0.50, subsurface=0.10),
        "loafer_brown":   make_mat("Mat_Loafer_DarkBrown",  (0.15, 0.09, 0.07), roughness=0.20, coat=0.75),
        "ceramic_white":  make_mat("Mat_Odachi_Ceramic",    (0.95, 0.96, 0.98), roughness=0.18, coat=0.55),
        "champagne_gold": make_mat("Mat_Odachi_Gold",       (0.88, 0.72, 0.40), roughness=0.22, metallic=0.88),
        "hilt_glow":      make_mat("Mat_Odachi_GoldBreath", (1.00, 0.84, 0.50), roughness=0.20, emission=(1.0, 0.80, 0.44), emission_strength=3.5),
        "particle_white": make_mat("Mat_Particle_White",    (1.00, 1.00, 1.00), roughness=0.10, emission=(0.95, 0.98, 1.0), emission_strength=3.5),
        "particle_gold":  make_mat("Mat_Particle_Gold",     (1.00, 0.90, 0.65), roughness=0.10, emission=(1.0, 0.86, 0.52), emission_strength=4.5),
    }

    env_root, grass_blades, particles = build_wasteland_environment(mats)
    rig = build_heroine_and_sword(mats)
    hilt_light = build_cinema_lighting(scene)
    cam_main = build_cameras_and_animate(scene, rig, grass_blades, particles, hilt_light, mats["hilt_glow"])

    blend_path = OUT_DIR / "screen2_sama_previz_v3.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[OK] Saved v3 Blender project -> {blend_path}")

    # Render 4 FULL-RES 2320x1080 Hero Stills (S1 Oblique Legs, S2 Fullbody Daydream, S3a Profile Daydream, S3b Turn & Sweet Smile!)
    scene.render.resolution_x = W_FULL
    scene.render.resolution_y = H_FULL
    scene.render.resolution_percentage = 100
    scene.cycles.samples = 40
    scene.camera = cam_main

    hero_renders = [
        (12,  OUT_DIR / "v3_shot1_legs_side.png"),         # Peak alternating swing!
        (114, OUT_DIR / "v3_shot2_fullbody_gaze.png"),     # Full body gazing afar + peak lively leg swing!
        (205, OUT_DIR / "v3_shot3a_profile_daydream.png"), # Ultra-close side profile daydreaming!
        (274, OUT_DIR / "v3_shot3b_turn_smile.png"),       # Sudden turn to camera + sweet smile!
    ]
    for fr, out_p in hero_renders:
        scene.frame_set(fr)
        scene.render.filepath = str(out_p)
        bpy.ops.render.render(write_still=True)
        print(f"[OK] Rendered hero frame {fr} -> {out_p.name}")

    if "--stills-only" in sys.argv:
        print("[DONE] v3 --stills-only complete!")
        return

    for old_f in FRAMES_DIR.glob("frame_*.png"):
        old_f.unlink()

    scene.render.resolution_x = W_ANIM
    scene.render.resolution_y = H_ANIM
    scene.cycles.samples = 10
    t0 = time.time()
    scene.frame_set(1)
    scene.render.filepath = str(FRAMES_DIR / "frame_0001.png")
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"[BENCH] 1 v3 anim frame ({W_ANIM}x{H_ANIM}, 10 spp) took {dt:.2f}s")

    # Use stride=2 (144 frames @ 12fps -> 24fps) so fast alternating leg swings & head-turn smile play super smoothly!
    stride = 2 if dt <= 1.5 else 3
    print(f"[INFO] Rendering full 12s v3 animation with stride={stride} ({TOTAL_FRAMES // stride} frames)...")
    for f in range(1 + stride, TOTAL_FRAMES + 1, stride):
        scene.frame_set(f)
        scene.render.filepath = str(FRAMES_DIR / f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)

    (OUT_DIR / "previz_meta.json").write_text(json.dumps({
        "stride": stride,
        "total_frames": TOTAL_FRAMES,
        "fps": 24,
        "anim_size": [W_ANIM, H_ANIM],
        "full_size": [W_FULL, H_FULL],
        "frame_sec_bench": round(dt, 3),
    }, indent=2), encoding="utf-8")
    print("[DONE] Blender 5.2 v3 pre-viz complete!")


if __name__ == "__main__":
    main()
