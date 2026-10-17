"""Recolor the delivered scenes by functional-anatomy role, without changing meshes or animation.
Usage: blender -b -t 2 --python recolor_existing.py -- lateral_raise --preview
       blender -b -t 2 --python recolor_existing.py -- battle_rope --preview
After mask review, replace --preview with --animation. Relative sources are the original scenes.
"""
import bpy, sys, math, json, hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector as V
ROOT=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
kind=args[0] if args else 'lateral_raise'
source=ROOT.parent/('lateral_raise/output/lateral_raise.blend' if kind=='lateral_raise' else 'battle_rope/output/battle_rope.blend')
if '--source' in args:source=Path(args[args.index('--source')+1]).resolve()
D=Path(args[args.index('--output-dir')+1]).resolve() if '--output-dir' in args else ROOT/kind
OUT=D/'output'; QA=D/'qa'
OUT.mkdir(exist_ok=True,parents=True); QA.mkdir(exist_ok=True,parents=True)
name='lateral_raise' if kind=='lateral_raise' else 'battle_rope'
preview='--preview' in args
bpy.ops.wm.open_mainfile(filepath=str(source))
h=bpy.data.objects['Human']; rig=bpy.data.objects['Human.rig']; scene=bpy.context.scene
n=len(h.data.vertices); xyz=np.empty(n*3,dtype=np.float32); h.data.vertices.foreach_get('co',xyz); xyz=xyz.reshape((-1,3))
geom_hash=hashlib.sha256(xyz.tobytes()).hexdigest()
old=np.empty(n*4,dtype=np.float32);attr=h.data.color_attributes['Anatomical fibres'];attr.data.foreach_get('color',old);old=old.reshape((-1,4))
x,y,z=xyz.T; ax=np.abs(x)
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1); return t*t*(3-2*t)
def band(v,a,b,w):return smooth(a-w,a+w,v)*(1-smooth(b-w,b+w,v))
def wrap(v):return (v+np.pi)%(2*np.pi)-np.pi
def angular(v,center,width,soft=.12):return 1-smooth(width-soft,width+soft,np.abs(wrap(v-center)))
def gauss(v,w):return np.exp(-np.minimum(70,(v/w)**2))
def muscle_belly(t,theta,tc,th,ac,ah):
 q=((t-tc)/th)**2+(wrap(theta-ac)/ah)**2
 return 1-smooth(.78,1.05,q)
regions={}
front=smooth(.01,.065,-y); back=smooth(.005,.055,y)
# Trapezius: paired upper triangles and lower converging triangles, posterior to clavicles.
upper_top=1.525-.70*ax
upper_bot=1.405-.07*ax
upper=band(z,upper_bot,upper_top,.008)*(1-smooth(.135,.168,ax))*smooth(-.025,.022,y)
# Lower trapezius ascends from lower thoracic midline to medial scapular spine.
lower_width=np.clip((z-1.135)*.52,0,.138)
lower=band(z,1.145,1.415,.008)*(1-smooth(lower_width-.008,lower_width+.008,ax))*back
regions['upper_trapezius']=upper
regions['lower_trapezius']=lower
# Visible serratus slips at the anterolateral lower ribs, below pectoralis major.
serratus=np.zeros(n,dtype=np.float32)
for level in [1.198,1.238,1.276]:
 line=level-.44*(ax-.105)
 serratus=np.maximum(serratus,gauss(z-line,.011)*band(ax,.107,.182,.009)*smooth(.0,.045,-y))
regions['serratus_anterior_visible_slips']=serratus
red=np.zeros(n,dtype=np.float32)
blue=np.maximum.reduce([upper,lower,serratus])
for side,sign in [('l',1),('r',-1)]:
 for part in ['upperarm','lowerarm','thigh']:
  bone=rig.data.bones[part+'_'+side];a=np.array(bone.head_local);u=np.array((bone.tail_local-bone.head_local).normalized());L=bone.length
  f=np.array((0,-1,0));f=f-u*np.dot(f,u);f/=np.linalg.norm(f);l=np.cross(u,f)
  if l[0]*sign<0:l=-l
  q=xyz-a;t=q@u/L;rad=q-np.outer(q@u,u);rho=np.linalg.norm(rad,axis=1);theta=np.arctan2(rad@l,rad@f)
  gate=(x*sign>0)&(rho>.012)&(rho<(.16 if part=='thigh' else .115))&(t>-.25)&(t<1.10)
  if part=='upperarm':
   capend=.47-.12*np.abs(np.sin(theta))+.025*np.cos(3*theta)
   cap=band(t,-.17,capend,.03)*smooth(.150,.174,ax)*smooth(-.95,-.65,np.sin(theta))*gate
   if kind=='lateral_raise':
    mid=cap*angular(theta,1.48,.84,.10)
    red=np.maximum(red,mid);regions['middle_deltoid_'+side]=mid
   else:
    red=np.maximum(red,cap);regions['deltoid_'+side]=cap
    # Biceps/brachialis anterior belly and triceps posterior belly support alternating elbow control.
    arm=np.maximum(muscle_belly(t,theta,.63,.33,.08,.96),muscle_belly(t,theta,.60,.37,2.85,1.17))*gate
    blue=np.maximum(blue,arm);regions['elbow_flexor_extensor_region_'+side]=arm
  elif part=='lowerarm' and kind=='battle_rope':
   # Grip-supporting flexor-pronator region; hand and distal tendons stay gray.
   fore=muscle_belly(t,theta,.40,.40,-.05,1.18)*gate
   blue=np.maximum(blue,fore);regions['forearm_grip_region_'+side]=fore
  elif part=='thigh' and kind=='battle_rope':
   # Visible quadriceps maintain the flexed-knee stance. The shorts occlude the proximal thighs.
   quad=np.maximum.reduce([muscle_belly(t,theta,.49,.43,-.06,.56),muscle_belly(t,theta,.50,.43,.83,.69),muscle_belly(t,theta,.73,.25,-.75,.65)])*gate
   blue=np.maximum(blue,quad);regions['quadriceps_stance_'+side]=quad
if kind=='battle_rope':
 rectus_width=.073-.035*(1.27-z)
 rectus=band(z,1.055,1.281,.014)*(1-smooth(rectus_width-.012,rectus_width+.007,ax))*front
 oblique_inner=.077+.22*(1.25-z)
 oblique=band(z,1.055,1.246,.015)*band(ax,oblique_inner,.174,.014)*front
 erectors=band(z,1.035,1.298,.018)*band(ax,.022,.066,.010)*back
 # Posterolateral latissimus participates in shoulder extension; retain a medial gap for lower traps.
 lat_medial=.048+.35*np.maximum(0,z-1.19)
 lat_lateral=.129+.24*(z-1.08)
 lat=band(z,1.065,1.355,.02)*band(ax,lat_medial,lat_lateral,.015)*back
 for nm,mask in [('rectus_abdominis',rectus),('external_oblique',oblique),('erector_spinae',erectors),('latissimus_extension_support',lat)]:
  regions[nm]=mask;blue=np.maximum(blue,mask)
# Geometry relief and per-vertex fibre brightness are retained when replacing old pigment.
# Chromaticity is reset first, so inherited shoulder masks never select functional roles.
value=np.clip(np.max(old[:,:3],axis=1)/.76,.52,1.05)
was_red=(old[:,0]>old[:,1]*1.4)&(old[:,0]>old[:,2]*1.4)
value[was_red]=np.clip(old[was_red,0]/.72,.52,1.05)
GRAY=np.array([.73,.75,.76]);RED=np.array([.72,.045,.03]);BLUE=np.array([.035,.18,.72])
base=GRAY[None,:]*value[:,None]
# Distinct categorical colors: red takes precedence at boundaries.
blue*=1-red
base=base*(1-blue[:,None])+BLUE[None,:]*value[:,None]*blue[:,None]
base=base*(1-red[:,None])+RED[None,:]*value[:,None]*red[:,None]
# Preserve the original dark surface under the tailored shorts exactly.
cloth_under=np.max(old[:,:3],axis=1)<.1;base[cloth_under]=old[cloth_under,:3]
out=np.concatenate([base,np.ones((n,1))],axis=1).astype(np.float32);attr.data.foreach_set('color',out.ravel());h.data.color_attributes.active_color=attr
assert hashlib.sha256(xyz.tobytes()).hexdigest()==geom_hash
scene.render.film_transparent=False;scene.render.image_settings.color_mode='RGB';scene.display.shading.background_type='WORLD';scene.world.color=(1,1,1)
scene.render.resolution_x=960;scene.render.resolution_y=960;scene.render.resolution_percentage=100
rep=19 if kind=='lateral_raise' else 7
scene.frame_set(rep)
qa={'exercise':kind,'source_scene':str(source),'mesh_vertices':n,'geometry_sha256':geom_hash,'geometry_and_animation':'unchanged; recolor modifies only vertex color attribute and output/background settings','palette_linear_rgb':{'primary':RED.tolist(),'secondary':BLUE.tolist(),'neutral':GRAY.tolist()},'colored_vertices':{'primary_gt_half':int((red>.5).sum()),'secondary_gt_half':int((blue>.5).sum())},'regions_vertices_gt_half':{k:int((v>.5).sum()) for k,v in regions.items()},'occlusion':['Supraspinatus lies deep to trapezius/deltoid and is not separately exposed by this continuous-surface mesh.','Shorts conceal gluteal and proximal-thigh anatomy.']}
(QA/'color_mapping.json').write_text(json.dumps(qa,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')),compress=True)
if '--save-only' in args:
 print('SAVED RECOLOR',kind,flush=True);sys.exit(0)
# Release all vectorized scratch masks before Workbench allocates its render buffers.
for scratch in ['xyz','x','y','z','ax','old','out','base','value','red','blue','regions','upper','lower','serratus','front','back','q','t','rad','rho','theta','gate','cap','mid','lower_width','upper_top','upper_bot']:
 globals().pop(scratch,None)
import gc;gc.collect()
scene.render.filepath=str(OUT/'representative.png');bpy.ops.render.render(write_still=True)
if preview:
 cam=scene.camera;oldcam=(cam.location.copy(),cam.rotation_euler.copy(),cam.data.ortho_scale)
 # Readable front/back anatomical mask checks use the existing high-abduction pose for lateral raise.
 for label,loc,target,scale in [('front',(0,-4,1.31),(0,0,1.25),.95),('back',(0,4,1.31),(0,0,1.25),.95)]:
  if kind=='battle_rope':loc=(0,-4,1.23) if label=='front' else (0,4,1.23);target=(0,0,1.19);scale=1.05
  cam.location=V(loc);cam.rotation_euler=(V(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  scene.render.filepath=str(QA/(label+'_mask.png'));bpy.ops.render.render(write_still=True)
 cam.location,cam.rotation_euler,cam.data.ortho_scale=oldcam
elif '--animation' in args:
 for frame in range(1,37 if kind=='lateral_raise' else 25):
  scene.frame_set(frame);scene.render.filepath=str(OUT/f'frame_{frame:03d}.png');bpy.ops.render.render(write_still=True)
print('RECOLOR COMPLETE',kind,flush=True)
