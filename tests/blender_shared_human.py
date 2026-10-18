"""Run with Blender; requires an already-built shared asset, never rebuilds it."""
import sys
import math
import numpy as np
from pathlib import Path
import bpy
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared_human import load_shared_human, validate_human, validate_vertex_weights

bpy.ops.wm.read_factory_settings(use_empty=True)
sentinel = bpy.data.objects.new('Existing equipment', None)
bpy.context.collection.objects.link(sentinel)
try:
    load_shared_human(expected_sha256='0' * 64)
except ValueError:
    pass
else:
    raise AssertionError('Mismatched checksum accepted')
assert len(bpy.data.objects) == 1
human = load_shared_human()
assert sentinel.name in bpy.context.scene.objects
assert len(bpy.context.scene.objects) == 4
assert human.report['body_vertices'] > 0
assert all(pb.matrix_basis == Matrix.Identity(4) for pb in human.rig.pose.bones)
pose = {name: matrix.copy() for name, matrix in human.rest.items()}
translation = Matrix.Translation((0.1, 0.0, 0.0))
human.apply({name: translation @ matrix for name, matrix in pose.items()})
assert (human.rig.pose.bones['pelvis'].matrix.translation -
        (translation @ pose['pelvis']).translation).length < 1e-5
human.apply(pose)
assert validate_human(human)['shared_armature']

# A real bent elbow plus hip flexion exercises child/parent transforms and cloth.
def evaluated_vertices(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get('co', coordinates)
        return coordinates.reshape(-1, 3)
    finally:
        evaluated.to_mesh_clear()

rest_body = evaluated_vertices(human.h)
rest_cloth = evaluated_vertices(human.shorts)
bent = {name: matrix.copy() for name, matrix in pose.items()}
for name, degrees in [('lowerarm_l', 65), ('thigh_l', 25)]:
    transform = pose[name] @ Matrix.Rotation(math.radians(degrees), 4, 'X') @ pose[name].inverted()
    bone = human.bones[name]
    for descendant in [bone, *bone.children_recursive]:
        bent[descendant.name] = transform @ pose[descendant.name]
human.apply(bent)
for name, expected in bent.items():
    assert np.max(np.abs(np.array(human.rig.pose.bones[name].matrix) - np.array(expected))) < 2e-5, name
assert (human.rig.pose.bones['lowerarm_l'].head - human.bones['lowerarm_l'].head_local).length < 1e-5
assert (human.rig.pose.bones['hand_l'].head - human.bones['hand_l'].head_local).length > .05
bent_body = evaluated_vertices(human.h)
bent_cloth = evaluated_vertices(human.shorts)
assert np.linalg.norm(bent_body - rest_body, axis=1).max() > .05
assert np.linalg.norm(bent_cloth - rest_cloth, axis=1).max() > .005

# Reference the existing Human.apply contract directly: desired parent in
# armature space -> parent-relative matrix_basis -> dependency-graph evaluation.
human.apply(pose)
for name, pb in human.rig.pose.bones.items():
    reference = (bent[pb.parent.name] @ pose[pb.parent.name].inverted() @ pose[name]
                 if pb.parent else pose[name])
    pb.matrix_basis = reference.inverted() @ bent[name]
    pb.rotation_mode = 'QUATERNION'
bpy.context.view_layer.update()
assert np.max(np.abs(evaluated_vertices(human.h) - bent_body)) < 1e-6
assert np.max(np.abs(evaluated_vertices(human.shorts) - bent_cloth)) < 1e-6
human.apply(pose)
del rest_body, rest_cloth, bent_body, bent_cloth

# A matching group name with no assigned weights must be rejected.
mesh = bpy.data.meshes.new('Unweighted test mesh')
mesh.from_pydata([(0, 0, 0)], [], [])
unweighted = bpy.data.objects.new('Unweighted test body', mesh)
unweighted.vertex_groups.new(name='pelvis')
try:
    validate_vertex_weights(unweighted, human.rig)
except ValueError:
    pass
else:
    raise AssertionError('Group names without real weights accepted')
bpy.data.objects.remove(unweighted, do_unlink=True)
bpy.data.meshes.remove(mesh)

shorts_arm = next(m for m in human.shorts.modifiers if m.type == 'ARMATURE')
shorts_arm.use_deform_preserve_volume = not human.report['preserve_volume']
try:
    validate_human(human)
except ValueError:
    pass
else:
    raise AssertionError('Mismatched skinning accepted')
shorts_arm.use_deform_preserve_volume = human.report['preserve_volume']
invalid_pose = {name: matrix.copy() for name, matrix in pose.items()}
invalid_pose['pelvis'][0][0] = float('nan')
try:
    human.apply(invalid_pose)
except ValueError:
    pass
else:
    raise AssertionError('Non-finite pose accepted')
try:
    human.apply({})
except ValueError:
    pass
else:
    raise AssertionError('Incomplete pose accepted')
try:
    load_shared_human()
except ValueError:
    pass
else:
    raise AssertionError('Duplicate load accepted')
print('SHARED HUMAN SMOKE PASS', human.report)
