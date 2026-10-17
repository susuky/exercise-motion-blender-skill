import bpy,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'output/sumo_deadlift.blend'));s=bpy.context.scene;h=bpy.data.objects['Human'];r=np.array([v.co[:] for v in h.data.vertices]);body=(r[:,2]<1.0)&(abs(r[:,0])<.43);hands=(abs(r[:,0])>.44)&(r[:,2]>.90)&(r[:,2]<1.12);pids=[p.vertices[:] for p in h.data.polygons if all(body[i] for i in p.vertices)];rows=[]
for f in range(1,42):
 s.frame_set(f);ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(coords,pids,all_triangles=False);count=0;minimum=10;closest=None
 for i in np.where(hands)[0]:
  pos,n,index,d=tree.find_nearest(coords[i]);signed=(coords[i]-pos).dot(n)
  if d<.04 and signed<-.0005:count+=1
  if signed<minimum and d<.04:minimum=signed;closest=[int(i),list(coords[i]),list(pos),float(d)]
 rows.append({'frame':f,'hand_vertices_over_0_5mm_inside_lowerbody_nearest_surface':count,'minimum_signed_distance_for_nearby_points_m':minimum,'closest':closest});ev.to_mesh_clear();print(rows[-1],flush=True)
(R/'qa/hand_leg_clearance.json').write_text(json.dumps(rows,indent=2))
