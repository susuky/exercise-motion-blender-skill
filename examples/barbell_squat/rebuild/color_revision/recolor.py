"""Color-only revision of approved 960 px Blender 4.3.2 exercise scenes.
Run blender -b -t 3 --python recolor.py -- squat patch|stills|render [start end].
All muscle regions are computed from immutable bind-space skin and rig bones.
"""
import bpy,sys,json,hashlib,shutil,os
import numpy as np
from pathlib import Path
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:];kind=args[0];mode=args[1]
NAME={'squat':'barbell_squat','pulldown':'lat_pulldown'}[kind]
BASE={'squat':'barbell_squat','pulldown':'lat_pulldown'}[kind]
DIR=ROOT/kind;OUT=DIR/'output';QA=DIR/'qa'
for p in [OUT,QA,DIR/'assets']:p.mkdir(parents=True,exist_ok=True)
source=Path(os.environ['SQUAT_BASE_SCENE']) if kind=='squat' else DIR/'assets'/f'{NAME}_original.blend'
if not source.exists():shutil.copy2(ROOT.parent/BASE/'output'/f'{NAME}.blend',source)
scene=OUT/f'{NAME}_recolored.blend'
bpy.ops.wm.open_mainfile(filepath=str(source if mode=='patch' else scene))
s=bpy.context.scene;h=bpy.data.objects['Human'];rig=bpy.data.objects['Human.rig'];cloth=bpy.data.objects['Black shorts'];bones=rig.data.bones
RED=np.array([.72,.045,.03]);BLUE=np.array([.035,.18,.72]);GRAY=np.array([.73,.75,.76])
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
def arr_co(mesh):
 a=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',a);return a.reshape(-1,3)
def digest_geometry():
 z=hashlib.sha256()
 for o in sorted(bpy.data.objects,key=lambda x:x.name):
  z.update(o.name.encode());z.update(np.asarray(o.matrix_world,dtype=np.float32).tobytes())
  if o.type=='MESH':z.update(arr_co(o.data).tobytes())
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    z.update(fc.data_path.encode());z.update(str(fc.array_index).encode());z.update(np.array([p.co[:] for p in fc.keyframe_points],dtype=np.float32).tobytes())
 return z.hexdigest()
if mode=='patch':
 before=digest_geometry();p=arr_co(h.data);x,y,z=p.T;ax=np.abs(x);n=len(p)
 attr=h.data.color_attributes.get('Anatomical fibres');old=np.empty(n*4,dtype=np.float32);attr.data.foreach_get('color',old);old=old.reshape(-1,4)
 # Keep pigment-value detail while discarding every old exercise hue.
 value=np.clip(np.max(old[:,:3],axis=1)/.76,.2,1.15)
 base=value[:,None]*GRAY
 masks={}
 def put(name,v,role):masks[name]={'mask':np.clip(v,0,1),'role':role}
 def limb(name,side):
  sign=1 if side=='l' else -1;b=bones[name+'_'+side];a=np.array(b.head_local);u=np.array((b.tail_local-b.head_local).normalized());f=np.array(V((0,-1,0)));f=f-u*np.dot(f,u);f=f/np.linalg.norm(f);lat=np.cross(u,f)
  if lat[0]*sign<0:lat=-lat
  q=p-a;t=q@u/b.length;rad=q-(q@u)[:,None]*u;rho=np.linalg.norm(rad,axis=1);rn=rad/np.maximum(rho[:,None],1e-10);front=rn@f;outer=rn@lat
  valid=(x*sign>0)&(rho>.015)&(rho<.15)
  return t,front,outer,valid
 back=smooth(.005,.065,y);front=smooth(.010,.065,-y)
 if kind=='squat':
  for side in ['l','r']:
   t,f,o,v=limb('thigh',side)
   # Anterior and anterolateral quadriceps; knee, posterior thigh and medial
   # adductor compartment are excluded by the angular boundaries.
   quad=band(t,.10,.91,.065)*smooth(-.08,.20,f)*v
   put('quadriceps_'+side,quad,'primary')
   # Posteromedial adductor magnus hip-extensor surface. Most of its proximal
   # belly is naturally occluded by shorts; this marks the exposed distal part.
   add=band(t,.10,.78,.09)*smooth(.20,.60,-o)*smooth(-.25,.20,-f)*v*(1-quad)
   put('adductor_magnus_'+side,add,'secondary')
   ham=band(t,.18,.83,.09)*smooth(.40,.75,-f)*v*(1-add)
   put('hamstring_stabilizers_'+side,ham,'secondary')
   tc,fc,oc,vc=limb('calf',side)
   soleus=band(tc,.35,.78,.10)*smooth(.18,.55,-fc)*vc
   put('calf_plantarflexors_'+side,soleus,'secondary')
  glute=band(z,.795,.97,.035)*band(ax,.025,.215,.02)*back
  put('gluteus_maximus',glute,'primary')
  erector=band(z,.99,1.36,.025)*band(ax,.020,.067,.010)*back
  put('erector_spinae',erector,'secondary')
  rectus=band(z,1.045,1.275,.016)*(1-smooth(.055,.072,ax))*front
  oblique=band(z,1.045,1.23,.02)*band(ax,.075,.165,.015)*front
  put('abdominal_brace',np.maximum(rectus,oblique),'secondary')
 else:
  # Latissimus muscle belly: fan from lumbar/iliac region toward posterior
  # axillary fold. Boundaries stay behind midaxillary line and below scapula.
  lo=1.015+.27*ax;hi=1.27+.50*ax
  lat=band(z,lo,hi,.018)*smooth(.045,.075,ax)*(1-smooth(.180,.208,ax))*smooth(-.010,.030,y)
  # Preserve the thoracolumbar fascia near the spine as gray.
  lat*=smooth(.030,.060,ax)
  put('latissimus_dorsi',lat,'primary')
  for side in ['l','r']:
   t,f,o,v=limb('upperarm',side)
   # Biceps anterior belly plus the exposed distal brachialis borders.
   bi=band(t,.36,.90,.065)*smooth(.20,.52,f)*v
   brach=band(t,.62,.91,.055)*smooth(.05,.45,f)*smooth(.38,.72,np.abs(o))*v
   put('elbow_flexors_'+side,np.maximum(bi,brach),'secondary')
   t,f,o,v=limb('lowerarm',side)
   brachiorad=band(t,.10,.60,.07)*smooth(.30,.65,o)*smooth(-.15,.35,f)*v
   grip=band(t,.15,.73,.08)*smooth(.52,.80,f)*v
   put('forearm_assistance_'+side,np.maximum(brachiorad,grip),'secondary')
  # Trapezius superficial footprint: mid/lower fibers around and below the
  # scapular spine. Rhomboids lie deep to this footprint.
  width=.025+.11*np.clip((z-1.18)/.22,0,1)
  traps=band(z,1.18,1.415,.018)*(1-smooth(width,width+.018,ax))*smooth(.009,.025,ax)*back
  put('middle_lower_trapezius',traps,'secondary')
  teres=band(z,1.315+.15*ax,1.375+.08*ax,.012)*band(ax,.100,.183,.015)*back
  put('teres_major',teres,'secondary')
 # Selected superficial muscles: deterministic red/blue conflict priority,
 # avoiding purple bands at adjacent muscle boundaries.
 red=np.maximum.reduce([m['mask'] for m in masks.values() if m['role']=='primary'])
 blue=np.maximum.reduce([m['mask'] for m in masks.values() if m['role']=='secondary'])
 redwins=red>=blue;blue[redwins]=0;red[~redwins]=0
 col=base*(1-red[:,None]-blue[:,None])+RED*value[:,None]*red[:,None]+BLUE*value[:,None]*blue[:,None]
 rgba=np.c_[col,np.ones(n)].astype(np.float32);attr.data.foreach_set('color',rgba.ravel());h.data.color_attributes.active_color=attr;h.data.update()
 # Semantic masks retained as Blender point attributes for review/reproduction.
 for name,ma in masks.items():
  key='role_'+name
  if key in h.data.attributes:h.data.attributes.remove(h.data.attributes[key])
  at=h.data.attributes.new(key,'FLOAT','POINT');at.data.foreach_set('value',ma['mask'].astype(np.float32))
 after=digest_geometry();assert before==after
 mirror_max=0.0
 for o in bpy.data.objects:
  if o.animation_data and o.animation_data.action:
   for fc in o.animation_data.action.fcurves:
    for f in range(42,81):mirror_max=max(mirror_max,abs(fc.evaluate(f)-fc.evaluate(82-f)))
 assert mirror_max<1e-5
 clothcol=[]
 for ca in cloth.data.color_attributes:
  co=np.empty(len(ca.data)*4,dtype=np.float32);ca.data.foreach_get('color',co);co=co.reshape(-1,4);clothcol.append({'attribute':ca.name,'max_rgb':co[:,:3].max(axis=0).tolist()})
 counts={key:{'role':ma['role'],'vertices_over_0_5':int((ma['mask']>.5).sum()),'bounds_bind_m':[[float(v) for v in row] for row in [p[ma['mask']>.5].min(axis=0),p[ma['mask']>.5].max(axis=0)]] if (ma['mask']>.5).any() else []} for key,ma in masks.items()}
 checks={'geometry_and_animation_before_sha256':before,'geometry_and_animation_after_sha256':after,'geometry_animation_exactly_unchanged':before==after,'all_39_reverse_frame_action_difference_max':mirror_max,'skin_vertex_count':n,'render_resolution':[s.render.resolution_x,s.render.resolution_y],'render_aa':s.display.render_aa,'fps':s.render.fps,'frames':[s.frame_start,s.frame_end],'palette_linear_rgb':{'primary':RED.tolist(),'secondary':BLUE.tolist(),'other':GRAY.tolist()},'shorts_vertex_attributes':clothcol,'shorts_materials':{m.name:list(m.diffuse_color) for m in cloth.data.materials if m},'mask_counts':counts,'red_front_chest_vertices':int(((red>.5)&(y<-.04)&(z>1.28)&(ax<.16)).sum())}
 if kind=='pulldown':assert checks['red_front_chest_vertices']==0
 (QA/'color_map_validation.json').write_text(json.dumps(checks,indent=2));s.frame_set(41);bpy.ops.wm.save_as_mainfile(filepath=str(scene),compress=True)
 print('PATCH COMPLETE',kind,flush=True)
elif mode in ['stills','side']:
 for frame in ([1,21,41] if mode=='stills' else []):
  s.frame_set(frame);s.render.filepath=str(QA/f'production_{frame:03d}.png');bpy.ops.render.render(write_still=True)
 # Diagnostic views use rest pose while keeping native clothing and camera
 # resolution. These changes are not saved to the production scene.
 for o in bpy.data.objects:
  if o.name not in ['Human','Human.rig','Black shorts',s.camera.name]:o.hide_render=True
 rig.data.pose_position='REST';bpy.context.view_layer.update();cam=s.camera
 for name,pos in ([('front',(0,-5,.86)),('back',(0,5,.86)),('side',(5,0,.86))] if mode=='stills' else [('side',(5,0,.86))]):
  target=V((0,0,.86));cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.85;s.render.filepath=str(QA/f'mask_{name}.png');bpy.ops.render.render(write_still=True)
 print('STILLS COMPLETE',kind,flush=True)
elif mode in ['render','render_mirror']:
 first=int(args[2]) if len(args)>2 else 1;last=int(args[3]) if len(args)>3 else (42 if mode=='render_mirror' else 81)
 for f in range(first,last):
  s.frame_set(f);s.render.filepath=str(OUT/f'frame_{f:03d}.png');bpy.ops.render.render(write_still=True)
 if mode=='render_mirror':
  maximum=0.0
  for o in bpy.data.objects:
   if o.animation_data and o.animation_data.action:
    for fc in o.animation_data.action.fcurves:
     for f in range(42,81):maximum=max(maximum,abs(fc.evaluate(f)-fc.evaluate(82-f)))
  assert maximum<1e-5
  for f in range(42,81):shutil.copy2(OUT/f'frame_{82-f:03d}.png',OUT/f'frame_{f:03d}.png')
  (QA/'reverse_frame_equivalence.json').write_text(json.dumps({'checked_frames':39,'all_action_channels_max_difference':maximum,'tolerance':1e-5},indent=2))
 print('RENDER COMPLETE',kind,flush=True)
