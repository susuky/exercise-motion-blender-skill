from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parent;O=R/'output';Q=R/'qa'
source_files=[R/n for n in ['README.md','build_battle_ropes.py','rebuild_improved_human.py','render_saved.py','validate_battle_ropes.py','compare_rebuilt_human.py','package.py','make_delivery.py','assets/base_human.blend','assets/LICENSE.ASSETS.md']]+sorted(Q.glob('*.json'))+[Q/'QA_summary.md']
with zipfile.ZipFile(R/'battle_rope_reproducible_source.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in source_files:z.write(p,p.relative_to(R))
full_files=[O/'battle_rope_xhigh.gif',O/'battle_rope_representative.png',O/'battle_rope_xhigh.blend',R/'battle_rope_reproducible_source.zip',R/'README.md']+sorted(Q.glob('*'))
with zipfile.ZipFile(R/'battle_rope_complete_sample.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in full_files:
  if p.is_file():z.write(p,p.relative_to(R))
manifest={}
for p in [O/'battle_rope_xhigh.gif',O/'battle_rope_representative.png',O/'battle_rope_xhigh.blend',R/'battle_rope_reproducible_source.zip',R/'battle_rope_complete_sample.zip']:
 manifest[str(p.relative_to(R))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(R/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
