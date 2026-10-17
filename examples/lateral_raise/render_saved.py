"""Render the delivered scene without rebuilding its sculpted mesh."""
import bpy,math,shutil
from pathlib import Path
from mathutils import Vector as V
R=Path(__file__).resolve().parent;O=R/'output'
bpy.ops.wm.open_mainfile(filepath=str(O/'lateral_raise.blend'))
s=bpy.context.scene;cam=s.camera;loc=cam.location.copy();rot=cam.rotation_euler.copy();scale=cam.data.ortho_scale
s.render.film_transparent=False;s.display.shading.background_type='WORLD';s.world.color=(1,1,1)
# Conform the 29 mm diameter handle to the verified cylindrical finger grip.
for ob in bpy.data.objects:
 if ob.name.startswith('Steel grip'):
  radius=max(math.hypot(v.co.x,v.co.y) for v in ob.data.vertices)
  factor=.0145/radius
  for v in ob.data.vertices:v.co.x*=factor;v.co.y*=factor
s.frame_set(19);bpy.ops.wm.save_as_mainfile(filepath=str(O/'lateral_raise.blend'),compress=True)
s.render.filepath=str(O/'frame_019.png');bpy.ops.render.render(write_still=True);shutil.copy2(O/'frame_019.png',O/'representative.png')
for i,side in enumerate(['l','r']):
 ob=bpy.data.objects['Dumbbell '+side];cam.location=ob.location+V((.30 if i==0 else -.30,-.48,.22));cam.rotation_euler=(ob.location-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.37;s.render.filepath=str(O/f'hand_{side}_check.png');bpy.ops.render.render(write_still=True)
cam.location=V((1.1,-3,1.57));target=V((0,-.04,1.255));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.66;s.render.filepath=str(O/'torso_check.png');bpy.ops.render.render(write_still=True)
cam.location=loc;cam.rotation_euler=rot;cam.data.ortho_scale=scale
for f in range(1,37):
 if f==19:continue
 s.frame_set(f);s.render.filepath=str(O/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
print('ALL FRAMES COMPLETE',flush=True)
