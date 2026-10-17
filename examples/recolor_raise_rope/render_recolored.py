"""Render unchanged animation from a recolored saved scene. Preview first, then --animation."""
import bpy,sys
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parent;args=sys.argv[sys.argv.index('--')+1:];kind=args[0];D=Path(args[args.index('--output-dir')+1]).resolve() if '--output-dir' in args else ROOT/kind;OUT=D/'output';QA=D/'qa'
name='lateral_raise' if kind=='lateral_raise' else 'battle_rope'
bpy.ops.wm.open_mainfile(filepath=str(OUT/(name+'.blend')))
s=bpy.context.scene;cam=s.camera;rep=19 if kind=='lateral_raise' else 7
s.frame_set(rep);s.render.filepath=str(OUT/'representative.png');bpy.ops.render.render(write_still=True)
if '--preview' in args:
 for label,loc,target,scale in [('front',(0,-4,1.31),(0,0,1.25),.95),('back',(0,4,1.31),(0,0,1.25),.95)]:
  if kind=='battle_rope':loc=(0,-4,1.23) if label=='front' else (0,4,1.23);target=(0,0,1.19);scale=1.05
  cam.location=V(loc);cam.rotation_euler=(V(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  s.render.filepath=str(QA/(label+'_mask.png'));bpy.ops.render.render(write_still=True)
elif '--animation' in args:
 for frame in range(1,37 if kind=='lateral_raise' else 25):
  if (OUT/f'frame_{frame:03d}.png').exists():continue
  s.frame_set(frame);s.render.filepath=str(OUT/f'frame_{frame:03d}.png');bpy.ops.render.render(write_still=True)
print('RENDER COMPLETE',kind,flush=True)
