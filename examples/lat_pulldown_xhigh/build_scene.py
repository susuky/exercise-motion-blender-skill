"""Reproducible seated wide-grip front lat pulldown, Blender 4.3.2.
Run: blender -b -t 4 --python build_scene.py -- --stills
Rerender saved scene using scripts/render.py.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector as V,Matrix
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent.parent/'assets/improved_human.blend'))
keep={'Human','Human.rig','Black shorts'}
for o in list(bpy.data.objects):
 if o.name not in keep:bpy.data.objects.remove(o,do_unlink=True)
h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];shorts=bpy.data.objects['Black shorts'];bones=rig.data.bones
for o in [h,rig,shorts]:o.animation_data_clear()
rest={b.name:b.matrix_local.copy() for b in bones}

def mat(n,c,rough=.65):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.roughness=rough;return m
steel=mat('Powder coated cool graphite',(.16,.20,.23));metal=mat('Brushed metal',(.47,.53,.56),.25);rubber=mat('Graphite padded upholstery',(.030,.038,.045));cablemat=mat('Black steel cable',(.025,.03,.035));accent=mat('Equipment inset',(.32,.37,.40));white=mat('White',(.96,.96,.96))

def cylinder(n,a,b,r,m,bevel=.003,vertices=48,parent=None):
 a,b=V(a),V(b);bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=n;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');o.data.materials.append(m);o.color=m.diffuse_color
 if bevel:be=o.modifiers.new('Rounded edge','BEVEL');be.width=bevel;be.segments=3
 for p in o.data.polygons:p.use_smooth=True
 if parent:o.parent=parent
 return o

def box(n,loc,scale,m,bevel=.018):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.color=m.diffuse_color
 if bevel:be=o.modifiers.new('Soft corners','BEVEL');be.width=bevel;be.segments=4
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def curve(n,pts,rad,ma):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=rad;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 ob=bpy.data.objects.new(n,cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(ma);ob.color=ma.diffuse_color;return ob

# A compact lat-pulldown station. The tower is behind the lifter, the pulley
# reaches forward and the knee restraint bears against the upper thighs.
box('Rear base',(0,.43,.038),(.70,.78,.065),steel)
box('Seat rail',(0,-.09,.075),(.10,1.20,.09),steel)
box('Seat pedestal',(0,.03,.21),(.095,.095,.27),steel)
box('Seat cushion',(0,.015,.371),(.43,.36,.075),rubber,.045)
box('Rear tower',(0,.69,.99),(.105,.11,1.91),steel)
box('Tower top cap',(0,.69,1.97),(.14,.14,.05),rubber)
box('Upper forward beam',(0,.22,1.928),(.075,1.05,.075),steel)
box('Stack bottom',(0,.49,.14),(.43,.30,.09),steel)
# Weight stack and guide rods remain clear of the body and seat.
for x in [-.16,.16]:cylinder('Weight guide rail',(x,.52,.20),(x,.52,1.43),.011,metal,.001)
for i in range(13):box('Stationary weight plate %02d'%i,(0,.52,.207+i*.026),(.34,.24,.023),steel,.005)
stack=box('Lifted selected weight stack',(0,.52,.665),(.34,.24,.15),accent,.006)
pin=cylinder('Selector pin',(.18,.41,.65),(.18,.33,.65),.012,rubber);pin.parent=stack;pin.matrix_parent_inverse=stack.matrix_world.inverted()
# Restraint support located in front of the knees, padded rollers sit on thighs.
box('Thigh pad support',(0,-.45,.38225),(.06,.07,.5945),steel,.012)
box('Thigh pad connecting bracket',(0,-.38,.6545),(.06,.21,.05),steel,.008)
cylinder('Thigh pad axle',(-.31,-.31,.6795),(.31,-.31,.6795),.018,metal,.002)
for s in [-1,1]:cylinder('Thigh restraint pad',(.045*s,-.31,.6795),(.30*s,-.31,.6795),.075,rubber,.016)
for y in [-.21,.57]:
 cylinder('Upper cable pulley',(-.029,y,1.868),(.029,y,1.868),.047,rubber,.003)
 cylinder('Pulley axle',(-.055,y,1.868),(.055,y,1.868),.012,metal,.002)
# Fixed upper cable makes contact with the upper circumference of both sheaves.
curve('Fixed cable over tower',[(0,-.21,1.915),(0,.57,1.915)],.0032,cablemat)
returncable=cylinder('Return cable to weight stack',(0,0,0),(0,0,1),.0032,cablemat,0,16)

# Straight center bar with curved-down safety tips; grips lie on its straight ends.
bar=bpy.data.objects.new('Lat bar animated assembly',None);bpy.context.collection.objects.link(bar)
cylinder('Wide grip bar',(-.575,0,0),(.575,0,0),.0135,metal,.002,parent=bar)
for sign in [-1,1]:
 cylinder('Knurled grip',(.375*sign,0,0),(.565*sign,0,0),.0145,rubber,.002,parent=bar)
 cylinder('Safety tip',(.575*sign,0,0),(.61*sign,0,-.035),.015,metal,.003,parent=bar)
 cylinder('Bar end plug',(.608*sign,0,-.033),(.615*sign,0,-.041),.019,rubber,.002,parent=bar)
cylinder('Cable attachment stem',(0,0,0),(0,0,.040),.013,metal,.002,parent=bar)
bpy.ops.mesh.primitive_torus_add(major_radius=.018,minor_radius=.004,major_segments=32,minor_segments=12,location=(0,0,.047),rotation=(math.pi/2,0,0));eye=bpy.context.object;eye.name='Bar cable eye';eye.data.materials.append(metal);eye.color=metal.diffuse_color;eye.parent=bar
livecable=cylinder('Taut active cable',(0,0,0),(0,0,1),.0032,cablemat,0,16)

# Transfer deltoid highlight to broad latissimus and elbow flexors.
attr=h.data.color_attributes.get('Anatomical fibres')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
for i,v in enumerate(h.data.vertices):
 x,y,z=v.co;ax=abs(x);c=attr.data[i].color
 if c[0]>c[1]+.0001:
  val=c[0]/.72;attr.data[i].color=(.73*val,.75*val,.76*val,1)
 # The lats taper to the lumbar fascia with no artificial circular boundary.
 lat=band(z,1.035,1.345,.035)*smooth(.057,.10,ax)*(1-smooth(.16,.211,ax))*smooth(-.025,.055,y)
 # Visible flank wraps around the side of the rib cage.
 flank=band(z,1.08,1.30,.04)*band(ax,.136,.193,.021)*smooth(-.11,-.015,y)
 red=max(lat,flank)
 if red>0:
  fib=(.5+.5*math.cos((z-.70*ax)*1350))**6
  rc=(.67*(1-.19*fib),.073*(1-.2*fib),.051*(1-.2*fib));c=attr.data[i].color;attr.data[i].color=tuple(c[k]*(1-red)+rc[k]*red for k in range(3))+(1,)

# Exact two-link arm geometry and per-digit cylindrical bar grip.
def segment(n,a,b):
 bone=bones[n];q=(bone.tail_local-bone.head_local).rotation_difference(b-a);return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n]

def pose(t):
 # Cosine motion has zero velocity at both ends; 80 frames sample one full cycle.
 pull=(1-math.cos(2*math.pi*t))/2
 lean=math.radians(-7-2*pull)
 hip=V((0,0,.5185));origin=bones['pelvis'].head_local.copy();Q=Matrix.Rotation(lean,4,'X');T=Matrix.Translation(hip)@Q@Matrix.Translation(-origin)
 desired={n:T@m for n,m in rest.items()};joints={}
 # Independent stable legs preserve thigh and shank lengths.
 for side,sign in [('l',1),('r',-1)]:
  a=T@bones['thigh_'+side].head_local;L=bones['thigh_'+side].length
  d=V((sign*.09,-1,-.015)).normalized();knee=a+d*L
  calf=bones['calf_'+side];d=V((sign*.035,-.055,-1)).normalized();ankle=knee+d*calf.length
  desired['thigh_'+side]=segment('thigh_'+side,a,knee);desired['calf_'+side]=segment('calf_'+side,knee,ankle)
  footT=Matrix.Translation(ankle-bones['foot_'+side].head_local)
  for part in ['foot','ball']:desired[part+'_'+side]=footT@rest[part+'_'+side]
  joints['hip_'+side]=tuple(a);joints['knee_'+side]=tuple(knee);joints['ankle_'+side]=tuple(ankle)
 bar.location=V((0,-.21+.13*pull,1.4865-.475*pull))
 for side,sign in [('l',1),('r',-1)]:
  # Scapular elevation at full stretch travels with the clavicle.
  c0=T@bones['clavicle_'+side].head_local;a=T@bones['upperarm_'+side].head_local+V((0,0,.026*(1-pull)))
  desired['clavicle_'+side]=segment('clavicle_'+side,c0,a)
  dx=V((-sign,0,0));dy=V((0,-.11+.06*pull,1)).normalized()
  center=bar.location+V((.435*sign,0,0));cy,cz=.095,-.039
  L1=bones['upperarm_'+side].length;L2=bones['lowerarm_'+side].length
  for grip_iteration in range(24):
   dz=dx.cross(dy).normalized();w=center-dy*cy-dz*(cz*sign)
   u=w-a;D=u.length;u.normalize()
   if D>L1+L2-.0003:raise RuntimeError(('Arm reach',t,side,D,L1+L2))
   along=(L1*L1-L2*L2+D*D)/(2*D);height=math.sqrt(max(0,L1*L1-along*along))
   pole=V((sign*.40,.08,-1));pole=(pole-u*pole.dot(u)).normalized();e=a+u*along+pole*height
   neutral=w-e;neutral.x=0;neutral.normalize();dy=(dy*.5+neutral*.5).normalized()
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed();C=Matrix((dx,dy,dz)).transposed();HT=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw);desired['hand_'+side]=HT@rest['hand_'+side]
  radius=.0325
  for finger in ['index','middle','ring','pinky']:
   n=f'{finger}_01_{side}';start=HT@bones[n].head_local;rel=start-w;tx=rel.dot(dx);sy=rel.dot(dy);sz=rel.dot(dz)*sign;ry0,rz0=sy-cy,sz-cz;d=math.hypot(ry0,rz0);L=bones[n].length;ca=max(-1,min(1,(d*d+radius*radius-L*L)/(2*d*radius)));ang=math.atan2(rz0,ry0)-math.acos(ca)
   for k in range(1,4):
    n=f'{finger}_{k:02}_{side}';bone=bones[n]
    if k>1:ang-=2*math.asin(min(.999,bone.length/(2*radius)))
    end=w+dx*tx+dy*(cy+radius*math.cos(ang))+dz*((cz+radius*math.sin(ang))*sign);original=HT.to_3x3()@(bone.tail_local-bone.head_local);turn=original.rotation_difference(end-start).to_matrix().to_4x4();desired[n]=Matrix.Translation(start)@turn@HT.to_3x3().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n];start=end
  start=HT@bones['thumb_01_'+side].head_local
  for kk,(tx,ty,tz) in enumerate([(.052,.069,-.008),(.039,.105,-.011),(.010,.116,-.019)],1):
   n=f'thumb_{kk:02}_{side}';target=w+dx*tx+dy*ty+dz*(tz*sign);end=start+(target-start).normalized()*bones[n].length;desired[n]=segment(n,start,end);start=end
  joints['shoulder_'+side]=tuple(a);joints['elbow_'+side]=tuple(e);joints['wrist_'+side]=tuple(w);joints['grip_'+side]=tuple(center)
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@desired[n]
 # Cylinder's own local Z length is rescaled, so its endpoints remain attached.
 start=V((0,-.257,1.868));end=bar.location+V((0,0,.063));livecable.location=(start+end)/2;livecable.rotation_quaternion=(end-start).to_track_quat('Z','Y');livecable.scale.z=(end-start).length
 initial_cable_length=(V((0,-.257,1.868))-V((0,-.21,1.5495))).length
 stack.location.z=.6075+(end-start).length-initial_cable_length
 returnstart=V((0,.617,1.868));returnend=V((0,.617,stack.location.z+.075));returncable.location=(returnstart+returnend)/2;returncable.rotation_quaternion=(returnend-returnstart).to_track_quat('Z','Y');returncable.scale.z=(returnend-returnstart).length
 bpy.context.view_layer.update();return {'t':t,'pull':pull,'joints':joints,'bar':tuple(bar.location),'cable_start':tuple(start),'cable_end':tuple(end)}

frames=[]
for f in range(1,82):
 frame=pose((f-1)/80);frames.append(frame)
 for pb in rig.pose.bones:
  pb.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=f)
 for o in [bar,livecable,returncable,stack]:
  for prop in ['location','rotation_quaternion','scale']:o.keyframe_insert(data_path=prop,frame=f)
for ob in [rig,bar,livecable,returncable,stack]:
 if ob.animation_data and ob.animation_data.action:
  for fc in ob.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
(OUT/'motion.json').write_text(json.dumps(frames,indent=2))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False;s.world.color=(1,1,1)
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
s.display.render_aa='8';s.view_settings.view_transform='Standard';s.view_settings.exposure=.28;s.render.fps=20;s.frame_start=1;s.frame_end=80
bpy.ops.object.camera_add(location=(3.15,-5.7,2.42));cam=bpy.context.object;cam.name='Full body seated pulldown camera';cam.rotation_euler=(V((0,.12,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.40;s.camera=cam
s.frame_set(41);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'lat_pulldown_xhigh.blend'),compress=True)
if '--stills' in sys.argv:
 for f in [1,21,41,61]:
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f:03d}.png');bpy.ops.render.render(write_still=True)
print('SCENE COMPLETE',flush=True)
