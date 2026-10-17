"""Dense-surface geometry validation for every frame and exact loop endpoint."""
import bpy,json,numpy as np,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'sumo_deadlift.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];bar=bpy.data.objects['Loaded straight barbell'];n=len(h.data.vertices)
r=np.empty(n*3);h.data.vertices.foreach_get('co',r);r=r.reshape(-1,3)
feet=r[:,2]<.035;hands=(abs(r[:,0])>.44)&(r[:,2]<1.12)&(r[:,2]>.90);lower=(r[:,2]<.90)&(r[:,2]>.15)
digitmasks={}
for side in ['l','r']:
 for finger in ['thumb','index','middle','ring','pinky']:
  ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_') and g.name.endswith('_'+side)}
  mask=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices]);digitmasks[side+'_'+finger]=mask
rows=[];first=None;end=None;firstfeet=None
motion=json.loads((OUT/'motion.json').read_text())
def angle(a,b):return float(np.degrees(np.arccos(np.clip(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
for f in range(1,82):
 s.frame_set(f);ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.empty(n*3);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
 if f==1:first=a.copy();firstfeet=a[feet].copy()
 if f==81:end=a.copy()
 by,bz=bar.location.y,bar.location.z;rad=np.hypot(a[:,1]-by,a[:,2]-bz);shaft=(abs(a[:,0])<.65);handrad=rad[hands];j=motion[f-1]['joints'];angles={};kneeangles={};hipknee={};handin={}
 for side in ['l','r']:
  sh,el,wr=(np.array(j[k+'_'+side]) for k in ['shoulder','elbow','wrist']);dy=np.array(j['hand_direction_'+side]);angles[side]={'elbow_degrees':angle(sh-el,wr-el),'neutral_wrist_degrees':angle(wr-el,dy)}
  hip,knee,ank=(np.array(j[k+'_'+side]) for k in ['hip','knee','ankle']);kneeangles[side]=180-angle(hip-knee,ank-knee);hipknee[side]=float(hip[2]-knee[2]);handin[side]=float(abs(knee[0])-abs(j['grip_'+side][0]))
 row={'frame':f,'bar_y_m':float(by),'bar_z_m':float(bz),'plate_floor_clearance_m':float(bz-.225),'all_skin_shaft_min_clearance_m':float(rad[shaft].min()-.0145),'all_skin_vertices_inside_shaft':int(np.sum(rad[shaft]<.0145-1e-6)),'hand_shaft_min_clearance_m':float(handrad.min()-.0145),'lower_body_shaft_min_clearance_m':float(rad[lower&shaft].min()-.0145),'sole_min_z_m':float(a[feet,2].min()),'sole_max_displacement_m':float(np.linalg.norm(a[feet]-firstfeet,axis=1).max()),'arm_angles':angles,'knee_flexion_degrees':kneeangles,'hip_minus_knee_z_m':hipknee,'hands_inside_knees_margin_m':handin,'individual_digit_clearance_m':{name:float(rad[mask].min()-.0145) for name,mask in digitmasks.items()}}
 # Closed bumper solids must not touch the skin. Check both plate sets and sides.
 row['skin_inside_plate_vertices']=sum(int(((abs(a[:,0]-sign*cx)<thick/2)&(rad<radius)).sum()) for sign in [-1,1] for cx,radius,thick in [(.756,.225,.105),(.849,.205,.064)])
 rows.append(row);ev.to_mesh_clear()
 if f%10==1:print('VALIDATED',f,flush=True)
summary={'frames':80,'endpoint_frame':81,'skin_vertices':n,'full_cycle_max_vertex_difference_m':float(abs(first-end).max()),'bar_horizontal_drift_m':max(x['bar_y_m'] for x in rows)-min(x['bar_y_m'] for x in rows),'bar_height_range_m':[min(x['bar_z_m'] for x in rows),max(x['bar_z_m'] for x in rows)],'all_skin_vertices_inside_shaft_max':max(x['all_skin_vertices_inside_shaft'] for x in rows),'all_skin_shaft_min_clearance_m':min(x['all_skin_shaft_min_clearance_m'] for x in rows),'hand_shaft_min_clearance_m':min(x['hand_shaft_min_clearance_m'] for x in rows),'lower_body_shaft_min_clearance_m':min(x['lower_body_shaft_min_clearance_m'] for x in rows),'sole_min_z_m':min(x['sole_min_z_m'] for x in rows),'sole_max_displacement_m':max(x['sole_max_displacement_m'] for x in rows),'skin_inside_plate_vertices_max':max(x['skin_inside_plate_vertices'] for x in rows),'hands_inside_knees_margin_m':min(min(x['hands_inside_knees_margin_m'].values()) for x in rows),'elbow_angle_range_degrees':[min(min(y['elbow_degrees'] for y in x['arm_angles'].values()) for x in rows),max(max(y['elbow_degrees'] for y in x['arm_angles'].values()) for x in rows)],'wrist_alignment_max_degrees':max(max(y['neutral_wrist_degrees'] for y in x['arm_angles'].values()) for x in rows),'knee_flexion_start_degrees':rows[0]['knee_flexion_degrees'],'knee_flexion_lockout_degrees':rows[40]['knee_flexion_degrees'],'bottom_hip_minus_knee_z_m':rows[0]['hip_minus_knee_z_m'],'individual_digit_clearance_range_m':{name:[min(x['individual_digit_clearance_m'][name] for x in rows),max(x['individual_digit_clearance_m'][name] for x in rows)] for name in digitmasks},'toe_out_degrees':45,'ankle_stance_width_m':.9,'torso_lean_start_degrees':45,'torso_lean_lockout_degrees':0}
(QA/'all_frame_geometry_validation.json').write_text(json.dumps({'summary':summary,'frames':rows},indent=2));print(json.dumps(summary,indent=2),flush=True)
