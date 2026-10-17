# Barbell squat

Garment-corrected source for the showcased squat. It preserves the original body, equipment, muscle colors, animation and view; the garment patch matches the shorts' armature deformation setting to the body's.

Requires Blender 4.3.2, Python 3, NumPy and Pillow. Run from this directory:

```sh
python build_from_shared.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 LP_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 --python render.py
python package.py
```

`BLENDER` optionally selects the Blender executable. The builder reads the shared root `assets/improved_human.blend` and checks mesh counts, rig bindings, required bones, skinning groups and anatomical vertex colors before assembling the scene.

The build runs base construction, leg tracking refinement, anatomical recoloring, exact animation restoration from `inputs/animation_channels.json`, then the garment-only patch. `inputs/motion.json` supplies the optional geometry validator. Keep these JSON files with the source.

Optional checks:

```sh
blender -b -t 2 --python validate_geometry.py
blender -b -t 2 --python validate_garment.py -- --stills
```

Generated data stay under `output/`, `qa/`, and the nested rebuild outputs. Packaging writes the GIF and its validation results. See `COLOR_MAPPING.md`. Shared asset license: [root license](../../assets/LICENSE.ASSETS.md).
