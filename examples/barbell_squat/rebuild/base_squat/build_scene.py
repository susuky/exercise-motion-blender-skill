"""High-bar barbell back squat, Blender 4.3.2. Reuses the improved skinned human.
Run: blender -b -t 3 --python build_scene.py -- --stills
"""
import bpy,math,json,sys,os,numpy as np
from pathlib import Path
from mathutils import Vector as V,Matrix
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';QA=ROOT/'qa'
OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(os.environ['HUMAN_BLEND'])))
# Validate required shared-asset structure rather than a serialized .blend hash.
# Vertex counts and required bone names come from the original compatible asset.
shared_rig=bpy.data.objects.get('Human.rig')
assert shared_rig is not None and shared_rig.type=='ARMATURE', 'HUMAN_BLEND must contain Human.rig armature'
required_bones={'spine_01', 'spine_03', 'spine_02', 'calf_l', 'calf_r', 'pelvis', 'foot_r', 'neck_01', 'ball_r', 'ring_03_r', 'ring_02_l', 'thumb_02_l', 'hand_l', 'pinky_02_l', 'ball_l', 'index_01_r', 'thumb_02_r', 'middle_03_l', 'index_01_l', 'index_03_l', 'pinky_02_r', 'middle_01_l', 'thumb_01_l', 'ring_02_r', 'head', 'thigh_l', 'foot_l', 'clavicle_r', 'ring_03_l', 'upperarm_r', 'upperarm_l', 'thigh_r', 'index_02_r', 'pinky_01_l', 'pinky_03_r', 'pinky_03_l', 'ring_01_l', 'middle_03_r', 'thumb_03_r', 'ring_01_r', 'lowerarm_r', 'hand_r', 'clavicle_l', 'index_03_r', 'middle_01_r', 'pinky_01_r', 'thumb_03_l', 'middle_02_l', 'thumb_01_r', 'lowerarm_l', 'middle_02_r', 'index_02_l'}
assert required_bones.issubset(set(shared_rig.data.bones.keys())), 'HUMAN_BLEND lacks required motion bones'
for mesh_name,expected_vertices in [('Human',856194),('Black shorts',35183)]:
 shared_mesh=bpy.data.objects.get(mesh_name)
 assert shared_mesh is not None and shared_mesh.type=='MESH', 'HUMAN_BLEND lacks required mesh: '+mesh_name
 assert len(shared_mesh.data.vertices)==expected_vertices, 'Incompatible vertex count: '+mesh_name
 armature_modifiers=[m for m in shared_mesh.modifiers if m.type=='ARMATURE']
 assert len(armature_modifiers)==1 and armature_modifiers[0].object==shared_rig, 'Mesh must bind to Human.rig: '+mesh_name
 assert required_bones.issubset(set(shared_mesh.vertex_groups.keys())), 'Mesh lacks required skinning groups: '+mesh_name
shared_colors=bpy.data.objects['Human'].data.color_attributes.get('Anatomical fibres')
assert shared_colors is not None and shared_colors.domain=='POINT' and len(shared_colors.data)==856194, 'HUMAN_BLEND lacks required per-vertex anatomical colors'
del shared_rig,required_bones,shared_mesh,armature_modifiers,shared_colors
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
 for i,(cx,rad,thick) in enumerate([(.756,.205,.105),(.849,.184,.064)]):
  cylinder('Loaded bumper plate %s %s'%(sign,i),((cx-thick/2)*sign,0,0),((cx+thick/2)*sign,0,0),rad,rubber,.008,96,bar)
  for side in [-1,1]:
   xx=(cx+side*thick/2)*sign
   torus('Moulded plate rim',xx,rad-.014,.005,ridge,bar)
   cylinder('Flush steel hub',((cx+side*thick/2-.0015)*sign,0,0),((cx+side*thick/2+.0015)*sign,0,0),.052,hubmat,.001,64,bar)
 cylinder('Locking collar',(.89*sign,0,0),(.929*sign,0,0),.043,hubmat,.005,parent=bar)
 cylinder('Sleeve end cap',(1.041*sign,0,0),(1.048*sign,0,0),.026,hubmat,.001,parent=bar)
# Retain the sculpted anatomical fibres; move primary red emphasis to quadriceps.
attr=h.data.color_attributes.get('Anatomical fibres')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
for i,v in enumerate(h.data.vertices):
 x,y,z=v.co;c=attr.data[i].color
 if c[0]>c[1]+.001:
  val=c[0]/.72;attr.data[i].color=(.73*val,.75*val,.76*val,1)
 side='l' if x>=0 else 'r';b=bones['thigh_'+side];u=(b.tail_local-b.head_local).normalized();q=v.co-b.head_local;t=q.dot(u)/b.length;rad=q-u*q.dot(u)
 if .12<t<.94 and .025<rad.length<.16 and c[0]>.1:
  front=V((0,-1,0));front=(front-u*front.dot(u)).normalized();co=rad.normalized().dot(front)
  red=band(t,.13,.91,.075)*smooth(-.15,.23,co)
  if red>0:
   fib=(.5+.5*math.cos(math.atan2(rad.x,rad.dot(front))*88+.12*t))**6
   rc=(.68*(1-.18*fib),.077*(1-.2*fib),.055*(1-.2*fib));c=attr.data[i].color;attr.data[i].color=tuple(c[k]*(1-red)+rc[k]*red for k in range(3))+(1,)

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

BAR_LOCAL=V((0,.0852,1.435));GRIP_X=.330
FINGER_RADII={f:.0325 for f in ['index','middle','ring','pinky']};THUMB_INSET=0.0
# The upper body carries the bar as one unit. A planar, wrapped grip is solved
# using the same dense-skin cylindrical finger construction as the lat pulldown.
def upper_pose():
 desired={n:m.copy() for n,m in rest.items()};joints={}
 for side,sign in [('l',1),('r',-1)]:
  a=bones['upperarm_'+side].head_local.copy();dx=V((-sign,0,0));dy=V((0,-.4,1)).normalized();center=BAR_LOCAL+V((sign*GRIP_X,0,0));cy,cz=.095,-.039
  for iteration in range(40):
   dz=dx.cross(dy).normalized();w=center-dy*cy-dz*(cz*sign)
   e=ik(a,w,bones['upperarm_'+side].length,bones['lowerarm_'+side].length,V((sign*1.0,-.4,-1.0)))
   neutral=w-e;neutral.x=0;neutral.normalize();dy=(dy*.5+neutral*.5).normalized()
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed();C=Matrix((dx,dy,dz)).transposed();HT=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw);desired['hand_'+side]=HT@rest['hand_'+side]
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
 return desired,joints
# Fit the bar against the posed upper trapezius using the evaluated dense mesh.
# The 0.25 mm contact tolerance avoids a floating bar and skin interpenetration.
rc=np.empty(len(h.data.vertices)*3);h.data.vertices.foreach_get('co',rc);rc=rc.reshape(-1,3)
trapmask=(rc[:,2]>1.30)&(rc[:,2]<1.49)&(abs(rc[:,0])<.25)
lo,hi=.078,.115
for fit_iteration in range(17):
 BAR_LOCAL.y=(lo+hi)/2;upper,uj=upper_pose()
 for n,pb in rig.pose.bones.items():
  ref=upper[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@upper[n]
 bpy.context.view_layer.update();ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3)
 gap=float(np.hypot(coords[trapmask,1]-BAR_LOCAL.y,coords[trapmask,2]-BAR_LOCAL.z).min()-BAR_RADIUS);ev.to_mesh_clear()
 if gap<.00025:lo=BAR_LOCAL.y
 else:hi=BAR_LOCAL.y
BAR_LOCAL.y=hi;upper,uj=upper_pose()
# Match each digit's surface to the shaft rather than using one finger radius.
# Simultaneous bisection respects the different index/ring/little finger thickness.
digitmasks={}
for finger in ['thumb','index','middle','ring','pinky']:
 ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_')}
 digitmasks[finger]=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices])
bounds={f:[.022,.038] for f in FINGER_RADII};thumbbounds=[0,.016]
for grip_fit_iteration in range(15):
 for finger in FINGER_RADII:FINGER_RADII[finger]=sum(bounds[finger])/2
 THUMB_INSET=sum(thumbbounds)/2;upper,uj=upper_pose()
 for n,pb in rig.pose.bones.items():
  ref=upper[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@upper[n]
 bpy.context.view_layer.update();ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3);rad=np.hypot(coords[:,1]-BAR_LOCAL.y,coords[:,2]-BAR_LOCAL.z);ev.to_mesh_clear()
 for finger in FINGER_RADII:
  gap=float(rad[digitmasks[finger]].min()-BAR_RADIUS)
  if gap<.00015:bounds[finger][0]=FINGER_RADII[finger]
  else:bounds[finger][1]=FINGER_RADII[finger]
 gap=float(rad[digitmasks['thumb']].min()-BAR_RADIUS)
 if gap<.00015:thumbbounds[1]=THUMB_INSET
 else:thumbbounds[0]=THUMB_INSET
for finger in FINGER_RADII:FINGER_RADII[finger]=bounds[finger][1]
THUMB_INSET=thumbbounds[0];upper,uj=upper_pose()
(QA/'grip_fit.json').write_text(json.dumps({'finger_bone_radii_m':FINGER_RADII,'thumb_inset_m':THUMB_INSET,'target_surface_clearance_m':.00015,'binary_iterations':15},indent=2))
(QA/'bar_fit.json').write_text(json.dumps({'bar_local':list(BAR_LOCAL),'target_contact_clearance_m':.00025,'binary_iterations':17},indent=2))
origin=bones['pelvis'].head_local.copy();records=[]
def pose(t,keyframe):
 depth=(1-math.cos(2*math.pi*t))/2;lean=math.radians(12+24*depth);Q=Matrix.Rotation(lean,4,'X')
 hipz=.916-.508*depth
 # Keep the loaded bar vertically above the foot's central support region.
 localbar=Q@(BAR_LOCAL-origin);hip=V((0,-.065-localbar.y,hipz));T=Matrix.Translation(hip)@Q@Matrix.Translation(-origin)
 desired={n:T@m for n,m in upper.items()};joints={}
 for n,v in uj.items():joints[n]=list(Q.to_3x3()@v if n.startswith('hand_direction') else T@v)
 for side,sign in [('l',1),('r',-1)]:
  a=T@bones['thigh_'+side].head_local;restankle=bones['calf_'+side].tail_local;ankle=V((sign*.205,-.0149,.0711));yaw=Matrix.Rotation(sign*math.radians(15),4,'Z')
  knee=ik(a,ankle,bones['thigh_'+side].length,bones['calf_'+side].length,V((sign*.40,-1,0)))
  desired['thigh_'+side]=segment('thigh_'+side,a,knee);desired['calf_'+side]=segment('calf_'+side,a if False else knee,ankle)
  F=Matrix.Translation(ankle)@yaw@Matrix.Translation(-restankle)
  for part in ['foot','ball']:desired[part+'_'+side]=F@rest[part+'_'+side]
  joints['hip_'+side]=list(a);joints['knee_'+side]=list(knee);joints['ankle_'+side]=list(ankle)
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@desired[n];pb.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=keyframe)
 bar.location=T@BAR_LOCAL
 for prop in ['location']:bar.keyframe_insert(data_path=prop,frame=keyframe)
 bpy.context.view_layer.update()
 records.append({'frame':keyframe,'t':t,'depth':depth,'torso_lean_degrees':math.degrees(lean),'bar':list(bar.location),'joints':joints})
for f in range(1,82):pose((f-1)/80,f)
for ob in [rig,bar]:
 for fc in ob.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
(OUT/'motion.json').write_text(json.dumps(records,indent=2))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False;s.world.color=(1,1,1)
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
s.display.render_aa='16';s.view_settings.view_transform='Standard';s.view_settings.exposure=.28;s.render.fps=20;s.frame_start=1;s.frame_end=80
bpy.ops.object.camera_add(location=(4.6,-6.7,2.8));cam=bpy.context.object;cam.name='Fixed full-body three-quarter squat camera';cam.rotation_euler=(V((0,-.02,.84))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.10;s.camera=cam
s.frame_set(41);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'barbell_squat.blend'),compress=True)
if '--stills' in sys.argv:
 for f in [1,21,41]:
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f:03d}.png');bpy.ops.render.render(write_still=True)
print('SCENE COMPLETE',flush=True)
