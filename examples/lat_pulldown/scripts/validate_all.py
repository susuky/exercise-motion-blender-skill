"""Numerical dense-mesh, kinematic, cable, and repeat-cycle checks."""
import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'lat_pulldown.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];bar=bpy.data.objects['Lat bar animated assembly'];shorts=bpy.data.objects['Black shorts']
n=len(h.data.vertices);rest=np.empty(n*3);h.data.vertices.foreach_get('co',rest);rest=rest.reshape(-1,3)
head=rest[:,2]>1.48;body=(rest[:,2]>1.0)&(rest[:,2]<1.43)&(abs(rest[:,0])<.16);hands=(abs(rest[:,0])>.44)&(rest[:,2]<1.12)&(rest[:,2]>.90);feet=rest[:,2]<.10
rows=[];first=None;last=None
for f in range(1,82):
 s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();ev=h.evaluated_get(dep);mesh=ev.to_mesh();co=np.empty(n*3);mesh.vertices.foreach_get('co',co);co=co.reshape(-1,3)
 if f==1:first=co.copy()
 if f==81:last=co.copy()
 by,bz=bar.location.y,bar.location.z;rad=np.sqrt((co[:,1]-by)**2+(co[:,2]-bz)**2)
 pad=(abs(co[:,0])>.045)&(abs(co[:,0])<.30)&(co[:,2]<.85);padrad=np.sqrt((co[:,1]+.31)**2+(co[:,2]-.6795)**2)
 row={'frame':f,'head_bar_surface_clearance_m':float(np.min(rad[head])-.0145),'torso_bar_surface_clearance_m':float(np.min(rad[body])-.0145),'hand_grip_surface_clearance_m':float(np.min(rad[hands])-.0145),'hand_vertices_inside_grip':int(np.sum(hands&(rad<.0145))),'thigh_pad_surface_clearance_m':float(np.min(padrad[pad])-.075),'thigh_vertices_inside_pad':int(np.sum(pad&(padrad<.075))),'foot_floor_clearance_m':float(np.min(co[feet,2]))}
 ev.to_mesh_clear()
 ev=shorts.evaluated_get(dep);mesh=ev.to_mesh();c=np.empty(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',c);c=c.reshape(-1,3);seat=(abs(c[:,0])<.21)&(c[:,1]>-.165)&(c[:,1]<.195)&(c[:,2]>.25)&(c[:,2]<.60);row['cloth_seat_surface_clearance_m']=float(np.min(c[seat,2])-.4085);ev.to_mesh_clear()
 lengths=[];endpoints=[]
 for nm in ['Taut active cable','Return cable to weight stack']:
  ob=bpy.data.objects[nm];lengths.append(float(ob.scale.z));endpoints.append([list(ob.matrix_world@V((0,0,z))) for z in [-.5,.5]])
 row['combined_moving_cable_length_m']=sum(lengths)
 rows.append(row)
 if f%10==1:print('VALIDATED',f,flush=True)
summary={'render_frames':80,'endpoint_validation_frames':81,'skin_vertices':n,'full_cycle_max_vertex_difference_m':float(np.max(abs(first-last))),'head_clearance_min_m':min(r['head_bar_surface_clearance_m'] for r in rows),'torso_clearance_min_m':min(r['torso_bar_surface_clearance_m'] for r in rows),'hand_clearance_min_m':min(r['hand_grip_surface_clearance_m'] for r in rows),'hand_penetrating_vertex_count_max':max(r['hand_vertices_inside_grip'] for r in rows),'thigh_pad_clearance_min_m':min(r['thigh_pad_surface_clearance_m'] for r in rows),'thigh_penetrating_vertex_count_max':max(r['thigh_vertices_inside_pad'] for r in rows),'cloth_seat_clearance_min_m':min(r['cloth_seat_surface_clearance_m'] for r in rows),'foot_floor_clearance_range_m':[min(r['foot_floor_clearance_m'] for r in rows),max(r['foot_floor_clearance_m'] for r in rows)],'moving_cable_total_length_variation_m':max(r['combined_moving_cable_length_m'] for r in rows)-min(r['combined_moving_cable_length_m'] for r in rows)}
(OUT/'all_frame_geometry_validation.json').write_text(json.dumps({'summary':summary,'frames':rows},indent=2));print(json.dumps(summary,indent=2),flush=True)
