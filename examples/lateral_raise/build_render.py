"""Lateral-raise scene using the shared skinned muscle human.
Run from this directory: blender -b --python build_render.py [-- --stills]
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector as V, Matrix, Quaternion
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parents[1]/'assets/improved_human.blend'))
for obj in list(bpy.data.objects):
 if obj.name not in {'Human','Human.rig','Black shorts'}:bpy.data.objects.remove(obj,do_unlink=True)
h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];bones=rig.data.bones
for obj in [h,rig,bpy.data.objects['Black shorts']]:obj.animation_data_clear()
for bone in rig.pose.bones:bone.matrix_basis.identity()
rest={b.name:b.matrix_local.copy() for b in bones}
def mat(n,c,rough=.65):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.roughness=rough;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough
 return m
rubber=mat('Dumbbell graphite rubber',(.035,.043,.050));metal=mat('Brushed stainless handle',(.38,.43,.46),.27)

# Dumbbells, sized for an ordinary hand and with individual plates and end caps.
def cylinder(n,a,b,rad,ma,bevel=.003,vertices=48):
 a,b=V(a),V(b);bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=rad,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=n;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');o.data.materials.append(ma);o.color=ma.diffuse_color
 if bevel:
  be=o.modifiers.new('Rounded manufacturing edge','BEVEL');be.width=bevel;be.segments=3
 for p in o.data.polygons:p.use_smooth=True
 return o
weights=[]
for side in ['l','r']:
 root=bpy.data.objects.new('Dumbbell '+side,None);bpy.context.collection.objects.link(root);root.rotation_mode='QUATERNION'
 objects=[cylinder('Steel grip',(0,-.075,0),(0,.075,0),.0145,metal,.0015)]
 for y in [-.100,.100]:
  objects.append(cylinder('Rubber head',(0,y-.026,0),(0,y+.026,0),.060,rubber,.006))
  objects.append(cylinder('Inset end cap',(0,y-.028,0),(0,y+.028,0),.026,metal,.001))
 for o in objects:o.parent=root
 weights.append(root)
expanded=json.loads((ROOT/'assets/motion.json').read_text())
def segment(name,a,b):
 bone=bones[name];q=(bone.tail_local-bone.head_local).rotation_difference(b-a)
 return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[name]

def pose(frame):
 desired={n:m.copy() for n,m in rest.items()};j=frame['joints_3d']
 for i,(side,source,sign) in enumerate([('l','R',1),('r','L',-1)]):
  def v(k):
   x,y,z=j[k+'_'+source];return V((x,-y,z))
  a=bones['upperarm_'+side].head_local.copy();du=(v('elbow')-v('shoulder')).normalized();df=(v('wrist')-v('elbow')).normalized();e=a+du*bones['upperarm_'+side].length;w=e+df*bones['lowerarm_'+side].length
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed()
  dy=df;dx=V((0,-1,0));dx=(dx-dy*dx.dot(dy)).normalized();dz=dx.cross(dy).normalized();C=Matrix((dx,dy,dz)).transposed();T=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw);desired['hand_'+side]=T@rest['hand_'+side]
  # Finger phalanges follow a common cylindrical grip instead of a generic closed fist.
  cy,cz=.095,-.039
  center=w+dy*cy+dz*(cz*sign)
  radius=.0325
  for finger in ['index','middle','ring','pinky']:
   n=f'{finger}_01_{side}';start=T@bones[n].head_local
   rel=start-w;tx=rel.dot(dx);sy=rel.dot(dy);sz=rel.dot(dz)*sign
   ry0,rz0=sy-cy,sz-cz;d=math.sqrt(ry0*ry0+rz0*rz0);L=bones[n].length
   ca=max(-1.,min(1.,(d*d+radius*radius-L*L)/(2*d*radius)))
   angle=math.atan2(rz0,ry0)-math.acos(ca)
   for k in range(1,4):
    n=f'{finger}_{k:02}_{side}';bone=bones[n]
    if k>1:angle-=2*math.asin(min(.999,bone.length/(2*radius)))
    end=w+dx*tx+dy*(cy+radius*math.cos(angle))+dz*((cz+radius*math.sin(angle))*sign)
    original_direction=T.to_3x3()@(bone.tail_local-bone.head_local)
    turn=original_direction.rotation_difference(end-start).to_matrix().to_4x4()
    desired[n]=Matrix.Translation(start)@turn@T.to_3x3().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n]
    start=end
  start=T@bones['thumb_01_'+side].head_local
  thumb_targets=[(.052,.069,-.008),(.039,.105,-.011),(.010,.116,-.019)]
  for kk,(tx,ty,tz) in enumerate(thumb_targets,1):
   n=f'thumb_{kk:02}_{side}';target=w+dx*tx+dy*ty+dz*(tz*sign)
   direction=(target-start).normalized();end=start+direction*bones[n].length
   desired[n]=segment(n,start,end);start=end
  weights[i].location=center;weights[i].rotation_quaternion=V((0,1,0)).rotation_difference(dx)
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n]
  pb.matrix_basis=ref.inverted()@desired[n]
 bpy.context.view_layer.update()
for k,f in enumerate(expanded['skeleton_frames']):
 pose(f)
 for pb in rig.pose.bones:
  pb.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=k+1)
 for o in weights:
  o.keyframe_insert('location',frame=k+1);o.keyframe_insert('rotation_quaternion',frame=k+1)
for ob in [rig,*weights]:
 if ob.animation_data and ob.animation_data.action:
  for fc in ob.animation_data.action.fcurves:
   for key in fc.keyframe_points:key.interpolation='LINEAR'
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False;scene.world.color=(1,1,1)
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
scene.display.render_aa='8';scene.view_settings.view_transform='Standard';scene.view_settings.exposure=.28;scene.render.fps=12;scene.frame_start=1;scene.frame_end=36
bpy.ops.object.camera_add(location=(2.45,-7,2.35));cam=bpy.context.object;cam.name='Full-body presentation camera';cam.rotation_euler=(V((0,0,.88))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.12;scene.camera=cam
scene.frame_set(19);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'lateral_raise.blend'),compress=True)
frames=[19,1,10] if '--stills' in sys.argv else [19]+[f for f in range(1,37) if f!=19]
for f in frames:
 scene.frame_set(f);scene.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
# Close-up views are part of QA, not a substitute for the full animation.
scene.frame_set(19);cam.location=V((1.1,-3,1.57));target=V((0,-.04,1.255));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.66;scene.render.filepath=str(OUT/'torso_check.png');bpy.ops.render.render(write_still=True)
for i,side in enumerate(['l','r']):
 cam.location=weights[i].location+V((.30 if i==0 else -.30,-.48,.22));cam.rotation_euler=(weights[i].location-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.37;scene.render.filepath=str(OUT/f'hand_{side}_check.png');bpy.ops.render.render(write_still=True)
print('DONE',len(h.data.vertices),'skin vertices; output',OUT)
