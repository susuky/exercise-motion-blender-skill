import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
import numpy as np
R=Path(__file__).resolve().parent;O=R/'output';bpy.ops.wm.open_mainfile(filepath=str(O/'lateral_raise_xhigh.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];r=bpy.data.objects['Human.rig']
groups={g.index:g.name for g in h.vertex_groups}
ids={side:[] for side in ['l','r']}
for v in h.data.vertices:
 for side in ids:
  names=[g for g in v.groups if groups[g.group].endswith('_'+side) and (groups[g.group].startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')))]
  if sum(g.weight for g in names)>.7:ids[side].append(v.index)
checks=[]
for f in range(1,37):
 s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();ev=h.evaluated_get(dg);me=ev.to_mesh()
 for side in ['l','r']:
  ob=bpy.data.objects['Dumbbell '+side];inv=ob.matrix_world.inverted();w=r.pose.bones['hand_'+side].head
  fore=(r.pose.bones['lowerarm_'+side].tail-r.pose.bones['lowerarm_'+side].head).normalized()
  palm=(r.pose.bones['middle_01_'+side].head-w).normalized()
  wrist_angle=math.degrees(fore.angle(palm))
  axis=ob.matrix_world.to_3x3()@V((0,1,0));shaft_angle=math.degrees(fore.angle(axis))
  plate_inside=0;deep_shaft=0;shaft_inside=0;shaft_distances=[]
  for vi in ids[side]:
   p=inv@(h.matrix_world@me.vertices[vi].co);rad=math.sqrt(p.x*p.x+p.z*p.z)
   if .074<abs(p.y)<.126 and rad<.060:plate_inside+=1
   if abs(p.y)<.074:
    shaft_distances.append(rad)
    if rad<.010:deep_shaft+=1
    if rad<.0145:shaft_inside+=1
  checks.append({'frame':f,'side':side,'wrist_alignment_degrees':round(wrist_angle,5),'shaft_forearm_angle_degrees':round(shaft_angle,5),'hand_to_grip_center_m':round((ob.location-w).length,6),'hand_vertices_inside_weight_head':plate_inside,'hand_vertices_inside_handle_inner_10mm':deep_shaft,'hand_vertices_inside_handle_surface':shaft_inside,'handle_radius_m':.0145,'closest_hand_surface_to_shaft_axis_m':round(min(shaft_distances),6)})
 ev.to_mesh_clear()
q={'frames':36,'fps':12,'resolution':[960,960],'continuous_skin_vertices':len(h.data.vertices),'continuous_skin_faces':len(h.data.polygons),'hand_mesh_tests':checks}
(O/'scene_validation.json').write_text(json.dumps(q,indent=2));print(json.dumps(q,indent=2))
