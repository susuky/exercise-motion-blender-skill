"""Evaluate the dense skinned mesh at all 81 timeline samples."""
import bpy,json,numpy as np,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'conventional_deadlift.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];bar=bpy.data.objects['Loaded straight barbell'];n=len(h.data.vertices)
r=np.empty(n*3);h.data.vertices.foreach_get('co',r);r=r.reshape(-1,3)
feet=r[:,2]<.035;leg=(r[:,2]>.10)&(r[:,2]<.90)&(abs(r[:,0])<.30)
digitmasks={}
for side in ['l','r']:
 for finger in ['thumb','index','middle','ring','pinky']:
  ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_') and g.name.endswith('_'+side)}
  digitmasks[side+'_'+finger]=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices])
rows=[];first=None;end=None;firstfeet=None
motion=json.loads((OUT/'motion.json').read_text())
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
for f in range(1,82):
 s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();ev=h.evaluated_get(dep);me=ev.to_mesh();a=np.empty(n*3);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
 if f==1:first=a.copy();firstfeet=a[feet].copy()
 if f==81:end=a.copy()
 by,bz=bar.location.y,bar.location.z;rad=np.hypot(a[:,1]-by,a[:,2]-bz);j=motion[f-1]['joints'];angles={};elbows={};knees={};armerr={}
 for side in ['l','r']:
  sh,el,wr=(np.array(j[k+'_'+side]) for k in ['shoulder','elbow','wrist']);dy=np.array(j['hand_direction_'+side]);angles[side]=angle(wr-el,dy);elbows[side]=angle(sh-el,wr-el)
  hi,kn,an=(np.array(j[k+'_'+side]) for k in ['hip','knee','ankle']);knees[side]=angle(hi-kn,an-kn)
  armerr[side]=float(abs(np.linalg.norm(wr-sh)-(rig.data.bones['upperarm_'+side].length+rig.data.bones['lowerarm_'+side].length)))
 row={'frame':f,'bar_y':float(by),'bar_z':float(bz),'plate_bottom_z_m':float(bz-.225),'all_skin_vertices_inside_bar':int(np.sum(rad<.0145-1e-6)),'all_skin_min_clearance_m':float(rad.min()-.0145),'leg_min_clearance_m':float(rad[leg].min()-.0145),'sole_min_z_m':float(a[feet,2].min()),'sole_max_displacement_m':float(np.linalg.norm(a[feet]-firstfeet,axis=1).max()),'wrist_direction_angle_degrees':angles,'elbow_interior_degrees':elbows,'knee_interior_degrees':knees,'arm_length_error_m':armerr,'individual_digit_clearance_m':{name:float(rad[mask].min()-.0145) for name,mask in digitmasks.items()}}
 ce=bpy.data.objects['Black shorts'].evaluated_get(dep);cm=ce.to_mesh();cloth=np.array([v.co[:] for v in cm.vertices]);cr=np.hypot(cloth[:,1]-by,cloth[:,2]-bz);row['shorts_min_clearance_m']=float(cr.min()-.0145);row['shorts_vertices_inside_bar']=int(np.sum(cr<.0145-1e-6));ce.to_mesh_clear()
 rows.append(row);ev.to_mesh_clear()
 if f%10==1:print('VALIDATED',f,flush=True)
summary={'shorts_min_clearance_m':min(x['shorts_min_clearance_m'] for x in rows),'shorts_inside_vertices_max':max(x['shorts_vertices_inside_bar'] for x in rows),'frames':80,'endpoint_frame':81,'skin_vertices':n,'all_skin_inside_vertices_max':max(x['all_skin_vertices_inside_bar'] for x in rows),'all_skin_min_clearance_m':min(x['all_skin_min_clearance_m'] for x in rows),'leg_min_clearance_m':min(x['leg_min_clearance_m'] for x in rows),'full_cycle_max_vertex_difference_m':float(abs(first-end).max()),'bar_horizontal_drift_m':max(x['bar_y'] for x in rows)-min(x['bar_y'] for x in rows),'floor_plate_bottom_z_m':rows[0]['plate_bottom_z_m'],'bar_z_range_m':[min(x['bar_z'] for x in rows),max(x['bar_z'] for x in rows)],'sole_min_z_m':min(x['sole_min_z_m'] for x in rows),'sole_max_displacement_m':max(x['sole_max_displacement_m'] for x in rows),'wrist_alignment_range_degrees':[min(min(x['wrist_direction_angle_degrees'].values()) for x in rows),max(max(x['wrist_direction_angle_degrees'].values()) for x in rows)],'elbow_interior_range_degrees':[min(min(x['elbow_interior_degrees'].values()) for x in rows),max(max(x['elbow_interior_degrees'].values()) for x in rows)],'arm_length_error_max_m':max(max(x['arm_length_error_m'].values()) for x in rows),'lockout_knee_interior_degrees':rows[40]['knee_interior_degrees'],'individual_digit_clearance_range_m':{name:[min(x['individual_digit_clearance_m'][name] for x in rows),max(x['individual_digit_clearance_m'][name] for x in rows)] for name in digitmasks}}
(QA/'all_frame_geometry_validation.json').write_text(json.dumps({'summary':summary,'frames':rows},indent=2));print(json.dumps(summary,indent=2),flush=True)
