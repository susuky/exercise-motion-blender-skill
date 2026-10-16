from PIL import Image,ImageDraw
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'output'
frames=sorted(OUT.glob('frame_*.png'))
for p in [*frames,*OUT.glob('*check.png')]:
 im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im);bg.convert('RGB').save(p)
if (OUT/'frame_019.png').exists():shutil.copy2(OUT/'frame_019.png',OUT/'representative.png')
if len(frames)==36:
 ims=[Image.open(p).convert('RGB') for p in frames]
 pal=Image.new('RGB',(240*6,240*6),'white')
 for i,im in enumerate(ims):pal.paste(im.resize((240,240)),((i%6)*240,(i//6)*240))
 palette=pal.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
 qs=[im.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG) for im in ims]
 qs[0].save(OUT/'lateral_raise_xhigh.gif',save_all=True,append_images=qs[1:],duration=[80,90,80]*12,loop=0,optimize=False,disposal=2)
 sheet=Image.new('RGB',(1280,960),'white');d=ImageDraw.Draw(sheet)
 for i,k in enumerate([1,4,7,10,13,16,19,22,25,28,31,36]):
  im=ims[k-1].resize((320,320));sheet.paste(im,((i%4)*320,(i//4)*320));d.text(((i%4)*320+8,(i//4)*320+8),str(k),fill='#777777')
 sheet.save(OUT/'animation_contact_sheet.jpg',quality=94)
 allsheet=Image.new('RGB',(1440,1440),'white');draw=ImageDraw.Draw(allsheet)
 for i,im in enumerate(ims):
  allsheet.paste(im.resize((240,240)),((i%6)*240,(i//6)*240));draw.text(((i%6)*240+6,(i//6)*240+6),str(i+1),fill='#777777')
 allsheet.save(OUT/'all_36_frames.jpg',quality=93)
 # Check all visible image bounds with conservative foreground threshold.
 import numpy as np
 qa=[]
 for p,im in zip(frames,ims):
  a=np.array(im);mask=np.min(a,axis=2)<235;ys,xs=np.where(mask)
  bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
  qa.append({'frame':int(p.stem.split('_')[1]),'foreground_bbox_px':bbox,'minimum_edge_margin_px':min(bbox[0],bbox[1],959-bbox[2],959-bbox[3])})
 (OUT/'frame_bounds.json').write_text(json.dumps(qa,indent=2))
 print('GIF',OUT/'lateral_raise_xhigh.gif','all frame min margin',min(x['minimum_edge_margin_px'] for x in qa))
else: print('Stills available:',len(frames))
