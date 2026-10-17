import bpy,sys,json,shutil,os
from pathlib import Path
D=Path(__file__).resolve().parent;O=D/'output';Q=D/'qa';bpy.ops.wm.open_mainfile(filepath=str(O/'barbell_squat_recolored_garment_v2.blend'));s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=int(os.environ.get('RENDER_THREADS','1'))
if '--preview' in sys.argv:frames=[1,21,41]
else:
 diff=0.
 for o in bpy.data.objects:
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    for f in range(42,81):diff=max(diff,abs(fc.evaluate(f)-fc.evaluate(82-f)))
 assert diff<1e-5
 (Q/'reverse_frame_equivalence.json').write_text(json.dumps({'checked_frames':39,'all_action_channels_max_difference':diff,'tolerance':1e-5},indent=2));frames=range(1,42)
for f in frames:
 p=O/f'frame_{f:03d}.png'
 if p.exists():continue
 s.frame_set(f);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
if '--preview' not in sys.argv:
 for f in range(42,81):shutil.copy2(O/f'frame_{82-f:03d}.png',O/f'frame_{f:03d}.png')
 shutil.copy2(O/'frame_041.png',O/'representative.png')
print('RENDER COMPLETE',flush=True)
