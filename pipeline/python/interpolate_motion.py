"""
Phase-aware motion interpolation and full-body 3D kinematic expansion.

Usage:
  python3 python/interpolate_motion.py [motion_spec.json] [output_expanded.json]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kinematics_engine import solve_frame_pose


def apply_easing(alpha: float, mode: str = "ease_in_out") -> float:
    alpha = max(0.0, min(1.0, float(alpha)))
    if mode == "linear":
        return alpha
    if mode == "hold":
        return 0.0 if alpha < 0.999 else 1.0
    if mode == "ease_in":
        return alpha * alpha
    if mode == "ease_out":
        return 1.0 - (1.0 - alpha) * (1.0 - alpha)
    if mode == "explosive":
        # Fast acceleration with smooth lockout (cubic ease-out)
        return 1.0 - pow(1.0 - alpha, 3.0)
    # Default smooth cosine ease_in_out
    return 0.5 * (1.0 - math.cos(math.pi * alpha))


def get_phase_At_time(phases: List[dict], t: float) -> dict:
    for p in phases:
        if float(p["start_t"]) <= t <= float(p["end_t"]) + 1e-6:
            return p
    return phases[-1] if phases else {"name": "default", "easing": "ease_in_out"}


def infer_easing_from_phase(phase: dict) -> str:
    if phase.get("easing"):
        return phase["easing"]
    hint = (phase.get("tempo_hint") or "").lower()
    name = (phase.get("name") or "").lower()
    if "hold" in hint or "pause" in hint or "lockout" in name:
        return "ease_in_out"
    if "explosive" in hint or "drive" in hint or "second_pull" in name or "jerk_drive" in name:
        return "explosive"
    return "ease_in_out"


def interp_track(track: List[dict], fps: int, duration: float, phases: Optional[List[dict]] = None) -> List[dict]:
    frames = []
    total = int(round(fps * duration))
    if not track:
        return frames

    # Collect all keys across track points
    all_keys = set()
    for pt in track:
        all_keys.update(pt.keys())
    all_keys.discard("t")
    sorted_keys = sorted(all_keys)

    for i in range(total):
        t = round(i / fps, 4)
        prev = track[0]
        nxt = track[-1]
        for j in range(len(track) - 1):
            if float(track[j]["t"]) <= t <= float(track[j + 1]["t"]) + 1e-9:
                prev = track[j]
                nxt = track[j + 1]
                break
        span = max(1e-6, float(nxt["t"]) - float(prev["t"]))
        raw_alpha = max(0.0, min(1.0, (t - float(prev["t"])) / span))

        phase = get_phase_At_time(phases or [], t)
        easing_mode = infer_easing_from_phase(phase)
        alpha = apply_easing(raw_alpha, easing_mode)

        item = {"t": t, "frame": i + 1, "phase": phase.get("name", "default")}
        for key in sorted_keys:
            pv = prev.get(key)
            nv = nxt.get(key)
            if pv is None and nv is None:
                item[key] = None
            elif pv is None:
                item[key] = float(nv)
            elif nv is None:
                item[key] = float(pv)
            else:
                item[key] = round(float(pv) + (float(nv) - float(pv)) * alpha, 4)
        frames.append(item)
    return frames


def expand_motion_spec(path: str) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    fps = int(spec["timing"]["fps"])
    dur = float(spec["timing"]["duration_sec"])
    phases = spec.get("phases", [])
    total_frames = int(round(fps * dur))

    out = {
        "exercise_id": spec.get("exercise_id", spec["exercise_name"].lower().replace(" ", "_")),
        "exercise_name": spec["exercise_name"],
        "variation": spec.get("variation", ""),
        "movement_pattern": spec.get("movement_pattern", ""),
        "source_reference": spec.get("source_reference", {}),
        "muscles": spec.get("muscles", {"primary": [], "secondary": []}),
        "setup": spec.get("setup", {}),
        "equipment": spec.get("equipment", []),
        "laterality": spec.get("laterality", "bilateral"),
        "fps": fps,
        "duration_sec": dur,
        "total_frames": total_frames,
        "phases": phases,
        "joints": {},
        "root_trajectory": [],
        "objects": {},
        "skeleton_frames": [],
        "diagnostics_summary": {},
    }

    for jt in spec.get("joint_targets", []):
        out["joints"][jt["joint"]] = interp_track(jt["track"], fps, dur, phases)

    if spec.get("root_trajectory"):
        out["root_trajectory"] = interp_track(spec["root_trajectory"], fps, dur, phases)

    raw_objects = {}
    for eq in spec.get("equipment_path", []):
        raw_objects[eq["object"]] = interp_track(eq["track"], fps, dur, phases)

    # Solve 3D full-body pose and constrained equipment transforms per frame
    solved_object_tracks: Dict[str, List[dict]] = {}
    max_grasp_err = 0.0
    min_foot_z = 10.0
    min_plate_clear = 10.0

    for i in range(total_frames):
        t = round(i / fps, 4)
        phase = get_phase_At_time(phases, t)
        jf = {jname: jtrack[i] for jname, jtrack in out["joints"].items() if i < len(jtrack)}
        rf = out["root_trajectory"][i] if i < len(out["root_trajectory"]) else None
        ef = {oname: otrack[i] for oname, otrack in raw_objects.items() if i < len(otrack)}

        joints_3d, objects_3d, diag = solve_frame_pose(spec, t, jf, rf, ef)
        max_grasp_err = max(max_grasp_err, diag["max_grasp_error_m"])
        min_foot_z = min(min_foot_z, diag["min_foot_z_m"])
        min_plate_clear = min(min_plate_clear, diag["min_plate_floor_clearance_m"])

        out["skeleton_frames"].append({
            "frame": i + 1,
            "t": t,
            "phase": phase.get("name", ""),
            "joints_3d": joints_3d,
            "diagnostics": diag,
        })

        for oname, otransform in objects_3d.items():
            solved_object_tracks.setdefault(oname, []).append({
                "frame": i + 1,
                "t": t,
                "phase": phase.get("name", ""),
                **otransform,
            })

    out["objects"] = solved_object_tracks
    out["diagnostics_summary"] = {
        "max_grasp_error_m": round(max_grasp_err, 5),
        "min_foot_z_m": round(min_foot_z, 4),
        "min_plate_floor_clearance_m": round(min_plate_clear, 4),
    }
    return out


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[1] / "samples"
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (base_dir / "dumbbell_lateral_raise.motion_spec.json")
    out_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else in_path.with_name(in_path.name.replace(".motion_spec.json", ".expanded.json"))
    )
    expanded = expand_motion_spec(str(in_path))
    out_path.write_text(json.dumps(expanded, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Expanded {in_path.name} -> {out_path} ({expanded['total_frames']} frames @ {expanded['fps']} fps)")
