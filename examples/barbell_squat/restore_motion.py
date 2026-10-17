import bpy,json,os
from pathlib import Path
D=Path(__file__).resolve().parent;P=Path(os.environ['SQUAT_ORIGINAL_BLEND']);bpy.ops.wm.open_mainfile(filepath=str(P));records=json.loads((D/'inputs/animation_channels.json').read_text())
for name,curves in records.items():
 ob=bpy.data.objects[name];ob.animation_data_clear();ob.animation_data_create();action=bpy.data.actions.new(name+' exact original motion');ob.animation_data.action=action
 for data in curves:
  fc=action.fcurves.new(data_path=data['path'],index=data['index']);fc.extrapolation=data['extrapolation'];fc.keyframe_points.add(len(data['keys']))
  for k,q in zip(fc.keyframe_points,data['keys']):
   k.co=q['co'];k.interpolation=q['interpolation'];k.handle_left_type=q['left_type'];k.handle_right_type=q['right_type'];k.handle_left=q['left'];k.handle_right=q['right']
  fc.update()
bpy.context.scene.frame_set(41);bpy.ops.wm.save_as_mainfile(filepath=str(P),compress=True);print('Restored exact original animation channels',flush=True)
