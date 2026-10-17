"""Validate rendered dense skin, bar, pad contact, foot placement, and loop."""
import bpy,json,numpy as np,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';QA=ROOT/'qa'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'barbell_bench_press.blend'))
s=bpy.context.scene;h=bpy.data.objects['Human'];shorts=bpy.data.objects['Black shorts'];bar=bpy.data.objects['Loaded straight barbell'];n=len(h.data.vertices)
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);a=a.reshape(-1,3);ev.to_mesh_clear();return a
r=np.empty(n*3);h.data.vertices.foreach_get('co',r);r=r.reshape(-1,3)
feet=r[:,2]<.035;hands=(abs(r[:,0])>.44)&(r[:,2]<1.12)&(r[:,2]>.90);chest=(r[:,2]>1.16)&(r[:,2]<1.40)&(abs(r[:,0])<.25)&(r[:,1]<-.025)
head=(r[:,2]>1.58)&(abs(r[:,0])<.10);back=(r[:,2]>1.24)&(r[:,2]<1.41)&(abs(r[:,0])<.15)&(r[:,1]>.045)
digits=[side+'_'+finger for side in ['l','r'] for finger in ['thumb','index','middle','ring','pinky']]
weights=np.zeros((len(digits),n),dtype=np.float32);groupmap={}
for g in h.vertex_groups:
 for k,name in enumerate(digits):
  side,finger=name.split('_')
  if g.name.startswith(finger+'_') and g.name.endswith('_'+side):groupmap[g.index]=k
for v in h.data.vertices:
 for g in v.groups:
  if g.group in groupmap:weights[groupmap[g.group],v.index]+=g.weight
digitmasks={name:weights[k]>.55 for k,name in enumerate(digits)}
rows=[];first=None;firstfeet=None;motion=json.loads((OUT/'motion.json').read_text())
fr=[1,18,37,54,81] if '--quick' in sys.argv else range(1,82)
for f in fr:
 s.frame_set(f);a=coords(h);cloth=coords(shorts)
 if f==1:first=a.copy();firstfeet=a[feet].copy()
 by,bz=bar.location.y,bar.location.z;rad=np.hypot(a[:,1]-by,a[:,2]-bz);j=motion[f-1]['joints'];wristangles={};elbowangles={}
 for side in ['l','r']:
  sh,el,wr=(np.array(j[k+'_'+side]) for k in ['shoulder','elbow','wrist']);dy=np.array(j['hand_direction_'+side]);fore=wr-el;fore/=np.linalg.norm(fore);wristangles[side]=float(np.degrees(np.arccos(np.clip(np.dot(fore,dy),-1,1))));a1=sh-el;a2=wr-el;elbowangles[side]=float(np.degrees(np.arccos(np.clip(np.dot(a1,a2)/(np.linalg.norm(a1)*np.linalg.norm(a2)),-1,1))))
 padzone=(abs(a[:,0])<.135)&(a[:,1]>-.40)&(a[:,1]<.9)
 buttmask=(abs(cloth[:,0])<.145)&(cloth[:,1]>-.29)&(cloth[:,1]<-.12)
 cp=(abs(cloth[:,0])<.135)&(cloth[:,1]>-.40)&(cloth[:,1]<.9)
 row={'frame':f,'bar':list(bar.location),'depth':motion[f-1]['depth'],'all_skin_bar_min_clearance_m':float(rad.min()-.0145),'all_skin_inside_bar':int((rad<.0145-1e-6).sum()),'chest_bar_clearance_m':float(rad[chest].min()-.0145),'hand_bar_clearance_m':float(rad[hands].min()-.0145),'sole_min_z_m':float(a[feet,2].min()),'sole_max_displacement_m':float(np.linalg.norm(a[feet]-firstfeet,axis=1).max()),'upperback_pad_clearance_m':float(a[back,2].min()-.43),'head_pad_clearance_m':float(a[head,2].min()-.43),'butt_cloth_pad_clearance_m':float(cloth[buttmask,2].min()-.43),'skin_pad_clearance_m':float(a[padzone,2].min()-.43),'cloth_pad_clearance_m':float(cloth[cp,2].min()-.43),'wrist_degrees':wristangles,'elbow_degrees':elbowangles}
 row['digit_clearance_m']={name:float(rad[mask].min()-.0145) for name,mask in digitmasks.items()}
 rows.append(row)
 if f==81:seam=float(abs(first-a).max())
 if f%10==1:print('VALIDATED',f,flush=True)
summary={'skin_vertices':n,'checked_frames':len(rows),'all_skin_inside_bar_max':max(r['all_skin_inside_bar'] for r in rows),'bar_clearance_min_m':min(r['all_skin_bar_min_clearance_m'] for r in rows),'bottom_chest_clearance_m':min(r['chest_bar_clearance_m'] for r in rows),'sole_max_displacement_m':max(r['sole_max_displacement_m'] for r in rows),'sole_min_z_m':min(r['sole_min_z_m'] for r in rows),'skin_pad_min_m':min(r['skin_pad_clearance_m'] for r in rows),'cloth_pad_min_m':min(r['cloth_pad_clearance_m'] for r in rows),'butt_support_m':[min(r['butt_cloth_pad_clearance_m'] for r in rows),max(r['butt_cloth_pad_clearance_m'] for r in rows)],'head_support_m':[min(r['head_pad_clearance_m'] for r in rows),max(r['head_pad_clearance_m'] for r in rows)],'upperback_support_m':[min(r['upperback_pad_clearance_m'] for r in rows),max(r['upperback_pad_clearance_m'] for r in rows)],'wrist_angle_range_degrees':[min(min(r['wrist_degrees'].values()) for r in rows),max(max(r['wrist_degrees'].values()) for r in rows)],'elbow_angle_range_degrees':[min(min(r['elbow_degrees'].values()) for r in rows),max(max(r['elbow_degrees'].values()) for r in rows)],'full_cycle_max_vertex_difference_m':seam}
summary['digit_clearance_ranges_m']={name:[min(r['digit_clearance_m'][name] for r in rows),max(r['digit_clearance_m'][name] for r in rows)] for name in digits}
(QA/('quick_geometry.json' if '--quick' in sys.argv else 'all_frame_geometry_validation.json')).write_text(json.dumps({'summary':summary,'frames':rows},indent=2));print(json.dumps(summary,indent=2),flush=True)
