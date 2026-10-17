"""Verify source and recolored scenes retain mesh geometry, rig, all keyframes and clothing."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;args=sys.argv[sys.argv.index('--')+1:];kind=args[0]
src=R.parent/('lateral_raise/output/lateral_raise.blend' if kind=='lateral_raise' else 'battle_rope/output/battle_rope.blend')
name='lateral_raise' if kind=='lateral_raise' else 'battle_rope';dst=R/kind/'output'/(name+'.blend')
def arr_digest(collection,property,items,typ=np.float32):
 a=np.empty(len(collection)*items,dtype=typ);collection.foreach_get(property,a);return hashlib.sha256(a.tobytes()).hexdigest()
def fingerprint(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.frame_set(19 if kind=='lateral_raise' else 7)
 meshes={}
 for o in bpy.data.objects:
  if o.type=='MESH':
   me=o.data;meshes[o.name]={'vertices':len(me.vertices),'coords':arr_digest(me.vertices,'co',3),'loop_topology':arr_digest(me.loops,'vertex_index',1,np.int32)}
 keys=hashlib.sha256();points=0
 for act in sorted(bpy.data.actions,key=lambda a:a.name):
  for fc in act.fcurves:
   keys.update(str((act.name,fc.data_path,fc.array_index)).encode());a=np.empty(len(fc.keyframe_points)*2,dtype=np.float32);fc.keyframe_points.foreach_get('co',a);keys.update(a.tobytes());points+=len(fc.keyframe_points)
 rig=bpy.data.objects['Human.rig'];bones={b.name:([list(row) for row in b.matrix_local],b.parent.name if b.parent else None) for b in rig.data.bones}
 cloth=bpy.data.objects['Black shorts'];mat=cloth.data.materials[0]
 return {'meshes':meshes,'animation_sha256':keys.hexdigest(),'keyframe_points':points,'bones_sha256':hashlib.sha256(json.dumps(bones,sort_keys=True).encode()).hexdigest(),'camera':{'location':list(s.camera.location),'rotation':list(s.camera.rotation_euler),'ortho_scale':s.camera.data.ortho_scale},'clothing':{'color':list(cloth.color),'material_diffuse':list(mat.diffuse_color)},'frame_start':s.frame_start,'frame_end':s.frame_end,'fps':s.render.fps}
a=fingerprint(src);b=fingerprint(dst);result={'exercise':kind,'unchanged':a==b,'source':a,'recolored':b}
(R/kind/'qa/scene_identity.json').write_text(json.dumps(result,indent=2));assert a==b,'Scene geometry or animation changed';print('IDENTITY VERIFIED',kind,flush=True)
