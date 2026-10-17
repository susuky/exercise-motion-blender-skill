"""Shared red/blue/gray GIF palette and all-frame checks. python package.py squat|pulldown"""
from pathlib import Path
from PIL import Image
import json,shutil,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parent;kind=sys.argv[1];D=ROOT/kind;OUT=D/'output';QA=D/'qa'
NAME={'squat':'barbell_squat','pulldown':'lat_pulldown'}[kind]
for required in ['mask_front.png','mask_back.png','mask_side.png']:
 assert (QA/required).exists(), 'Missing QA still: '+required
frames=[Image.open(OUT/f'frame_{i:03d}.png').convert('RGB') for i in range(1,81)]
# Keep even tiny, partly occluded red muscle regions in the shared palette.
a=np.concatenate([np.asarray(frames[i]).reshape(-1,3)[::2] for i in range(0,80,5)])
f=a.astype(np.float32);red=(f[:,0]-f[:,1]>14)&(f[:,0]>1.15*f[:,1]);blue=(f[:,2]-f[:,0]>14)&(f[:,2]>1.10*f[:,1]);gray=~(red|blue)
def pool(px,n):
 px=px[::max(1,len(px)//300000)][:300000]
 if len(px)==0:raise RuntimeError('A semantic color is absent')
 q=Image.fromarray(px.reshape(-1,1,3)).quantize(colors=n,method=Image.Quantize.MEDIANCUT);return q.getpalette()[:n*3]
palette=Image.new('P',(1,1));palette.putpalette(pool(a[gray],128)+pool(a[red],64)+pool(a[blue],64))
q=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
gif=OUT/f'{NAME}_recolored.gif';q[0].save(gif,save_all=True,append_images=q[1:],duration=50,loop=0,disposal=2,optimize=False)
shutil.copy2(OUT/'frame_041.png',OUT/'representative.png')
# Contact sheets are inspection deliverables, with no text on the exercise images.
sheet=Image.new('RGB',(1920,960),'white')
for k,i in enumerate([0,10,20,30,40,50,60,70]):sheet.paste(frames[i].resize((480,480),Image.Resampling.LANCZOS),((k%4)*480,(k//4)*480))
sheet.save(OUT/'animation_contact_sheet.jpg',quality=95)
sheet=Image.new('RGB',(1920,2400),'white')
for k,im in enumerate(frames):sheet.paste(im.resize((240,240),Image.Resampling.LANCZOS),((k%8)*240,(k//8)*240))
sheet.save(OUT/'all_80_frames.jpg',quality=95)
rows=[]
for i,im in enumerate(frames,1):
 p=np.asarray(im);a=p.astype(np.int16);obj=np.min(a,axis=2)<245;y,x=np.where(obj)
 r=(a[:,:,0]-a[:,:,1]>14)&(a[:,:,0]>a[:,:,1]*1.15);b=(a[:,:,2]-a[:,:,0]>14)&(a[:,:,2]>a[:,:,1]*1.1)
 corners=all(im.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])
 rows.append({'frame':i,'bounds':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],'red_pixels':int(r.sum()),'blue_pixels':int(b.sum()),'white_corners':corners})
with Image.open(gif) as im:
 durations=[]
 for i in range(im.n_frames):im.seek(i);durations.append(im.info.get('duration',0))
 info={'size':list(im.size),'frames':im.n_frames,'duration_ms':sum(durations),'per_frame_ms':sorted(set(durations)),'loop':im.info.get('loop')}
assert info['size']==[960,960] and info['frames']==80 and info['duration_ms']==4000 and info['loop']==0
assert all(r['white_corners'] and r['blue_pixels']>0 and r['bounds'][0]>0 and r['bounds'][1]>0 and r['bounds'][2]<960 and r['bounds'][3]<960 for r in rows)
(QA/'all_frame_color_qa.json').write_text(json.dumps({'gif':info,'frames':rows},indent=2))
manifest={}
for p in [gif,OUT/'representative.png',OUT/f'{NAME}_recolored.blend',QA/'color_map_validation.json',QA/'all_frame_color_qa.json',ROOT/'recolor.py',ROOT/'ANATOMICAL_COLOR_MAP.md']:
 manifest[str(p.relative_to(ROOT))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(D/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(info));print('COMPLETE',kind)
