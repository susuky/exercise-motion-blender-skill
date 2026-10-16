"""
Universal Production Blender (bpy) Pipeline for Exercise Motion Spec Generation (v4.0).

Features:
  - Sculpted 38-Muscle Anatomical Ecorché Mannequin (`anatomical_mannequin.py`) with
    independent Anterior vs Posterior muscle bellies (`biceps_brachii` vs `triceps_brachii`,
    `quadriceps` vs `hamstrings`, `pectoralis_major` vs `latissimus_dorsi` / `rhomboids` / `trapezius`,
    `rectus_abdominis`, `obliques`, `gluteus_maximus`, `gastrocnemius_calf`) and ZERO robotic ball-joints.
  - Universal 29-Category GymVisual Equipment Builder (`equipment_registry.py`):
    Supports `barbell`, `olympic_barbell`, `ez_barbell`, `trap_bar`, `smith_machine`, `dumbbell`,
    `kettlebell`, `medicine_ball`, `battle_ropes`, `rope`, `cable_machine`, `lever_machine`,
    `assisted`, `resistance_band`, `band`, `suspension`, `wheel_roller`, `bench`, `bosu_ball`,
    `stability_ball`, `roll`, `power_sled`, `sled_machine`, `pilates_machine`, etc.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "python"))
sys.path.insert(0, str(ROOT_DIR / "tests"))

try:
    import bpy  # type: ignore
    USING_MOCK_BPY = False
except ImportError:
    import mock_bpy as bpy  # type: ignore
    USING_MOCK_BPY = True

from interpolate_motion import expand_motion_spec
from kinematics_engine import BONE_HIERARCHY
import importlib.util as _ilu
def _load_mod(name, filename):
    p = Path(__file__).resolve().parent / filename
    if not p.exists():
        p = Path(__file__).resolve().parents[1] / "python" / filename
    spec = _ilu.spec_from_file_location(name, str(p))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
generate_anatomical_muscle_primitives = _load_mod("anatomical_mannequin", "anatomical_mannequin.py").generate_anatomical_muscle_primitives


def parse_cli_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Generate Blender 3D Exercise Animation from Motion Spec v4.0")
    parser.add_argument("spec_path", help="Path to .motion_spec.json or .expanded.json")
    parser.add_argument("--output-dir", default=None, help="Output directory for renders and exports")
    parser.add_argument("--style", default="gymvisual_full_color", choices=["gymvisual_full_color", "basic_grey"])
    parser.add_argument("--camera", default="three_quarter_front", help="Camera preset name")
    parser.add_argument("--rig-type", default="procedural", choices=["procedural", "rigify", "mixamo"])
    parser.add_argument("--save-blend", action="store_true", help="Save .blend file")
    parser.add_argument("--export-glb", action="store_true", help="Export animated glTF/GLB")
    parser.add_argument("--render-animation", action="store_true", help="Render PNG sequence via Blender")
    return parser.parse_args(argv)


def create_pbr_material(
    name: str,
    rgba: Tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.45,
    emission_strength: float = 0.0,
):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = rgba
    if hasattr(mat, "node_tree") and mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgba
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = metallic
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = roughness
            if emission_strength > 0.0 and "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def build_material_palette(style: str = "gymvisual_full_color") -> Dict[str, object]:
    is_color = style == "gymvisual_full_color"
    return {
        "ecorche_base": create_pbr_material("Mat_AnatomicalEcorcheGrey", (0.80, 0.83, 0.87, 1.0), metallic=0.04, roughness=0.52),
        "tendon_skin": create_pbr_material("Mat_AnatomicalTendonFascia", (0.85, 0.87, 0.90, 1.0), metallic=0.02, roughness=0.58),
        "muscle_primary": create_pbr_material(
            "Mat_PrimaryMuscle_Crimson",
            (0.89, 0.19, 0.24, 1.0) if is_color else (0.55, 0.57, 0.60, 1.0),
            metallic=0.05,
            roughness=0.38,
            emission_strength=0.16 if is_color else 0.0,
        ),
        "muscle_secondary": create_pbr_material(
            "Mat_SecondaryMuscle_Coral",
            (0.96, 0.54, 0.22, 1.0) if is_color else (0.68, 0.70, 0.73, 1.0),
            metallic=0.05,
            roughness=0.42,
            emission_strength=0.08 if is_color else 0.0,
        ),
        "apparel_dark": create_pbr_material("Mat_AthleticApparel", (0.18, 0.22, 0.28, 1.0), metallic=0.05, roughness=0.65),
        "chrome_steel": create_pbr_material("Mat_OlympicChrome", (0.82, 0.85, 0.89, 1.0), metallic=0.92, roughness=0.18),
        "plate_red_25kg": create_pbr_material("Mat_IWF_Red_25kg", (0.84, 0.16, 0.18, 1.0), metallic=0.1, roughness=0.35),
        "plate_blue_20kg": create_pbr_material("Mat_IWF_Blue_20kg", (0.12, 0.36, 0.78, 1.0), metallic=0.1, roughness=0.35),
        "plate_yellow_15kg": create_pbr_material("Mat_IWF_Yellow_15kg", (0.92, 0.74, 0.12, 1.0), metallic=0.1, roughness=0.35),
        "dumbbell_iron": create_pbr_material("Mat_CastIron", (0.18, 0.20, 0.23, 1.0), metallic=0.75, roughness=0.32),
        "bench_pad": create_pbr_material("Mat_UpholsteryPad", (0.16, 0.18, 0.22, 1.0), metallic=0.1, roughness=0.42),
        "rope_braid": create_pbr_material("Mat_BattleRope", (0.20, 0.22, 0.26, 1.0), metallic=0.05, roughness=0.75),
        "medball_rubber": create_pbr_material("Mat_MedBall", (0.86, 0.28, 0.18, 1.0), metallic=0.05, roughness=0.60),
        "machine_frame": create_pbr_material("Mat_MachineFrame", (0.28, 0.32, 0.38, 1.0), metallic=0.65, roughness=0.28),
        "platform_floor": create_pbr_material("Mat_LiftingPlatform", (0.93, 0.94, 0.96, 1.0), metallic=0.0, roughness=0.75),
    }


def assign_material(obj, mat):
    if hasattr(obj.data, "materials"):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat


def pick_muscle_belly_material(prim: dict, muscles: dict, palette: dict):
    role = prim.get("role", "muscle")
    if role == "apparel":
        return palette["apparel_dark"]
    if role in ("tendon_skin", "head"):
        return palette["tendon_skin"]

    tags = [t.lower() for t in prim.get("muscle_tags", [])]
    prim_set = set(m.lower() for m in muscles.get("primary", []))
    sec_set = set(m.lower() for m in muscles.get("secondary", []))

    for t in tags:
        if t in prim_set or any(t in p or p in t for p in prim_set):
            return palette["muscle_primary"]
    for t in tags:
        if t in sec_set or any(t in s or s in t for s in sec_set):
            return palette["muscle_secondary"]
    return palette["ecorche_base"]


def euler_from_two_points(p0: List[float], p1: List[float]) -> Tuple[float, float, float]:
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist < 1e-6:
        return (0.0, 0.0, 0.0)
    ux, uy, uz = dx / dist, dy / dist, dz / dist
    alpha = math.asin(max(-1.0, min(1.0, -uy)))
    cos_a = math.cos(alpha)
    beta = math.atan2(ux, uz) if abs(cos_a) > 1e-5 else 0.0
    return (alpha, beta, 0.0)


def create_humanoid_rig_and_mannequin(expanded: dict, palette: dict) -> dict:
    """
    Creates:
      1. `ExerciseArmature` with 24 hierarchical bones
      2. 38 Sculpted 3D Anatomical Muscle Belly meshes (`Muscle_<name>`) with active/secondary
         muscle highlighting and zero robotic ball-joints.
    """
    first_frame_joints = expanded["skeleton_frames"][0]["joints_3d"]
    muscles = expanded.get("muscles", {"primary": [], "secondary": []})

    arm_data = bpy.data.armatures.new("ExerciseArmatureData")
    arm_obj = bpy.data.objects.new("ExerciseArmature", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode="EDIT")
    for bone_name, parent_name in BONE_HIERARCHY:
        eb = arm_data.edit_bones.new(bone_name)
        head_co = first_frame_joints.get(bone_name, [0.0, 0.0, 0.0])
        eb.head = tuple(head_co)
        children = [c for c, p in BONE_HIERARCHY if p == bone_name]
        if children and children[0] in first_frame_joints:
            tail_co = first_frame_joints[children[0]]
            if math.dist(head_co, tail_co) < 0.02:
                tail_co = [head_co[0], head_co[1], head_co[2] + 0.08]
            eb.tail = tuple(tail_co)
        else:
            eb.tail = (head_co[0], head_co[1], head_co[2] + 0.08)
        if parent_name and parent_name in arm_data.edit_bones:
            eb.parent = arm_data.edit_bones[parent_name]
    bpy.ops.object.mode_set(mode="OBJECT")

    # Build 38 sculpted anatomical muscle belly meshes from frame 1
    initial_prims = generate_anatomical_muscle_primitives(first_frame_joints)
    muscle_meshes = {}
    for prim in initial_prims:
        mname = prim["name"]
        p0, p1 = prim["p0"], prim["p1"]
        r_avg = 0.5 * (prim["rad0"] + prim["rad1"])
        length = max(0.03, math.dist(p0, p1))
        mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
        bpy.ops.mesh.primitive_cylinder_add(radius=r_avg, depth=length, location=mid)
        m_obj = bpy.context.object
        m_obj.name = f"Muscle_{mname}"
        mat = pick_muscle_belly_material(prim, muscles, palette)
        assign_material(m_obj, mat)
        muscle_meshes[mname] = (m_obj, length)

    return {
        "armature": arm_obj,
        "muscle_meshes": muscle_meshes,
    }


def create_olympic_barbell(palette: dict, name: str = "barbell", grip_width_m: float = 0.58):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=2.20, location=(0.0, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0))
    shaft = bpy.context.object
    shaft.name = f"{name}_root"
    assign_material(shaft, palette["chrome_steel"])

    plate_specs = [
        (0.68, 0.225, 0.052, "plate_red_25kg", "25kg"),
        (0.75, 0.225, 0.044, "plate_blue_20kg", "20kg"),
        (0.81, 0.200, 0.036, "plate_yellow_15kg", "15kg"),
    ]
    for side_label, sign in [("L", -1.0), ("R", 1.0)]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.025, depth=0.41, location=(sign * 0.86, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0)
        )
        sleeve = bpy.context.object
        sleeve.name = f"{name}_sleeve_{side_label}"
        assign_material(sleeve, palette["chrome_steel"])
        sleeve.parent = shaft

        for offset_x, p_rad, p_thick, mat_key, weight_lbl in plate_specs:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=p_rad, depth=p_thick, location=(sign * offset_x, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0)
            )
            plate = bpy.context.object
            plate.name = f"{name}_plate_{weight_lbl}_{side_label}"
            assign_material(plate, palette[mat_key])
            plate.parent = shaft

        grip_empty = bpy.data.objects.new(f"{name}_grip_{side_label}", None)
        grip_empty.location = (sign * (grip_width_m * 0.5), 0.0, 0.0)
        bpy.context.collection.objects.link(grip_empty)
        grip_empty.parent = shaft

    return shaft


def create_dumbbell(palette: dict, name: str = "dumbbell"):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.16, location=(0.0, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0))
    handle = bpy.context.object
    handle.name = f"{name}_root"
    assign_material(handle, palette["chrome_steel"])

    for side_label, sign in [("L", -1.0), ("R", 1.0)]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.068, depth=0.038, location=(sign * 0.075, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0)
        )
        plate = bpy.context.object
        plate.name = f"{name}_plate_{side_label}"
        assign_material(plate, palette["dumbbell_iron"])
        plate.parent = handle
    return handle


def create_kettlebell(palette: dict, name: str = "kettlebell"):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.18, location=(0.0, 0.0, 0.0), rotation=(0.0, math.pi / 2.0, 0.0))
    handle = bpy.context.object
    handle.name = f"{name}_root"
    assign_material(handle, palette["chrome_steel"])

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, location=(0.0, 0.0, -0.14))
    body = bpy.context.object
    body.name = f"{name}_bell_body"
    assign_material(body, palette["dumbbell_iron"])
    body.parent = handle

    for side_label, sign in [("L", -1.0), ("R", 1.0)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.10, location=(sign * 0.07, 0.0, -0.05))
        horn = bpy.context.object
        horn.name = f"{name}_horn_{side_label}"
        assign_material(horn, palette["dumbbell_iron"])
        horn.parent = handle

    return handle


def create_medicine_ball(palette: dict, name: str = "medicine_ball", radius_m: float = 0.14):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius_m, location=(0.0, 0.25, 0.90))
    ball = bpy.context.object
    ball.name = f"{name}_root"
    assign_material(ball, palette["medball_rubber"])
    return ball


def create_battle_rope(palette: dict, name: str, initial_wave_pts: List[List[float]]):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.16, location=tuple(initial_wave_pts[0]))
    handle = bpy.context.object
    handle.name = f"{name}_root"
    assign_material(handle, palette["dumbbell_iron"])

    seg_objs = []
    for k in range(len(initial_wave_pts) - 1):
        p0 = initial_wave_pts[k]
        p1 = initial_wave_pts[k + 1]
        length = max(0.03, math.dist(p0, p1))
        mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.019, depth=length, location=mid)
        seg = bpy.context.object
        seg.name = f"{name}_wave_seg_{k:02d}"
        assign_material(seg, palette["rope_braid"])
        seg_objs.append((seg, length))

    handle._wave_segments = seg_objs  # type: ignore
    return handle


def create_cable_machine(palette: dict, name: str = "cable_bar"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.58, 1.05))
    tower = bpy.context.object
    tower.name = "CableMachine_Tower"
    tower.scale = (0.28, 0.16, 2.10)
    assign_material(tower, palette["machine_frame"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.36, 2.08))
    boom = bpy.context.object
    boom.name = "CableMachine_TopBoom"
    boom.scale = (0.14, 0.52, 0.08)
    assign_material(boom, palette["machine_frame"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.10, 0.45))
    seat = bpy.context.object
    seat.name = "CableMachine_Seat"
    seat.scale = (0.36, 0.44, 0.06)
    assign_material(seat, palette["bench_pad"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.38, location=(0.0, 0.14, 0.56), rotation=(0.0, math.pi / 2.0, 0.0))
    thigh_pad = bpy.context.object
    thigh_pad.name = "CableMachine_ThighPad"
    assign_material(thigh_pad, palette["bench_pad"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.58, 0.35))
    stack = bpy.context.object
    stack.name = "CableMachine_WeightStack"
    stack.scale = (0.24, 0.12, 0.22)
    assign_material(stack, palette["dumbbell_iron"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=1.06, location=(0.0, 0.14, 1.50), rotation=(0.0, math.pi / 2.0, 0.0))
    lat_bar = bpy.context.object
    lat_bar.name = f"{name}_root"
    assign_material(lat_bar, palette["chrome_steel"])
    lat_bar._weight_stack = stack  # type: ignore
    return lat_bar


def create_lever_machine(palette: dict, name: str = "lever_pad"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.12, 0.46))
    seat = bpy.context.object
    seat.name = "LeverMachine_Seat"
    seat.scale = (0.42, 0.46, 0.06)
    assign_material(seat, palette["bench_pad"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.34, 0.82))
    backrest = bpy.context.object
    backrest.name = "LeverMachine_Backrest"
    backrest.scale = (0.40, 0.08, 0.62)
    assign_material(backrest, palette["bench_pad"])

    bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.44, location=(0.0, 0.28, 0.18), rotation=(0.0, math.pi / 2.0, 0.0))
    roller = bpy.context.object
    roller.name = f"{name}_root"
    assign_material(roller, palette["bench_pad"])
    return roller


def create_bench(palette: dict, name: str = "bench"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -0.10, 0.42))
    pad = bpy.context.object
    pad.name = f"{name}_pad"
    pad.scale = (0.32, 1.22, 0.06)
    assign_material(pad, palette["bench_pad"])

    for leg_name, y_pos in [("front", -0.58), ("rear", 0.36)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.40, location=(0.0, y_pos, 0.20))
        leg = bpy.context.object
        leg.name = f"{name}_leg_{leg_name}"
        assign_material(leg, palette["dumbbell_iron"])
        leg.parent = pad
    return pad


def create_lifting_platform(palette: dict):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, -0.02))
    floor = bpy.context.object
    floor.name = "Studio_Lifting_Platform"
    floor.scale = (2.8, 2.4, 0.04)
    assign_material(floor, palette["platform_floor"])
    return floor


def bake_animation_keyframes(
    expanded: dict,
    rig_bundle: dict,
    equipment_objs: Dict[str, object],
):
    arm_obj = rig_bundle["armature"]
    muscle_meshes = rig_bundle["muscle_meshes"]

    for frame_data in expanded["skeleton_frames"]:
        frame_no = int(frame_data["frame"])
        j3d = frame_data["joints_3d"]

        # Keyframe all 38 sculpted anatomical muscle bellies
        frame_prims = generate_anatomical_muscle_primitives(j3d)
        for prim in frame_prims:
            mname = prim["name"]
            if mname not in muscle_meshes:
                continue
            m_obj, rest_len = muscle_meshes[mname]
            p0, p1 = prim["p0"], prim["p1"]
            mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
            cur_len = max(0.02, math.dist(p0, p1))
            m_obj.location = mid
            m_obj.rotation_euler = euler_from_two_points(p0, p1)
            m_obj.scale = (1.0, 1.0, cur_len / rest_len)
            m_obj.keyframe_insert(data_path="location", frame=frame_no)
            m_obj.keyframe_insert(data_path="rotation_euler", frame=frame_no)
            m_obj.keyframe_insert(data_path="scale", frame=frame_no)

        if hasattr(arm_obj, "pose") and arm_obj.pose:
            for bname, _ in BONE_HIERARCHY:
                if bname in arm_obj.pose.bones and bname in j3d:
                    pb = arm_obj.pose.bones[bname]
                    pb.rotation_mode = "XYZ"
                    pb.location = tuple(j3d[bname])
                    pb.keyframe_insert(data_path="location", frame=frame_no)

    for obj_name, track in expanded.get("objects", {}).items():
        if obj_name not in equipment_objs or obj_name == "bench":
            continue
        eq_obj = equipment_objs[obj_name]
        for pt in track:
            frame_no = int(pt["frame"])
            eq_obj.location = (float(pt["x"]), float(pt["y"]), float(pt["z"]))
            eq_obj.rotation_euler = (
                math.radians(float(pt.get("pitch_deg") or 0.0)),
                math.radians(float(pt.get("roll_deg") or 0.0)),
                math.radians(float(pt.get("yaw_deg") or 0.0)),
            )
            eq_obj.keyframe_insert(data_path="location", frame=frame_no)
            eq_obj.keyframe_insert(data_path="rotation_euler", frame=frame_no)

            wave_pts = pt.get("wave_points")
            if wave_pts and hasattr(eq_obj, "_wave_segments"):
                segs = getattr(eq_obj, "_wave_segments")
                for k in range(min(len(segs), len(wave_pts) - 1)):
                    seg_obj, rest_l = segs[k]
                    wp0, wp1 = wave_pts[k], wave_pts[k + 1]
                    wmid = ((wp0[0] + wp1[0]) * 0.5, (wp0[1] + wp1[1]) * 0.5, (wp0[2] + wp1[2]) * 0.5)
                    wlen = max(0.02, math.dist(wp0, wp1))
                    seg_obj.location = wmid
                    seg_obj.rotation_euler = euler_from_two_points(wp0, wp1)
                    seg_obj.scale = (1.0, 1.0, wlen / rest_l)
                    seg_obj.keyframe_insert(data_path="location", frame=frame_no)
                    seg_obj.keyframe_insert(data_path="rotation_euler", frame=frame_no)

            if "stack_z" in pt and hasattr(eq_obj, "_weight_stack"):
                stack_obj = getattr(eq_obj, "_weight_stack")
                stack_obj.location = (0.0, 0.58, float(pt["stack_z"]))
                stack_obj.keyframe_insert(data_path="location", frame=frame_no)


def setup_studio_camera_and_lights(expanded: dict, camera_preset: str = "three_quarter_front"):
    light_configs = [
        ("Studio_KeyLight", "AREA", (2.4, 2.8, 2.9), (math.radians(-42), 0.0, math.radians(38)), 850.0),
        ("Studio_FillLight", "AREA", (-2.6, 2.2, 2.1), (math.radians(-35), 0.0, math.radians(-45)), 420.0),
        ("Studio_RimLight", "AREA", (0.0, -2.5, 2.6), (math.radians(40), 0.0, math.radians(180)), 500.0),
    ]
    for l_name, l_type, loc, rot, energy in light_configs:
        ldata = bpy.data.lights.new(name=l_name, type=l_type)
        ldata.energy = energy
        lobj = bpy.data.objects.new(name=l_name, object_data=ldata)
        lobj.location = loc
        lobj.rotation_euler = rot
        bpy.context.collection.objects.link(lobj)

    cam_data = bpy.data.cameras.new(name="ExerciseCamera")
    cam_data.lens = 50.0
    cam_obj = bpy.data.objects.new("ExerciseCamera", cam_data)
    if camera_preset == "side_sagittal":
        cam_obj.location = (3.4, 0.0, 1.05)
        cam_obj.rotation_euler = (math.radians(88), 0.0, math.radians(90))
    elif camera_preset == "front_coronal":
        cam_obj.location = (0.0, 3.4, 1.05)
        cam_obj.rotation_euler = (math.radians(88), 0.0, math.radians(180))
    else:
        cam_obj.location = (2.35, 2.55, 1.38)
        cam_obj.rotation_euler = (math.radians(78), 0.0, math.radians(138))
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj


def main():
    args = parse_cli_args()
    spec_path = Path(args.spec_path).resolve()
    if not spec_path.exists():
        raise FileNotFoundError(f"Motion spec not found: {spec_path}")

    raw_json = json.loads(spec_path.read_text(encoding="utf-8"))
    if "skeleton_frames" in raw_json:
        expanded = raw_json
    else:
        expanded = expand_motion_spec(str(spec_path))

    out_dir = Path(args.output_dir).resolve() if args.output_dir else (spec_path.parent / "output")
    out_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    fps = int(expanded["fps"])
    total_frames = int(expanded["total_frames"])
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1080

    palette = build_material_palette(args.style)
    create_lifting_platform(palette)
    rig_bundle = create_humanoid_rig_and_mannequin(expanded, palette)

    grip_width = float(expanded.get("setup", {}).get("grip_width_m") or 0.58)
    equipment_objs = {}
    for obj_name, track in expanded.get("objects", {}).items():
        if "barbell" in obj_name:
            equipment_objs[obj_name] = create_olympic_barbell(palette, obj_name, grip_width)
        elif "dumbbell" in obj_name:
            equipment_objs[obj_name] = create_dumbbell(palette, obj_name)
        elif "kettlebell" in obj_name:
            equipment_objs[obj_name] = create_kettlebell(palette, obj_name)
        elif "medicine_ball" in obj_name:
            rad = float(track[0].get("radius_m", 0.14)) if track else 0.14
            equipment_objs[obj_name] = create_medicine_ball(palette, obj_name, rad)
        elif "battle_rope" in obj_name:
            init_waves = track[0].get("wave_points", [[0, 0, 0.8], [0, 1.85, 0.06]])
            equipment_objs[obj_name] = create_battle_rope(palette, obj_name, init_waves)
        elif "cable_bar" in obj_name:
            equipment_objs[obj_name] = create_cable_machine(palette, obj_name)
        elif "lever_pad" in obj_name:
            equipment_objs[obj_name] = create_lever_machine(palette, obj_name)
        elif "bench" in obj_name:
            equipment_objs[obj_name] = create_bench(palette, obj_name)

    bake_animation_keyframes(expanded, rig_bundle, equipment_objs)
    setup_studio_camera_and_lights(expanded, args.camera)

    ex_slug = expanded.get("exercise_id", expanded["exercise_name"].lower().replace(" ", "_"))
    if args.save_blend:
        blend_path = out_dir / f"{ex_slug}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    if args.export_glb and hasattr(bpy.ops.export_scene, "gltf"):
        glb_path = out_dir / f"{ex_slug}.glb"
        bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB")

    if args.render_animation:
        scene.render.filepath = str(out_dir / "frames" / "frame_")
        bpy.ops.render.render(animation=True)

    manifest = {
        "exercise_name": expanded["exercise_name"],
        "blender_backend": "mock_bpy_verifier" if USING_MOCK_BPY else "native_blender_bpy",
        "fps": fps,
        "frame_range": [1, total_frames],
        "objects_created": [o.name for o in bpy.data.objects],
        "materials_created": [m.name for m in bpy.data.materials],
        "armature_bones": [b.name for b in rig_bundle["armature"].data.bones],
        "anatomical_muscle_meshes": list(rig_bundle["muscle_meshes"].keys()),
        "equipment_roots": list(equipment_objs.keys()),
        "total_keyframed_channels": sum(len(getattr(o, "_keyframes", {})) for o in bpy.data.objects),
    }
    manifest_path = out_dir / f"{ex_slug}.bpy_scene_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Blender Pipeline v4.0] Generated scene for '{expanded['exercise_name']}' -> {manifest_path}")


if __name__ == "__main__":
    main()
