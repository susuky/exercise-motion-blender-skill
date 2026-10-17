"""Build the fixed-palette GIF, overview sheets, and render validation."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil,numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output';QA=ROOT/'qa'
frames=[Image.open(OUT/f'frame_{i:03d}.png').convert('RGB') for i in range(1,81)]
canvas=Image.new('RGB',(960*4,960*4),'white')
for k,i in enumerate(range(0,80,5)):canvas.paste(frames[i],((k%4)*960,(k//4)*960))
a=np.asarray(canvas).reshape(-1,3);red=(a[:,0].astype(int)-a[:,1].astype(int)>12)&(a[:,0]>a[:,1]*1.15)
blue=(a[:,2].astype(int)-a[:,0].astype(int)>12)&(a[:,2]>a[:,1]*1.15)
def pool(arr,n):
 arr=arr[::max(1,len(arr)//500000)][:500000];q=Image.fromarray(arr.reshape((-1,1,3)).astype('uint8'),'RGB').quantize(colors=n,method=Image.Quantize.MEDIANCUT);return q.getpalette()[:n*3]
colors=pool(a[~(red|blue)],160)+pool(a[red],48)+pool(a[blue],48)
white=min(range(256),key=lambda i:sum((255-v)**2 for v in colors[i*3:i*3+3]));colors[white*3:white*3+3]=[255,255,255]
pal=Image.new('P',(1,1));pal.putpalette(colors);q=[]
for im in frames:
 quant=im.quantize(palette=pal,dither=Image.Dither.NONE);idx=np.array(quant);idx[np.all(np.asarray(im)==255,axis=2)]=white;quant=Image.fromarray(idx,'P');quant.putpalette(colors);q.append(quant)
gif=OUT/'barbell_bench_press.gif';q[0].save(gif,save_all=True,append_images=q[1:],duration=50,loop=0,disposal=2,optimize=False,background=white)
shutil.copy2(OUT/'frame_037.png',OUT/'representative.png')
sheet=Image.new('RGB',(1920,960),'white')
for k,i in enumerate([0,10,20,33,40,50,60,73]):sheet.paste(frames[i].resize((480,480),Image.Resampling.LANCZOS),((k%4)*480,(k//4)*480))
sheet.save(OUT/'animation_contact_sheet.jpg',quality=95)
sheet=Image.new('RGB',(1280,1600),'white')
for k,im in enumerate(frames):sheet.paste(im.resize((160,160),Image.Resampling.LANCZOS),((k%8)*160,(k//8)*160))
sheet.save(OUT/'all_80_frames.jpg',quality=94)
bounds=[]
for i,im in enumerate(frames,1):
 a=np.array(im);y,x=np.where(a.min(axis=2)<245);bounds.append({'frame':i,'bounds':[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1],'white_corners':all(im.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])})
with Image.open(gif) as im:
 dur=[]
 for i in range(im.n_frames):
  im.seek(i);dur.append(im.info.get('duration',0));rgb=im.convert('RGB')
  assert all(rgb.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])
 info={'size':list(im.size),'encoded_frames':im.n_frames,'timeline_frames':80,'total_duration_ms':sum(dur),'durations_ms':sorted(set(dur)),'loop':im.info.get('loop')}
assert info['total_duration_ms']==4000
assert all(b['white_corners'] for b in bounds)
assert min(min(b['bounds'][0],b['bounds'][1],960-b['bounds'][2],960-b['bounds'][3]) for b in bounds)>15
(OUT/'gif_validation.json').write_text(json.dumps({'gif':info,'frames':bounds},indent=2))
if (QA/'all_frame_geometry_validation.json').exists():
 geom=json.loads((QA/'all_frame_geometry_validation.json').read_text())['summary']
 assert geom['all_skin_inside_bar_max']==0
 assert geom['sole_max_displacement_m']<1e-5
 assert geom['full_cycle_max_vertex_difference_m']<1e-5
 assert geom['skin_pad_min_m']>-.0002
 assert geom['elbow_angle_range_degrees'][1]<176
manifest={}
for p in [gif,OUT/'representative.png',OUT/'barbell_bench_press.blend']:
 manifest[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
