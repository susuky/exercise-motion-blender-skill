# Pulldown muscle colors

Requires Blender 4.3.2, Python 3, NumPy and Pillow. Build `../lat_pulldown` first, then run here:

```sh
blender -b -t 3 --python recolor.py -- pulldown patch
blender -b -t 3 --python recolor.py -- pulldown stills
blender -b -t 3 --python recolor.py -- pulldown render_mirror
python package.py pulldown
```

The original red/blue palette and 80-frame/four-second encoding are retained. The recoloring script also retains its original squat branch; the current garment-corrected squat is rebuilt through `../barbell_squat/build_from_shared.py`, which includes its own original recoloring stage. See `ANATOMICAL_COLOR_MAP.md`. Shared asset license: [root license](../../assets/LICENSE.ASSETS.md).
