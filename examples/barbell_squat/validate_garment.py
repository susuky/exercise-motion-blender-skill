"""Read-only original/matched garment comparison. Optional --stills adds closeups."""
import bpy,json,numpy as np,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector as V
D=Path(__file__).resolve().parent;Q=D/'qa';bpy.ops.wm.open_mainfile(filepath=str(D/'output/barbell_squat_recolored_garment_v2.blend'));s=bpy.context.scene
h=bpy.data.objects['Human'];cloth=bpy.data.objects['Black shorts'];hm=next(m for m in h.modifiers if m.type=='ARMATURE');cm=next(m for m in cloth.modifiers if m.type=='ARMATURE')
result={'body_preserve_volume':hm.use_deform_preserve_volume,'saved_scene_unchanged':True,'sample_stride':15,'frames':[]}
for f in [1,21,41,61]:
 s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();ob=h.evaluated_get(dg);me=ob.to_mesh();verts=[ob.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];bt=BVHTree.FromPolygons(verts,faces,all_triangles=False);ob.to_mesh_clear();del verts,faces;row={'frame':f}
 for mode,flag in [('original',True),('matched',hm.use_deform_preserve_volume)]:
  cm.use_deform_preserve_volume=flag;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ob=cloth.evaluated_get(dg);me=ob.to_mesh();ds=[]
  for v in list(me.vertices)[::15]:
   q=ob.matrix_world@v.co;p,n,face,d=bt.find_nearest(q);ds.append(float((q-p).dot(n)))
  a=np.asarray(ds);row[mode]={'sampled_shell_vertices':len(a),'minimum_signed_clearance_m':float(a.min()),'median_signed_clearance_m':float(np.median(a)),'inside_over_2mm_count':int((a<-.002).sum()),'clearance_percentiles_m':np.percentile(a,[0,1,10,50,90,99,100]).tolist()};ob.to_mesh_clear()
 result['frames'].append(row);del bt
(Q/'garment_recheck.json').write_text(json.dumps(result,indent=2))
if '--stills' in sys.argv:
 s.frame_set(41);s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=1
 for o in s.objects:
  if o.type=='MESH' and o.name not in ['Human','Black shorts']:o.hide_render=True
 rig=bpy.data.objects['Human.rig'];target=rig.matrix_world@rig.pose.bones['pelvis'].head+V((0,0,-.07));cam=s.camera;cam.data.shift_x=cam.data.shift_y=0;cam.data.ortho_scale=.76
 for mode,flag in [('original',True),('matched',hm.use_deform_preserve_volume)]:
  cm.use_deform_preserve_volume=flag;bpy.context.view_layer.update()
  for label,offset in [('front',V((1.8,-3,.8))),('back',V((1.8,3,.8)))]:
   cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(Q/f'garment_{mode}_{label}.png');bpy.ops.render.render(write_still=True)
print(json.dumps(result,indent=2))
