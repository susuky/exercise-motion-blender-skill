"""Rebuild the improved sculpted human from the provided licensed base mesh."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector as V, Matrix, Quaternion
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/base_human.blend'))
h=bpy.data.objects['Human']; rig=bpy.data.objects['Human.rig']; bones=rig.data.bones
rest={b.name:b.matrix_local.copy() for b in bones}

def mat(n,c,rough=.65):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1);m.roughness=rough;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough
 return m
skin=mat('Porcelain anatomical skin',(.73,.75,.76)); short=mat('Matte black woven shorts',(.025,.030,.036)); rubber=mat('Dumbbell graphite rubber',(.035,.043,.050)); metal=mat('Brushed stainless handle',(.38,.43,.46),.27)
h.data.materials.clear(); h.data.materials.append(skin)
for p in h.data.polygons:p.material_index=0;p.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');h.select_set(True);bpy.context.view_layer.objects.active=h
if h.data.shape_keys:
 mixed=h.shape_key_add(name='BakedShape',from_mix=True);coords=[p.co.copy() for p in mixed.data];h.shape_key_clear()
 for v,co in zip(h.data.vertices,coords):v.co=co
for mod in list(h.modifiers):
 if mod.type=='MASK':bpy.ops.object.modifier_apply(modifier=mod.name)
sub=h.modifiers.new('Anatomical sculpt topology','SUBSURF');sub.levels=3
# Put subdivision before the live armature so relief and fibre fields are fully skinned.
bpy.ops.object.modifier_move_up(modifier=sub.name)
bpy.ops.object.modifier_apply(modifier=sub.name)

def clamp(x):return max(0.,min(1.,x))
def smooth(a,b,x):
 t=clamp((x-a)/(b-a));return t*t*(3-2*t)
def g(x,w):return math.exp(-min(70.,(x/w)**2))
def band(x,a,b,w):return smooth(a-w,a+w,x)*(1-smooth(b-w,b+w,x))
def wrapped(a):return (a+math.pi)%(2*math.pi)-math.pi
# Front/palm/outer bases follow the armature's genuine rest-pose axes.
limbs=[]
for side,s in [('l',1),('r',-1)]:
 for name in ['upperarm','lowerarm','thigh','calf']:
  b=bones[name+'_'+side];u=(b.tail_local-b.head_local).normalized()
  f=V((0,-1,0));f=(f-u*f.dot(u)).normalized();l=u.cross(f).normalized()
  if l.x*s<0:l=-l
  limbs.append((name,s,b.head_local.copy(),u,f,l,b.length))
print('SCULPT',len(h.data.vertices),flush=True)
colors=[]
for v in h.data.vertices:
 orig=v.co.copy();x,y,z=orig;ax=abs(x);s=1 if x>=0 else -1
 delta=V(); shade=0.; fiber=0.; highlight=0.;red=0.; redfib=0.
 front=smooth(-.012,-.075,y) if False else smooth(.012,.075,-y)
 # Wide fan-shaped pectoralis: flat belly, soft superior origin, undercut lower fold.
 if ax<.205 and 1.24<z<1.43:
  lo=1.281+.045*(ax/.19)**2;hi=1.414-.18*ax
  med=smooth(.001,.025,ax);lat=1-smooth(.157,.194,ax)
  core=band(z,lo,hi,.014)*med*lat*front
  belly=.0075*core*(.8+.2*g(ax-.082,.078))
  fold=g(z-lo,.004)*med*lat*front
  delta.y-=belly-.0019*fold
  shade=max(shade,.24*fold,.14*g(ax-.005,.004)*band(z,1.29,1.415,.012)*front)
  angle=math.atan2(z-1.369,ax-.204)
  stria=(.5+.5*math.cos(angle*113))**6
  fiber+=.035*stria*core
  delta.y+=.00012*stria*core
  # Clavicular division follows a shallow diagonal, never an oval ring.
  clav=g(z-(1.385-.055*ax),.0023)*core
  shade=max(shade,.10*clav)
 # Rectus abdominis: shallow, broad muscle bellies with soft tendinous intersections.
 if ax<.095 and 1.03<z<1.292:
  abdomen=band(z,1.045,1.284,.020)*front
  for cx,cz,rx,rz in [(.035,1.249,.043,.031),(.034,1.186,.041,.029),(.032,1.120,.038,.034)]:
   cz+=s*.0015
   q=(abs((ax-cx)/rx)**2.7+abs((z-cz)/rz)**3.3)
   belly=math.exp(-min(70,q*1.3))*front
   delta.y-=.0062*belly
   fiber+=.022*(.5+.5*math.cos(ax*1850+6*math.sin(z*11)))**7*belly
  for zz in [1.151,1.218]:
   line=zz+.055*ax-.12*ax*ax
   cut=g(z-line,.0050)*(1-smooth(.043,.063,ax))*front
   delta.y+=.0013*cut;shade=max(shade,.13*cut)
  mid=g(x,.0038)*abdomen
  delta.y+=.0018*mid;shade=max(shade,.18*mid)
  outer=g(ax-(.064-.035*(1.27-z)),.0055)*abdomen
  shade=max(shade,.085*outer)
  nav=g(x,.005)*g(z-1.083,.005)*front
  delta.y+=.002*nav;shade=max(shade,.25*nav)
 # External oblique and serratus overlap, with tapering diagonal slips.
 if .057<ax<.211 and 1.025<z<1.32:
  side=band(ax,.069,.178,.018)*front*band(z,1.045,1.292,.020)
  oblique=band(z,1.065,1.24,.02)*side
  delta.y-=.003*oblique
  fiber+=.035*(.5+.5*math.cos((z+.65*ax)*1720))**6*oblique
  for zz in [1.198,1.238,1.276]:
   line=zz-.44*(ax-.105)
   slip=g(z-line,.007)*band(ax,.095,.184,.015)*front
   delta.y-=.0024*slip
   shade=max(shade,.14*g(z-line-.010,.0037)*band(ax,.100,.183,.014)*front)
  flank=g(ax-(.077+.22*(1.25-z)),.0045)*band(z,1.06,1.25,.022)*front
  shade=max(shade,.16*flank)
 # Sternocleidomastoid tendons and collarbone stay subtle.
 if 1.39<z<1.53 and ax<.14:
  neck=band(z,1.415,1.505,.02)*front
  path=.028+.40*(1.505-z)
  tendon=g(ax-path,.007)*neck
  delta.y-=.0025*tendon;shade=max(shade,.10*g(ax-path-.010,.004)*neck)
 for name,sign,a,u,f,l,L in limbs:
  if x*sign<0:continue
  q=orig-a;t=q.dot(u)/L;rad=q-u*q.dot(u);rho=rad.length
  if rho<.012 or rho>.16 or t<-.25 or t>1.10:continue
  rn=rad.normalized();theta=math.atan2(rad.dot(l),rad.dot(f));frontang=math.cos(theta)
  if name=='upperarm':
   # Deltoid converges to a distal V, then blends into the continuous arm surface.
   capend=.47-.12*abs(math.sin(theta))+.025*math.cos(3*theta)
   cap=band(t,-.17,capend,.045)*smooth(.139,.17,ax)*smooth(-.95,-.65,math.sin(theta))
   delta+=rn*(.006*cap)
   red=max(red,cap)
   stria=(.5+.5*math.cos((theta+.36*t)*35))**5
   redfib=max(redfib,stria*cap)
   capedge=g(t-capend,.018)*smooth(.155,.18,ax)
   shade=max(shade,.24*capedge)
   # Biceps long head and brachialis taper organically at the elbow.
   length=band(t,.28,.95,.10)
   belly=g(t-.62,.25)*g(wrapped(theta+.12),.76)*length
   brach=g(t-.64,.23)*g(wrapped(theta-1.0),.45)*length
   tri=g(t-.57,.28)*g(wrapped(theta-2.3),.75)*length
   delta+=rn*(.0080*belly+.0048*brach+.006*tri)
   for ang in [-.95,.75,1.50]:
    sep=g(wrapped(theta-ang-.10*t),.055)*length
    shade=max(shade,.29*sep)
    delta-=rn*.0014*sep
   fiber+=.045*(.5+.5*math.cos((theta+.20*t)*57))**7*length*(1-cap)
  elif name=='lowerarm':
   length=band(t,.08,.90,.12);prox=g(t-.30,.28)
   belly=(g(wrapped(theta-.35),.65)+.6*g(wrapped(theta+1.10),.48))*prox*length
   delta+=rn*.0040*belly
   for ang in [-.92,.18,1.02,2.4]:
    sep=g(wrapped(theta-ang+.48*t),.045)*length
    shade=max(shade,.23*sep);delta-=rn*.0009*sep
   fiber+=.035*(.5+.5*math.cos((theta+.48*t)*70))**7*length
  elif name=='thigh':
   # No z cutoff at shorts: all quadriceps continue under the garment.
   length=band(t,.05,.96,.13)
   rect=g(wrapped(theta+.06),.43)*g(t-.48,.34)*length
   lat=g(wrapped(theta-.83),.51)*g(t-.50,.32)*length
   med=g(wrapped(theta+.75),.48)*g(t-.76,.18)*length
   delta+=rn*(.009*rect+.010*lat+.008*med)
   # Two curving aponeuroses outline long muscle bellies rather than rings.
   for ang in [-.45+.14*t,.45+.23*t]:
    sep=g(wrapped(theta-ang),.045)*band(t,.19,.90,.13)
    shade=max(shade,.32*sep);delta-=rn*.0020*sep
   sep=g(wrapped(theta+1.02-.30*t),.045)*band(t,.16,.83,.13)
   shade=max(shade,.22*sep)
   fiber+=.04*(.5+.5*math.cos((theta+.10*math.sin(t*3))*88))**7*length*max(0,frontang)
   # Patellar rim subtly enclosed at the base, smoothly blending to tendon.
   knee=g(t-.985,.042)*g(theta,.58)
   shade=max(shade,.09*knee)
  elif name=='calf':
   length=band(t,.08,.90,.12)
   tib=g(wrapped(theta+.22),.22)*length
   delta+=rn*.0032*tib
   sep=g(wrapped(theta+.48-.15*t),.048)*length
   shade=max(shade,.24*sep)
   gastro=(g(wrapped(theta-2.55),.58)+.85*g(wrapped(theta+2.55),.58))*g(t-.30,.21)
   delta+=rn*.005*gastro
   fiber+=.03*(.5+.5*math.cos((theta+.12*t)*85))**7*length
 v.co+=delta
 # Fine, restrained anatomical pigment. Broad relief is in the geometry itself.
 value=1-.52*shade-fiber
 base=[.73*value,.75*value,.76*value]
 if red>0:
  rc=(.72*(1-.25*redfib),.080*(1-.32*redfib),.055*(1-.32*redfib))
  base=[base[k]*(1-red)+rc[k]*red for k in range(3)]
 colors.append((*base,1))
h.data.update()
print('SCULPT DONE',flush=True)
attr=h.data.color_attributes.new(name='Anatomical fibres',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):attr.data[i].color=c
h.data.color_attributes.active_color=attr
# Native material supports the same colors when switching from Workbench to EEVEE/Cycles.
bs=skin.node_tree.nodes.get('Principled BSDF');vc=skin.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name=attr.name;skin.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])

# Tailored shorts are a separate, fully skinned, gently offset cloth surface.
# Selected from the continuous skin topology, with geometric thickness and piping.
verts=h.data.vertices
faceids=[]
for p in h.data.polygons:
 c=sum((verts[i].co for i in p.vertices),V())/len(p.vertices)
 # Slightly higher outer hem; low centre hems cover the upper adductors.
 hem=.735+.025*smooth(.11,.24,abs(c.x))
 if hem<c.z<.994 and abs(c.x)<.28:faceids.append(p.index)
used=sorted({i for pi in faceids for i in h.data.polygons[pi].vertices});lookup={i:j for j,i in enumerate(used)}
vs=[]
for i in used:
 v=verts[i];co=v.co+v.normal*.005
 # Fine cloth ease, no sculpted anatomy showing through the black fabric.
 co.y+=.002*math.cos(co.x*48)*band(co.z,.76,.94,.03)
 vs.append(co)
me=bpy.data.meshes.new('Shorts tailored shell');me.from_pydata(vs,[],[[lookup[i] for i in h.data.polygons[pi].vertices] for pi in faceids]);me.update()
shorts=bpy.data.objects.new('Black shorts',me);shorts.color=short.diffuse_color;bpy.context.collection.objects.link(shorts);me.materials.append(short)
for p in me.polygons:p.use_smooth=True
for group in h.vertex_groups:shorts.vertex_groups.new(name=group.name)
for old,new in lookup.items():
 for vg in verts[old].groups:shorts.vertex_groups[vg.group].add([new],vg.weight,'REPLACE')
am=shorts.modifiers.new('Same anatomical rig','ARMATURE');am.object=rig;am.use_deform_preserve_volume=True
# Snap boundary loops to a smooth tailored hem and waistband.
edge_counts={}
for p in me.polygons:
 for e in p.edge_keys:edge_counts[e]=edge_counts.get(e,0)+1
boundary={vi for e,n in edge_counts.items() if n==1 for vi in e}
for vi in boundary:
 v=me.vertices[vi];hem=.735+.025*smooth(.11,.24,abs(v.co.x))
 if abs(v.co.z-.994)<.02:v.co.z=.994
 elif abs(v.co.z-hem)<.02:v.co.z=hem
so=shorts.modifiers.new('Fabric hem thickness','SOLIDIFY');so.thickness=.0018;so.offset=0
# The actual solidified shell supplies a clean narrow hem without excessive bevel topology.
# Dark skin beneath the garment edges prevents white numerical seams, without banding the thigh.
for i,v in enumerate(verts):
 hem=.735+.025*smooth(.11,.24,abs(v.co.x))
 if hem+.003<v.co.z<.991 and abs(v.co.x)<.28:attr.data[i].color=(.026,.031,.037,1)


bpy.ops.object.camera_add(location=(2.45,-7,2.35));cam=bpy.context.object;cam.name='Full-body presentation camera';bpy.context.scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/improved_human.blend'),compress=True)
print('IMPROVED HUMAN REBUILT',flush=True)
