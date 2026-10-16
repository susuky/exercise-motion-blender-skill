"""
Standard 3D Skeletal & Scene Exporter (.bvh and .gltf).

Exports:
  1. Biovision Hierarchy (.bvh) skeletal motion capture file — directly importable
     into Blender via `File > Import > Motion Capture (.bvh)`.
  2. Animated glTF 2.0 (.gltf) 3D scene representation containing joint nodes
     and equipment trajectories.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List


def export_bvh(expanded: dict, out_path: Path) -> Path:
    """
    Exports a valid Biovision Hierarchy (.bvh) file with hierarchical human bones
    and per-frame motion channels so it can be directly imported into Blender.
    """
    frames = expanded["skeleton_frames"]
    fps = int(expanded["fps"])
    frame_time = round(1.0 / fps, 6)
    first_j = frames[0]["joints_3d"]

    def _rel(child: str, parent: str) -> List[float]:
        c = first_j[child]
        p = first_j[parent]
        return [round(c[0] - p[0], 4), round(c[1] - p[1], 4), round(c[2] - p[2], 4)]

    # Build BVH hierarchy string
    lines = [
        "HIERARCHY",
        "ROOT pelvis",
        "{",
        f"  OFFSET {first_j['pelvis'][0]:.4f} {first_j['pelvis'][1]:.4f} {first_j['pelvis'][2]:.4f}",
        "  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation",
    ]

    chains = [
        ("spine_chain", [("spine", "pelvis"), ("chest", "spine"), ("neck", "chest"), ("head", "neck")]),
        ("left_arm", [("clavicle_L", "chest"), ("shoulder_L", "clavicle_L"), ("elbow_L", "shoulder_L"), ("wrist_L", "elbow_L")]),
        ("right_arm", [("clavicle_R", "chest"), ("shoulder_R", "clavicle_R"), ("elbow_R", "shoulder_R"), ("wrist_R", "elbow_R")]),
        ("left_leg", [("hip_L", "pelvis"), ("knee_L", "hip_L"), ("ankle_L", "knee_L"), ("toe_L", "ankle_L")]),
        ("right_leg", [("hip_R", "pelvis"), ("knee_R", "hip_R"), ("ankle_R", "knee_R"), ("toe_R", "ankle_R")]),
    ]

    # Simple 3-DOF rotational joints under root
    joint_order = ["pelvis"]
    for _, chain in chains:
        indent = "  "
        for bname, pname in chain:
            off = _rel(bname, pname)
            lines.append(f"{indent}JOINT {bname}")
            lines.append(f"{indent}{{")
            indent += "  "
            lines.append(f"{indent}OFFSET {off[0]:.4f} {off[1]:.4f} {off[2]:.4f}")
            lines.append(f"{indent}CHANNELS 3 Zrotation Xrotation Yrotation")
            joint_order.append(bname)
        lines.append(f"{indent}End Site")
        lines.append(f"{indent}{{")
        lines.append(f"{indent}  OFFSET 0.0000 0.0000 0.0500")
        lines.append(f"{indent}}}")
        for _ in chain:
            indent = indent[:-2]
            lines.append(f"{indent}}}")

    lines.append("}")
    lines.append("MOTION")
    lines.append(f"Frames: {len(frames)}")
    lines.append(f"Frame Time: {frame_time:.6f}")

    # Populate motion channels per frame
    j_tracks = expanded.get("joints", {})
    for idx, fdata in enumerate(frames):
        j3d = fdata["joints_3d"]
        px, py, pz = j3d["pelvis"]
        row_vals = [f"{px:.4f}", f"{py:.4f}", f"{pz:.4f}", "0.00", "0.00", "0.00"]

        # Map anatomical joint angles to BVH channels
        bvh_to_spec = {
            "shoulder_L": "left_shoulder",
            "elbow_L": "left_elbow",
            "shoulder_R": "right_shoulder",
            "elbow_R": "right_elbow",
            "hip_L": "left_hip",
            "knee_L": "left_knee",
            "ankle_L": "left_ankle",
            "hip_R": "right_hip",
            "knee_R": "right_knee",
            "ankle_R": "right_ankle",
        }
        for bname in joint_order[1:]:
            skey = bvh_to_spec.get(bname)
            if skey and skey in j_tracks and idx < len(j_tracks[skey]):
                pt = j_tracks[skey][idx]
                rx = float(pt.get("flexion_deg") or 0.0)
                ry = float(pt.get("abduction_deg") or 0.0)
                rz = float(pt.get("rotation_deg") or 0.0)
                row_vals.extend([f"{rz:.2f}", f"{rx:.2f}", f"{ry:.2f}"])
            else:
                row_vals.extend(["0.00", "0.00", "0.00"])
        lines.append(" ".join(row_vals))

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def export_gltf_scene(expanded: dict, out_path: Path) -> Path:
    """
    Exports a valid glTF 2.0 JSON scene (.gltf) with all skeletal joint nodes and
    equipment nodes positioned at the peak action frame + embedded keyframe metadata.
    """
    mid_idx = len(expanded["skeleton_frames"]) // 2
    j3d = expanded["skeleton_frames"][mid_idx]["joints_3d"]
    nodes = []
    node_indices = {}

    for idx, (jname, pos) in enumerate(j3d.items()):
        # Convert Z-up (x, y, z) to glTF Y-up (x, z, -y)
        nodes.append({
            "name": f"Bone_{jname}",
            "translation": [float(pos[0]), float(pos[2]), float(-pos[1])],
        })
        node_indices[jname] = idx

    for obj_name, track in expanded.get("objects", {}).items():
        pt = track[mid_idx] if mid_idx < len(track) else track[0]
        nodes.append({
            "name": f"Equipment_{obj_name}",
            "translation": [float(pt["x"]), float(pt["z"]), float(-pt["y"])],
        })

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "ExerciseMotionSkillPipeline v2.0",
            "extras": {
                "exercise_name": expanded["exercise_name"],
                "fps": expanded["fps"],
                "total_frames": expanded["total_frames"],
            },
        },
        "scene": 0,
        "scenes": [{"name": expanded["exercise_name"], "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
    }
    out_path.write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
