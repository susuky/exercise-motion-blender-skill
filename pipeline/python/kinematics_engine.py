"""
Universal Full-Body 3D Anthropometric Forward & Inverse Kinematics Engine (v4.1).

Covers all 10 body postures and all 29 GymVisual equipment categories.
"""
from __future__ import annotations

import importlib.util as _ilu
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


def _load_mod(name: str, filename: str):
    p = Path(__file__).resolve().parent / filename
    if not p.exists():
        p = Path(__file__).resolve().parents[1] / "python" / filename
    spec = _ilu.spec_from_file_location(name, str(p))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


_eq_reg = _load_mod("equipment_registry", "equipment_registry.py")
get_equipment_archetype = _eq_reg.get_equipment_archetype
normalize_equipment_type = _eq_reg.normalize_equipment_type
EQUIPMENT_TAXONOMY = _eq_reg.EQUIPMENT_TAXONOMY


RIG_METRICS = {
    "ankle_height": 0.075,
    "shin_len": 0.415,
    "thigh_len": 0.430,
    "hip_half_width": 0.105,
    "pelvis_to_spine": 0.135,
    "spine_to_chest": 0.195,
    "chest_to_neck": 0.155,
    "neck_to_head": 0.125,
    "head_radius": 0.105,
    "shoulder_half_width": 0.205,
    "upper_arm_len": 0.305,
    "forearm_len": 0.275,
    "hand_len": 0.080,
    "foot_len": 0.195,
}

BONE_HIERARCHY = [
    ("root", None),
    ("pelvis", "root"),
    ("spine", "pelvis"),
    ("chest", "spine"),
    ("neck", "chest"),
    ("head", "neck"),
    ("clavicle_L", "chest"),
    ("shoulder_L", "clavicle_L"),
    ("elbow_L", "shoulder_L"),
    ("wrist_L", "elbow_L"),
    ("hand_L", "wrist_L"),
    ("clavicle_R", "chest"),
    ("shoulder_R", "clavicle_R"),
    ("elbow_R", "shoulder_R"),
    ("wrist_R", "elbow_R"),
    ("hand_R", "wrist_R"),
    ("hip_L", "pelvis"),
    ("knee_L", "hip_L"),
    ("ankle_L", "knee_L"),
    ("toe_L", "ankle_L"),
    ("hip_R", "pelvis"),
    ("knee_R", "hip_R"),
    ("ankle_R", "knee_R"),
    ("toe_R", "ankle_R"),
]


def _vec(x: float, y: float, z: float) -> np.ndarray:
    return np.array([float(x), float(y), float(z)], dtype=np.float64)


def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-9:
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)
    return v / n


def solve_two_bone_ik(
    root_pos: np.ndarray,
    target_pos: np.ndarray,
    len1: float,
    len2: float,
    pole_dir: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    diff = target_pos - root_pos
    dist = float(np.linalg.norm(diff))
    max_reach = (len1 + len2) * 0.998
    min_reach = abs(len1 - len2) + 0.02

    if dist < 1e-6:
        forward = _normalize(pole_dir)
        mid = root_pos + forward * len1
        end = mid - forward * len2
        return mid, end

    dir_to_target = diff / dist
    clamped_dist = max(min_reach, min(max_reach, dist))

    cos_alpha = (len1 * len1 + clamped_dist * clamped_dist - len2 * len2) / (2.0 * len1 * clamped_dist)
    cos_alpha = max(-1.0, min(1.0, cos_alpha))
    sin_alpha = math.sqrt(max(0.0, 1.0 - cos_alpha * cos_alpha))

    pole_proj = pole_dir - np.dot(pole_dir, dir_to_target) * dir_to_target
    if np.linalg.norm(pole_proj) < 1e-6:
        fallback = np.array([0.0, 1.0, 0.0]) if abs(dir_to_target[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        pole_proj = fallback - np.dot(fallback, dir_to_target) * dir_to_target
    bend_dir = _normalize(pole_proj)

    mid_pos = root_pos + dir_to_target * (len1 * cos_alpha) + bend_dir * (len1 * sin_alpha)
    if dist <= max_reach:
        end_pos = target_pos.copy()
        seg2 = _normalize(end_pos - mid_pos) * len2
        end_pos = mid_pos + seg2
    else:
        end_pos = root_pos + dir_to_target * (len1 + len2)
        mid_pos = root_pos + dir_to_target * len1

    return mid_pos, end_pos


def compute_arm_fk_direction(
    side: str,
    shoulder_pos: np.ndarray,
    shoulder_angles: Dict[str, float],
    elbow_angles: Dict[str, float],
    torso_up: np.ndarray,
    torso_forward: np.ndarray,
    torso_right: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    sign = -1.0 if side == "L" else 1.0
    flex = math.radians(float(shoulder_angles.get("flexion_deg") or 0.0))
    abd = math.radians(float(shoulder_angles.get("abduction_deg") or 0.0))
    rot = math.radians(float(shoulder_angles.get("rotation_deg") or 0.0))
    elb_flex = math.radians(max(0.0, float(elbow_angles.get("flexion_deg") or 0.0)))

    fwd = torso_forward
    lat = sign * torso_right

    z_comp = -math.cos(flex) * math.cos(abd)
    y_comp = math.sin(flex) * math.cos(abd * 0.65)
    x_comp = math.sin(abd) * max(0.25, abs(math.cos(flex * 0.5)))

    upper_dir = _normalize(z_comp * torso_up + y_comp * fwd + x_comp * lat)
    elbow_pos = shoulder_pos + upper_dir * RIG_METRICS["upper_arm_len"]

    bend_target = _normalize(0.82 * fwd + 0.55 * torso_up - 0.25 * sign * math.sin(rot) * torso_right)
    bend_perp = bend_target - np.dot(bend_target, upper_dir) * upper_dir
    if np.linalg.norm(bend_perp) < 1e-6:
        bend_perp = torso_forward - np.dot(torso_forward, upper_dir) * upper_dir
    bend_perp = _normalize(bend_perp)

    forearm_dir = _normalize(math.cos(elb_flex) * upper_dir + math.sin(elb_flex) * bend_perp)
    wrist_pos = elbow_pos + forearm_dir * RIG_METRICS["forearm_len"]

    pole_dir = _normalize(-0.65 * bend_perp + 0.35 * lat + 0.20 * upper_dir)
    return elbow_pos, wrist_pos, pole_dir


def is_contact_active(contact: dict, t: float) -> bool:
    st = contact.get("start_t")
    et = contact.get("end_t")
    if st is not None and t < float(st) - 1e-4:
        return False
    if et is not None and t > float(et) + 1e-4:
        return False
    return True


def build_battle_rope_wave_points(
    hand_pos: np.ndarray,
    anchor_pos: np.ndarray,
    t: float,
    z_mid: float,
    amp_hand: float,
    omega: float,
    phase_offset: float = 0.0,
    num_nodes: int = 36,
) -> List[List[float]]:
    """
    Propagates the exact travelling wave history of the hand's vertical oscillation
    (`z_hand(t) = z_mid + amp_hand * cos(omega * t + phase_offset)`) forward along
    the rope (`s` from 0 at the hand to 1 at the floor anchor) with 1.55 smooth
    wavelengths and natural catenary gravity droop.
    """
    pts = []
    k_wave = 1.85 * 2.0 * math.pi  # 1.85 full rolling sinusoidal waves along the rope

    for idx in range(num_nodes):
        s = idx / float(num_nodes - 1)
        bx = (1.0 - s) * float(hand_pos[0]) + s * float(anchor_pos[0])
        by = (1.0 - s) * float(hand_pos[1]) + s * float(anchor_pos[1])

        delayed_phase = omega * t + phase_offset - k_wave * s
        center_z = z_mid * pow(1.0 - s, 1.25) + float(anchor_pos[2]) * (1.0 - pow(1.0 - s, 1.25))
        amp_s = amp_hand * (1.0 - 0.85 * s) * (1.0 + 0.35 * math.sin(math.pi * s))
        z_raw = center_z + amp_s * math.cos(delayed_phase)
        z_val = max(0.024, z_raw)

        pts.append([round(bx, 4), round(by, 4), round(z_val, 4)])

    pts[0] = [round(float(hand_pos[0]), 4), round(float(hand_pos[1]), 4), round(float(hand_pos[2]), 4)]
    pts[-1] = [round(float(anchor_pos[0]), 4), round(float(anchor_pos[1]), 4), round(float(anchor_pos[2]), 4)]
    return pts


def solve_frame_pose(
    spec: dict,
    t: float,
    joint_frame: Dict[str, Dict[str, Optional[float]]],
    root_frame: Optional[Dict[str, Optional[float]]],
    equip_frame: Dict[str, Dict[str, Optional[float]]],
) -> Tuple[Dict[str, List[float]], Dict[str, Dict[str, float]], Dict[str, float]]:
    setup = spec.get("setup", {})
    body_pos = setup.get("body_position", "standing")
    grip_width = float(setup.get("grip_width_m") or 0.56)
    stance_width = float(setup.get("stance_width_m") or (RIG_METRICS["hip_half_width"] * 2.1))
    half_stance = stance_width * 0.5
    half_grip = grip_width * 0.5

    equipment_types = [normalize_equipment_type(eq.get("type", "")) for eq in spec.get("equipment", [])]
    objects_3d: Dict[str, Dict[str, float]] = {}

    if body_pos in ("supine_on_bench", "incline_bench"):
        pelvis = _vec(0.0, -0.34, 0.48)
        spine = _vec(0.0, -0.18, 0.49)
        chest = _vec(0.0, 0.04, 0.50)
        neck = _vec(0.0, 0.20, 0.50)
        head = _vec(0.0, 0.33, 0.52)

        hip_L = _vec(-RIG_METRICS["hip_half_width"], -0.36, 0.47)
        hip_R = _vec(RIG_METRICS["hip_half_width"], -0.36, 0.47)
        knee_L = _vec(-0.18, -0.72, 0.43)
        knee_R = _vec(0.18, -0.72, 0.43)
        ankle_L = _vec(-0.20, -0.76, 0.075)
        ankle_R = _vec(0.20, -0.76, 0.075)
        toe_L = _vec(-0.22, -0.92, 0.02)
        toe_R = _vec(0.22, -0.92, 0.02)

        clavicle_L = chest + _vec(-0.07, 0.08, 0.0)
        clavicle_R = chest + _vec(0.07, 0.08, 0.0)
        shoulder_L = chest + _vec(-RIG_METRICS["shoulder_half_width"], 0.10, 0.01)
        shoulder_R = chest + _vec(RIG_METRICS["shoulder_half_width"], 0.10, 0.01)

        el_L_ang = joint_frame.get("left_elbow", {})
        elb_flex_L = math.radians(float(el_L_ang.get("flexion_deg") or 10.0))
        press_alpha = max(0.0, min(1.0, (85.0 - math.degrees(elb_flex_L)) / 80.0))
        bar_z = 0.62 + press_alpha * 0.35
        bar_y = 0.06 + press_alpha * 0.06

        if "barbell" in equip_frame and equip_frame["barbell"].get("z") is not None:
            bar_x = float(equip_frame["barbell"].get("x") or 0.0)
            bar_y = float(equip_frame["barbell"].get("y") or bar_y)
            bar_z = float(equip_frame["barbell"].get("z") or bar_z)
        else:
            bar_x = 0.0

        grip_L = _vec(bar_x - half_grip, bar_y, bar_z)
        grip_R = _vec(bar_x + half_grip, bar_y, bar_z)

        pole_L = _vec(-0.7, -0.5, -0.3)
        pole_R = _vec(0.7, -0.5, -0.3)
        elbow_L, wrist_L = solve_two_bone_ik(
            shoulder_L, grip_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_L
        )
        elbow_R, wrist_R = solve_two_bone_ik(
            shoulder_R, grip_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_R
        )
        hand_L = grip_L.copy()
        hand_R = grip_R.copy()

        objects_3d["barbell"] = {
            "x": float(bar_x),
            "y": float(bar_y),
            "z": float(bar_z),
            "pitch_deg": 0.0,
            "roll_deg": 0.0,
            "yaw_deg": 0.0,
        }
        objects_3d["bench"] = {
            "x": 0.0,
            "y": -0.15,
            "z": 0.225,
            "pitch_deg": 0.0,
            "roll_deg": 0.0,
            "yaw_deg": 0.0,
        }

    elif body_pos == "seated":
        seat_z = float(setup.get("seat_height_m") or 0.48)
        pelvis_y = float((root_frame or {}).get("y") or -0.12)
        pelvis = _vec(0.0, pelvis_y, seat_z + 0.04)

        hip_L = pelvis + _vec(-RIG_METRICS["hip_half_width"], 0.0, -0.01)
        hip_R = pelvis + _vec(RIG_METRICS["hip_half_width"], 0.0, -0.01)

        knee_L = hip_L + _vec(-0.02, RIG_METRICS["thigh_len"] * 0.96, -0.02)
        knee_R = hip_R + _vec(0.02, RIG_METRICS["thigh_len"] * 0.96, -0.02)

        knee_L_deg = float((joint_frame.get("left_knee") or {}).get("flexion_deg") or 90.0)
        knee_R_deg = float((joint_frame.get("right_knee") or {}).get("flexion_deg") or 90.0)

        def _seated_leg(knee_p: np.ndarray, k_deg: float, side_s: float):
            k_rad = math.radians(max(0.0, min(130.0, k_deg)))
            shin_dir = _normalize(_vec(0.0, math.cos(k_rad), -math.sin(k_rad)))
            ank = knee_p + shin_dir * RIG_METRICS["shin_len"]
            ank[2] = max(0.075, float(ank[2]))
            foot_dir = _normalize(_vec(side_s * 0.04, math.sin(k_rad), math.cos(k_rad) * 0.65))
            toe = ank + foot_dir * RIG_METRICS["foot_len"]
            toe[2] = max(0.02, float(toe[2]))
            return ank, toe

        ankle_L, toe_L = _seated_leg(knee_L, knee_L_deg, -1.0)
        ankle_R, toe_R = _seated_leg(knee_R, knee_R_deg, 1.0)

        lean_deg = float((root_frame or {}).get("torso_lean_deg") or -8.0)
        lean_rad = math.radians(lean_deg)
        torso_up = _normalize(_vec(0.0, math.sin(lean_rad), math.cos(lean_rad)))
        torso_forward = _normalize(_vec(0.0, math.cos(lean_rad), -math.sin(lean_rad)))
        torso_right = _vec(1.0, 0.0, 0.0)

        spine = pelvis + torso_up * RIG_METRICS["pelvis_to_spine"]
        chest = spine + torso_up * RIG_METRICS["spine_to_chest"]
        neck = chest + torso_up * RIG_METRICS["chest_to_neck"]
        head = neck + _normalize(_vec(0.0, math.sin(lean_rad * 0.3), math.cos(lean_rad * 0.3))) * RIG_METRICS["neck_to_head"]

        clavicle_L = chest + torso_up * 0.08 - torso_right * 0.08
        clavicle_R = chest + torso_up * 0.08 + torso_right * 0.08
        shoulder_L = chest + torso_up * 0.10 - torso_right * RIG_METRICS["shoulder_half_width"]
        shoulder_R = chest + torso_up * 0.10 + torso_right * RIG_METRICS["shoulder_half_width"]

        sh_L_ang = joint_frame.get("left_shoulder", {})
        sh_R_ang = joint_frame.get("right_shoulder", {})
        el_L_ang = joint_frame.get("left_elbow", {})
        el_R_ang = joint_frame.get("right_elbow", {})

        elbow_L, wrist_L, pole_L = compute_arm_fk_direction(
            "L", shoulder_L, sh_L_ang, el_L_ang, torso_up, torso_forward, torso_right
        )
        elbow_R, wrist_R, pole_R = compute_arm_fk_direction(
            "R", shoulder_R, sh_R_ang, el_R_ang, torso_up, torso_forward, torso_right
        )

        if "cable_machine" in equipment_types:
            bar_eq = equip_frame.get("cable_bar") or equip_frame.get("cable_machine") or {}
            if bar_eq and bar_eq.get("z") is not None:
                bar_x = float(bar_eq.get("x") or 0.0)
                bar_y = float(bar_eq.get("y") or 0.08)
                bar_z = float(bar_eq.get("z") or 1.45)
            else:
                mid_w = 0.5 * (wrist_L + wrist_R)
                bar_x, bar_y, bar_z = float(mid_w[0]), float(mid_w[1]), float(mid_w[2])

            grip_L = _vec(bar_x - half_grip, bar_y, bar_z)
            grip_R = _vec(bar_x + half_grip, bar_y, bar_z)
            # Downward pole vector drives elbows straight down toward flanks (z=0.66m when bar_z=0.88m)
            pole_L = _normalize(_vec(-0.22, -0.06, -1.0))
            pole_R = _normalize(_vec(0.22, -0.06, -1.0))
            elbow_L, wrist_L = solve_two_bone_ik(
                shoulder_L, grip_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_L
            )
            elbow_R, wrist_R = solve_two_bone_ik(
                shoulder_R, grip_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_R
            )
            solved_mid = 0.5 * (wrist_L + wrist_R)
            bar_y, bar_z = float(solved_mid[1]), float(solved_mid[2])
            grip_L = _vec(bar_x - half_grip, bar_y, bar_z)
            grip_R = _vec(bar_x + half_grip, bar_y, bar_z)
            wrist_L, wrist_R = grip_L.copy(), grip_R.copy()

            pull_dist = max(0.0, 1.50 - bar_z)
            stack_z = 0.32 + pull_dist * 0.85
            objects_3d["cable_bar"] = {
                "x": float(bar_x),
                "y": float(bar_y),
                "z": float(bar_z),
                "pulley_x": 0.0,
                "pulley_y": float(bar_y + 0.04),
                "pulley_z": 2.08,
                "stack_z": round(stack_z, 4),
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        elif "lever_machine" in equipment_types:
            handle_L = _vec(-0.28, pelvis_y + 0.08, seat_z + 0.06)
            handle_R = _vec(0.28, pelvis_y + 0.08, seat_z + 0.06)
            elbow_L, wrist_L = solve_two_bone_ik(
                shoulder_L, handle_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(-0.3, -0.6, -0.6)
            )
            elbow_R, wrist_R = solve_two_bone_ik(
                shoulder_R, handle_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(0.3, -0.6, -0.6)
            )
            wrist_L, wrist_R = handle_L.copy(), handle_R.copy()

            ank_mid = 0.5 * (ankle_L + ankle_R)
            knee_mid = 0.5 * (knee_L + knee_R)
            avg_k_deg = 0.5 * (knee_L_deg + knee_R_deg)
            lift_ratio = max(0.0, min(1.0, (95.0 - avg_k_deg) / 90.0))
            objects_3d["lever_pad"] = {
                "x": 0.0,
                "y": float(ank_mid[1] + 0.04),
                "z": float(ank_mid[2] + 0.03),
                "pivot_x": 0.0,
                "pivot_y": float(knee_mid[1]),
                "pivot_z": float(knee_mid[2]),
                "stack_z": round(0.28 + lift_ratio * 0.42, 4),
                "pitch_deg": round(90.0 - avg_k_deg, 2),
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        hand_L = wrist_L.copy()
        hand_R = wrist_R.copy()

    else:
        knee_L_deg = float((joint_frame.get("left_knee") or {}).get("flexion_deg") or 5.0)
        knee_R_deg = float((joint_frame.get("right_knee") or {}).get("flexion_deg") or 5.0)
        hip_L_deg = float((joint_frame.get("left_hip") or {}).get("flexion_deg") or 5.0)
        hip_R_deg = float((joint_frame.get("right_hip") or {}).get("flexion_deg") or 5.0)
        hip_L_abd = float((joint_frame.get("left_hip") or {}).get("abduction_deg") or 8.0)
        hip_R_abd = float((joint_frame.get("right_hip") or {}).get("abduction_deg") or 8.0)
        ankle_L_deg = float((joint_frame.get("left_ankle") or {}).get("flexion_deg") or 0.0)
        ankle_R_deg = float((joint_frame.get("right_ankle") or {}).get("flexion_deg") or 0.0)

        split_step = float((root_frame or {}).get("split_step_m") or 0.0)
        flight_z = max(0.0, float((root_frame or {}).get("flight_z_m") or 0.0))
        torso_lean_override = (root_frame or {}).get("torso_lean_deg")

        ankle_L = _vec(-half_stance, split_step * 0.95, RIG_METRICS["ankle_height"] + flight_z)
        toe_lift = -0.035 if flight_z > 0.02 else 0.0
        toe_L = ankle_L + _vec(-0.020, RIG_METRICS["foot_len"], -RIG_METRICS["ankle_height"] + 0.018 + toe_lift)
        toe_L[2] = max(0.018, float(toe_L[2]))

        rear_heel_lift = min(0.055, abs(split_step) * 0.12) if abs(split_step) > 0.05 else 0.0
        ankle_R = _vec(half_stance, -split_step * 1.05, RIG_METRICS["ankle_height"] + rear_heel_lift + flight_z)
        toe_R = _vec(half_stance + 0.020, -split_step * 1.05 + RIG_METRICS["foot_len"], max(0.018, 0.018 + flight_z + toe_lift))

        def solve_leg(ankle_pos: np.ndarray, knee_deg: float, hip_deg: float, ankle_deg: float, is_rear_split: bool, side_sign: float):
            k_rad = math.radians(max(0.0, knee_deg))
            if is_rear_split:
                shin_tilt = math.radians(-18.0 - 0.35 * knee_deg)
            else:
                shin_tilt = math.radians(min(42.0, knee_deg * 0.40 + ankle_deg * 0.5))
            shin_lateral = side_sign * 0.08 * math.sin(k_rad * 0.7)
            shin_dir = _normalize(_vec(shin_lateral, math.sin(shin_tilt), math.cos(shin_tilt)))
            knee_pos = ankle_pos + shin_dir * RIG_METRICS["shin_len"]

            thigh_pitch = k_rad - shin_tilt
            thigh_dir = _normalize(_vec(-shin_lateral * 0.5, -math.sin(thigh_pitch), math.cos(thigh_pitch)))
            hip_pos = knee_pos + thigh_dir * RIG_METRICS["thigh_len"]
            return knee_pos, hip_pos

        is_split = abs(split_step) > 0.08
        knee_L, hip_L_raw = solve_leg(ankle_L, knee_L_deg, hip_L_deg, ankle_L_deg, False, -1.0)
        knee_R, hip_R_raw = solve_leg(ankle_R, knee_R_deg, hip_R_deg, ankle_R_deg, is_split, 1.0)

        pelvis_y = 0.5 * (hip_L_raw[1] + hip_R_raw[1])
        pelvis_z = 0.5 * (hip_L_raw[2] + hip_R_raw[2])
        if root_frame and root_frame.get("z") is not None:
            pelvis_z = float(root_frame["z"]) + flight_z
        if root_frame and root_frame.get("y") is not None:
            pelvis_y = float(root_frame["y"])

        pelvis = _vec(0.0, pelvis_y, pelvis_z)
        hip_L = pelvis + _vec(-RIG_METRICS["hip_half_width"], 0.0, 0.0)
        hip_R = pelvis + _vec(RIG_METRICS["hip_half_width"], 0.0, 0.0)

        flare_L = 0.14 + 0.015 * max(0.0, hip_L_abd)
        flare_R = 0.14 + 0.015 * max(0.0, hip_R_abd)
        knee_L, ankle_L = solve_two_bone_ik(
            hip_L, ankle_L, RIG_METRICS["thigh_len"], RIG_METRICS["shin_len"], _vec(-flare_L, 1.0, 0.12)
        )
        knee_R, ankle_R = solve_two_bone_ik(
            hip_R, ankle_R, RIG_METRICS["thigh_len"], RIG_METRICS["shin_len"], _vec(flare_R, 1.0, 0.12)
        )

        if torso_lean_override is not None:
            lean_deg = float(torso_lean_override)
        else:
            avg_hip = 0.5 * (hip_L_deg + hip_R_deg)
            avg_knee = 0.5 * (knee_L_deg + knee_R_deg)
            lean_deg = max(-8.0, min(62.0, (avg_hip - avg_knee * 0.45) * 0.65))

        lean_rad = math.radians(lean_deg)
        torso_up = _normalize(_vec(0.0, math.sin(lean_rad), math.cos(lean_rad)))
        torso_forward = _normalize(_vec(0.0, math.cos(lean_rad), -math.sin(lean_rad)))
        torso_right = _vec(1.0, 0.0, 0.0)

        spine = pelvis + torso_up * RIG_METRICS["pelvis_to_spine"]
        chest = spine + torso_up * RIG_METRICS["spine_to_chest"]
        neck = chest + torso_up * RIG_METRICS["chest_to_neck"]
        head_up = _normalize(_vec(0.0, math.sin(lean_rad * 0.25), math.cos(lean_rad * 0.25)))
        head = neck + head_up * RIG_METRICS["neck_to_head"]

        clavicle_L = chest + torso_up * 0.08 - torso_right * 0.08
        clavicle_R = chest + torso_up * 0.08 + torso_right * 0.08
        shoulder_L = chest + torso_up * 0.10 - torso_right * RIG_METRICS["shoulder_half_width"]
        shoulder_R = chest + torso_up * 0.10 + torso_right * RIG_METRICS["shoulder_half_width"]

        sh_L_ang = joint_frame.get("left_shoulder", {})
        sh_R_ang = joint_frame.get("right_shoulder", {})
        el_L_ang = joint_frame.get("left_elbow", {})
        el_R_ang = joint_frame.get("right_elbow", {})

        elbow_L, wrist_L, pole_L = compute_arm_fk_direction(
            "L", shoulder_L, sh_L_ang, el_L_ang, torso_up, torso_forward, torso_right
        )
        elbow_R, wrist_R, pole_R = compute_arm_fk_direction(
            "R", shoulder_R, sh_R_ang, el_R_ang, torso_up, torso_forward, torso_right
        )

        if "barbell" in equipment_types or "ez_barbell" in equipment_types or "trap_bar" in equipment_types or "smith_machine" in equipment_types:
            bar_eq = equip_frame.get("barbell", {})
            if bar_eq and bar_eq.get("z") is not None:
                bar_x = float(bar_eq.get("x") or 0.0)
                bar_y = float(bar_eq.get("y") or 0.14)
                bar_z = float(bar_eq.get("z") or 0.225)
            else:
                mid_w = 0.5 * (wrist_L + wrist_R)
                bar_x, bar_y, bar_z = float(mid_w[0]), float(mid_w[1]), max(0.225, float(mid_w[2]))

            bar_z = max(0.225, bar_z)
            grip_L = _vec(bar_x - half_grip, bar_y, bar_z)
            grip_R = _vec(bar_x + half_grip, bar_y, bar_z)

            sh_flex_avg = 0.5 * (
                float(sh_L_ang.get("flexion_deg") or 0.0) + float(sh_R_ang.get("flexion_deg") or 0.0)
            )
            el_flex_avg = 0.5 * (
                float(el_L_ang.get("flexion_deg") or 0.0) + float(el_R_ang.get("flexion_deg") or 0.0)
            )
            if 70.0 <= sh_flex_avg <= 135.0 and el_flex_avg >= 75.0:
                pole_L = _normalize(_vec(-0.35, 1.0, -0.15))
                pole_R = _normalize(_vec(0.35, 1.0, -0.15))
            elif sh_flex_avg > 135.0:
                pole_L = _normalize(_vec(-0.75, 0.35, -0.20))
                pole_R = _normalize(_vec(0.75, 0.35, -0.20))
            else:
                pole_L = _normalize(_vec(-0.85, -0.25, 0.25))
                pole_R = _normalize(_vec(0.85, -0.25, 0.25))

            elbow_L, wrist_L = solve_two_bone_ik(
                shoulder_L, grip_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_L
            )
            elbow_R, wrist_R = solve_two_bone_ik(
                shoulder_R, grip_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_R
            )
            solved_mid = 0.5 * (wrist_L + wrist_R)
            bar_y = float(solved_mid[1])
            bar_z = max(0.225, float(solved_mid[2]))
            grip_L = _vec(bar_x - half_grip, bar_y, bar_z)
            grip_R = _vec(bar_x + half_grip, bar_y, bar_z)
            wrist_L = grip_L.copy()
            wrist_R = grip_R.copy()

            objects_3d["barbell"] = {
                "x": float(bar_x),
                "y": float(bar_y),
                "z": float(bar_z),
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        elif "battle_ropes" in equipment_types or "rope" in equipment_types:
            # Continuous harmonic wave solver for Battle Ropes:
            # Derive frequency omega from cycle duration so the hand's exact harmonic motion
            # propagates seamlessly into the 36-node rope wave without any sawtooth kinks!
            dur_sec = float(spec.get("timing", {}).get("duration_sec", 2.4))
            n_cycles = 3.0
            omega = 2.0 * math.pi * n_cycles / max(0.5, dur_sec)

            z_mid = float(pelvis[2]) + 0.16
            amp_hand = 0.27
            phase_off_R = math.pi if spec.get("laterality") == "alternating" else 0.0

            hand_z_L = z_mid + amp_hand * math.cos(omega * t)
            hand_z_R = z_mid + amp_hand * math.cos(omega * t + phase_off_R)
            hand_y_L = float(pelvis[1]) + 0.42 + 0.03 * math.sin(omega * t)
            hand_y_R = float(pelvis[1]) + 0.42 + 0.03 * math.sin(omega * t + phase_off_R)

            target_L = _vec(-half_grip, hand_y_L, hand_z_L)
            target_R = _vec(half_grip, hand_y_R, hand_z_R)
            # Pull elbows backward (-Y) and downward (-Z) so forearms reach forward toward the ropes!
            pole_L = _normalize(_vec(-0.22, -0.85, -0.50))
            pole_R = _normalize(_vec(0.22, -0.85, -0.50))
            elbow_L, wrist_L = solve_two_bone_ik(
                shoulder_L, target_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_L
            )
            elbow_R, wrist_R = solve_two_bone_ik(
                shoulder_R, target_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], pole_R
            )

            anchor_pt = [0.0, 1.95, 0.05]
            for eq in spec.get("equipment", []):
                if normalize_equipment_type(eq.get("type", "")) in ("battle_ropes", "rope") and eq.get("anchor_point"):
                    anchor_pt = list(eq["anchor_point"])
            anchor_L = _vec(anchor_pt[0] - 0.15, anchor_pt[1], anchor_pt[2])
            anchor_R = _vec(anchor_pt[0] + 0.15, anchor_pt[1], anchor_pt[2])

            wave_L = build_battle_rope_wave_points(
                wrist_L, anchor_L, t, z_mid=z_mid, amp_hand=amp_hand, omega=omega, phase_offset=0.0, num_nodes=36
            )
            wave_R = build_battle_rope_wave_points(
                wrist_R, anchor_R, t, z_mid=z_mid, amp_hand=amp_hand, omega=omega, phase_offset=phase_off_R, num_nodes=36
            )

            objects_3d["left_battle_rope"] = {
                "x": float(wrist_L[0]),
                "y": float(wrist_L[1]),
                "z": float(wrist_L[2]),
                "anchor_x": float(anchor_L[0]),
                "anchor_y": float(anchor_L[1]),
                "anchor_z": float(anchor_L[2]),
                "wave_points": wave_L,
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }
            objects_3d["right_battle_rope"] = {
                "x": float(wrist_R[0]),
                "y": float(wrist_R[1]),
                "z": float(wrist_R[2]),
                "anchor_x": float(anchor_R[0]),
                "anchor_y": float(anchor_R[1]),
                "anchor_z": float(anchor_R[2]),
                "wave_points": wave_R,
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        elif "resistance_band" in equipment_types or "band" in equipment_types or "suspension" in equipment_types:
            is_trx = "suspension" in equipment_types
            default_anchor = [0.0, 0.85, 2.15] if is_trx else [0.0, 0.05, 0.02]
            for eq in spec.get("equipment", []):
                if eq.get("anchor_point"):
                    default_anchor = list(eq["anchor_point"])
            anc_L = _vec(default_anchor[0] - half_grip, default_anchor[1], default_anchor[2])
            anc_R = _vec(default_anchor[0] + half_grip, default_anchor[1], default_anchor[2])
            objects_3d["left_tether"] = {
                "x": float(wrist_L[0]),
                "y": float(wrist_L[1]),
                "z": float(wrist_L[2]),
                "anchor_x": float(anc_L[0]),
                "anchor_y": float(anc_L[1]),
                "anchor_z": float(anc_L[2]),
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }
            objects_3d["right_tether"] = {
                "x": float(wrist_R[0]),
                "y": float(wrist_R[1]),
                "z": float(wrist_R[2]),
                "anchor_x": float(anc_R[0]),
                "anchor_y": float(anc_R[1]),
                "anchor_z": float(anc_R[2]),
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        elif "medicine_ball" in equipment_types:
            ball_rad = 0.14
            for eq in spec.get("equipment", []):
                if normalize_equipment_type(eq.get("type", "")) == "medicine_ball" and eq.get("ball_radius_m"):
                    ball_rad = float(eq["ball_radius_m"])

            grasp_active = any(
                c.get("mode") == "grasp" and c.get("target") == "medicine_ball" and is_contact_active(c, t)
                for c in spec.get("contacts", [])
            )
            mb_eq = equip_frame.get("medicine_ball", {})
            if grasp_active:
                if mb_eq and mb_eq.get("z") is not None:
                    bx = float(mb_eq.get("x") or 0.0)
                    by = float(mb_eq.get("y") or 0.24)
                    bz = max(ball_rad, float(mb_eq.get("z") or 0.90))
                else:
                    mid_w = 0.5 * (wrist_L + wrist_R)
                    bx, by, bz = float(mid_w[0]), float(mid_w[1]), max(ball_rad, float(mid_w[2]))

                grip_L = _vec(bx - ball_rad * 0.92, by, bz)
                grip_R = _vec(bx + ball_rad * 0.92, by, bz)
                elbow_L, wrist_L = solve_two_bone_ik(
                    shoulder_L, grip_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(-0.6, 0.3, -0.2)
                )
                elbow_R, wrist_R = solve_two_bone_ik(
                    shoulder_R, grip_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(0.6, 0.3, -0.2)
                )
                solved_mid = 0.5 * (wrist_L + wrist_R)
                by, bz = float(solved_mid[1]), max(ball_rad, float(solved_mid[2]))
                wrist_L = _vec(bx - ball_rad * 0.92, by, bz)
                wrist_R = _vec(bx + ball_rad * 0.92, by, bz)
            else:
                bx = float(mb_eq.get("x") or 0.0)
                by = float(mb_eq.get("y") or 0.32)
                bz = max(ball_rad, float(mb_eq.get("z") or ball_rad))

            objects_3d["medicine_ball"] = {
                "x": float(bx),
                "y": float(by),
                "z": float(bz),
                "radius_m": ball_rad,
                "grasp_active": 1.0 if grasp_active else 0.0,
                "pitch_deg": 0.0,
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        elif "kettlebell" in equipment_types:
            kb_eq = equip_frame.get("kettlebell", {})
            if kb_eq and kb_eq.get("z") is not None:
                kx = float(kb_eq.get("x") or 0.0)
                ky = float(kb_eq.get("y") or 0.22)
                kz = max(0.12, float(kb_eq.get("z") or 0.55))
                kpitch = float(kb_eq.get("pitch_deg") or 0.0)
            else:
                mid_w = 0.5 * (wrist_L + wrist_R)
                kx, ky, kz = float(mid_w[0]), float(mid_w[1]), max(0.12, float(mid_w[2]))
                kpitch = 0.0

            grip_L = _vec(kx - 0.055, ky, kz)
            grip_R = _vec(kx + 0.055, ky, kz)
            elbow_L, wrist_L = solve_two_bone_ik(
                shoulder_L, grip_L, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(-0.6, 0.2, -0.2)
            )
            elbow_R, wrist_R = solve_two_bone_ik(
                shoulder_R, grip_R, RIG_METRICS["upper_arm_len"], RIG_METRICS["forearm_len"], _vec(0.6, 0.2, -0.2)
            )
            solved_mid = 0.5 * (wrist_L + wrist_R)
            ky, kz = float(solved_mid[1]), max(0.12, float(solved_mid[2]))
            wrist_L = _vec(kx - 0.055, ky, kz)
            wrist_R = _vec(kx + 0.055, ky, kz)

            objects_3d["kettlebell"] = {
                "x": float(kx),
                "y": float(ky),
                "z": float(kz),
                "pitch_deg": float(kpitch),
                "roll_deg": 0.0,
                "yaw_deg": 0.0,
            }

        hand_L = wrist_L.copy()
        hand_R = wrist_R.copy()

        for db_name, side_wrist in [
            ("left_dumbbell", wrist_L),
            ("right_dumbbell", wrist_R),
        ]:
            if db_name in equip_frame or "dumbbell" in equipment_types:
                objects_3d[db_name] = {
                    "x": float(side_wrist[0]),
                    "y": float(side_wrist[1]),
                    "z": float(side_wrist[2]),
                    "pitch_deg": 0.0,
                    "roll_deg": 0.0,
                    "yaw_deg": 0.0,
                }

    joints_map = {
        "root": _vec(pelvis[0], pelvis[1], 0.0),
        "pelvis": pelvis,
        "spine": spine,
        "chest": chest,
        "neck": neck,
        "head": head,
        "clavicle_L": clavicle_L,
        "shoulder_L": shoulder_L,
        "elbow_L": elbow_L,
        "wrist_L": wrist_L,
        "hand_L": hand_L,
        "clavicle_R": clavicle_R,
        "shoulder_R": shoulder_R,
        "elbow_R": elbow_R,
        "wrist_R": wrist_R,
        "hand_R": hand_R,
        "hip_L": hip_L,
        "knee_L": knee_L,
        "ankle_L": ankle_L,
        "toe_L": toe_L,
        "hip_R": hip_R,
        "knee_R": knee_R,
        "ankle_R": ankle_R,
        "toe_R": toe_R,
    }

    grasp_errors = []
    for contact in spec.get("contacts", []):
        if not is_contact_active(contact, t):
            continue
        mode = contact.get("mode")
        bp = contact.get("body_part", "")
        tgt = contact.get("target", "")
        if mode in ("grasp", "tethered_wave"):
            h_pos = joints_map["hand_L"] if "left" in bp else joints_map["hand_R"]
            if tgt in ("barbell", "cable_bar") and tgt in objects_3d:
                bx, by, bz = objects_3d[tgt]["x"], objects_3d[tgt]["y"], objects_3d[tgt]["z"]
                gx = bx - half_grip if "left" in bp else bx + half_grip
                grasp_errors.append(float(np.linalg.norm(h_pos - _vec(gx, by, bz))))
            elif tgt == "medicine_ball" and "medicine_ball" in objects_3d:
                mb = objects_3d["medicine_ball"]
                rad = float(mb.get("radius_m", 0.14))
                gx = mb["x"] - rad * 0.92 if "left" in bp else mb["x"] + rad * 0.92
                grasp_errors.append(float(np.linalg.norm(h_pos - _vec(gx, mb["y"], mb["z"]))))
            elif tgt == "kettlebell" and "kettlebell" in objects_3d:
                kb = objects_3d["kettlebell"]
                gx = kb["x"] - 0.055 if "left" in bp else kb["x"] + 0.055
                grasp_errors.append(float(np.linalg.norm(h_pos - _vec(gx, kb["y"], kb["z"]))))
            elif tgt in objects_3d:
                ox, oy, oz = objects_3d[tgt]["x"], objects_3d[tgt]["y"], objects_3d[tgt]["z"]
                grasp_errors.append(float(np.linalg.norm(h_pos - _vec(ox, oy, oz))))

    min_foot_z = min(float(joints_map["toe_L"][2]), float(joints_map["toe_R"][2]), float(joints_map["ankle_L"][2]))
    plate_clearance = 1.0
    if "barbell" in objects_3d:
        plate_clearance = objects_3d["barbell"]["z"] - 0.225
    elif "medicine_ball" in objects_3d:
        plate_clearance = objects_3d["medicine_ball"]["z"] - float(objects_3d["medicine_ball"].get("radius_m", 0.14))

    diagnostics = {
        "max_grasp_error_m": round(max(grasp_errors) if grasp_errors else 0.0, 5),
        "min_foot_z_m": round(min_foot_z, 4),
        "min_plate_floor_clearance_m": round(plate_clearance, 4),
    }

    serialized_joints = {
        k: [round(float(v[0]), 4), round(float(v[1]), 4), round(float(v[2]), 4)]
        for k, v in joints_map.items()
    }
    serialized_objects = {}
    for k, v in objects_3d.items():
        serialized_objects[k] = {
            ok: (ov if isinstance(ov, list) else round(float(ov), 4))
            for ok, ov in v.items()
        }
    return serialized_joints, serialized_objects, diagnostics
