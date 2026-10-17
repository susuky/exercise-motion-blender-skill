"""Conventional barbell deadlift, Blender 4.3.2. Reuses the improved skinned human.
Run: blender -b -t 3 --python build_scene.py -- --stills
"""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector as V,Matrix
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';QA=ROOT/'qa'
OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parents[1]/'assets/improved_human.blend'))
keep={'Human','Human.rig','Black shorts'}
for o in list(bpy.data.objects):
 if o.name not in keep:bpy.data.objects.remove(o,do_unlink=True)
h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];shorts=bpy.data.objects['Black shorts'];bones=rig.data.bones
for o in [h,rig,shorts]:o.animation_data_clear()
for p in rig.pose.bones:p.matrix_basis.identity()
rest={b.name:b.matrix_local.copy() for b in bones}

def mat(n,c,rough=.65):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.roughness=rough;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough
 return m
metal=mat('Brushed stainless steel',(.48,.53,.56),.25);knurl=mat('Fine knurled steel',(.35,.40,.43),.42);rubber=mat('Dark graphite bumper plates',(.035,.044,.053));ridge=mat('Bumper rim rubber',(.055,.065,.075));hubmat=mat('Recessed steel plate hubs',(.27,.31,.34),.28)

def cylinder(n,a,b,r,m,bevel=.002,vertices=64,parent=None):
 a,b=V(a),V(b);bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=n;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');o.data.materials.append(m);o.color=m.diffuse_color
 if bevel:be=o.modifiers.new('Soft machined edge','BEVEL');be.width=bevel;be.segments=3
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 if parent:o.parent=parent
 return o

def torus(n,x,r,t,ma,parent):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=96,minor_segments=12,location=(x,0,0),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=n;o.data.materials.append(ma);o.color=ma.diffuse_color;o.parent=parent
 for p in o.data.polygons:p.use_smooth=True
 return o
bar=bpy.data.objects.new('Loaded straight barbell',None);bpy.context.collection.objects.link(bar);bar.rotation_mode='QUATERNION'
BAR_RADIUS=.0145
cylinder('Central straight shaft',(-.265,0,0),(.265,0,0),BAR_RADIUS,metal,0,parent=bar)
for sign in [-1,1]:cylinder('Outer straight shaft',(.625*sign,0,0),(1.03*sign,0,0),BAR_RADIUS,metal,0,parent=bar)
# Fine darker grips remain straight and are the same diameter as the bar.
for sign in [-1,1]:
 cylinder('Knurled grip zone',(.265*sign,0,0),(.625*sign,0,0),BAR_RADIUS,knurl,0,parent=bar)
 cylinder('Sleeve shoulder',(.65*sign,0,0),(.69*sign,0,0),.046,metal,.003,parent=bar)
 cylinder('50 mm loading sleeve',(.69*sign,0,0),(1.045*sign,0,0),.025,metal,.002,parent=bar)
 for i,(cx,rad,thick) in enumerate([(.756,.225,.105),(.849,.225,.064)]):
  cylinder('Loaded bumper plate %s %s'%(sign,i),((cx-thick/2)*sign,0,0),((cx+thick/2)*sign,0,0),rad,rubber,.008,96,bar)
  for side in [-1,1]:
   xx=(cx+side*thick/2)*sign
   torus('Moulded plate rim',xx,rad-.014,.005,ridge,bar)
   cylinder('Flush steel hub',((cx+side*thick/2-.0015)*sign,0,0),((cx+side*thick/2+.0015)*sign,0,0),.052,hubmat,.001,64,bar)
 cylinder('Locking collar',(.89*sign,0,0),(.929*sign,0,0),.043,hubmat,.005,parent=bar)
 cylinder('Sleeve end cap',(1.041*sign,0,0),(1.048*sign,0,0),.026,hubmat,.001,parent=bar)
# Qualitative anatomy-oriented role overlay. Bone-relative masks are applied
# in bind space, so colors stay on the same skin throughout deformation.
# Primary red: gluteal/quadriceps regions; secondary blue: hamstrings/erectors.
attr=h.data.color_attributes.get('Anatomical fibres')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
spinebase=bones['spine_01'].head_local;spinetop=bones['spine_03'].tail_local;spineaxis=(spinetop-spinebase).normalized();spinelen=(spinetop-spinebase).length
for i,v in enumerate(h.data.vertices):
 x,y,z=v.co;c=attr.data[i].color
 if c[0]>c[1]+.001:
  val=c[0]/.72;attr.data[i].color=(.73*val,.75*val,.76*val,1)
 side='l' if x>=0 else 'r';b=bones['thigh_'+side];axis=(b.tail_local-b.head_local).normalized();q=v.co-b.head_local;t=q.dot(axis)/b.length;rad=q-axis*q.dot(axis)
 dynamic=0.;stabilizer=0.;secondary=0.;phase=0.
 if .12<t<.94 and .025<rad.length<.16 and c[0]>.1:
  back=V((0,1,0));back=(back-axis*back.dot(axis)).normalized();co=rad.normalized().dot(back)
  hamstring=band(t,.16,.88,.065)*smooth(.12,.45,co)
  quad=band(t,.16,.88,.065)*smooth(.10,.42,-co)
  dynamic=quad;secondary=hamstring;phase=math.atan2(rad.x,rad.dot(back))*88+.12*t
 # Posterior gluteal skin is marked beneath the unchanged garment.
 hip=bones['thigh_'+side].head_local;g=v.co-hip
 glute=band(g.z,-.095,.067,.025)*band(abs(g.x),.012,.120,.022)*smooth(.025,.090,g.y)
 dynamic=max(dynamic,glute)
 sq=v.co-spinebase;st=sq.dot(spineaxis)/spinelen;sr=sq-spineaxis*sq.dot(spineaxis)
 stabilizer=max(secondary,band(st,.06,1.08,.12)*band(abs(sr.x),.025,.090,.017)*smooth(.018,.058,sr.y))
 if dynamic>0 or stabilizer>0:
  fib=(.5+.5*math.cos(phase if dynamic>=stabilizer or secondary>=stabilizer else sr.x*1320+st*8))**6
  base=(.68,.077,.055) if dynamic>=stabilizer else (.055,.22,.68)
  strength=max(dynamic,stabilizer);rc=tuple(v*(1-.18*fib) for v in base);c=attr.data[i].color;attr.data[i].color=tuple(c[k]*(1-strength)+rc[k]*strength for k in range(3))+(1,)

# Pin the plantar skin to the fixed foot transform, fading back to the original
# ankle weights above 4 cm. This removes sub-millimetre heel drift from calf blend.
for v in h.data.vertices:
 if v.co.z<.065:
  side='l' if v.co.x>=0 else 'r';footgroup=h.vertex_groups['foot_'+side];pin=1-smooth(.040,.065,v.co.z)
  old=[(g.group,g.weight) for g in v.groups]
  for gi,wt in old:h.vertex_groups[gi].add([v.index],wt*(1-pin),'REPLACE')
  former=sum(wt for gi,wt in old if gi==footgroup.index);footgroup.add([v.index],former*(1-pin)+pin,'REPLACE')

def segment(n,a,b):
 bone=bones[n];q=(bone.tail_local-bone.head_local).rotation_difference(b-a);return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n]

def ik(a,w,L1,L2,pole):
 v=w-a;D=v.length;u=v.normalized()
 if D>L1+L2-.00005:raise RuntimeError(('Unreachable',D,L1+L2))
 p=(pole-u*pole.dot(u)).normalized();al=(L1*L1-L2*L2+D*D)/(2*D);he=math.sqrt(max(0,L1*L1-al*al));return a+u*al+p*he

BAR_Y=-.163;PLATE_RADIUS=.225;GRIP_X=.290
CY,CZ=.095,-.039
FINGER_RADII={f:.0325 for f in ['index','middle','ring','pinky']};THUMB_INSET=0.0
origin=bones['pelvis'].head_local.copy()
ANKLE=V((.140,-.0149,.0711));KNEE_X=.135
L1=bones['thigh_l'].length;L2=bones['calf_l'].length
TY=math.sqrt(L1*L1-(KNEE_X-bones['thigh_l'].head_local.x)**2)
SY=math.sqrt(L2*L2-(ANKLE.x-KNEE_X)**2)
ARM=bones['upperarm_l'].length+bones['lowerarm_l'].length
ARM_YZ=math.sqrt(ARM*ARM-(GRIP_X-bones['upperarm_l'].head_local.x)**2)
A=ARM_YZ+CY;R=math.hypot(A,CZ)

def skeleton(u,lean0):
 shin=math.radians(25*(1-u)**1.5);thigh=math.radians(68*(1-u)+.8*u)
 lean=math.radians(lean0*(1-u**2.5))
 knee=V((KNEE_X,ANKLE.y-SY*math.sin(shin),ANKLE.z+SY*math.cos(shin)))
 hipjoint=V((bones['thigh_l'].head_local.x,knee.y+TY*math.sin(thigh),knee.z+TY*math.cos(thigh)))
 Q=Matrix.Rotation(lean,4,'X');hip=hipjoint-Q@(bones['thigh_l'].head_local-origin)
 T=Matrix.Translation(hip)@Q@Matrix.Translation(-origin)
 shoulder=T@bones['upperarm_l'].head_local;off=BAR_Y-shoulder.y
 bz=shoulder.z-math.sqrt(R*R-off*off)
 return T,knee,V((0,BAR_Y,bz)),lean
# A grounded standard 450 mm plate determines the exact floor setup lean.
lo,hi=55.,75.
for _ in range(40):
 mid=(lo+hi)/2
 if skeleton(0,mid)[2].z>PLATE_RADIUS:lo=mid
 else:hi=mid
LEAN0=(lo+hi)/2

def full_pose(u):
 T,knee,bc,lean=skeleton(u,LEAN0);desired={n:T@m for n,m in rest.items()};joints={}
 for side,sign in [('l',1),('r',-1)]:
  a=T@bones['thigh_'+side].head_local;kn=V((sign*knee.x,knee.y,knee.z));an=V((sign*ANKLE.x,ANKLE.y,ANKLE.z));yaw=Matrix.Rotation(sign*math.radians(7),4,'Z');F=Matrix.Translation(an)@yaw@Matrix.Translation(-bones['calf_'+side].tail_local)
  desired['thigh_'+side]=segment('thigh_'+side,a,kn);desired['calf_'+side]=segment('calf_'+side,kn,an)
  for part in ['foot','ball']:desired[part+'_'+side]=F@rest[part+'_'+side]
  joints.update({'hip_'+side:a,'knee_'+side:kn,'ankle_'+side:an})
  a=T@bones['upperarm_'+side].head_local;center=bc+V((sign*GRIP_X,0,0));v=center-a;dy=V((0,A*v.y-CZ*v.z,CZ*v.y+A*v.z)).normalized();dx=V((-sign,0,0));dz=dx.cross(dy).normalized();w=center-dy*CY-dz*(CZ*sign);e=a+(w-a)*(bones['upperarm_'+side].length/ARM)
  if abs((w-a).length-ARM)>.00001:raise RuntimeError(('Arm length mismatch',u,(w-a).length,ARM))
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed();C=Matrix((dx,dy,dz)).transposed();HT=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw);desired['hand_'+side]=HT@rest['hand_'+side]
  cy,cz=CY,CZ
  for finger in ['index','middle','ring','pinky']:
   radius=FINGER_RADII[finger]
   n=f'{finger}_01_{side}';start=HT@bones[n].head_local;rel=start-w;tx=rel.dot(dx);sy=rel.dot(dy);sz=rel.dot(dz)*sign;ry0,rz0=sy-cy,sz-cz;d=math.hypot(ry0,rz0);L=bones[n].length;ca=max(-1,min(1,(d*d+radius*radius-L*L)/(2*d*radius)));ang=math.atan2(rz0,ry0)-math.acos(ca)
   for k in range(1,4):
    n=f'{finger}_{k:02}_{side}';bone=bones[n]
    if k>1:ang-=2*math.asin(min(.999,bone.length/(2*radius)))
    end=w+dx*tx+dy*(cy+radius*math.cos(ang))+dz*((cz+radius*math.sin(ang))*sign);original=HT.to_3x3()@(bone.tail_local-bone.head_local);turn=original.rotation_difference(end-start).to_matrix().to_4x4();desired[n]=Matrix.Translation(start)@turn@HT.to_3x3().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n];start=end
  start=HT@bones['thumb_01_'+side].head_local
  for kk,(tx,ty,tz) in enumerate([(.052,.069,-.008),(.039,.105,-.011),(.010,.116,-.019)],1):
   n=f'thumb_{kk:02}_{side}';target=w+dx*tx+dy*ty+dz*(tz*sign);radial=target-center;radial-=dx*radial.dot(dx);target-=radial.normalized()*THUMB_INSET;end=start+(target-start).normalized()*bones[n].length;desired[n]=segment(n,start,end);start=end
  joints['shoulder_'+side]=a;joints['elbow_'+side]=e;joints['wrist_'+side]=w;joints['grip_'+side]=center
  joints['hand_direction_'+side]=dy
 return desired,joints,bc,lean

def apply(desired):
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@desired[n];pb.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
# Fit each digit's surface once in the invariant local grip frame.
digitmasks={}
for finger in ['thumb','index','middle','ring','pinky']:
 ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_')}
 digitmasks[finger]=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices])
bounds={f:[.022,.038] for f in FINGER_RADII};thumbbounds=[0,.016]
for fit_iteration in range(15):
 for finger in FINGER_RADII:FINGER_RADII[finger]=sum(bounds[finger])/2
 THUMB_INSET=sum(thumbbounds)/2;desired,joints,bc,lean=full_pose(.5);apply(desired)
 ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3);rad=np.hypot(coords[:,1]-bc.y,coords[:,2]-bc.z);ev.to_mesh_clear()
 for finger in FINGER_RADII:
  if float(rad[digitmasks[finger]].min()-BAR_RADIUS)<.00060:bounds[finger][0]=FINGER_RADII[finger]
  else:bounds[finger][1]=FINGER_RADII[finger]
 if float(rad[digitmasks['thumb']].min()-BAR_RADIUS)<.00060:thumbbounds[1]=THUMB_INSET
 else:thumbbounds[0]=THUMB_INSET
for finger in FINGER_RADII:FINGER_RADII[finger]=bounds[finger][1]
THUMB_INSET=thumbbounds[0]
(QA/'grip_fit.json').write_text(json.dumps({'finger_bone_radii_m':FINGER_RADII,'thumb_inset_m':THUMB_INSET,'target_surface_clearance_m':.00060,'binary_iterations':15},indent=2))
records=[]
for f in range(1,82):
 t=(f-1)/80;u=(1-math.cos(2*math.pi*t))/2;desired,joints,bc,lean=full_pose(u);apply(desired)
 for pb in rig.pose.bones:
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=f)
 bar.location=bc;bar.keyframe_insert(data_path='location',frame=f)
 records.append({'frame':f,'t':t,'progress':u,'torso_lean_degrees':math.degrees(lean),'bar':list(bc),'joints':{n:list(v) for n,v in joints.items()}})
for ob in [rig,bar]:
 for fc in ob.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
(OUT/'motion.json').write_text(json.dumps(records,indent=2))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False;s.world.color=(1,1,1)
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
s.display.render_aa='16';s.view_settings.view_transform='Standard';s.view_settings.exposure=.28;s.render.fps=20;s.frame_start=1;s.frame_end=80
bpy.ops.object.camera_add(location=(5.8,5.5,2.9));cam=bpy.context.object;cam.name='Fixed posterior three-quarter deadlift camera';cam.rotation_euler=(V((0,-.02,.84))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.22;s.camera=cam
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'conventional_deadlift.blend'),compress=True)
if '--stills' in sys.argv:
 for f in [1,11,21,31,41]:
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f:03d}.png');bpy.ops.render.render(write_still=True)
print('SCENE COMPLETE',flush=True)
