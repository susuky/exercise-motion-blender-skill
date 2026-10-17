"""Render the full 80-frame cycle or direct grip/foot/side closeups."""
import bpy,sys,json,shutil
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'conventional_deadlift.blend'))
s=bpy.context.scene;cam=s.camera;records=json.loads((OUT/'motion.json').read_text())
def look(target,offset,scale,path):
 cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
if '--previews' in sys.argv:
 for f in [1,11,21,31,41]:
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f:03d}.png');bpy.ops.render.render(write_still=True)
elif '--path-qa' in sys.argv:
 s.render.resolution_x=720;s.render.resolution_y=720
 for ob in bpy.data.objects:
  if ob.parent and ob.parent.name=='Loaded straight barbell' and not ('shaft' in ob.name or 'grip zone' in ob.name):ob.hide_render=True
 for f in [1,15,21,31,41]:
  s.frame_set(f);look(V((0,.0,.84)),V((3.3,-1.0,.18)),2.05,QA/f'bar_path_{f:03d}.png')
elif '--qa' in sys.argv:
 s.render.resolution_x=720;s.render.resolution_y=720
 for f in [1,15,41]:
  s.frame_set(f);row=records[f-1];bar=V(row['bar'])
  for side,sign in [('l',1),('r',-1)]:
   target=V(row['joints']['grip_'+side]);look(target,V((.22*sign,.48,.12)),.30,QA/f'grip_{side}_{f:03d}.png');look(target,V((.20*sign,-.48,.12)),.30,QA/f'grip_front_{side}_{f:03d}.png')
  look(V((0,-.02,.10)),V((.8,-1.7,.55)),.60,QA/f'feet_{f:03d}.png')
  look(V((0,.01,.85)),V((3.3,0,.12)),2.05,QA/f'side_{f:03d}.png')
else:
 for f in range(1,42):
  preview=OUT/f'preview_{f:03d}.png'
  if preview.exists() and preview.stat().st_mtime>(OUT/'conventional_deadlift.blend').stat().st_mtime:
   shutil.copy2(preview,OUT/f'frame_{f:03d}.png');continue
  s.frame_set(f);s.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
 for f in range(42,81):shutil.copy2(OUT/f'frame_{82-f:03d}.png',OUT/f'frame_{f:03d}.png')
 shutil.copy2(OUT/'frame_001.png',OUT/'representative.png')
print('RENDER COMPLETE',flush=True)
