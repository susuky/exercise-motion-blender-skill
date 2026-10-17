"""Dense-skin validation for every frame and the duplicate loop endpoint."""
import bpy,json,numpy as np,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'barbell_squat_recolored_garment_v2.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];bar=bpy.data.objects['Loaded straight barbell'];n=len(h.data.vertices)
r=np.empty(n*3);h.data.vertices.foreach_get('co',r);r=r.reshape(-1,3)
feet=r[:,2]<.035;hands=(abs(r[:,0])>.44)&(r[:,2]<1.12)&(r[:,2]>.90);body=(r[:,2]>1.30)&(r[:,2]<1.49)&(abs(r[:,0])<.25);neck=(r[:,2]>1.477)&(abs(r[:,0])<.12);head=r[:,2]>1.50
digitmasks={}
for side in ['l','r']:
 for finger in ['thumb','index','middle','ring','pinky']:
  ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_') and g.name.endswith('_'+side)}
  mask=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices])
  digitmasks[side+'_'+finger]=mask
rows=[];first=None;end=None;firstfeet=None
motion=json.loads((ROOT/'inputs/motion.json').read_text())
for f in range(1,82):
 s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();ev=h.evaluated_get(dep);me=ev.to_mesh();a=np.empty(n*3);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
 if f==1:first=a.copy();firstfeet=a[feet].copy()
 if f==81:end=a.copy()
 by,bz=bar.location.y,bar.location.z;rad=np.hypot(a[:,1]-by,a[:,2]-bz);handrad=rad[hands];bodyrad=rad[body]
 j=motion[f-1]['joints'];angles={}
 for side in ['l','r']:
  sh,el,wr=(np.array(j[k+'_'+side]) for k in ['shoulder','elbow','wrist']);dy=np.array(j['hand_direction_'+side]);fore=(wr-el);fore/=np.linalg.norm(fore);angles[side]=float(np.degrees(np.arccos(np.clip(np.dot(fore,dy),-1,1))))
 row={'frame':f,'bar_y':float(by),'bar_z':float(bz),'hand_bar_min_clearance_m':float(handrad.min()-.0145),'hand_vertices_inside_bar':int((handrad<.0145-1e-6).sum()),'upper_back_min_clearance_m':float(bodyrad.min()-.0145),'upper_back_vertices_inside_bar':int((bodyrad<.0145-1e-6).sum()),'neck_min_clearance_m':float(rad[neck].min()-.0145),'head_min_clearance_m':float(rad[head].min()-.0145),'sole_min_z_m':float(a[feet,2].min()),'sole_max_displacement_m':float(np.linalg.norm(a[feet]-firstfeet,axis=1).max()),'wrist_direction_angle_degrees':angles,'hip_minus_knee_z_l_m':float(j['hip_l'][2]-j['knee_l'][2])}
 row['all_skin_vertices_inside_bar']=int(np.sum(rad<.0145-1e-6))
 row['all_skin_min_clearance_m']=float(rad.min()-.0145)
 row['individual_digit_clearance_m']={name:float(rad[mask].min()-.0145) for name,mask in digitmasks.items()}
 rows.append(row);ev.to_mesh_clear()
 if f%10==1:print('VALIDATED',f,flush=True)
summary={'all_skin_inside_vertices_max':max(x['all_skin_vertices_inside_bar'] for x in rows),'all_skin_min_clearance_m':min(x['all_skin_min_clearance_m'] for x in rows),'frames':80,'endpoint_frame':81,'skin_vertices':n,'full_cycle_max_vertex_difference_m':float(abs(first-end).max()),'bar_horizontal_drift_m':max(x['bar_y'] for x in rows)-min(x['bar_y'] for x in rows),'hand_bar_min_clearance_m':min(x['hand_bar_min_clearance_m'] for x in rows),'hand_inside_vertices_max':max(x['hand_vertices_inside_bar'] for x in rows),'upper_back_min_clearance_m':min(x['upper_back_min_clearance_m'] for x in rows),'upper_back_inside_vertices_max':max(x['upper_back_vertices_inside_bar'] for x in rows),'neck_min_clearance_m':min(x['neck_min_clearance_m'] for x in rows),'head_min_clearance_m':min(x['head_min_clearance_m'] for x in rows),'sole_min_z_m':min(x['sole_min_z_m'] for x in rows),'sole_max_displacement_m':max(x['sole_max_displacement_m'] for x in rows),'wrist_alignment_range_degrees':[min(min(x['wrist_direction_angle_degrees'].values()) for x in rows),max(max(x['wrist_direction_angle_degrees'].values()) for x in rows)],'bottom_hip_minus_knee_z_m':rows[40]['hip_minus_knee_z_l_m'],'individual_digit_clearance_m':rows[40]['individual_digit_clearance_m']}
(QA/'all_frame_geometry_validation.json').write_text(json.dumps({'summary':summary,'frames':rows},indent=2));print(json.dumps(summary,indent=2),flush=True)
