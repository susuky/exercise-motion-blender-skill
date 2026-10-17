"""Apply the source's final toe-aligned knee pole without recomputing grips."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector as V,Matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'barbell_squat.blend'))
s=bpy.context.scene;rig=bpy.data.objects['Human.rig'];bones=rig.data.bones;rest={b.name:b.matrix_local.copy() for b in bones}
records=json.loads((OUT/'motion.json').read_text())
def segment(n,a,b):
 bone=bones[n];q=(bone.tail_local-bone.head_local).rotation_difference(b-a);return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n]
for record in records:
 f=record['frame'];s.frame_set(f);desired={n:pb.matrix.copy() for n,pb in rig.pose.bones.items()};j=record['joints']
 for side,sign in [('l',1),('r',-1)]:
  a=V(j['hip_'+side]);w=V(j['ankle_'+side]);L1=bones['thigh_'+side].length;L2=bones['calf_'+side].length;v=w-a;D=v.length;u=v.normalized();pole=V((sign*.4,-1,0));pole=(pole-u*pole.dot(u)).normalized();along=(L1*L1-L2*L2+D*D)/(2*D);k=a+u*along+pole*math.sqrt(max(0,L1*L1-along*along));j['knee_'+side]=list(k)
  desired['thigh_'+side]=segment('thigh_'+side,a,k);desired['calf_'+side]=segment('calf_'+side,k,w)
  for part in ['thigh','calf','foot','ball']:
   n=part+'_'+side;pb=rig.pose.bones[n];ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n];pb.matrix_basis=ref.inverted()@desired[n];pb.rotation_mode='QUATERNION'
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=f)
for fc in rig.animation_data.action.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
(OUT/'motion.json').write_text(json.dumps(records,indent=2));s.frame_set(41);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'barbell_squat.blend'),compress=True)
