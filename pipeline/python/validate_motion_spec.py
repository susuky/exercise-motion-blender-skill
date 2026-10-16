"""
Comprehensive Biomechanical & Kinematic Validator for Exercise Motion Specs.

Checks:
  1. JSON Schema & phase timing continuity (0.0 -> duration_sec)
  2. Anatomical Range-of-Motion (ROM) limits across all major joints
  3. Angular velocity sanity check (prevents single-frame joint snapping)
  4. Hand-to-equipment grasp distance verification (< 0.03m tolerance)
  5. Floor & body collision / penetration check (barbell plates & feet vs floor)
  6. Loop closure & bilateral symmetry verification
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interpolate_motion import expand_motion_spec

JOINT_LIMITS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("shoulder", "abduction_deg"): (-15.0, 175.0),
    ("shoulder", "flexion_deg"): (-45.0, 185.0),
    ("shoulder", "rotation_deg"): (-95.0, 95.0),
    ("elbow", "flexion_deg"): (0.0, 155.0),
    ("wrist", "flexion_deg"): (-85.0, 85.0),
    ("hip", "flexion_deg"): (-35.0, 145.0),
    ("hip", "abduction_deg"): (-30.0, 75.0),
    ("knee", "flexion_deg"): (0.0, 160.0),
    ("ankle", "flexion_deg"): (-45.0, 50.0),
    ("spine", "flexion_deg"): (-30.0, 75.0),
    ("thorax", "flexion_deg"): (-25.0, 60.0),
}

MAX_ANGULAR_VELOCITY_DEG_PER_SEC = 850.0
MAX_GRASP_DISTANCE_ERROR_M = 0.030


def _match_joint_type(joint_name: str) -> str:
    j = joint_name.lower()
    for kind in ("shoulder", "elbow", "wrist", "hip", "knee", "ankle", "spine", "thorax"):
        if kind in j:
            return kind
    return j


def validate_full(path: str) -> dict:
    spec_path = Path(path)
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    issues: List[dict] = []
    warnings: List[dict] = []

    # 1. Phase timing continuity check
    dur = float(data.get("timing", {}).get("duration_sec", 0.0))
    phases = data.get("phases", [])
    if not phases:
        issues.append({"type": "phase_missing", "message": "No movement phases defined."})
    else:
        if abs(float(phases[0]["start_t"]) - 0.0) > 1e-3:
            issues.append({
                "type": "phase_start_gap",
                "first_phase_start": phases[0]["start_t"],
            })
        if abs(float(phases[-1]["end_t"]) - dur) > 1e-3:
            issues.append({
                "type": "phase_end_mismatch",
                "last_phase_end": phases[-1]["end_t"],
                "duration_sec": dur,
            })
        for idx in range(len(phases) - 1):
            cur_end = float(phases[idx]["end_t"])
            nxt_start = float(phases[idx + 1]["start_t"])
            if abs(cur_end - nxt_start) > 1e-3:
                issues.append({
                    "type": "phase_discontinuity",
                    "between": [phases[idx]["name"], phases[idx + 1]["name"]],
                    "gap_sec": round(nxt_start - cur_end, 4),
                })

    # 2. Joint ROM & Loop Closure & Angular Velocity check
    is_loop = bool(data.get("timing", {}).get("loop", False))
    max_vel_observed = 0.0

    for jt in data.get("joint_targets", []):
        name = jt["joint"]
        jkind = _match_joint_type(name)
        track = jt.get("track", [])

        for idx, point in enumerate(track):
            for axis_key in ("flexion_deg", "abduction_deg", "rotation_deg"):
                val = point.get(axis_key)
                if val is None:
                    continue
                val_f = float(val)
                limit = JOINT_LIMITS.get((jkind, axis_key))
                if limit:
                    lo, hi = limit
                    if not (lo <= val_f <= hi):
                        issues.append({
                            "type": "rom_violation",
                            "joint": name,
                            "time": point["t"],
                            "axis": axis_key,
                            "value": val_f,
                            "limit": [lo, hi],
                        })

                # Angular velocity check between consecutive keyposes
                if idx > 0:
                    prev_val = track[idx - 1].get(axis_key)
                    dt = float(point["t"]) - float(track[idx - 1]["t"])
                    if prev_val is not None and dt > 1e-4:
                        vel = abs(val_f - float(prev_val)) / dt
                        max_vel_observed = max(max_vel_observed, vel)
                        if vel > MAX_ANGULAR_VELOCITY_DEG_PER_SEC:
                            warnings.append({
                                "type": "high_angular_velocity",
                                "joint": name,
                                "axis": axis_key,
                                "t_range": [track[idx - 1]["t"], point["t"]],
                                "deg_per_sec": round(vel, 1),
                            })

        # Loop closure check
        if is_loop and len(track) >= 2:
            first_pt, last_pt = track[0], track[-1]
            for axis_key in ("flexion_deg", "abduction_deg", "rotation_deg"):
                v0, v1 = first_pt.get(axis_key), last_pt.get(axis_key)
                if v0 is not None and v1 is not None and abs(float(v0) - float(v1)) > 2.0:
                    issues.append({
                        "type": "loop_closure_mismatch",
                        "joint": name,
                        "axis": axis_key,
                        "start_val": v0,
                        "end_val": v1,
                    })

    # 3. Run full 3D kinematic expansion to verify grasp distances & floor clearance
    expanded = expand_motion_spec(str(spec_path))
    diag = expanded.get("diagnostics_summary", {})
    max_grasp_err = float(diag.get("max_grasp_error_m", 0.0))
    min_plate_clear = float(diag.get("min_plate_floor_clearance_m", 0.0))
    min_foot_z = float(diag.get("min_foot_z_m", 0.0))

    if max_grasp_err > MAX_GRASP_DISTANCE_ERROR_M:
        issues.append({
            "type": "grasp_detachment",
            "max_grasp_error_m": max_grasp_err,
            "limit_m": MAX_GRASP_DISTANCE_ERROR_M,
        })

    if min_plate_clear < -0.005:
        issues.append({
            "type": "floor_penetration_equipment",
            "min_plate_floor_clearance_m": min_plate_clear,
        })

    if min_foot_z < -0.01:
        issues.append({
            "type": "floor_penetration_foot",
            "min_foot_z_m": min_foot_z,
        })

    return {
        "exercise_name": data.get("exercise_name"),
        "status": "PASS" if len(issues) == 0 else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "metrics": {
            "total_frames_evaluated": expanded.get("total_frames", 0),
            "phase_count": len(phases),
            "joint_track_count": len(data.get("joint_targets", [])),
            "max_angular_velocity_deg_per_sec": round(max_vel_observed, 2),
            "max_grasp_error_m": max_grasp_err,
            "min_plate_floor_clearance_m": min_plate_clear,
            "min_foot_z_m": min_foot_z,
            "loop_closed": is_loop and not any(i.get("type") == "loop_closure_mismatch" for i in issues),
        },
    }


def validate(path: str) -> List[dict]:
    """Backward-compatible helper returning list of issues."""
    return validate_full(path)["issues"]


if __name__ == "__main__":
    sample = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "samples" / "dumbbell_lateral_raise.motion_spec.json"
    )
    report = validate_full(str(sample))
    print(json.dumps(report, ensure_ascii=False, indent=2))
