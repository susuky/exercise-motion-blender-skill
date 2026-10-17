import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector as V
R=Path(__file__).resolve().parent;O=R/'output';Q=R/'qa'
bpy.ops.wm.open_mainfile(filepath=str(O/'battle_rope.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];r=bpy.data.objects['Human.rig'];groups={g.index:g.name for g in h.vertex_groups};ids={side:[] for side in ['l','r']}
for v in h.data.vertices:
 for side in ids:
  if sum(g.weight for g in v.groups if groups[g.group].endswith('_'+side) and groups[g.group].startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')))>.7:ids[side].append(v.index)
checks=[]
for f in range(1,25):
 s.frame_set(f);ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 for side in ['l','r']:
  ob=bpy.data.objects['Rope handle '+side];inv=ob.matrix_world.inverted();w=r.pose.bones['hand_'+side].head;fore=(r.pose.bones['lowerarm_'+side].tail-r.pose.bones['lowerarm_'+side].head).normalized();palm=(r.pose.bones['middle_01_'+side].head-w).normalized();radius=[]
  for vi in ids[side]:
   p=inv@(h.matrix_world@me.vertices[vi].co)
   if abs(p.y)<.063:radius.append(math.hypot(p.x,p.z))
  rope=bpy.data.objects['Battle rope '+side];points=[V(p.co[:3]) for p in rope.data.splines[0].points];exit=ob.matrix_world@V((0,.071,0))
  checks.append({'frame':f,'side':side,'wrist_alignment_degrees':math.degrees(fore.angle(palm)),'hand_to_grip_center_m':(ob.location-w).length,'handle_radius_m':.0145,'closest_hand_surface_to_shaft_axis_m':min(radius),'hand_vertices_inside_handle_inner_10mm':sum(x<.010 for x in radius),'rope_exit_error_m':(points[0]-exit).length,'rope_surface_ground_clearance_m':min(p.z for p in points)-.0195,'anchor':list(points[-1])})
 ev.to_mesh_clear()
s.frame_set(1);poses1=[b.matrix.copy() for b in r.pose.bones];rope1=[p.co.copy() for side in ['l','r'] for p in bpy.data.objects['Battle rope '+side].data.splines[0].points];s.frame_set(25);poses2=[b.matrix.copy() for b in r.pose.bones];rope2=[p.co.copy() for side in ['l','r'] for p in bpy.data.objects['Battle rope '+side].data.splines[0].points]
summary={'unique_frames':24,'animation_fps':24,'delivery_cycles':4,'delivery_duration_seconds':4,'resolution':[960,960],'continuous_skin_vertices':len(h.data.vertices),'max_grip_exit_error_m':max(c['rope_exit_error_m'] for c in checks),'minimum_rope_ground_clearance_m':min(c['rope_surface_ground_clearance_m'] for c in checks),'max_wrist_alignment_degrees':max(c['wrist_alignment_degrees'] for c in checks),'max_deep_handle_penetrating_vertices':max(c['hand_vertices_inside_handle_inner_10mm'] for c in checks),'rig_loop_closure_max_matrix_error':max(max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4)) for a,b in zip(poses1,poses2)),'rope_loop_closure_max_point_error_m':max((a-b).length for a,b in zip(rope1,rope2))}
(Q/'scene_validation.json').write_text(json.dumps({'summary':summary,'frame_checks':checks},indent=2));print(json.dumps(summary,indent=2))
