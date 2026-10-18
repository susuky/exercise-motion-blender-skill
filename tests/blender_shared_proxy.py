"""Opt-in integration test; one decimation, no rendering or human rebuilding."""
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared_human import load_shared_human
from experiments.shared_proxy import create_shared_proxy

bpy.ops.wm.read_factory_settings(use_empty=True)
human = load_shared_human()
human.h.select_set(True)
bpy.context.view_layer.objects.active = human.h
source_vertices = len(human.h.data.vertices)
source_visibility = (human.h.hide_get(), human.h.hide_render)
for ratio in [0, -1, 1.1, float('nan'), True]:
    try:
        create_shared_proxy(human, ratio)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid ratio accepted')
assert len(bpy.data.objects) == 3
proxy, report = create_shared_proxy(human)
assert report['weighted_vertices'] == len(proxy.data.vertices)
assert len(proxy.data.vertices) < source_vertices / 10
assert next(m for m in proxy.modifiers if m.type == 'ARMATURE').object == human.rig
assert bpy.context.view_layer.objects.active == human.h
assert bpy.context.selected_objects == [human.h]
assert source_visibility == (human.h.hide_get(), human.h.hide_render)
assert len(human.h.data.vertices) == source_vertices
assert proxy.hide_get() and proxy.hide_render
try:
    create_shared_proxy(human)
except ValueError:
    pass
else:
    raise AssertionError('Duplicate proxy accepted')
proxy.hide_set(False)

def evaluated(obj):
    obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.to_mesh()
    try:
        vertices = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get('co', vertices)
        return vertices.reshape(-1, 3)
    finally:
        obj.to_mesh_clear()

rest = {name: matrix.copy() for name, matrix in human.rest.items()}
human.apply(rest)
rest_low = evaluated(proxy)
rest_high = evaluated(human.h)
bent = {name: matrix.copy() for name, matrix in rest.items()}
bone = human.bones['lowerarm_l']
transform = rest[bone.name] @ Matrix.Rotation(math.radians(65), 4, 'X') @ rest[bone.name].inverted()
for descendant in [bone, *bone.children_recursive]:
    bent[descendant.name] = transform @ rest[descendant.name]
human.apply(bent)
assert np.linalg.norm(evaluated(proxy) - rest_low, axis=1).max() > .05
assert np.linalg.norm(evaluated(human.h) - rest_high, axis=1).max() > .05
human.apply(rest)
assert np.max(np.abs(evaluated(proxy) - rest_low)) < 1e-5
assert np.max(np.abs(evaluated(human.h) - rest_high)) < 1e-5
print('SHARED PROXY SMOKE PASS', report)
