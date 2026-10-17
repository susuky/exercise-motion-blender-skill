"""Create a fixed-palette looping GIF, QA sheets and render validation."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,hashlib,shutil,sys
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'
geometry=json.loads((ROOT/'qa/all_frame_geometry_validation.json').read_text())['summary']
assert geometry['all_skin_inside_vertices_max']==0
assert geometry['shorts_inside_vertices_max']==0
assert geometry['leg_min_clearance_m']>0
assert geometry['sole_max_displacement_m']<1e-5
assert geometry['bar_horizontal_drift_m']<1e-5
assert geometry['full_cycle_max_vertex_difference_m']<1e-5
assert geometry['elbow_interior_range_degrees'][0]>179.9
assert abs(geometry['floor_plate_bottom_z_m'])<1e-5
paths=[OUT/f'frame_{i:03d}.png' for i in range(1,81)]
missing=[str(p) for p in paths if not p.exists()]
if missing:raise SystemExit('Missing render frames: '+', '.join(missing))
frames=[Image.open(p).convert('RGB') for p in paths]
# A shared palette prevents per-frame palette changes at the loop seam.
canvas=Image.new('RGB',(960*4,960*4),'white')
for k,i in enumerate(range(0,80,5)):canvas.paste(frames[i],((k%4)*960,(k//4)*960))
pixels=np.asarray(canvas).reshape(-1,3)
redmask=(pixels[:,0].astype(int)-pixels[:,1].astype(int)>12)&(pixels[:,0]>pixels[:,1]*1.15)
def color_pool(arr,count):
 # Balanced samples retain the relatively small muscle-highlight region.
 arr=arr[::max(1,len(arr)//500000)][:500000]
 sample=Image.fromarray(arr.reshape((-1,1,3)).astype('uint8'),'RGB')
 q=sample.quantize(colors=count,method=Image.Quantize.MEDIANCUT)
 return q.getpalette()[:count*3]
bluemask=(pixels[:,2].astype(int)-pixels[:,0].astype(int)>12)&(pixels[:,2]>pixels[:,1]*1.15)
combined=color_pool(pixels[~redmask & ~bluemask],160)+color_pool(pixels[redmask],48)+color_pool(pixels[bluemask],48)
# Reserve exact white for the untextured background.
colors=np.array(combined,dtype=int).reshape(-1,3);wi=int(np.argmin(((255-colors)**2).sum(axis=1)));combined[wi*3:wi*3+3]=[255,255,255]
palette=Image.new('P',(1,1));palette.putpalette(combined)
quantized=[]
for im in frames:
 q=im.quantize(palette=palette,dither=Image.Dither.NONE)
 # Pillow's palette lookup cache can map white to a neighbouring near-white.
 q.paste(wi,mask=Image.fromarray((np.all(np.asarray(im)==255,axis=2)*255).astype('uint8'),'L'));quantized.append(q)
gif=OUT/'conventional_deadlift.gif';quantized[0].save(gif,save_all=True,append_images=quantized[1:],duration=50,loop=0,disposal=2,optimize=False,background=wi)
shutil.copy2(OUT/'frame_001.png',OUT/'representative.png')
sheet=Image.new('RGB',(960*4,960*2),'white')
for k,i in enumerate([0,10,20,30,40,50,60,70]):sheet.paste(frames[i],((k%4)*960,(k//4)*960))
sheet.resize((1920,960),Image.Resampling.LANCZOS).save(OUT/'animation_contact_sheet.jpg',quality=93)
allframes=Image.new('RGB',(160*8,160*10),'white')
for k,im in enumerate(frames):allframes.paste(im.resize((160,160),Image.Resampling.LANCZOS),((k%8)*160,(k//8)*160))
allframes.save(OUT/'all_80_frames.jpg',quality=93)
bounds=[]
for i,im in enumerate(frames,1):
 a=np.array(im);mask=np.min(a,axis=2)<245;y,x=np.where(mask);bounds.append({'frame':i,'bounds':[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1],'white_corners':all(im.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])})
with Image.open(gif) as im:
 durations=[]
 for k in range(im.n_frames):im.seek(k);durations.append(im.info.get('duration',0))
 gifcheck={'size':list(im.size),'frame_count':im.n_frames,'duration_ms':sum(durations),'frame_durations_ms':sorted(set(durations)),'loop':im.info.get('loop')}
assert gifcheck['frame_count']==80 and gifcheck['duration_ms']==4000
with Image.open(gif) as check:
 for k in range(check.n_frames):
  check.seek(k);decoded=check.convert('RGB')
  if k==20:decoded.save(ROOT/'qa/decoded_gif_frame_021.png')
  assert all(decoded.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])
assert all(b['white_corners'] for b in bounds)
assert min(min(b['bounds'][0],b['bounds'][1],960-b['bounds'][2],960-b['bounds'][3]) for b in bounds)>15
(OUT/'gif_validation.json').write_text(json.dumps({'gif':gifcheck,'frames':bounds},indent=2))
manifest={}
for p in [gif,OUT/'representative.png',OUT/'conventional_deadlift.blend',ROOT/'qa/all_frame_geometry_validation.json']:
 manifest[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(gifcheck),flush=True)
