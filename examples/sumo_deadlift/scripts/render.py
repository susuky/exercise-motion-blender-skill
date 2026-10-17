"""Render the cycle or targeted grip, feet, and stance contact closeups."""
import bpy,sys,json,shutil
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'sumo_deadlift.blend'))
s=bpy.context.scene;cam=s.camera;records=json.loads((OUT/'motion.json').read_text())
def look(target,offset,scale,path):
 cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
if '--qa' in sys.argv or '--lockout-qa' in sys.argv:
 h=bpy.data.objects['Human'];shorts=bpy.data.objects['Black shorts'];group=h.vertex_groups.new(name='QA isolated hands');group.add([v.index for v in h.data.vertices if abs(v.co.x)>.43 and .87<v.co.z<1.16],1,'REPLACE');mask=h.modifiers.new('QA isolate palms for rear inspection','MASK');mask.vertex_group=group.name;mask.show_render=False
 for f in ([41] if '--lockout-qa' in sys.argv else [1,21,41]):
  s.frame_set(f);row=records[f-1]
  if f!=21:
   for side,sign in [('l',1),('r',-1)]:
    target=V(row['joints']['grip_'+side]);look(target,V((.20*sign,-.48,.18)),.31,QA/f'grip_front_{side}_{f:03d}.png');mask.show_render=(f==41);shorts.hide_render=(f==41);look(target,V((.20*sign,.48,-.05)),.31,QA/f'grip_back_{side}_{f:03d}.png');mask.show_render=False;shorts.hide_render=False
   look(V((0,-.06,.10)),V((.6,-1.7,.52)),1.25,QA/f'feet_{f:03d}.png')
  look(V((0,-.01,.78)),V((3.3,0,.2)),1.94,QA/f'side_{f:03d}.png')
  if f!=41:look(V((0,-.02,.41)),V((0,-3.3,1.6)),1.43,QA/f'knees_{f:03d}.png')
else:
 start,end=1,42
 if '--range' in sys.argv:
  idx=sys.argv.index('--range');start,end=int(sys.argv[idx+1]),int(sys.argv[idx+2])
 for f in range(start,end):
  s.frame_set(f);s.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
 if '--range' not in sys.argv:
  for f in range(42,81):shutil.copy2(OUT/f'frame_{82-f:03d}.png',OUT/f'frame_{f:03d}.png')
  shutil.copy2(OUT/'frame_001.png',OUT/'representative.png')
print('RENDER COMPLETE',flush=True)
