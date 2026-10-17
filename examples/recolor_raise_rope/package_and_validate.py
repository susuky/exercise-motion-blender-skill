"""Package unchanged timing with a shared palette and exact-white GIF background."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageSequence
import numpy as np,json,sys,hashlib,shutil
R=Path(__file__).resolve().parent
kind=sys.argv[1];O=R/kind/'output';Q=R/kind/'qa';N=36 if kind=='lateral_raise' else 24
files=[O/f'frame_{f:03d}.png' for f in range(1,N+1)];assert all(p.exists() for p in files)
ims=[Image.open(p).convert('RGB') for p in files]
# Build one palette across all phases. Exact-white index is reserved explicitly.
contact=Image.new('RGB',(240*6,240*((N+5)//6)),'white')
for i,im in enumerate(ims):contact.paste(im.resize((240,240)),((i%6)*240,(i//6)*240))
# Stratify the palette by functional color class so small support regions survive encoding.
# Each class learns its rendered shade range; white has its own fixed index.
samples={'neutral':[],'red':[],'blue':[]}
for im in ims:
 a=np.asarray(im);r=(a[:,:,0]>a[:,:,1]*1.20)&(a[:,:,0]>a[:,:,2]*1.20)
 b=(a[:,:,2]>a[:,:,0]*1.20)&(a[:,:,2]>a[:,:,1]*1.05)
 neutral=(~r)&(~b)&(a.min(2)<250)
 samples['red'].append(a[r][::2]);samples['blue'].append(a[b][::2]);samples['neutral'].append(a[neutral][::12])
basepal=[];class_palettes={};class_offsets={};offset=1
for key,count in [('neutral',127),('red',64),('blue',64)]:
 pixels=np.concatenate(samples[key],axis=0);assert len(pixels)>0,key
 colors=Image.fromarray(pixels.reshape((-1,1,3)),'RGB').quantize(colors=count,method=Image.Quantize.MEDIANCUT)
 cp=colors.getpalette()[:count*3];basepal+=cp
 class_image=Image.new('P',(1,1));class_image.putpalette(cp+cp[-3:]*(256-count))
 class_palettes[key]=(class_image,count);class_offsets[key]=offset;offset+=count
palette=Image.new('P',(1,1));palette.putpalette([255,255,255]+basepal)
qs=[]
for im in ims:
 a=np.asarray(im);r=(a[:,:,0]>a[:,:,1]*1.20)&(a[:,:,0]>a[:,:,2]*1.20);b=(a[:,:,2]>a[:,:,0]*1.20)&(a[:,:,2]>a[:,:,1]*1.05)
 masks={'red':r,'blue':b,'neutral':(~r)&(~b)};qi=np.zeros(a.shape[:2],dtype=np.uint8)
 # Quantize within each source class so red/blue dithering cannot speckle gray anatomy or black clothing.
 for key in ['neutral','red','blue']:
  cp,count=class_palettes[key];indices=np.array(im.quantize(palette=cp,dither=Image.Dither.NONE));indices=np.minimum(indices,count-1)
  qi[masks[key]]=indices[masks[key]]+class_offsets[key]
 qi[np.all(a==255,axis=2)]=0
 fixed=Image.fromarray(qi,'P');fixed.putpalette(palette.getpalette());qs.append(fixed)
if kind=='lateral_raise':name='lateral_raise';seq=qs;durations=[80,90,80]*12;rep=19
else:name='battle_rope';seq=qs*4;durations=[40,40,40,40,40,50]*16;rep=7
seq[0].save(O/(name+'.gif'),save_all=True,append_images=seq[1:],duration=durations,loop=0,optimize=False,disposal=2,background=0)
shutil.copy2(files[rep-1],O/'representative.png')
if kind=='battle_rope':shutil.copy2(O/'representative.png',O/'battle_rope_representative.png')
contact.save(Q/'all_frames.png')
checks=[]
for f,im in enumerate(ims,1):
 a=np.array(im);ys,xs=np.where(a.min(2)<235);bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
 red=(a[:,:,0]>a[:,:,1]*1.35)&(a[:,:,0]>a[:,:,2]*1.35)&(a[:,:,0]>80)
 blue=(a[:,:,2]>a[:,:,0]*1.35)&(a[:,:,2]>a[:,:,1]*1.10)&(a[:,:,2]>70)
 checks.append({'frame':f,'size':list(im.size),'bbox':bbox,'edge_margin_px':min(bbox[0],bbox[1],959-bbox[2],959-bbox[3]),'red_pixels':int(red.sum()),'blue_pixels':int(blue.sum()),'corners_exact_white':all(tuple(a[yy,xx])==(255,255,255) for yy,xx in [(0,0),(0,959),(959,0),(959,959)])})
g=Image.open(O/(name+'.gif'));gd=0;gif_white=True;gif_frames=0;background_mismatches=0;gif_red_min=960*960;gif_blue_min=960*960
for fr in ImageSequence.Iterator(g):
 a=np.array(fr.convert('RGB'));source_arr=np.array(ims[gif_frames%N]);known_white=np.all(source_arr==255,axis=2);background_mismatches+=int(np.sum(known_white & np.any(a!=255,axis=2)));gd+=fr.info.get('duration',0);gif_frames+=1;gif_white &= all(tuple(a[y,x])==(255,255,255) for y,x in [(0,0),(0,959),(959,0),(959,959)])
 gr=(a[:,:,0]>a[:,:,1]*1.35)&(a[:,:,0]>a[:,:,2]*1.35)&(a[:,:,0]>80);gb=(a[:,:,2]>a[:,:,0]*1.35)&(a[:,:,2]>a[:,:,1]*1.10)&(a[:,:,2]>70)
 gif_red_min=min(gif_red_min,int(gr.sum()));gif_blue_min=min(gif_blue_min,int(gb.sum()))
res={'exercise':kind,'png_frames':N,'gif_frames':gif_frames,'duration_ms':gd,'gif_background_white':bool(gif_white),'all_background_pixel_mismatches':background_mismatches,'decoded_gif_min_red_pixels':gif_red_min,'decoded_gif_min_blue_pixels':gif_blue_min,'all_frames_have_red_and_blue':all(x['red_pixels']>0 and x['blue_pixels']>0 for x in checks),'min_edge_margin_px':min(x['edge_margin_px'] for x in checks),'frames':checks,'gif_sha256':hashlib.sha256((O/(name+'.gif')).read_bytes()).hexdigest()}
(Q/'render_validation.json').write_text(json.dumps(res,indent=2));assert gif_white and background_mismatches==0 and res['all_frames_have_red_and_blue'];assert res['min_edge_margin_px']>0 and gif_red_min>0 and gif_blue_min>0
assert gif_frames==(36 if kind=='lateral_raise' else 96) and gd==(3000 if kind=='lateral_raise' else 4000)
print(json.dumps({k:v for k,v in res.items() if k!='frames'},indent=2))
