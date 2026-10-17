"""One-setting garment revision; approved baseline is read-only."""
import bpy,os,json,hashlib,numpy as np
from pathlib import Path
D=Path(os.environ.get('REVISION_OUTPUT_ROOT',Path(__file__).resolve().parent));O=D/'output';Q=D/'qa';O.mkdir(parents=True,exist_ok=True);Q.mkdir(parents=True,exist_ok=True)
P=Path(os.environ.get('SQUAT_ORIGINAL_BLEND',D/'rebuild/color_revision/squat/output/barbell_squat_recolored.blend'))
expected='a7ffdcea3f3776b418aead09bd15a07f6d74be1a0da3eeea17ac590dd114ef74';baseline=hashlib.sha256(P.read_bytes()).hexdigest()
if not os.environ.get('ALLOW_REBUILT_BASELINE'):assert baseline==expected,(baseline,expected)
bpy.ops.wm.open_mainfile(filepath=str(P));s=bpy.context.scene;h=bpy.data.objects['Human'];c=bpy.data.objects['Black shorts'];hm=next(m for m in h.modifiers if m.type=='ARMATURE');cm=next(m for m in c.modifiers if m.type=='ARMATURE')
def prop(collection,name,count):
 a=np.empty(len(collection)*count,np.float32);collection.foreach_get(name,a);return a.tobytes()
def digest():
 geom=hashlib.sha256();colors=hashlib.sha256();actions=hashlib.sha256()
 for ob in sorted(bpy.data.objects,key=lambda o:o.name):
  geom.update(ob.name.encode());geom.update(np.asarray(ob.matrix_world,np.float32).tobytes())
  if ob.type=='MESH':
   geom.update(prop(ob.data.vertices,'co',3))
   for a in ob.data.color_attributes:colors.update(ob.name.encode()+a.name.encode()+prop(a.data,'color',4))
  if ob.animation_data and ob.animation_data.action:
   for fc in ob.animation_data.action.fcurves:
    actions.update((ob.name+fc.data_path+str(fc.array_index)).encode());actions.update(np.asarray([(list(k.co),list(k.handle_left),list(k.handle_right)) for k in fc.keyframe_points],np.float32).tobytes())
 cam=s.camera;view={'matrix_world':list(map(list,cam.matrix_world)),'type':cam.data.type,'ortho_scale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'fps':s.render.fps,'frames':[s.frame_start,s.frame_end],'aa':s.display.render_aa,'view_transform':s.view_settings.view_transform,'exposure':s.view_settings.exposure}
 return {'bind_geometry_and_object_transforms_sha256':geom.hexdigest(),'all_vertex_colors_sha256':colors.hexdigest(),'all_animation_curves_sha256':actions.hexdigest(),'camera_and_visual_settings':view}
s.frame_set(41);before=digest();old=cm.use_deform_preserve_volume;cm.use_deform_preserve_volume=hm.use_deform_preserve_volume;bpy.context.view_layer.update();after=digest();assert before==after
record={'revision':'garment-v2','baseline_sha256':baseline,'reference_production_baseline_sha256':expected,'only_intended_change':{'object':c.name,'modifier':cm.name,'setting':'use_deform_preserve_volume','before':old,'after':cm.use_deform_preserve_volume},'body_preserve_volume':hm.use_deform_preserve_volume,'bind_geometry_colors_animation_camera_unchanged':before==after,'before':before,'after':after,'original_file_unchanged':hashlib.sha256(P.read_bytes()).hexdigest()==baseline}
(Q/'revision_identity.json').write_text(json.dumps(record,indent=2));s.render.threads_mode='FIXED';s.render.threads=2;bpy.ops.wm.save_as_mainfile(filepath=str(O/'barbell_squat_recolored_garment_v2.blend'),compress=True);print('Versioned scene prepared; baseline untouched',flush=True)
