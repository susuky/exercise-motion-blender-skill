"""Render one unique cycle from the delivered self-contained blend file."""
import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'output'
bpy.ops.wm.open_mainfile(filepath=str(O/'battle_rope.blend'))
s=bpy.context.scene
for f in range(1,25):
 s.frame_set(f);s.render.filepath=str(O/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
