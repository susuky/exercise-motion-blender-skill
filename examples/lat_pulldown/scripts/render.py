"""Render all 80 frames, or --qa for closeups of endpoints and contacts."""
import bpy,sys,shutil,json,math,numpy as np
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'lat_pulldown.blend'))
s=bpy.context.scene;cam=s.camera;loc=cam.location.copy();rot=cam.rotation_euler.copy();scale=cam.data.ortho_scale
if '--qa' in sys.argv:
 for f in [1,21,41]:
  s.frame_set(f);cam.location=loc;cam.rotation_euler=rot;cam.data.ortho_scale=scale;s.render.filepath=str(OUT/f'qa_full_{f:03d}.png');bpy.ops.render.render(write_still=True)
  bar=bpy.data.objects['Lat bar animated assembly'];center=bar.location
  for side,sign in [('l',1),('r',-1)]:
   target=center+V((.435*sign,0,0));cam.location=target+V((.22*sign,-.45,.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.29;s.render.filepath=str(OUT/f'qa_hand_{side}_{f:03d}.png');bpy.ops.render.render(write_still=True)
 s.frame_set(41);target=V((0,-.18,.51));cam.location=V((1.1,-1.3,.86));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.92;s.render.filepath=str(OUT/'qa_seat_thigh_contact.png');bpy.ops.render.render(write_still=True)
 s.frame_set(41);target=V((0,-.03,1.05));cam.location=V((2.1,-.03,1.16));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.8;s.render.filepath=str(OUT/'qa_chest_bar_clearance.png');bpy.ops.render.render(write_still=True)
else:
 for f in range(1,81):
  s.frame_set(f);s.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
 shutil.copy2(OUT/'frame_041.png',OUT/'representative.png')
print('RENDER COMPLETE',flush=True)
