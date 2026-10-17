"""Encode and validate the unchanged four-second motion, then validate generated frames."""
from pathlib import Path
from PIL import Image
import json,hashlib,numpy as np,shutil,sys
D=Path(__file__).resolve().parent;O=D/'output';Q=D/'qa';slug='barbell_squat_recolored_garment_v2'
paths=[O/f'frame_{i:03d}.png' for i in range(1,81)];assert all(p.exists() for p in paths)
frames=[Image.open(p).convert('RGB') for p in paths]
a=np.concatenate([np.asarray(frames[i].resize((240,240))).reshape(-1,3) for i in range(0,80,5)])
red=(a[:,0].astype(int)-a[:,1].astype(int)>12)&(a[:,0]>a[:,1]*1.15)
blue=(a[:,2].astype(int)-a[:,0].astype(int)>12)&(a[:,2]>a[:,1]*1.15)
def pool(arr,n):
 if not len(arr):return [0,0,0]*n
 p=Image.fromarray(arr.reshape(-1,1,3).astype('uint8'),'RGB').quantize(colors=n,method=Image.Quantize.MEDIANCUT).getpalette()[:n*3]
 return p+[0]*(n*3-len(p))
colors=pool(a[~(red|blue)],160)+pool(a[red],48)+pool(a[blue],48)
white=min(range(256),key=lambda i:sum((255-v)**2 for v in colors[i*3:i*3+3]));colors[white*3:white*3+3]=[255]*3
pal=Image.new('P',(1,1));pal.putpalette(colors);quantized=[];bounds=[]
for i,im in enumerate(frames,1):
 ar=np.asarray(im);quant=im.quantize(palette=pal,dither=Image.Dither.NONE);idx=np.array(quant);idx[np.all(ar==255,axis=2)]=white
 quant=Image.fromarray(idx,'P');quant.putpalette(colors);quantized.append(quant)
 y,x=np.where(ar.min(axis=2)<245)
 bounds.append({'frame':i,'bounds':[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1],'white_corners':all(im.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])})
gif=O/(slug+'.gif');quantized[0].save(gif,save_all=True,append_images=quantized[1:],duration=50,loop=0,disposal=2,optimize=False,background=white)
shutil.copy2(paths[40],O/'representative.png')
for name,cols,cell,indices in [('animation_contact_sheet.jpg',4,480,[0,10,20,30,40,50,60,70]),('all_80_frames.jpg',8,160,list(range(80)))]:
 sheet=Image.new('RGB',(cols*cell,((len(indices)+cols-1)//cols)*cell),'white')
 for k,i in enumerate(indices):sheet.paste(frames[i].resize((cell,cell),Image.Resampling.LANCZOS),((k%cols)*cell,(k//cols)*cell))
 sheet.save(O/name,quality=94)
with Image.open(gif) as im:
 durations=[]
 for i in range(im.n_frames):
  im.seek(i);durations.append(im.info.get('duration',0));rgb=im.convert('RGB');assert all(rgb.getpixel(p)==(255,255,255) for p in [(0,0),(959,0),(0,959),(959,959)])
 info={'size':list(im.size),'encoded_frames':im.n_frames,'timeline_frames':80,'total_duration_ms':sum(durations),'durations_ms':sorted(set(durations)),'loop':im.info.get('loop')}
assert info['size']==[960,960] and info['total_duration_ms']==4000
margin=min(min(b['bounds'][0],b['bounds'][1],960-b['bounds'][2],960-b['bounds'][3]) for b in bounds)
assert margin>15 and all(b['white_corners'] for b in bounds)
(Q/'gif_validation.json').write_text(json.dumps({'gif':info,'minimum_border_pixels':margin,'frames':bounds},indent=2))
identity=json.loads((Q/'revision_identity.json').read_text());assert identity['bind_geometry_colors_animation_camera_unchanged'] and identity['original_file_unchanged']
assert json.loads((Q/'reverse_frame_equivalence.json').read_text())['all_action_channels_max_difference']<1e-5
print(json.dumps(info))
