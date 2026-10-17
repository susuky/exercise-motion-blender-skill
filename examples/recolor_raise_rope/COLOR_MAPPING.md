# Functional-anatomy color mapping

Red = exercise target / principal moving region. Blue = assisting and stabilizing regions. Other exposed anatomy = gray. These are qualitative roles; one shared palette is used throughout: red `(0.72, 0.045, 0.03)`, blue `(0.035, 0.18, 0.72)`, gray `(0.73, 0.75, 0.76)` in linear RGB. The original surface relief and fiber brightness remain visible.

## Dumbbell lateral raise

- Red: middle (acromial) deltoid, restricted to the lateral shoulder cap and tapering toward its humeral insertion.
- Blue: upper and lower trapezius regions and the exposed lower-rib slips of serratus anterior, which support scapular upward rotation and control.
- Gray: anterior chest, other deltoid portions, arms, abdomen, and legs.
- Supraspinatus assists abduction and humeral-head stabilization. Its belly lies beneath trapezius and its tendon passes beneath the acromion/deltoid; the continuous surface model does not expose it separately.

The fixed source movement raises the upper arms laterally toward shoulder height. Middle-deltoid emphasis follows this movement. The front and back mask checks make the surface location of the red deltoid and blue scapular regions visible.

## Alternating battle-rope waves

- Red: deltoid caps, representing the shoulder-driven alternating flexion/extension with the arms held slightly out from the torso.
- Blue: visible biceps/brachialis and triceps regions for elbow control; forearm flexor-pronator regions for grip; trapezius and serratus for scapular support; latissimus for shoulder-extension assistance; rectus abdominis, external oblique, and erector-spinae regions for trunk bracing; quadriceps for the held flexed-knee stance.
- Gray: chest, hands, lower-leg anatomy, and other exposed regions.
- The black shorts conceal the gluteal and proximal-thigh areas. Rotator-cuff muscles are mostly covered by the surface muscles.

The delivered motion uses short alternating waves, varying elbow flexion, a small forward trunk inclination, and a held partial squat. Blue includes the stance and grip work visible in that specific movement. The shoulder cap is treated as a deltoid region because the source mesh provides one continuous cap rather than separately modeled heads.

## Evidence used for role assignment

- [Deltoid structure and function, StatPearls](https://www.ncbi.nlm.nih.gov/books/NBK537056/): lateral deltoid supports abduction; anterior and posterior portions contribute to flexion and extension.
- [Arm abductor anatomy, StatPearls](https://www.ncbi.nlm.nih.gov/books/NBK537148/): deltoid and supraspinatus act at the glenohumeral joint; trapezius and serratus coordinate scapular upward rotation.
- [ACE-sponsored battle-rope study](https://www.acefitness.org/continuing-education/certified/research/7470/muscle-activation-during-battle-rope-exercises/): describes alternating shoulder flexion/extension and records activity in anterior deltoid, upper trapezius, forearm, trunk, and lower-body muscles. Its measured percentages are not encoded by the colors.

## Source and reproduction

`recolor_existing.py` reads the delivered scene and replaces only its per-vertex pigment. All meshes, rig, finger contact, apparatus, camera, keyframes, and timing are retained. It reconstructs neutral pigment from the existing brightness and derives new role masks from rest-pose anatomy, bone axes, and localized surface regions.

1. Run Blender 4.3.2 with `--python recolor_existing.py -- lateral_raise --save-only` or `battle_rope --save-only`.
2. Run `render_recolored.py` with the same exercise plus `--preview`; review the front/back masks and representative image.
3. Run with `--animation` to render every unique motion phase.
4. Run `python package_and_validate.py lateral_raise` or `battle_rope`.
5. Run Blender with `--python verify_scene_identity.py -- lateral_raise` or `battle_rope` to compare original and recolored geometry, animation, camera, rig, and clothing hashes.

The GIF encoder reserves separate neutral, red, and blue shade ranges and an exact-white palette entry. Quantization is constrained to the source color class, preserving small blue regions and keeping colored speckles out of gray anatomy and black clothing. Validation checks every decoded frame for red/blue visibility and checks every source-white pixel for exact-white preservation.

The lateral raise retains 36 frames / 3 seconds. Battle ropes retain 24 unique phases repeated four times, 96 frames / 4 seconds. Both are 960×960 with an exact-white GIF background, full-body framing, no image labels, and black clothing.
