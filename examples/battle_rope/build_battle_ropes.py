"""Battle rope exercise from the improved continuous-skin anatomical human.
Blender 4.3.2: blender -b -t 4 --python build_battle_ropes.py -- --preview
Omit --preview to build, save and render 24 unique frames (one seamless cycle).
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector as V, Matrix
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'output'; QA=ROOT/'qa'
OUT.mkdir(exist_ok=True); QA.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent.parent/'assets/improved_human.blend'))
rig=bpy.data.objects['Human.rig']; human=bpy.data.objects['Human']; bones=rig.data.bones
rest={b.name:b.matrix_local.copy() for b in bones}
for o in list(bpy.data.objects):
 if o.name not in ['Human','Human.rig','Black shorts','Full-body presentation camera']:
  bpy.data.objects.remove(o,do_unlink=True)
for o in [rig,human,bpy.data.objects['Black shorts']]:o.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()

def mat(n,c,rough=.7):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough
 return m
rope_mat=mat('Braided charcoal rope',(.075,.087,.095));grip_mat=mat('Textured rubber grips',(.020,.025,.030));metal=mat('Anchor steel',(.18,.21,.23),.3);ringmat=mat('Brushed steel hardware',(.40,.44,.46),.3)

def cyl(n,a,b,r,ma,bevel=.002):
 a,b=V(a),V(b);bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=(b-a).length,location=(a+b)/2)
 o=bpy.context.object;o.name=n;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');o.data.materials.append(ma);o.color=ma.diffuse_color
 if bevel:mod=o.modifiers.new('Soft edge','BEVEL');mod.width=bevel;mod.segments=2
 for p in o.data.polygons:p.use_smooth=True
 return o

def curve(n,points,rad,ma):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=rad;c.bevel_resolution=3;c.resolution_u=2
 s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,co in zip(s.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);o.data.materials.append(ma);o.color=ma.diffuse_color
 return o

def box(n,loc,scale,ma):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);o.color=ma.diffuse_color
 b=o.modifiers.new('Rounded steel edge','BEVEL');b.width=.006;b.segments=3
 return o
# A single rope is looped around a fixed steel bollard and gives two free working ends.
box('Floor anchor plate',(0,-3.08,.014),(.31,.24,.028),metal)
for x in [-.12,.12]:
 for y in [-3.165,-2.995]:cyl('Anchor bolt',(x,y,.025),(x,y,.033),.013,ringmat,.001)
cyl('Fixed anchor bollard',(0,-3.08,.028),(0,-3.08,.14),.047,ringmat,.003)
cyl('Bollard retaining cap',(0,-3.08,.136),(0,-3.08,.153),.061,metal,.003)
loop=[]
for i in range(65):
 a=math.pi*i/64;loop.append(V((.066*math.cos(a),-3.08-.066*math.sin(a),.056)))
curve('Continuous rope loop around bollard',loop,.018,rope_mat)
handles=[];ropes=[];braids=[]
N=161
for side in ['l','r']:
 root=bpy.data.objects.new('Rope handle '+side,None);bpy.context.collection.objects.link(root);root.rotation_mode='QUATERNION'
 for ob in [cyl('Rubber hand grip '+side,(0,-.065,0),(0,.065,0),.0145,grip_mat),cyl('Grip end lip '+side,(0,.065,0),(0,.071,0),.0175,grip_mat,.001)]:ob.parent=root
 # Fine shallow ridges remain beneath the enclosing fingers.
 for yy in [-.052,-.035,-.018,-.001,.016,.033,.050]:
  ob=cyl('Grip rib '+side,(0,yy-.001,0),(0,yy+.001,0),.0148,grip_mat,.0004);ob.parent=root
 handles.append(root)
 ropes.append(curve('Battle rope '+side,[V((0,0,0))]*N,.018,rope_mat))
 # Dark helical filament over each cable makes the rope material visible in close-up.
 braid_mat=mat('Rope strand accent '+side,(.051,.061,.069))
 braids.append([curve('Braided strand '+side+str(j),[V((0,0,0))]*N,.0015,braid_mat) for j in range(2)])

def segment(name,a,b):
 bone=bones[name];q=(bone.tail_local-bone.head_local).rotation_difference(b-a)
 return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[name]

def ik(a,w,L1,L2,pole):
 d=w-a;dist=d.length;u=d.normalized();q=pole-u*pole.dot(u);q.normalize()
 along=(L1*L1-L2*L2+dist*dist)/(2*dist);height=math.sqrt(max(0,L1*L1-along*along))
 return a+u*along+q*height

def setgrip(desired,side,s,w,df):
 rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed()
 dy=df;dx=V((0,-1,0));dx=(dx-dy*dx.dot(dy)).normalized();dz=dx.cross(dy).normalized();C=Matrix((dx,dy,dz)).transposed();T=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw)
 desired['hand_'+side]=T@rest['hand_'+side]
 cy,cz=.095,-.039;center=w+dy*cy+dz*(cz*s);radius=.0325
 for finger in ['index','middle','ring','pinky']:
  name=f'{finger}_01_{side}';start=T@bones[name].head_local;rel=start-w;tx=rel.dot(dx);sy=rel.dot(dy);sz=rel.dot(dz)*s
  ry0,rz0=sy-cy,sz-cz;d=math.hypot(ry0,rz0);L=bones[name].length
  ca=max(-1.,min(1.,(d*d+radius*radius-L*L)/(2*d*radius)));angle=math.atan2(rz0,ry0)-math.acos(ca)
  for k in range(1,4):
   name=f'{finger}_{k:02}_{side}';b=bones[name]
   if k>1:angle-=2*math.asin(min(.999,b.length/(2*radius)))
   end=w+dx*tx+dy*(cy+radius*math.cos(angle))+dz*((cz+radius*math.sin(angle))*s)
   old=T.to_3x3()@(b.tail_local-b.head_local);turn=old.rotation_difference(end-start).to_matrix().to_4x4()
   desired[name]=Matrix.Translation(start)@turn@T.to_3x3().to_4x4()@Matrix.Translation(-b.head_local)@rest[name];start=end
 start=T@bones['thumb_01_'+side].head_local
 for k,(tx,ty,tz) in enumerate([(.052,.069,-.008),(.039,.105,-.011),(.010,.116,-.019)],1):
  n=f'thumb_{k:02}_{side}';target=w+dx*tx+dy*ty+dz*(tz*s);end=start+(target-start).normalized()*bones[n].length;desired[n]=segment(n,start,end);start=end
 return center,dx

def ropepoints(start,tangent,anchor,phase):
 points=[]
 for i in range(N):
  u=i/(N-1);p=start.lerp(anchor,u)
  # Decaying hand-height envelope plus a travelling, floor-clearing transverse wave.
  amp=.160*math.sin(math.pi*u)**.68
  p.z=anchor.z+(start.z-anchor.z)*(1-u)**3+amp*(1+math.sin(phase-2*math.pi*2.15*u))
  # Match the handle exit tangent over the initial segment to avoid a rope kink.
  if u<.12:
   t=u/.12;q=.12;end=start.lerp(anchor,q);a=.160*math.sin(math.pi*q)**.68;end.z=anchor.z+(start.z-anchor.z)*(1-q)**3+a*(1+math.sin(phase-2*math.pi*2.15*q))
   eps=.0001;q2=q+eps;end2=start.lerp(anchor,q2);a2=.160*math.sin(math.pi*q2)**.68;end2.z=anchor.z+(start.z-anchor.z)*(1-q2)**3+a2*(1+math.sin(phase-2*math.pi*2.15*q2))
   m1=(end2-end)/eps*.12;m0=tangent*.22
   p=(2*t**3-3*t*t+1)*start+(t**3-2*t*t+t)*m0+(-2*t**3+3*t*t)*end+(t**3-t*t)*m1
  points.append(p)
 return points

records=[]
def pose(frame,key=True):
 phase=2*math.pi*(frame-1)/24
 desired={n:m.copy() for n,m in rest.items()}
 hip=bones['pelvis'].head_local.copy();T=Matrix.Translation(V((0,.085,-.092)))@Matrix.Translation(hip)@Matrix.Rotation(math.radians(9),4,'X')@Matrix.Translation(-hip)
 for n in desired:
  if n!='Root':desired[n]=T@rest[n]
 for side,s in [('l',1),('r',-1)]:
  a=T@bones['thigh_'+side].head_local;ankle=bones['calf_'+side].tail_local+V((s*.095,0,0));knee=ik(a,ankle,bones['thigh_'+side].length,bones['calf_'+side].length,V((s*.2,-1,0)))
  desired['thigh_'+side]=segment('thigh_'+side,a,knee);desired['calf_'+side]=segment('calf_'+side,knee,ankle)
  F=Matrix.Translation(ankle-bones['calf_'+side].tail_local)
  for n in ['foot_'+side,'ball_'+side]:desired[n]=F@rest[n]
 frame_data={'frame':frame,'phase':phase,'handles':[],'rope_min_heights':[]}
 for i,(side,s) in enumerate([('l',1),('r',-1)]):
  ph=phase+i*math.pi;a=T@bones['upperarm_'+side].head_local
  w=V((s*.285,-.36-.018*math.sin(ph),.99+.113*math.sin(ph)))
  e=ik(a,w,bones['upperarm_'+side].length,bones['lowerarm_'+side].length,V((s*.33,-.7,-.72)))
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  df=(w-e).normalized();center,axis=setgrip(desired,side,s,w,df)
  handles[i].location=center;handles[i].rotation_quaternion=V((0,1,0)).rotation_difference(axis)
  # Rope exits the front of the short cylindrical grip, maintaining continuous contact.
  start=center+axis*.071;anchor=V((s*.066,-3.08,.056));points=ropepoints(start,axis,anchor,ph)
  for p,co in zip(ropes[i].data.splines[0].points,points):
   p.co=(*co,1)
   if key:p.keyframe_insert('co',frame=frame)
  for j,braid in enumerate(braids[i]):
   for k,(p,co) in enumerate(zip(braid.data.splines[0].points,points)):
    prev=points[max(0,k-1)];nxt=points[min(N-1,k+1)];tan=(nxt-prev).normalized();b=tan.cross(V((1,0,0))).normalized();c=tan.cross(b).normalized();angle=k*.71+j*math.pi;pp=co+.018*(b*math.cos(angle)+c*math.sin(angle));p.co=(*pp,1)
    if key:p.keyframe_insert('co',frame=frame)
  frame_data['handles'].append({'side':side,'center':list(center),'wrist':list(w),'elbow':list(e),'shoulder':list(a),'axis':list(axis),'rope_exit':list(start),'anchor':list(anchor),'forearm_hand_alignment_degrees':0.0})
  frame_data['rope_min_heights'].append(min(p.z for p in points)-.0195)
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n]
  pb.matrix_basis=ref.inverted()@desired[n];pb.rotation_mode='QUATERNION'
  if key:
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=frame)
 for o in handles:
  if key:o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_quaternion',frame=frame)
 bpy.context.view_layer.update();return frame_data

for f in range(1,26):records.append(pose(f))
for action in bpy.data.actions:
 for fc in action.fcurves:
  for key in fc.keyframe_points:key.interpolation='LINEAR'
  fc.modifiers.new('CYCLES')
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False;scene.world.color=(1,1,1)
sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
scene.display.render_aa='8';scene.view_settings.view_transform='Standard';scene.view_settings.exposure=.28;scene.render.fps=24;scene.frame_start=1;scene.frame_end=96
cam=scene.camera;cam.location=V((4.4,-6.4,3.5));target=V((0,-1.35,.72));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.95
scene.frame_set(7);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'battle_rope_xhigh.blend'),compress=True)
(QA/'motion_geometry.json').write_text(json.dumps(records,indent=2))
frames=[7,19,1] if '--preview' in sys.argv else [7]+[f for f in range(1,25) if f!=7]
for f in frames:
 scene.frame_set(f);scene.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
if '--preview' in sys.argv:
 scene.frame_set(7)
 for i,s in enumerate(['l','r']):
  p=handles[i].location;cam.location=p+V(((1 if s=='l' else -1)*.28,-.43,.22));cam.rotation_euler=(p-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.32;scene.render.filepath=str(QA/f'grip_{s}.png');bpy.ops.render.render(write_still=True)
print('DONE',flush=True)
