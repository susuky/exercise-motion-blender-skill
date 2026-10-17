"""Rebuild using only these compact sources and the shared HUMAN_BLEND asset."""
import os,subprocess,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;env=os.environ.copy()
env.setdefault('HUMAN_BLEND',str(D.parents[1]/'assets/improved_human.blend'))
assert Path(env['HUMAN_BLEND']).exists(),'Build the shared assets/improved_human.blend with rebuild_human.py first.'
threads=env.get('BLENDER_THREADS','1')
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','LP_NUM_THREADS'):env.setdefault(key,threads)
blender=env.get('BLENDER','blender')
def run(script,*args):
 available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))) if Path('/proc/meminfo').exists() else 2**30
 assert available>1048576,'Wait for at least 1 GiB available RAM before rebuilding.'
 subprocess.run([blender,'-b','-t',threads,'--python-exit-code','1','--python',str(script)]+(['--']+list(args) if args else []),env=env,check=True)
run(D/'rebuild/base_squat/build_scene.py');run(D/'rebuild/base_squat/scripts/refine_leg_tracking.py')
env['SQUAT_BASE_SCENE']=str(D/'rebuild/base_squat/output/barbell_squat.blend');run(D/'rebuild/color_revision/recolor.py','squat','patch')
env['SQUAT_ORIGINAL_BLEND']=str(D/'rebuild/color_revision/squat/output/barbell_squat_recolored.blend');run(D/'restore_motion.py');env['ALLOW_REBUILT_BASELINE']='1';run(D/'patch_scene.py')
print('Scene rebuilt from the shared human; next run render.py and package.py.')
