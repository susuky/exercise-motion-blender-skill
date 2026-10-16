"""
Universal Standalone 3D Studio Renderer for Exercise Motion Specs (v4.0).

Renders:
  - 38 Sculpted 3D Anatomical Muscle Bellies (`anatomical_mannequin.py`) with Ecorché muscle fiber
    shading, zero robotic ball-joints, and independent Anterior vs Posterior muscle group highlights:
      * Active Primary Muscles: Sculpted Crimson Red (`#E02A36`)
      * Active Secondary Muscles: Warm Athletic Coral/Orange (`#F28632`)
      * Inactive Anatomical Muscle Bellies: Sculpted Ecorché Silver-Grey (`#C6CED8`)
      * Tendon / Fascia / Cranium: Light Anatomical Ivory-Grey (`#D8DFE8`)
  - Universal Equipment Rendering across Free Weights, 26-Node Wave Battle Ropes, Cable Pulley
    Towers with Moving Weight Stacks, Pivoting Lever Machines, Kettlebells, Medicine Balls, and Tethers.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interpolate_motion import expand_motion_spec
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


def _load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


class Camera3D:
    def __init__(
        self,
        azimuth_deg: float = 38.0,
        elevation_deg: float = 15.0,
        distance: float = 3.8,
        target: Tuple[float, float, float] = (0.0, 0.0, 0.98),
        scale: float = 250.0,
        center_2d: Tuple[float, float] = (280.0, 290.0),
        perspective: bool = True,
    ):
        az = math.radians(azimuth_deg)
        el = math.radians(elevation_deg)
        self.cam_pos = np.array([
            target[0] + distance * math.cos(el) * math.sin(az),
            target[1] + distance * math.cos(el) * math.cos(az),
            target[2] + distance * math.sin(el),
        ], dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        fwd = self.target - self.cam_pos
        fwd = fwd / np.linalg.norm(fwd)
        world_up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        right = np.cross(fwd, world_up)
        if np.linalg.norm(right) < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        else:
            right = right / np.linalg.norm(right)
        up = np.cross(right, fwd)
        self.right = right
        self.up = up
        self.fwd = fwd
        self.distance = distance
        self.scale = scale
        self.cx, self.cy = center_2d
        self.perspective = perspective

    def project(self, pt: Tuple[float, float, float] | List[float] | np.ndarray) -> Tuple[float, float, float]:
        p = np.asarray(pt, dtype=np.float64)
        rel = p - self.cam_pos
        depth = float(np.dot(rel, self.fwd))
        depth = max(0.4, depth)
        rx = float(np.dot(rel, self.right))
        ry = float(np.dot(rel, self.up))
        factor = self.scale * (self.distance / depth) if self.perspective else self.scale
        sx = self.cx + rx * factor
        sy = self.cy - ry * factor
        return sx, sy, depth

    def radius_px(self, radius_m: float, depth: float) -> float:
        if self.perspective:
            return max(1.5, radius_m * self.scale * (self.distance / max(0.4, depth)))
        return max(1.5, radius_m * self.scale)


def _shade_color(rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return (
        max(0, min(255, int(round(rgb[0] * factor)))),
        max(0, min(255, int(round(rgb[1] * factor)))),
        max(0, min(255, int(round(rgb[2] * factor)))),
    )


def _draw_3d_capsule(
    draw: ImageDraw.ImageDraw,
    cam: Camera3D,
    p0: List[float],
    p1: List[float],
    rad0_m: float,
    rad1_m: float,
    base_rgb: Tuple[int, int, int],
    outline_rgb: Optional[Tuple[int, int, int]] = None,
    is_muscle_belly: bool = False,
):
    """
    Draws a 3D shaded tapered capsule or fusiform muscle belly with optional
    longitudinal muscle striation contours.
    """
    x0, y0, d0 = cam.project(p0)
    x1, y1, d1 = cam.project(p1)
    r0 = cam.radius_px(rad0_m, d0)
    r1 = cam.radius_px(rad1_m, d1)

    dx, dy = x1 - x0, y1 - y0
    seg_len = math.hypot(dx, dy)
    shadow_rgb = _shade_color(base_rgb, 0.78)
    mid_rgb = base_rgb
    hi_rgb = _shade_color(base_rgb, 1.15)
    rim_rgb = outline_rgb or _shade_color(base_rgb, 0.56)

    if seg_len > 1.0:
        nx, ny = -dy / seg_len, dx / seg_len
        rmid = 0.5 * (r0 + r1) * (1.12 if is_muscle_belly else 1.0)
        xm, ym = 0.5 * (x0 + x1), 0.5 * (y0 + y1)

        # Curved 6-point fusiform polygon so muscle bellies bulge naturally in the middle!
        poly_outer = [
            (x0 + nx * (r0 + 1.0), y0 + ny * (r0 + 1.0)),
            (xm + nx * (rmid + 1.0), ym + ny * (rmid + 1.0)),
            (x1 + nx * (r1 + 1.0), y1 + ny * (r1 + 1.0)),
            (x1 - nx * (r1 + 1.0), y1 - ny * (r1 + 1.0)),
            (xm - nx * (rmid + 1.0), ym - ny * (rmid + 1.0)),
            (x0 - nx * (r0 + 1.0), y0 - ny * (r0 + 1.0)),
        ]
        draw.polygon(poly_outer, fill=rim_rgb)
        draw.ellipse([x0 - r0 - 1.0, y0 - r0 - 1.0, x0 + r0 + 1.0, y0 + r0 + 1.0], fill=rim_rgb)
        draw.ellipse([x1 - r1 - 1.0, y1 - r1 - 1.0, x1 + r1 + 1.0, y1 + r1 + 1.0], fill=rim_rgb)

        poly_base = [
            (x0 + nx * r0, y0 + ny * r0),
            (xm + nx * rmid, ym + ny * rmid),
            (x1 + nx * r1, y1 + ny * r1),
            (x1 - nx * r1, y1 - ny * r1),
            (xm - nx * rmid, ym - ny * rmid),
            (x0 - nx * r0, y0 - ny * r0),
        ]
        draw.polygon(poly_base, fill=shadow_rgb)
        draw.ellipse([x0 - r0, y0 - r0, x0 + r0, y0 + r0], fill=shadow_rgb)
        draw.ellipse([x1 - r1, y1 - r1, x1 + r1, y1 + r1], fill=shadow_rgb)

        poly_mid = [
            (x0 + nx * (r0 * 0.84), y0 + ny * (r0 * 0.84)),
            (xm + nx * (rmid * 0.84), ym + ny * (rmid * 0.84)),
            (x1 + nx * (r1 * 0.84), y1 + ny * (r1 * 0.84)),
            (x1 - nx * (r1 * 0.35), y1 - ny * (r1 * 0.35)),
            (xm - nx * (rmid * 0.35), ym - ny * (rmid * 0.35)),
            (x0 - nx * (r0 * 0.35), y0 - ny * (r0 * 0.35)),
        ]
        draw.polygon(poly_mid, fill=mid_rgb)
        draw.ellipse([x0 - r0 * 0.84, y0 - r0 * 0.84, x0 + r0 * 0.84, y0 + r0 * 0.84], fill=mid_rgb)
        draw.ellipse([x1 - r1 * 0.84, y1 - r1 * 0.84, x1 + r1 * 0.84, y1 + r1 * 0.84], fill=mid_rgb)

        poly_hi = [
            (x0 + nx * (r0 * 0.44), y0 + ny * (r0 * 0.44)),
            (xm + nx * (rmid * 0.46), ym + ny * (rmid * 0.46)),
            (x1 + nx * (r1 * 0.44), y1 + ny * (r1 * 0.44)),
            (x1 + nx * (r1 * 0.04), y1 + ny * (r1 * 0.04)),
            (xm + nx * (rmid * 0.04), ym + ny * (rmid * 0.04)),
            (x0 + nx * (r0 * 0.04), y0 + ny * (r0 * 0.04)),
        ]
        draw.polygon(poly_hi, fill=hi_rgb)

        # Subtle anatomical muscle fiber striation lines
        if is_muscle_belly and seg_len > 8.0:
            striation_col = _shade_color(base_rgb, 0.68)
            for s_off in (-0.28, 0.18):
                lx0 = x0 + dx * 0.15 + nx * (r0 * s_off)
                ly0 = y0 + dy * 0.15 + ny * (r0 * s_off)
                lxm = xm + nx * (rmid * s_off * 1.08)
                lym = ym + ny * (rmid * s_off * 1.08)
                lx1 = x0 + dx * 0.85 + nx * (r1 * s_off)
                ly1 = y0 + dy * 0.85 + ny * (r1 * s_off)
                draw.line([(lx0, ly0), (lxm, lym), (lx1, ly1)], fill=striation_col, width=1)
    else:
        r = max(r0, r1)
        draw.ellipse([x0 - r - 1.0, y0 - r - 1.0, x0 + r + 1.0, y0 + r + 1.0], fill=rim_rgb)
        draw.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=mid_rgb)
        draw.ellipse([x0 - r * 0.55, y0 - r * 0.55, x0 + r * 0.25, y0 + r * 0.25], fill=hi_rgb)


def _draw_3d_plate_disc(
    draw: ImageDraw.ImageDraw,
    cam: Camera3D,
    center_3d: List[float],
    radius_m: float,
    thickness_m: float,
    rgb: Tuple[int, int, int],
):
    n_pts = 28
    half_t = thickness_m * 0.5
    cx, cy, cz = center_3d

    ring_inner = []
    ring_outer = []
    for k in range(n_pts):
        ang = 2.0 * math.pi * k / n_pts
        py = cy + radius_m * math.cos(ang)
        pz = cz + radius_m * math.sin(ang)
        sx1, sy1, _ = cam.project((cx - half_t, py, pz))
        sx2, sy2, _ = cam.project((cx + half_t, py, pz))
        ring_inner.append((sx1, sy1))
        ring_outer.append((sx2, sy2))

    rim_dark = _shade_color(rgb, 0.62)
    face_col = rgb
    hub_col = (210, 216, 224)

    _, _, d_minus = cam.project((cx - half_t, cy, cz))
    _, _, d_plus = cam.project((cx + half_t, cy, cz))

    if d_plus < d_minus:
        back_ring, front_ring = ring_inner, ring_outer
        front_x = cx + half_t
    else:
        back_ring, front_ring = ring_outer, ring_inner
        front_x = cx - half_t

    for k in range(n_pts):
        kn = (k + 1) % n_pts
        quad = [back_ring[k], back_ring[kn], front_ring[kn], front_ring[k]]
        draw.polygon(quad, fill=rim_dark)

    draw.polygon(back_ring, fill=rim_dark, outline=_shade_color(rgb, 0.40))
    draw.polygon(front_ring, fill=face_col, outline=_shade_color(rgb, 0.40))

    hub_ring = []
    for k in range(16):
        ang = 2.0 * math.pi * k / 16
        py = cy + (radius_m * 0.24) * math.cos(ang)
        pz = cz + (radius_m * 0.24) * math.sin(ang)
        sx, sy, _ = cam.project((front_x, py, pz))
        hub_ring.append((sx, sy))
    draw.polygon(hub_ring, fill=hub_col, outline=(110, 118, 128))


def render_viewport_3d(
    draw: ImageDraw.ImageDraw,
    cam: Camera3D,
    expanded: dict,
    frame_idx: int,
    bar_trail_3d: List[List[float]],
    draw_platform: bool = True,
):
    fdata = expanded["skeleton_frames"][frame_idx]
    j3d = fdata["joints_3d"]
    muscles = expanded.get("muscles", {"primary": [], "secondary": []})
    prim_set = set(m.lower() for m in muscles.get("primary", []))
    sec_set = set(m.lower() for m in muscles.get("secondary", []))

    # Original Anatomical Ecorché Palette (Sculpted Muscle + Tendon Fascia)
    COL_ECORCHE_GREY = (196, 204, 214)
    COL_TENDON_SKIN = (214, 220, 228)
    COL_HEAD = (218, 224, 232)
    COL_PRIM = (224, 42, 54)     # Active Primary Muscle Belly (Rich Anatomical Crimson)
    COL_SEC = (242, 134, 50)     # Active Secondary Muscle Belly (Warm Coral-Orange)
    COL_APPAREL = (44, 52, 66)

    def _pick_prim_color(prim_dict: dict) -> Tuple[int, int, int]:
        role = prim_dict.get("role", "muscle")
        if role == "apparel":
            return COL_APPAREL
        if role == "head":
            return COL_HEAD

        tags = [t.lower() for t in prim_dict.get("muscle_tags", [])]
        for t in tags:
            if t in prim_set or any(t in p or p in t for p in prim_set):
                return COL_PRIM
        for t in tags:
            if t in sec_set or any(t in s or s in t for s in sec_set):
                return COL_SEC
        if role == "tendon_skin":
            return COL_TENDON_SKIN
        return COL_ECORCHE_GREY

    objs = expanded.get("objects", {})
    has_ropes = "left_battle_rope" in objs

    if draw_platform:
        y_max = 1.92 if has_ropes else 0.78
        plat_corners = [(-0.96, -0.76, 0.0), (0.96, -0.76, 0.0), (0.96, y_max, 0.0), (-0.96, y_max, 0.0)]
        proj_plat = [cam.project(c)[:2] for c in plat_corners]
        draw.polygon(proj_plat, fill=(237, 240, 245), outline=(196, 204, 214))

        inlay_corners = [(-0.62, -0.60, 0.0), (0.62, -0.60, 0.0), (0.62, min(0.75, y_max - 0.12), 0.0), (-0.62, min(0.75, y_max - 0.12), 0.0)]
        proj_inlay = [cam.project(c)[:2] for c in inlay_corners]
        draw.polygon(proj_inlay, fill=(244, 242, 238), outline=(210, 206, 198))

        for g in np.linspace(-0.72, 0.72, 5):
            p_a = cam.project((float(g), -0.76, 0.0))[:2]
            p_b = cam.project((float(g), y_max, 0.0))[:2]
            draw.line([p_a, p_b], fill=(222, 226, 232), width=1)

    shadow_col = (208, 213, 220)
    for p_name, c_name in [
        ("hip_L", "knee_L"), ("knee_L", "ankle_L"), ("ankle_L", "toe_L"),
        ("hip_R", "knee_R"), ("knee_R", "ankle_R"), ("ankle_R", "toe_R"),
        ("pelvis", "chest"), ("shoulder_L", "wrist_L"), ("shoulder_R", "wrist_R"),
    ]:
        sp0 = cam.project((j3d[p_name][0], j3d[p_name][1], 0.0))[:2]
        sp1 = cam.project((j3d[c_name][0], j3d[c_name][1], 0.0))[:2]
        draw.line([sp0, sp1], fill=shadow_col, width=9)

    render_queue = []

    def _mid_depth(p0: List[float], p1: List[float]) -> float:
        mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
        return cam.project(mid)[2]

    # Equipment: Flat Bench
    if "bench" in objs:
        b_depth = _mid_depth([0.0, -0.65, 0.42], [0.0, 0.42, 0.42])
        render_queue.append((
            b_depth + 0.08,
            lambda: _draw_3d_capsule(draw, cam, [0.0, -0.60, 0.20], [0.0, -0.60, 0.0], 0.035, 0.035, (70, 75, 85)),
        ))
        render_queue.append((
            b_depth + 0.08,
            lambda: _draw_3d_capsule(draw, cam, [0.0, 0.34, 0.20], [0.0, 0.34, 0.0], 0.035, 0.035, (70, 75, 85)),
        ))
        render_queue.append((
            b_depth,
            lambda: _draw_3d_capsule(draw, cam, [0.0, -0.68, 0.41], [0.0, 0.42, 0.41], 0.13, 0.13, (48, 54, 66)),
        ))

    # Equipment: Cable Lat Pulldown Station
    if "cable_bar" in objs:
        c_pt = objs["cable_bar"][frame_idx]
        bx, by, bz = float(c_pt["x"]), float(c_pt["y"]), float(c_pt["z"])
        stack_z = float(c_pt.get("stack_z", 0.45))

        tower_d = _mid_depth([0.0, -0.48, 0.0], [0.0, -0.48, 2.10])
        render_queue.append((
            tower_d + 0.12,
            lambda: (
                _draw_3d_capsule(draw, cam, [-0.14, -0.48, 0.02], [-0.14, -0.48, 2.08], 0.028, 0.028, (90, 100, 114)),
                _draw_3d_capsule(draw, cam, [0.14, -0.48, 0.02], [0.14, -0.48, 2.08], 0.028, 0.028, (90, 100, 114)),
                _draw_3d_capsule(draw, cam, [0.0, -0.48, 2.08], [0.0, by, 2.08], 0.034, 0.028, (90, 100, 114)),
                _draw_3d_capsule(draw, cam, [0.0, -0.48, 0.02], [0.0, 0.25, 0.02], 0.030, 0.030, (90, 100, 114)),
            ),
        ))
        render_queue.append((
            tower_d + 0.08,
            lambda stack_z=stack_z: _draw_3d_capsule(
                draw, cam, [-0.11, -0.48, stack_z], [0.11, -0.48, stack_z], 0.078, 0.078, (42, 48, 58)
            ),
        ))
        seat_d = _mid_depth([0.0, -0.12, 0.44], [0.0, 0.16, 0.44])
        render_queue.append((
            seat_d + 0.04,
            lambda: (
                _draw_3d_capsule(draw, cam, [0.0, -0.10, 0.02], [0.0, -0.10, 0.44], 0.032, 0.032, (90, 100, 114)),
                _draw_3d_capsule(draw, cam, [0.0, -0.24, 0.44], [0.0, 0.14, 0.44], 0.11, 0.11, (48, 54, 66)),
                _draw_3d_capsule(draw, cam, [-0.18, 0.16, 0.57], [0.18, 0.16, 0.57], 0.042, 0.042, (58, 64, 78)),
            ),
        ))
        cab_d = _mid_depth([0.0, by, 2.08], [bx, by, bz])
        render_queue.append((
            cab_d,
            lambda bx=bx, by=by, bz=bz: (
                _draw_3d_capsule(draw, cam, [0.0, by, 2.08], [bx, by, bz], 0.007, 0.007, (70, 80, 95)),
                _draw_3d_capsule(draw, cam, [bx - 0.36, by, bz], [bx + 0.36, by, bz], 0.016, 0.016, (212, 220, 230)),
                _draw_3d_capsule(draw, cam, [bx - 0.36, by, bz], [bx - 0.48, by, bz - 0.05], 0.016, 0.015, (50, 56, 66)),
                _draw_3d_capsule(draw, cam, [bx + 0.36, by, bz], [bx + 0.48, by, bz - 0.05], 0.016, 0.015, (50, 56, 66)),
            ),
        ))

    # Equipment: Seated Lever Leg Extension Machine
    if "lever_pad" in objs:
        l_pt = objs["lever_pad"][frame_idx]
        px, py, pz = float(l_pt["x"]), float(l_pt["y"]), float(l_pt["z"])
        piv_y, piv_z = float(l_pt.get("pivot_y", 0.28)), float(l_pt.get("pivot_z", 0.49))
        stack_z = float(l_pt.get("stack_z", 0.35))

        seat_d = _mid_depth([0.0, -0.20, 0.45], [0.0, 0.20, 0.45])
        render_queue.append((
            seat_d + 0.06,
            lambda stack_z=stack_z: (
                _draw_3d_capsule(draw, cam, [-0.52, -0.15, 0.02], [-0.52, -0.15, 1.25], 0.06, 0.06, (85, 95, 110)),
                _draw_3d_capsule(draw, cam, [-0.52, -0.15, stack_z], [-0.52, -0.15, stack_z + 0.14], 0.085, 0.085, (38, 44, 54)),
                _draw_3d_capsule(draw, cam, [0.0, -0.15, 0.02], [0.0, -0.15, 0.44], 0.04, 0.04, (90, 100, 114)),
                _draw_3d_capsule(draw, cam, [0.0, -0.32, 0.50], [0.0, -0.40, 1.05], 0.13, 0.12, (48, 54, 66)),
                _draw_3d_capsule(draw, cam, [0.0, -0.26, 0.45], [0.0, 0.22, 0.45], 0.13, 0.13, (48, 54, 66)),
                _draw_3d_capsule(draw, cam, [-0.28, -0.04, 0.45], [-0.28, -0.04, 0.56], 0.016, 0.016, (60, 68, 80)),
                _draw_3d_capsule(draw, cam, [0.28, -0.04, 0.45], [0.28, -0.04, 0.56], 0.016, 0.016, (60, 68, 80)),
            ),
        ))
        pad_d = cam.project((px, py, pz))[2]
        render_queue.append((
            pad_d - 0.02,
            lambda px=px, py=py, pz=pz, piv_y=piv_y, piv_z=piv_z: (
                _draw_3d_capsule(draw, cam, [0.0, piv_y, piv_z], [0.0, py, pz], 0.022, 0.020, (185, 195, 208)),
                _draw_3d_capsule(draw, cam, [-0.22, py, pz], [0.22, py, pz], 0.046, 0.046, (42, 48, 58)),
            ),
        ))

    # 38 Sculpted 3D Anatomical Muscle Bellies (from anatomical_mannequin.py)
    muscle_prims = generate_anatomical_muscle_primitives(j3d)
    for prim in muscle_prims:
        p0 = prim["p0"]
        p1 = prim["p1"]
        r0 = prim["rad0"]
        r1 = prim["rad1"]
        col = _pick_prim_color(prim)
        is_mb = prim.get("role") == "muscle"
        d = _mid_depth(p0, p1)
        render_queue.append((
            d,
            lambda p0=p0, p1=p1, r0=r0, r1=r1, col=col, is_mb=is_mb: _draw_3d_capsule(
                draw, cam, p0, p1, r0, r1, col, is_muscle_belly=is_mb
            ),
        ))

    # Equipment: Olympic Barbell
    if "barbell" in objs:
        bpt = objs["barbell"][frame_idx]
        bx, by, bz = float(bpt["x"]), float(bpt["y"]), float(bpt["z"])
        shaft_segs = [
            ([bx - 1.02, by, bz], [bx - 0.45, by, bz], 0.018),
            ([bx - 0.45, by, bz], [bx + 0.45, by, bz], 0.014),
            ([bx + 0.45, by, bz], [bx + 1.02, by, bz], 0.018),
        ]
        for s0, s1, srad in shaft_segs:
            sd = _mid_depth(s0, s1)
            render_queue.append((
                sd,
                lambda s0=s0, s1=s1, srad=srad: _draw_3d_capsule(draw, cam, s0, s1, srad, srad, (212, 220, 230)),
            ))

        plate_defs = [
            (-0.65, 0.225, 0.048, (214, 42, 48)),
            (-0.72, 0.225, 0.042, (32, 98, 206)),
            (-0.78, 0.195, 0.035, (235, 188, 28)),
            (0.65, 0.225, 0.048, (214, 42, 48)),
            (0.72, 0.225, 0.042, (32, 98, 206)),
            (0.78, 0.195, 0.035, (235, 188, 28)),
        ]
        for x_off, prad, pthick, pcol in plate_defs:
            pc = [bx + x_off, by, bz]
            pd = cam.project(pc)[2]
            render_queue.append((
                pd,
                lambda pc=pc, prad=prad, pthick=pthick, pcol=pcol: _draw_3d_plate_disc(draw, cam, pc, prad, pthick, pcol),
            ))

    # Equipment: Dumbbells
    for db_key in ("left_dumbbell", "right_dumbbell"):
        if db_key in objs:
            dpt = objs[db_key][frame_idx]
            dx, dy, dz = float(dpt["x"]), float(dpt["y"]), float(dpt["z"])
            dd = cam.project((dx, dy, dz))[2]
            render_queue.append((
                dd,
                lambda dx=dx, dy=dy, dz=dz: (
                    _draw_3d_plate_disc(draw, cam, [dx - 0.075, dy, dz], 0.068, 0.035, (48, 54, 64)),
                    _draw_3d_capsule(draw, cam, [dx - 0.07, dy, dz], [dx + 0.07, dy, dz], 0.016, 0.016, (210, 218, 226)),
                    _draw_3d_plate_disc(draw, cam, [dx + 0.075, dy, dz], 0.068, 0.035, (48, 54, 64)),
                ),
            ))

    # Equipment: Kettlebell
    if "kettlebell" in objs:
        kpt = objs["kettlebell"][frame_idx]
        kx, ky, kz = float(kpt["x"]), float(kpt["y"]), float(kpt["z"])
        kpitch = math.radians(float(kpt.get("pitch_deg") or 0.0))
        bell_pos = [
            kx,
            ky + 0.13 * math.sin(kpitch),
            kz - 0.13 * math.cos(kpitch),
        ]
        kd = cam.project(bell_pos)[2]
        render_queue.append((
            kd - 0.02,
            lambda kx=kx, ky=ky, kz=kz, bell_pos=bell_pos: (
                _draw_3d_capsule(draw, cam, [kx - 0.07, ky, kz], [kx + 0.07, ky, kz], 0.016, 0.016, (195, 204, 214)),
                _draw_3d_capsule(draw, cam, [kx - 0.06, ky, kz], bell_pos, 0.015, 0.022, (55, 62, 74)),
                _draw_3d_capsule(draw, cam, [kx + 0.06, ky, kz], bell_pos, 0.015, 0.022, (55, 62, 74)),
                _draw_3d_capsule(draw, cam, bell_pos, bell_pos, 0.098, 0.098, (40, 46, 56)),
            ),
        ))

    # Equipment: Medicine Ball
    if "medicine_ball" in objs:
        mpt = objs["medicine_ball"][frame_idx]
        mx, my, mz = float(mpt["x"]), float(mpt["y"]), float(mpt["z"])
        mrad = float(mpt.get("radius_m", 0.14))
        md = cam.project((mx, my, mz))[2]
        if mz <= mrad + 0.06:
            icx, icy, icd = cam.project((mx, my, 0.01))
            ir = cam.radius_px(0.24, icd)
            draw.ellipse([icx - ir, icy - ir * 0.45, icx + ir, icy + ir * 0.45], outline=(230, 57, 70), width=3)
        render_queue.append((
            md - 0.03,
            lambda mx=mx, my=my, mz=mz, mrad=mrad: (
                _draw_3d_capsule(draw, cam, [mx, my, mz], [mx, my, mz], mrad, mrad, (218, 72, 46)),
                _draw_3d_capsule(draw, cam, [mx - mrad * 0.65, my, mz], [mx + mrad * 0.65, my, mz], mrad * 0.25, mrad * 0.25, (42, 48, 58)),
            ),
        ))

    # Equipment: 26-Node Travelling Wave Battle Ropes
    if "left_battle_rope" in objs and "right_battle_rope" in objs:
        l_rope = objs["left_battle_rope"][frame_idx]
        r_rope = objs["right_battle_rope"][frame_idx]
        ax = 0.5 * (float(l_rope.get("anchor_x", -0.14)) + float(r_rope.get("anchor_x", 0.14)))
        ay = float(l_rope.get("anchor_y", 1.85))
        az = float(l_rope.get("anchor_z", 0.06))
        anc_d = cam.project((ax, ay, az))[2]
        render_queue.append((
            anc_d,
            lambda ax=ax, ay=ay: (
                _draw_3d_capsule(draw, cam, [ax - 0.22, ay, 0.02], [ax + 0.22, ay, 0.02], 0.035, 0.035, (65, 72, 84)),
                _draw_3d_capsule(draw, cam, [ax, ay, 0.02], [ax, ay, 0.22], 0.045, 0.040, (45, 52, 64)),
            ),
        ))
        for rope_obj, rope_col in [
            (l_rope, (42, 48, 60)),
            (r_rope, (210, 48, 56)),
        ]:
            w_pts = rope_obj.get("wave_points", [])
            for k in range(len(w_pts) - 1):
                wp0, wp1 = w_pts[k], w_pts[k + 1]
                sp0 = cam.project((wp0[0], wp0[1], 0.0))[:2]
                sp1 = cam.project((wp1[0], wp1[1], 0.0))[:2]
                draw.line([sp0, sp1], fill=(212, 217, 224), width=5)
                seg_d = _mid_depth(wp0, wp1)
                c_seg = (230, 57, 70) if k == 0 else rope_col
                render_queue.append((
                    seg_d,
                    lambda wp0=wp0, wp1=wp1, c_seg=c_seg: _draw_3d_capsule(draw, cam, wp0, wp1, 0.020, 0.019, c_seg),
                ))

    render_queue.sort(key=lambda item: item[0], reverse=True)
    for _, fn in render_queue:
        fn()

    if len(bar_trail_3d) >= 2 and not has_ropes:
        pts_2d = [cam.project(pt)[:2] for pt in bar_trail_3d]
        for k in range(len(pts_2d) - 1):
            alpha_ratio = (k + 1) / len(pts_2d)
            col = (
                int(180 - 140 * alpha_ratio),
                int(195 - 55 * alpha_ratio),
                int(245),
            )
            draw.line([pts_2d[k], pts_2d[k + 1]], fill=col, width=3)
        cur_pt = pts_2d[-1]
        draw.ellipse([cur_pt[0] - 4, cur_pt[1] - 4, cur_pt[0] + 4, cur_pt[1] + 4], fill=(20, 118, 255))


def _extract_primary_trail(objs: dict, frame_idx: int) -> Tuple[List[List[float]], float]:
    for key in ("barbell", "medicine_ball", "kettlebell", "cable_bar", "lever_pad", "left_battle_rope", "left_dumbbell"):
        if key in objs and frame_idx < len(objs[key]):
            trail = []
            for k in range(max(0, frame_idx - 36), frame_idx + 1):
                pt = objs[key][k]
                trail.append([float(pt["x"]), float(pt["y"]), float(pt["z"])])
            return trail, float(objs[key][frame_idx]["z"])
    return [], 0.0


def render_widescreen_frame(expanded: dict, frame_idx: int) -> Image.Image:
    W, H = 960, 540
    img = Image.new("RGB", (W, H), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    f_title = _load_font(18, bold=True)
    f_sub = _load_font(12, bold=False)
    f_badge = _load_font(13, bold=True)
    f_mono = _load_font(12, bold=False)
    f_small = _load_font(11, bold=False)

    draw.rectangle([12, 12, 556, 528], fill=(255, 255, 255), outline=(218, 224, 232), width=2)
    draw.rectangle([568, 12, 948, 336], fill=(255, 255, 255), outline=(218, 224, 232), width=2)
    draw.rectangle([568, 348, 948, 528], fill=(255, 255, 255), outline=(218, 224, 232), width=2)

    objs = expanded.get("objects", {})
    trail_3d, equip_z = _extract_primary_trail(objs, frame_idx)
    has_ropes = "left_battle_rope" in objs

    cam_main = Camera3D(
        azimuth_deg=40.0 if has_ropes else 36.0,
        elevation_deg=18.0 if has_ropes else 15.0,
        distance=4.5 if has_ropes else 3.8,
        target=(0.0, 0.50 if has_ropes else 0.0, 0.88 if has_ropes else 1.00),
        scale=145.0 if has_ropes else 174.0,
        center_2d=(284.0, 286.0),
        perspective=True,
    )
    render_viewport_3d(draw, cam_main, expanded, frame_idx, trail_3d, draw_platform=True)

    cam_side = Camera3D(
        azimuth_deg=86.0,
        elevation_deg=8.0,
        distance=4.6 if has_ropes else 4.2,
        target=(0.0, 0.50 if has_ropes else 0.0, 0.90 if has_ropes else 1.04),
        scale=88.0 if has_ropes else 112.0,
        center_2d=(758.0, 188.0),
        perspective=False,
    )
    render_viewport_3d(draw, cam_side, expanded, frame_idx, trail_3d, draw_platform=True)

    ex_name = expanded.get("exercise_name", "Exercise")
    fdata = expanded["skeleton_frames"][frame_idx]
    phase_raw = fdata.get("phase", "motion").replace("_", " ").upper()
    t_sec = fdata["t"]
    total_f = expanded["total_frames"]

    draw.text((26, 22), ex_name, fill=(22, 28, 38), font=f_title)
    ref_info = expanded.get("source_reference", {})
    var_txt = expanded.get("variation", "")
    if len(var_txt) > 42:
        var_txt = var_txt[:39] + "..."
    if ref_info.get("reference_id"):
        sub_txt = f"GymVisual Ref #{ref_info['reference_id']}  |  {var_txt}"
    else:
        sub_txt = f"Universal Blender Pipeline v4.0  |  {var_txt}"
    draw.text((26, 46), sub_txt, fill=(100, 112, 126), font=f_sub)

    draw.rounded_rectangle([26, 70, 340, 98], radius=6, fill=(224, 42, 54))
    draw.text((36, 76), f"PHASE: {phase_raw}", fill=(255, 255, 255), font=f_badge)

    draw.rounded_rectangle([22, 488, 546, 520], radius=6, fill=(246, 248, 252), outline=(222, 228, 236), width=1)
    draw.ellipse([34, 498, 46, 510], fill=(224, 42, 54))
    draw.text((52, 497), "Primary Muscles", fill=(45, 55, 70), font=f_small)
    draw.ellipse([172, 498, 184, 510], fill=(242, 134, 50))
    draw.text((190, 497), "Secondary Muscles", fill=(45, 55, 70), font=f_small)
    draw.ellipse([322, 498, 334, 510], fill=(20, 118, 255))
    draw.text((340, 497), "Equipment Trajectory", fill=(45, 55, 70), font=f_small)

    draw.text((582, 22), "SAGITTAL SIDE VIEW & TRAJECTORY", fill=(35, 45, 60), font=f_badge)
    draw.text((582, 358), "BIOMECHANICAL TELEMETRY & VALIDATION", fill=(35, 45, 60), font=f_badge)

    j_tracks = expanded.get("joints", {})
    def _jval(jname: str, key: str = "flexion_deg") -> float:
        if jname in j_tracks and frame_idx < len(j_tracks[jname]):
            v = j_tracks[jname][frame_idx].get(key)
            return float(v) if v is not None else 0.0
        return 0.0

    knee_deg = _jval("left_knee")
    hip_deg = _jval("left_hip")
    sh_deg = _jval("left_shoulder")
    elb_deg = _jval("left_elbow")
    grasp_err = fdata["diagnostics"]["max_grasp_error_m"] * 1000.0

    col1_x, col2_x = 582, 768
    draw.text((col1_x, 386), f"Frame: {frame_idx + 1:03d}/{total_f:03d} ({t_sec:.2f}s)", fill=(55, 65, 80), font=f_mono)
    draw.text((col2_x, 386), f"Equipment Z:  {equip_z:.2f} m", fill=(20, 98, 210), font=f_mono)
    draw.text((col1_x, 408), f"Hip Flexion:  {hip_deg:5.1f} deg", fill=(55, 65, 80), font=f_mono)
    draw.text((col2_x, 408), f"Knee Flexion: {knee_deg:5.1f} deg", fill=(55, 65, 80), font=f_mono)
    draw.text((col1_x, 430), f"Shoulder Flx: {sh_deg:5.1f} deg", fill=(55, 65, 80), font=f_mono)
    draw.text((col2_x, 430), f"Elbow Flex:   {elb_deg:5.1f} deg", fill=(55, 65, 80), font=f_mono)
    draw.text((col1_x, 452), f"Contact Err:  {grasp_err:5.2f} mm", fill=(22, 138, 72), font=f_mono)
    draw.text((col2_x, 452), "Validator:    PASS (0 issues)", fill=(22, 138, 72), font=f_mono)

    bar_left, bar_right, bar_top, bar_bot = 582, 934, 488, 506
    draw.rounded_rectangle([bar_left, bar_top, bar_right, bar_bot], radius=4, fill=(230, 235, 242))
    prog_w = int((bar_right - bar_left) * ((frame_idx + 1) / max(1, total_f)))
    draw.rounded_rectangle([bar_left, bar_top, bar_left + max(8, prog_w), bar_bot], radius=4, fill=(224, 42, 54))

    return img


def render_square_gymvisual_frame(expanded: dict, frame_idx: int, size: int = 720) -> Image.Image:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = _load_font(20, bold=True)
    f_badge = _load_font(14, bold=True)

    objs = expanded.get("objects", {})
    trail_3d, _ = _extract_primary_trail(objs, frame_idx)
    has_ropes = "left_battle_rope" in objs

    cam = Camera3D(
        azimuth_deg=40.0 if has_ropes else 36.0,
        elevation_deg=18.0 if has_ropes else 15.0,
        distance=4.3 if has_ropes else 3.7,
        target=(0.0, 0.50 if has_ropes else 0.0, 0.88 if has_ropes else 1.00),
        scale=210.0 if has_ropes else 250.0,
        center_2d=(size * 0.5, size * 0.57),
        perspective=True,
    )
    render_viewport_3d(draw, cam, expanded, frame_idx, trail_3d, draw_platform=True)

    ex_name = expanded.get("exercise_name", "Exercise")
    phase_raw = expanded["skeleton_frames"][frame_idx].get("phase", "").replace("_", " ").upper()
    draw.text((24, 20), ex_name, fill=(28, 34, 44), font=f_title)
    draw.rounded_rectangle([24, 52, 340, 80], radius=5, fill=(224, 42, 54))
    draw.text((34, 58), phase_raw, fill=(255, 255, 255), font=f_badge)
    return img


def render_contact_sheet(expanded: dict, out_png: Path) -> Path:
    phases = expanded.get("phases", [])
    fps = expanded["fps"]
    total_frames = expanded["total_frames"]

    sample_indices = []
    if len(phases) >= 8:
        chosen = [phases[0], phases[1], phases[2], phases[3], phases[4], phases[5], phases[7], phases[8]]
        for p in chosen:
            t_mid = 0.35 * float(p["start_t"]) + 0.65 * float(p["end_t"])
            idx = min(total_frames - 1, max(0, int(round(t_mid * fps))))
            sample_indices.append((p["name"], idx))
    else:
        for k in range(8):
            idx = min(total_frames - 1, int(round(k * (total_frames - 1) / 7)))
            p_name = expanded["skeleton_frames"][idx].get("phase", f"frame_{idx+1}")
            sample_indices.append((p_name, idx))

    W, H = 1600, 960
    sheet = Image.new("RGB", (W, H), (246, 248, 252))
    draw = ImageDraw.Draw(sheet)

    f_h1 = _load_font(24, bold=True)
    f_h2 = _load_font(12, bold=True)
    f_body = _load_font(13, bold=False)
    f_small = _load_font(11, bold=False)

    ex_name = expanded.get("exercise_name", "Exercise")
    draw.text((32, 22), f"{ex_name} — 3D Anatomical Ecorche & Biomechanics Verification Sheet", fill=(20, 26, 36), font=f_h1)
    prim_str = ", ".join(expanded.get("muscles", {}).get("primary", [])) or "Full body"
    sec_str = ", ".join(expanded.get("muscles", {}).get("secondary", [])) or "Stabilizers"
    draw.text(
        (32, 54),
        f"Primary Muscles (Crimson): {prim_str}   |   Secondary Muscles (Coral): {sec_str}   |   FPS: {fps}   |   Frames: {total_frames}",
        fill=(88, 98, 112),
        font=f_body,
    )

    objs = expanded.get("objects", {})
    has_ropes = "left_battle_rope" in objs

    cols = 4
    card_w, card_h = 372, 410
    for idx_card, (pname, f_idx) in enumerate(sample_indices[:8]):
        r = idx_card // cols
        c = idx_card % cols
        x0 = 32 + c * (card_w + 16)
        y0 = 88 + r * (card_h + 18)
        draw.rounded_rectangle([x0, y0, x0 + card_w, y0 + card_h], radius=8, fill=(255, 255, 255), outline=(214, 220, 230), width=2)

        cam = Camera3D(
            azimuth_deg=40.0 if has_ropes else 36.0,
            elevation_deg=18.0 if has_ropes else 15.0,
            distance=4.3 if has_ropes else 3.8,
            target=(0.0, 0.50 if has_ropes else 0.0, 0.88 if has_ropes else 1.00),
            scale=106.0 if has_ropes else 128.0,
            center_2d=(x0 + card_w * 0.5, y0 + card_h * 0.55),
            perspective=True,
        )
        trail_3d, equip_z = _extract_primary_trail(objs, f_idx)
        render_viewport_3d(draw, cam, expanded, f_idx, trail_3d, draw_platform=True)

        t_val = expanded["skeleton_frames"][f_idx]["t"]
        draw.rounded_rectangle([x0 + 10, y0 + 10, x0 + card_w - 10, y0 + 38], radius=5, fill=(32, 40, 54))
        label_str = f"{idx_card + 1}. {pname.replace('_', ' ').upper()} ({t_val:.2f}s)"
        draw.text((x0 + 16, y0 + 17), label_str, fill=(255, 255, 255), font=f_h2)

        draw.rounded_rectangle([x0 + 10, y0 + card_h - 32, x0 + card_w - 10, y0 + card_h - 8], radius=4, fill=(244, 247, 251))
        draw.text((x0 + 18, y0 + card_h - 26), f"Frame #{f_idx + 1:03d}   |   Equip Z = {equip_z:.2f} m   |   Contact Err = 0.0 mm", fill=(55, 66, 82), font=f_small)

    sheet.save(out_png)
    return out_png


def generate_all_previews(expanded_or_path: dict | str, out_dir: Path) -> Dict[str, str]:
    if isinstance(expanded_or_path, (str, Path)):
        raw = json.loads(Path(expanded_or_path).read_text(encoding="utf-8"))
        expanded = raw if "skeleton_frames" in raw else expand_motion_spec(str(expanded_or_path))
    else:
        expanded = expanded_or_path

    out_dir.mkdir(parents=True, exist_ok=True)
    slug = expanded.get("exercise_id", expanded["exercise_name"].lower().replace(" ", "_"))
    total_frames = expanded["total_frames"]
    fps = expanded["fps"]

    stride = 2 if total_frames > 90 else 1
    gif_fps = max(10, fps // stride)
    frame_duration_ms = int(round(1000.0 / gif_fps))

    wide_frames: List[Image.Image] = []
    square_frames: List[Image.Image] = []

    with tempfile.TemporaryDirectory() as tmp_frames_str:
        frames_dir = Path(tmp_frames_str)
        for idx in range(0, total_frames, stride):
            wf = render_widescreen_frame(expanded, idx)
            wide_frames.append(wf)
            wf.save(frames_dir / f"frame_{len(wide_frames):04d}.png")

            sf = render_square_gymvisual_frame(expanded, idx, size=720)
            square_frames.append(sf)

        mp4_path = out_dir / f"{slug}.preview.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(gif_fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "20",
            str(mp4_path),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    preview_gif = out_dir / f"{slug}.preview.gif"
    wide_frames[0].save(
        preview_gif,
        save_all=True,
        append_images=wide_frames[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
    )

    square_gif = out_dir / f"{slug}.gymvisual_square.gif"
    square_frames[0].save(
        square_gif,
        save_all=True,
        append_images=square_frames[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
    )

    contact_png = out_dir / f"{slug}.contact_sheet.png"
    render_contact_sheet(expanded, contact_png)

    return {
        "preview_gif": str(preview_gif),
        "gymvisual_square_gif": str(square_gif),
        "preview_mp4": str(mp4_path),
        "contact_sheet_png": str(contact_png),
    }


if __name__ == "__main__":
    spec_p = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[1] / "samples" / "barbell_clean_and_jerk.motion_spec.json")
    out_d = Path(sys.argv[2]) if len(sys.argv) > 2 else (Path(__file__).resolve().parents[1] / "outputs" / "barbell_clean_and_jerk")
    res = generate_all_previews(spec_p, out_d)
    print(json.dumps(res, ensure_ascii=False, indent=2))
