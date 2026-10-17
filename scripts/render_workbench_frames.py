"""Render unchanged Workbench scenes in fresh single-core Blender processes.

This avoids memory accumulation across frames. Example:
python scripts/render_workbench_frames.py examples/barbell_bench_press/output/barbell_bench_press.blend --output examples/barbell_bench_press/output --frames 1,18,37
"""
import argparse, json, os, subprocess, sys, tempfile
try:
    import resource
except ImportError:
    resource = None
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', required=True, help='Comma separated frames; inclusive ranges such as 1-41 allowed')
    p.add_argument('--worker', choices=['freeze', 'render'])
    p.add_argument('--frame', type=int)
    p.add_argument('--temporary', type=Path)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    a.output = a.output.resolve()
    a.output.mkdir(parents=True, exist_ok=True)
    if a.worker:
        import bpy
        if a.worker == 'freeze':
            bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
            scene = bpy.context.scene
            scene.frame_set(a.frame)
            graph = bpy.context.evaluated_depsgraph_get()
            for obj in list(bpy.data.objects):
                if obj.type != 'MESH':
                    continue
                world = obj.matrix_world.copy()
                mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), preserve_all_data_layers=True, depsgraph=graph)
                obj.modifiers.clear()
                obj.data = mesh
                obj.parent = None
                obj.matrix_world = world
                obj.vertex_groups.clear()
                obj.animation_data_clear()
            for obj in list(bpy.data.objects):
                if obj.type == 'ARMATURE':
                    bpy.data.objects.remove(obj, do_unlink=True)
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.render.threads_mode = 'FIXED'
            scene.render.threads = 1
            scene.render.image_settings.file_format = 'PNG'
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(a.temporary), compress=False)
        else:
            bpy.ops.wm.open_mainfile(filepath=str(a.temporary))
            bpy.context.scene.render.filepath = str(a.output/f'frame_{a.frame:03d}.png')
            bpy.ops.render.render(write_still=True)
        return
    frames = []
    for item in a.frames.split(','):
        if '-' in item:
            first, last = map(int, item.split('-'))
            frames.extend(range(first, last+1))
        else:
            frames.append(int(item))
    assert frames and min(frames) > 0
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', LP_NUM_THREADS='1', MALLOC_ARENA_MAX='2')
    records = []
    with tempfile.TemporaryDirectory(dir=a.output) as temporary:
        for frame in frames:
            output = a.output/f'frame_{frame:03d}.png'
            output.unlink(missing_ok=True)
            for stage in ['freeze', 'render']:
                command = [env.get('BLENDER', 'blender'), '-b', '-t', '1', '--python-exit-code', '1', '--python', str(Path(__file__).resolve()), '--', str(a.scene.resolve()), '--output', str(a.output), '--frames', str(frame), '--worker', stage, '--frame', str(frame), '--temporary', str(Path(temporary)/'frame.blend')]
                with (a.output/f'workbench_{frame:03d}_{stage}.log').open('w') as log:
                    result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
                records.append(dict(frame=frame, stage=stage, returncode=result.returncode, cumulative_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if resource else None))
                (a.output/'workbench_render_manifest.json').write_text(json.dumps(records, indent=2))
                if result.returncode:
                    raise RuntimeError(f'Frame {frame} {stage} failed; inspect output log')
            if not output.exists():
                raise RuntimeError(f'Frame {frame} missing')
            print(output, flush=True)

if __name__ == '__main__':
    main()
