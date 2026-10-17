"""Powerlifting barbell bench press, Blender 4.3.2. Reuses the improved skinned human.
Run: blender -b -t 3 --python build_scene.py -- --stills
"""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector as V,Matrix
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';QA=ROOT/'qa'
OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
import os
candidates=[Path(os.environ['HUMAN_BLEND'])] if 'HUMAN_BLEND' in os.environ else [ROOT.parents[1]/'assets/improved_human.blend']
BASE=next((p for p in candidates if p.exists()),candidates[0])
bpy.ops.wm.open_mainfile(filepath=str(BASE))
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

def box(n,loc,scale,m,bevel=.018):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.color=m.diffuse_color
 if bevel:be=o.modifiers.new('Soft corners','BEVEL');be.width=bevel;be.segments=4
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
steel=mat('Bench powder coat',(.16,.20,.23));padmat=mat('Firm padded black upholstery',(.028,.034,.04));PAD_TOP=.43
box('Full length padded competition bench',(0,.245,PAD_TOP-.035),(.305,1.35,.07),padmat,.018)
box('Bench longitudinal underframe',(0,.245,.33),(.09,1.27,.09),steel,.008)
for y in [-.31,.80]:
 box('Bench support pedestal',(0,y,.21),(.09,.09,.32),steel,.009)
 box('Bench ground crossbar',(0,y,.038),(.61,.13,.065),steel,.014)
 for x in [-.28,.28]:box('Bench rubber foot',(x,y,.018),(.10,.15,.035),padmat,.009)
# Rack stands behind the working bar path, leaving the chest and arms visible.
for sign in [-1,1]:
 x=sign*.56
 box('Rack upright',(x,.70,.595),(.065,.065,1.13),steel,.008)
 box('Rack ground stabilizer',(x,.59,.037),(.11,.65,.065),steel,.012)
 box('Adjustable rack sleeve',(x,.70,1.06),(.080,.080,.19),metal,.006)
 box('J cup bottom',(x,.649,1.12),(.10,.15,.025),steel,.006)
 box('J cup front lip',(x,.585,1.145),(.10,.025,.065),steel,.006)
 box('J cup padding',(x,.637,1.137),(.078,.098,.012),padmat,.003)
 cylinder('Rack adjustment pin',(x-.065,.70,1.05),(x+.065,.70,1.05),.009,hubmat,.001)
box('Rack rear cross brace',(0,.78,.125),(1.18,.065,.065),steel,.008)
# Exercise colours: pectoralis major RED; triceps/anterior deltoid BLUE.
attr=h.data.color_attributes.get('Anatomical fibres')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
for i,v in enumerate(h.data.vertices):
 x,y,z=v.co;ax=abs(x);c=attr.data[i].color
 # Reset all inherited or previous exercise highlights to neutral tissue.
 if c[0]>c[1]+.001 or c[2]>c[1]+.08:
  val=max(c[0],c[2])/.72;attr.data[i].color=(.73*val,.75*val,.76*val,1)
 pec=smooth(1.281+.045*(ax/.19)**2,1.289+.045*(ax/.19)**2,z)*(1-smooth(1.406-.18*ax,1.414-.18*ax,z))*band(ax,.014,.178,.018)*(1-smooth(-.065,-.025,y))
 side='l' if x>=0 else 'r';armgroup=h.vertex_groups['upperarm_'+side].index;armweight=sum(g.weight for g in v.groups if g.group==armgroup);armmask=smooth(.25,.65,armweight);b=bones['upperarm_'+side];u=(b.tail_local-b.head_local).normalized();q=v.co-b.head_local;t=q.dot(u)/b.length;rad=q-u*q.dot(u)
 tri=0.;anterior_deltoid=0.
 if -.20<t<.98 and .025<rad.length<.12:
  back=V((0,1,0));back=(back-u*back.dot(u)).normalized();facing=rad.normalized().dot(back)
  tri=.88*band(t,.18,.91,.08)*smooth(.04,.45,facing)*armmask
  anterior_deltoid=.88*band(t,-.12,.30,.09)*smooth(.15,.50,-facing)*smooth(.15,.195,ax)*armmask
 secondary=max(tri,anterior_deltoid)*(1-pec)
 fib=(.5+.5*math.cos((z-.37*ax)*1400))**6
 red=(.72*(1-.18*fib),.045*(1-.2*fib),.03*(1-.2*fib));blue=(.035*(1-.18*fib),.18*(1-.18*fib),.72*(1-.18*fib))
 c=attr.data[i].color;mid=tuple(c[k]*(1-secondary)+blue[k]*secondary for k in range(3));attr.data[i].color=tuple(mid[k]*(1-pec)+red[k]*pec for k in range(3))+(1,)
# Fixed plantar weights preserve flat-foot contact throughout the press.
for v in h.data.vertices:
 if v.co.z<.065:
  side='l' if v.co.x>=0 else 'r';footgroup=h.vertex_groups['foot_'+side];pin=1-smooth(.040,.065,v.co.z);old=[(g.group,g.weight) for g in v.groups]
  for gi,wt in old:h.vertex_groups[gi].add([v.index],wt*(1-pin),'REPLACE')
  former=sum(wt for gi,wt in old if gi==footgroup.index);footgroup.add([v.index],former*(1-pin)+pin,'REPLACE')

# Keep the contact patch over the scapulae fixed on the bench during arm motion.
# An 18 mm blend avoids a hard skin seam at the edge of the pinned back patch.
for v in h.data.vertices:
 x,y,z=v.co
 pin=smooth(.040,.062,y)*band(z,1.22,1.405,.018)*(1-smooth(.125,.155,abs(x)))
 if pin>0:
  vg=h.vertex_groups['spine_03'];old=[(g.group,g.weight) for g in v.groups]
  for gi,wt in old:h.vertex_groups[gi].add([v.index],wt*(1-pin),'REPLACE')
  former=sum(wt for gi,wt in old if gi==vg.index);vg.add([v.index],former*(1-pin)+pin,'REPLACE')

def segment(n,a,b):
 bone=bones[n];q=(bone.tail_local-bone.head_local).rotation_difference(b-a);return Matrix.Translation(a)@q.to_matrix().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n]
def ik(a,w,L1,L2,pole):
 v=w-a;D=v.length;u=v.normalized()
 if D>L1+L2-.00005:raise RuntimeError(('Unreachable',D,L1+L2))
 p=(pole-u*pole.dot(u)).normalized();al=(L1*L1-L2*L2+D*D)/(2*D);he=math.sqrt(max(0,L1*L1-al*al));return a+u*al+p*he
origin=bones['pelvis'].head_local.copy();Q=Matrix.Rotation(-math.pi/2,4,'X');HIP=V((0,-.20,.56))
GRIP_X=.375;BOTTOM_Y=.115;BOTTOM_Z=.715;TOP_Y=.265;TOP_Z=1.12
OFF={'pelvis':0.,'spine_01':.023,'spine_02':.038,'spine_03':.014,'neck_01':0.,'head':0.}
FINGER_RADII={f:.0325 for f in ['index','middle','ring','pinky']};THUMB_INSET=0.

def solve(depth):
 T=Matrix.Translation(HIP)@Q@Matrix.Translation(-origin);desired={n:T@m for n,m in rest.items()};joints={}
 for n,dz in OFF.items():
  if n in desired:desired[n]=Matrix.Translation(V((0,0,dz)))@desired[n]
 # The neck and cranium stay at the same supported position for the full cycle.
 for side,sign in [('l',1),('r',-1)]:
  a=T@bones['thigh_'+side].head_local;ankle=V((sign*.255,-.57,.0711));yaw=Matrix.Rotation(sign*math.radians(15),4,'Z')
  knee=ik(a,ankle,bones['thigh_'+side].length,bones['calf_'+side].length,V((sign*.15,-1,.2)))
  desired['thigh_'+side]=segment('thigh_'+side,a,knee);desired['calf_'+side]=segment('calf_'+side,knee,ankle)
  F=Matrix.Translation(ankle)@yaw@Matrix.Translation(-bones['calf_'+side].tail_local)
  for part in ['foot','ball']:desired[part+'_'+side]=F@rest[part+'_'+side]
  joints['hip_'+side]=list(a);joints['knee_'+side]=list(knee);joints['ankle_'+side]=list(ankle)
 centerbar=V((0,TOP_Y+(BOTTOM_Y-TOP_Y)*depth,TOP_Z+(BOTTOM_Z-TOP_Z)*depth))
 for side,sign in [('l',1),('r',-1)]:
  a=T@bones['upperarm_'+side].head_local;dx=V((-sign,0,0));dy=V((0,.1,1)).normalized();center=centerbar+V((sign*GRIP_X,0,0));cy,cz=.095,-.039
  for iteration in range(48):
   dz=dx.cross(dy).normalized();w=center-dy*cy-dz*(cz*sign)
   e=ik(a,w,bones['upperarm_'+side].length,bones['lowerarm_'+side].length,V((sign*1.5,-.7,-.8)))
   neutral=w-e;neutral.x=0;neutral.normalize();dy=(dy*.5+neutral*.5).normalized()
  desired['upperarm_'+side]=segment('upperarm_'+side,a,e);desired['lowerarm_'+side]=segment('lowerarm_'+side,e,w)
  rw=bones['hand_'+side].head_local;ry=(bones['middle_01_'+side].head_local-rw).normalized();rx=(bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local).normalized();rz=rx.cross(ry).normalized();rx=ry.cross(rz).normalized();B=Matrix((rx,ry,rz)).transposed();C=Matrix((dx,dy,dz)).transposed();HT=Matrix.Translation(w)@(C@B.inverted()).to_4x4()@Matrix.Translation(-rw);desired['hand_'+side]=HT@rest['hand_'+side]
  for finger in ['index','middle','ring','pinky']:
   radius=FINGER_RADII[finger];n=f'{finger}_01_{side}';start=HT@bones[n].head_local;rel=start-w;tx=rel.dot(dx);sy=rel.dot(dy);sz=rel.dot(dz)*sign;ry0,rz0=sy-cy,sz-cz;d=math.hypot(ry0,rz0);L=bones[n].length;ca=max(-1,min(1,(d*d+radius*radius-L*L)/(2*d*radius)));ang=math.atan2(rz0,ry0)-math.acos(ca)
   for k in range(1,4):
    n=f'{finger}_{k:02}_{side}';bone=bones[n]
    if k>1:ang-=2*math.asin(min(.999,bone.length/(2*radius)))
    end=w+dx*tx+dy*(cy+radius*math.cos(ang))+dz*((cz+radius*math.sin(ang))*sign);original=HT.to_3x3()@(bone.tail_local-bone.head_local);turn=original.rotation_difference(end-start).to_matrix().to_4x4();desired[n]=Matrix.Translation(start)@turn@HT.to_3x3().to_4x4()@Matrix.Translation(-bone.head_local)@rest[n];start=end
  start=HT@bones['thumb_01_'+side].head_local
  for kk,(tx,ty,tz) in enumerate([(.052,.069,-.008),(.039,.105,-.011),(.010,.116,-.019)],1):
   n=f'thumb_{kk:02}_{side}';target=w+dx*tx+dy*ty+dz*(tz*sign);radial=target-center;radial-=dx*radial.dot(dx);target-=radial.normalized()*THUMB_INSET;end=start+(target-start).normalized()*bones[n].length;desired[n]=segment(n,start,end);start=end
  joints['shoulder_'+side]=list(a);joints['elbow_'+side]=list(e);joints['wrist_'+side]=list(w);joints['grip_'+side]=list(center);joints['hand_direction_'+side]=list(dy)
 for n,pb in rig.pose.bones.items():
  ref=desired[pb.parent.name]@rest[pb.parent.name].inverted()@rest[n] if pb.parent else rest[n];pb.matrix_basis=ref.inverted()@desired[n];pb.rotation_mode='QUATERNION'
 bar.location=centerbar;bpy.context.view_layer.update();return joints

def meshcoords(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);a=a.reshape(-1,3);ev.to_mesh_clear();return a
rc=np.empty(len(h.data.vertices)*3);h.data.vertices.foreach_get('co',rc);rc=rc.reshape(-1,3)
# Fit the main support points to a common flat upholstered surface.
# These small translations create a stable thoracic/lumbar arch.
solve(1);a=meshcoords(h)
headmask=(rc[:,2]>1.58)&(abs(rc[:,0])<.10);backmask=(rc[:,2]>1.24)&(rc[:,2]<1.41)&(abs(rc[:,0])<.15)&(rc[:,1]>.045)
cloth=meshcoords(shorts);buttmask=(abs(cloth[:,0])<.145)&(cloth[:,1]>-.29)&(cloth[:,1]<-.12)
buttz=float(cloth[buttmask,2].min());HIP.z+=PAD_TOP+.0003-buttz
solve(1);a=meshcoords(h);OFF['spine_03']+=PAD_TOP+.0003-float(a[backmask,2].min());OFF['head']=PAD_TOP+.0003-float(a[headmask,2].min());OFF['neck_01']=OFF['head']*.60
# Place the cylinder on the upper envelope of the lower-chest surface.
chestmask=(rc[:,2]>1.16)&(rc[:,2]<1.40)&(abs(rc[:,0])<.25)&(rc[:,1]<-.025)
for ii in range(4):
 solve(1);a=meshcoords(h);m=chestmask&(abs(a[:,1]-BOTTOM_Y)<BAR_RADIUS)
 BOTTOM_Z=float(np.max(a[m,2]+np.sqrt(np.maximum(0,BAR_RADIUS**2-(a[m,1]-BOTTOM_Y)**2))))+.00025
# Numerically locate a 174 degree elbow lockout without hyperextension.
lo,hi=HIP.z+.55,HIP.z+.62
for ii in range(25):
 TOP_Z=(lo+hi)/2
 try:
  j=solve(0);a,e,w=[V(j[k+'_l']) for k in ['shoulder','elbow','wrist']];angle=math.degrees((a-e).angle(w-e))
 except RuntimeError:
  hi=TOP_Z;continue
 if angle<174:lo=TOP_Z
 else:hi=TOP_Z
TOP_Z=lo
# Individual digit fits use all three arm phases, retaining tiny surface clearance.
digitmasks={}
for finger in ['thumb','index','middle','ring','pinky']:
 ids={g.index for g in h.vertex_groups if g.name.startswith(finger+'_')};digitmasks[finger]=np.array([sum(g.weight for g in v.groups if g.group in ids)>.55 for v in h.data.vertices])
bounds={f:[.022,.039] for f in FINGER_RADII};thumbbounds=[0,.018]
for fit in range(14):
 for finger in FINGER_RADII:FINGER_RADII[finger]=sum(bounds[finger])/2
 THUMB_INSET=sum(thumbbounds)/2;mins={f:1. for f in digitmasks}
 for dep in [0,.5,1]:
  solve(dep);a=meshcoords(h);rad=np.hypot(a[:,1]-bar.location.y,a[:,2]-bar.location.z)
  for f,mask in digitmasks.items():mins[f]=min(mins[f],float(rad[mask].min()-BAR_RADIUS))
 for finger in FINGER_RADII:
  bounds[finger][0 if mins[finger]<.0002 else 1]=FINGER_RADII[finger]
 thumbbounds[1 if mins['thumb']<.0002 else 0]=THUMB_INSET
for finger in FINGER_RADII:FINGER_RADII[finger]=bounds[finger][1]
THUMB_INSET=thumbbounds[0]
(QA/'contact_fit.json').write_text(json.dumps({'hip':list(HIP),'spine_offsets':OFF,'bar_bottom':[0,BOTTOM_Y,BOTTOM_Z],'bar_top':[0,TOP_Y,TOP_Z],'finger_radii':FINGER_RADII,'thumb_inset':THUMB_INSET},indent=2))
# 4 s cycle: 1.65 s controlled lowering, 0.35 s chest pause, 1.65 s press,
# 0.35 s supported lockout. Both moving phases use smooth easing.
def depth_at(t):
 seconds=(t%1)*4
 if seconds<1.65:return (1-math.cos(math.pi*seconds/1.65))/2
 if seconds<2.00:return 1.
 if seconds<3.65:return (1+math.cos(math.pi*(seconds-2)/1.65))/2
 return 0.
records=[]
for f in range(1,82):
 t=(f-1)/80;depth=depth_at(t);j=solve(depth)
 for pb in rig.pose.bones:
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=f)
 bar.keyframe_insert(data_path='location',frame=f);records.append({'frame':f,'t':t,'depth':depth,'bar':list(bar.location),'joints':j})
for ob in [rig,bar]:
 for fc in ob.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
(OUT/'motion.json').write_text(json.dumps(records,indent=2))
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=960;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False;s.world.color=(1,1,1)
sh=s.display.shading;sh.light='STUDIO';sh.studio_light='studio.sl';sh.studiolight_rotate_z=.25;sh.color_type='VERTEX';sh.background_type='WORLD';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=.45;sh.curvature_valley_factor=.55;sh.cavity_ridge_factor=.4;sh.cavity_valley_factor=.5;sh.show_specular_highlight=True;sh.show_object_outline=False
s.display.render_aa='16';s.view_settings.view_transform='Standard';s.view_settings.exposure=.28;s.render.fps=20;s.frame_start=1;s.frame_end=80
bpy.ops.object.camera_add(location=(4.7,-6.4,4.0));cam=bpy.context.object;cam.name='Fixed three-quarter bench press camera';cam.rotation_euler=(V((0,.06,.62))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.35;s.camera=cam
s.frame_set(37);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'barbell_bench_press.blend'),compress=True)
if '--stills' in sys.argv:
 for f in [1,37]:
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f:03d}.png');bpy.ops.render.render(write_still=True)
print('SCENE COMPLETE',flush=True)
