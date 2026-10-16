#!/usr/bin/env python3
"""Reproducible standalone exercise-motion pipeline, built on the uploaded v4 source."""
from __future__ import annotations
import argparse, json, shutil, sys, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python'))
from interpolate_motion import expand_motion_spec
from validate_motion_spec import validate_full
from export_3d import export_bvh,export_gltf_scene
from render_preview import generate_all_previews

def run(spec_path:Path,out_dir:Path,render=True,force=False):
    out_dir.mkdir(parents=True,exist_ok=True)
    stamp=time.time()
    result={'source':str(spec_path),'status':'ERROR','stages':{},'generated':{},'elapsed_seconds':None}
    try:
        validation=validate_full(str(spec_path))
        p=out_dir/(spec_path.name.removesuffix('.motion_spec.json')+'.validation_report.json')
        p.write_text(json.dumps(validation,indent=2,ensure_ascii=False),encoding='utf-8')
        result['stages']['validate']={'status':validation['status'],'report':str(p),'issues':len(validation['issues'])}
        if validation['status']!='PASS' and not force:
            result['status']='INVALID_SPEC'
            return result
        expanded=expand_motion_spec(str(spec_path)); slug=expanded['exercise_id']
        expanded_path=out_dir/f'{slug}.expanded.json'
        expanded_path.write_text(json.dumps(expanded,ensure_ascii=False,indent=2),encoding='utf-8')
        result['generated']['expanded']=str(expanded_path)
        result['generated']['bvh']=str(export_bvh(expanded,out_dir/f'{slug}.bvh'))
        result['generated']['gltf']=str(export_gltf_scene(expanded,out_dir/f'{slug}.gltf'))
        result['stages']['kinematics']={'status':'PASS','frames':expanded['total_frames']}
        if render:
            for key,value in generate_all_previews(expanded,out_dir).items():
                result['generated'][key]=str(value)
            result['stages']['render']={'status':'PASS'}
        else:
            result['stages']['render']={'status':'SKIPPED'}
        result['status']='PASS' if validation['status']=='PASS' else 'GENERATED_WITH_VALIDATION_ISSUES'
    except Exception as exc:
        result['error']=f'{type(exc).__name__}: {exc}'
        result['traceback']=traceback.format_exc(limit=8)
    finally:
        result['elapsed_seconds']=round(time.time()-stamp,2)
        result_file=out_dir/'pipeline_result.json'
        result_file.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

def main():
    ap=argparse.ArgumentParser(description='Run motion validation, kinematics, optional preview rendering and 3D export.')
    ap.add_argument('spec',nargs='?',type=Path)
    ap.add_argument('--all',action='store_true',help='Run all *.motion_spec.json in samples/')
    ap.add_argument('--output-dir',type=Path,default=ROOT/'outputs_v5')
    ap.add_argument('--no-render',action='store_true',help='Export 3D and validation only')
    ap.add_argument('--force',action='store_true',help='Generate even if validator reports failures (research only)')
    args=ap.parse_args()
    if bool(args.spec)==bool(args.all):ap.error('provide either SPEC or --all')
    specs=sorted((ROOT/'samples').glob('*.motion_spec.json')) if args.all else [args.spec]
    results=[]
    for spec in specs:
        dest=args.output_dir/(spec.name.removesuffix('.motion_spec.json') if args.all else '')
        print(f'Processing {spec}...',flush=True)
        res=run(spec,dest,render=not args.no_render,force=args.force)
        results.append(res)
        print('  ',res['status'],res['elapsed_seconds'],res.get('error',''),flush=True)
    (args.output_dir/'batch_report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if all(x['status']=='PASS' for x in results) else 1
if __name__=='__main__':raise SystemExit(main())
