# Lateral raise and battle rope muscle colors

Requires Blender 4.3.2, Python 3, NumPy and Pillow. First build the original scene in `../lateral_raise` or `../battle_rope`. Run from this directory; replace `lateral_raise` with `battle_rope` for the other exercise.

```sh
blender -b -t 2 --python recolor_existing.py -- lateral_raise
blender -b -t 2 --python render_recolored.py -- lateral_raise --animation
blender -b -t 2 --python verify_scene_identity.py -- lateral_raise
python package_and_validate.py lateral_raise
```

Outputs are written under `<exercise>/output/`; checks go under `<exercise>/qa/`. The encoder retains the original 36-pose/three-second lateral raise and 24-pose/four-repeat battle-rope timing. See `COLOR_MAPPING.md`. Shared asset license: [root license](../../assets/LICENSE.ASSETS.md).
