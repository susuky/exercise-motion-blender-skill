from PIL import Image,ImageDraw
from pathlib import Path
import json,shutil
import numpy as np
R=Path(__file__).resolve().parent;O=R/'output';Q=R/'qa';frames=sorted(O.glob('frame_*.png'));assert len(frames)==24,len(frames)
ims=[Image.open(p).convert('RGB') for p in frames]
pal=Image.new('RGB',(240*6,240*4),'white')
for i,im in enumerate(ims):pal.paste(im.resize((240,240)),((i%6)*240,(i//6)*240))
palette=pal.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
qs=[im.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG) for im in ims]*4
qs[0].save(O/'battle_rope.gif',save_all=True,append_images=qs[1:],duration=[40,40,40,40,40,50]*16,loop=0,optimize=False,disposal=2)
shutil.copy2(O/'frame_007.png',O/'battle_rope_representative.png')
sheet=Image.new('RGB',(1440,960),'white');d=ImageDraw.Draw(sheet)
for i,im in enumerate(ims):sheet.paste(im.resize((240,240)),((i%6)*240,(i//6)*240));d.text(((i%6)*240+7,(i//6)*240+7),str(i+1),fill='#777777')
sheet.save(Q/'all_24_frames.jpg',quality=95)
bounds=[]
for i,im in enumerate(ims):
 a=np.array(im);ys,xs=np.where(np.min(a,axis=2)<235);bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())];bounds.append({'frame':i+1,'foreground_bbox_px':bbox,'minimum_edge_margin_px':min(bbox[0],bbox[1],959-bbox[2],959-bbox[3])})
(Q/'frame_bounds.json').write_text(json.dumps(bounds,indent=2))
gif=Image.open(O/'battle_rope.gif');duration=0
for i in range(gif.n_frames):gif.seek(i);duration+=gif.info['duration']
print('GIF',gif.n_frames,'frames,',duration,'ms, min margin',min(x['minimum_edge_margin_px'] for x in bounds))
