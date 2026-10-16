import bpy,hashlib,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent
out={}
for key,path in [('delivered_scene',R/'output/battle_rope_xhigh.blend'),('rebuilt_human',R/'assets/improved_human.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));m=bpy.data.objects['Human'].data;a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a);c=m.color_attributes['Anatomical fibres'];b=np.empty(len(c.data)*4,dtype=np.float32);c.data.foreach_get('color',b)
 short=bpy.data.objects['Black shorts'].data;d=np.empty(len(short.vertices)*3,dtype=np.float32);short.vertices.foreach_get('co',d)
 out[key]={'vertices':len(m.vertices),'mesh_coordinates_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'vertex_colors_sha256':hashlib.sha256(b.tobytes()).hexdigest(),'shorts_mesh_sha256':hashlib.sha256(d.tobytes()).hexdigest()}
out['exact_match']=out['delivered_scene']==out['rebuilt_human'];(R/'qa/rebuild_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
