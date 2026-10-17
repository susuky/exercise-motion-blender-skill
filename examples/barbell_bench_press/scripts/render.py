"""Render exact unique phases and reuse identical poses; --qa checks contacts."""
import bpy,sys,json,shutil
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'barbell_bench_press.blend'))
s=bpy.context.scene;cam=s.camera;records=json.loads((OUT/'motion.json').read_text())
def look(target,offset,scale,path):
 cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
if '--qa' in sys.argv:
 for f in [1,18,37]:
  s.frame_set(f);row=records[f-1];bar=V(row['bar'])
  for side,sign in [('l',1),('r',-1)]:
   target=V(row['joints']['grip_'+side]);look(target,V((.22*sign,-.48,.25)),.31,QA/f'grip_front_{side}_{f:03d}.png')
   if f==37:look(target,V((.20*sign,.48,.15)),.31,QA/f'grip_back_{side}_{f:03d}.png')
  look(V((0,.06,.57)),V((3.3,0,.28)),2.00,QA/f'side_{f:03d}.png')
  if f==37:
   look(V((0,.115,.60)),V((2,-1,.8)),.76,QA/'chest_touch.png')
   look(V((0,-.60,.11)),V((1,-1.8,.50)),.83,QA/'feet.png')
else:
 cache={}
 for f,row in enumerate(records[:80],1):
  key=round(row['depth'],8);p=OUT/f'frame_{f:03d}.png'
  if key in cache:shutil.copy2(cache[key],p)
  else:
   s.frame_set(f);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);cache[key]=p
 shutil.copy2(OUT/'frame_037.png',OUT/'representative.png')
 print('UNIQUE RENDERED PHASES',len(cache),flush=True)
print('RENDER COMPLETE',flush=True)
