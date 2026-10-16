---
name: exercise-motion-blender-pipeline
description: Convert any fitness or strength exercise across all 29 GymVisual equipment categories (Assisted, Band, Barbell, Battling Rope, Body weight, Bosu ball, Cable, Dumbbell, EZ Barbell, Hammer, Kettlebell, Leverage machine, Medicine Ball, Olympic barbell, Pilates Machine, Power Sled, Resistance Band, Roll, Rollball, Rope, Sled machine, Smith machine, Stability ball, Stick, Suspension, Trap bar, Vibrate Plate, Weighted, Wheel roller) into a validated 3D motion specification (motion_spec.json) and generate procedural Blender 3D animations (.blend, .glb, .bvh, .gif, .mp4) with a 38-muscle sculpted anatomical Ecorche mannequin.
---
# Exercise Motion Blender Pipeline

## Summary

A universal two-layer biomechanical motion and 3D animation pipeline that converts exercise descriptions or reference media into structured movement specifications (`motion_spec.json`), solves full-body 3D Forward and Inverse Kinematics (`kinematics_engine.py`) across 10 body postures and 29 equipment categories (`equipment_registry.py`), validates anatomical and contact constraints (`validate_motion_spec.py`), and generates procedural 3D Blender scenes and animations featuring a 38-muscle sculpted anatomical Ecorche mannequin (`anatomical_mannequin.py`, `generate_from_motion_spec.py`, and `render_preview.py`).

## When to Use

- Translating any exercise from a reference catalog (such as GymVisual's 6,558 animated GIFs across 29 equipment types), video, or coaching cues into a copyright-clean, reusable `motion_spec.json`.
- Generating 3D animations with an original sculpted muscular Ecorche human figure (separate anterior/posterior muscle bellies for pectorals, lats, traps, rhomboids, abs, obliques, glutes, 3-head deltoids, biceps vs triceps, quadriceps vs hamstrings, and gastrocnemius calves).
- Animating free weights, travelling-wave battle ropes, cable pulley towers with moving weight stacks, pivoting leverage machines, ballistic medicine ball slams, kettlebells, resistance bands, TRX suspension straps, sleds, reformers, and stability props.
- Validating joint range-of-motion (ROM) limits, angular velocity, time-windowed hand/ankle equipment contact errors, floor clearance, and loop closure.

## Steps

1. **Classify the Exercise Posture and Equipment Archetype (All 29 Categories)**

   Map the exercise's equipment from the 29 GymVisual categories to one of the 8 composable kinematic archetypes in `scripts/equipment_registry.py` (see `references/EQUIPMENT_AND_POSTURE_TAXONOMY.md` for the full 29-item mapping table):

   - **`rigid_bilateral_bar`**: `barbell`, `olympic_barbell`, `ez_barbell`, `trap_bar`, `stick`, `smith_machine`, `wheel_roller`, `hammer`.
   - **`independent_handheld`**: `dumbbell`, `kettlebell` (supports `pitch_deg` swing rotation), `medicine_ball` (supports time-windowed `grasp` and `ballistic_release` floor bounce), `weighted`.
   - **`wave_rope`**: `battling_rope` (`battle_ropes`), `rope` (36-node travelling harmonic wave solver from hands to floor anchor).
   - **`elastic_tether`**: `band`, `resistance_band`, `suspension` (TRX straps anchored overhead or low).
   - **`cable_pulley_station`**: `cable` (`cable_machine` with rear/side pulley tower, overhead cantilever boom, live cable line, and counter-moving weight stack).
   - **`pivoting_lever_station`**: `leverage_machine` (`lever_machine`), `assisted` (driven by hands, ankles/shins via `roller_pad`, or knees).
   - **`linear_sled_carriage`**: `power_sled`, `sled_machine`, `pilates_machine`.
   - **`floor_prop_surface`**: `body_weight` (`bodyweight`), `bench`, `bosu_ball`, `stability_ball`, `roll` (foam roller), `rollball`, `vibrate_plate`.

2. **Configure Body Setup and Continuous Phases**

   Set `setup.body_position` (`standing`, `split_stance`, `seated`, `supine_on_bench`, `incline_bench`, `prone`, `kneeling`, `plank`, `hanging`, or `sled_incline_seated`) and break the cycle (`0.0` to `timing.duration_sec`) into contiguous phases (`start_t` to `end_t`) with easing (`ease_in_out`, `explosive`, `linear`, `hold`).

3. **Apply Biomechanically Exact Joint Targets and Elbow/Knee Pole Rules**

   - **Vertical Pulls (`cable_machine` Lat Pulldown / Pull-up)**: Use a wide grip (`grip_width_m: 0.84` to `0.88`), pull the bar down to upper-chest/clavicle height (`z = 0.88` m when seated, below shoulder height `z = 0.93` m), and use the downward adducted elbow pole vector (`pole = [±0.22, -0.06, -1.0]`) so elbows drive straight down toward the ribcage (`elbow_z = 0.66` m) with vertical forearms. Tag `latissimus_dorsi`, `rhomboids`, `trapezius` as primary and `biceps_brachii`, `forearm_flexors` as secondary so posterior `triceps_brachii` stays neutral grey.
   - **Battle Ropes (`battle_ropes`)**: Use an athletic half-squat stance (`pelvis_z = 0.64` to `0.68` m, `torso_lean_deg = 24` deg), keep hands in parallel sagittal lanes (`x = ±0.22` m, `y = 0.38` m) with elbows pulled back toward the ribs (`pole = [±0.22, -0.85, -0.50]`), and let the 36-node travelling-history wave solver propagate smooth S-waves to the anchor at `y = 1.95` m.
   - **Ballistic Slams (`medicine_ball`)**: Scope `grasp` contacts with `start_t` and `end_t`, and switch to `ballistic_release` during the slam and floor rebound (`z = 0.14` m).
   - **Lower-Body Leverage Machines (`lever_machine`)**: Drive the movement via `left_knee` and `right_knee` flexion (`95` deg to `6` deg) with `roller_pad` contacts on the ankles, and tag only `quadriceps` (`rectus_femoris`, `vastus_lateralis`) as primary so posterior `hamstrings` and lower-leg `shin_tibialis` stay neutral grey.

4. **Run the Pipeline and Inspect Outputs**

   Execute the unified runner to validate, solve 3D kinematics, generate the 38-muscle sculpted Ecorche scene, and render previews:

   ```bash
   python3 run_pipeline.py samples/<exercise>.motion_spec.json --output-dir outputs/<exercise>
   ```

   For native Blender `.blend` and `.glb` generation:

   ```bash
   blender --background --python blender/generate_from_motion_spec.py -- \
     samples/<exercise>.motion_spec.json \
     --output-dir outputs/<exercise> \
     --style gymvisual_full_color \
     --save-blend --export-glb --render-animation
   ```

## Gotchas

- Never copy frames pixel-by-pixel from reference GIFs. Always translate the movement into biomechanical phases and synthesize the 3D animation through the procedural 38-muscle Ecorche mannequin and IK solver.
- Ensure right-handed coordinate cross products (`torso_f = cross(torso_u, torso_r)` and `thigh_f = cross(torso_r, thigh_u)`) are preserved in `anatomical_mannequin.py` so anterior muscles (`pectoralis_major`, `biceps_brachii`, `quadriceps`) always sit on the anatomical front/top surface and posterior muscles (`latissimus_dorsi`, `triceps_brachii`, `hamstrings`) sit on the back/underside.
- In Lat Pulldowns, never stop the bar at forehead height (`z > 1.05` m when seated) or use a high lateral elbow pole vector, as that makes the movement look like a triceps pushdown. Always pull the bar to clavicle level (`z = 0.88` m) with elbows dropping to `z = 0.66` m.
