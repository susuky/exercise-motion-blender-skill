"""Load the reusable muscular human; no mesh generation or scene replacement."""
import hashlib
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OBJECT_TYPES = {'Human': 'MESH', 'Human.rig': 'ARMATURE', 'Black shorts': 'MESH'}
REQUIRED_BONES = ('pelvis',) + tuple(
    f'{part}_{side}' for side in ('l', 'r')
    for part in ('upperarm', 'lowerarm', 'hand', 'thigh', 'calf', 'foot')
) + tuple(f'{finger}_{segment:02}_{side}' for side in ('l', 'r')
          for finger in ('thumb', 'index', 'middle', 'ring', 'pinky')
          for segment in (1, 2, 3))


def resolve_asset(asset_path=None):
    """An explicit path or HUMAN_BLEND overrides the repository default."""
    path = Path(asset_path or os.environ.get('HUMAN_BLEND') or
                ROOT / 'assets/improved_human.blend').expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f'Missing shared muscular human: {path}. Run '
            'blender -b --python rebuild_human.py once, or set HUMAN_BLEND '
            'to an existing improved_human.blend.')
    return path


def asset_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_vertex_weights(obj, rig):
    """Require real, finite, positive deform-bone weights on every vertex."""
    deform_groups = {group.index for group in obj.vertex_groups
                     if group.name in rig.data.bones and
                     rig.data.bones[group.name].use_deform}
    if not deform_groups:
        raise ValueError(f'{obj.name} has no deform-bone vertex groups')
    weighted = 0
    for vertex in obj.data.vertices:
        total = 0.0
        for assignment in vertex.groups:
            if assignment.group in deform_groups:
                if not math.isfinite(assignment.weight) or assignment.weight < 0:
                    raise ValueError(f'{obj.name} has invalid deform weights')
                total += assignment.weight
        if total > 0:
            weighted += 1
    if weighted != len(obj.data.vertices):
        raise ValueError(f'{obj.name} has {len(obj.data.vertices) - weighted} '
                         'vertices without positive deform-bone weights')
    return weighted


def validate_human(human):
    """Check the shared asset contract; this is not motion/contact QA."""
    h, rig, shorts = human.h, human.rig, human.shorts
    for name, obj in zip(OBJECT_TYPES, (h, rig, shorts)):
        if obj.type != OBJECT_TYPES[name]:
            raise ValueError(f'{name} must be {OBJECT_TYPES[name]}')
    missing = set(REQUIRED_BONES) - set(rig.data.bones.keys())
    if missing:
        raise ValueError(f'Missing required bones: {sorted(missing)}')
    attr = h.data.color_attributes.get('Anatomical fibres')
    if attr is None or attr.domain != 'POINT' or len(attr.data) != len(h.data.vertices):
        raise ValueError('Expected per-vertex Anatomical fibres color attribute')
    arms = []
    weighted_counts = {}
    for obj in (h, shorts):
        mods = [m for m in obj.modifiers if m.type == 'ARMATURE']
        if len(mods) != 1 or mods[0].object != rig:
            raise ValueError(f'{obj.name} must deform with the shared Human.rig')
        if not mods[0].show_viewport or not mods[0].show_render:
            raise ValueError(f'{obj.name} armature must be enabled')
        if not len(obj.data.vertices) or not len(obj.vertex_groups):
            raise ValueError(f'{obj.name} must contain a weighted mesh')
        weighted_counts[obj.name] = validate_vertex_weights(obj, rig)
        arms.append(mods[0])
    if arms[0].use_deform_preserve_volume != arms[1].use_deform_preserve_volume:
        raise ValueError('Body and shorts deformation settings differ')
    if not any(m.type == 'SOLIDIFY' and m.thickness > 0 for m in shorts.modifiers):
        raise ValueError('Shorts must retain their physical shell thickness')
    return {'body_vertices': len(h.data.vertices), 'bones': len(rig.data.bones),
            'shorts_vertices': len(shorts.data.vertices),
            'preserve_volume': arms[0].use_deform_preserve_volume,
            'shared_armature': True,
            'color_attribute': attr.name, 'color_domain': attr.domain,
            'weighted_vertices': weighted_counts}


class SharedHuman:
    """Body, clothing and rest-space pose interface for new exercise builders."""
    def __init__(self, body, rig, shorts):
        self.h, self.rig, self.shorts = body, rig, shorts
        self.bones = rig.data.bones
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}

    def apply(self, desired):
        """Set a complete pose of bone matrices in armature object space.

        Start from {name: matrix.copy() for name, matrix in human.rest.items()}.
        Both full-resolution body and any separately created proxy must reference
        self.rig, rather than copying animation onto another skeleton.
        """
        import bpy
        if set(desired) != set(self.rest):
            raise ValueError('Pose must provide exactly all shared rig bone names')
        # Validate before mutation; no partial pose on invalid input.
        from mathutils import Matrix
        if any(not isinstance(matrix, Matrix) or len(matrix) != 4 or
               len(matrix[0]) != 4 or
               any(not math.isfinite(value) for row in matrix for value in row)
               for matrix in desired.values()):
            raise ValueError('Pose matrices must be finite 4 by 4 matrices')
        basis = {}
        for name, pb in self.rig.pose.bones.items():
            parent = pb.parent
            ref = (desired[parent.name] @ self.rest[parent.name].inverted() @
                   self.rest[name]) if parent else self.rest[name]
            basis[name] = ref.inverted() @ desired[name]
        for name, pb in self.rig.pose.bones.items():
            pb.rotation_mode = 'QUATERNION'
            pb.matrix_basis = basis[name]
        bpy.context.view_layer.update()


def clear_role_colors(body):
    """Neutralize previous red/blue overlays, preserving their fibre intensity.

    This assumes the repository's red/blue palette, not arbitrary imported maps.
    Exercise builders must supply anatomically reviewed masks separately.
    """
    import numpy as np
    attr = body.data.color_attributes['Anatomical fibres']
    colors = np.empty(len(attr.data) * 4, dtype=np.float32)
    attr.data.foreach_get('color', colors)
    colors = colors.reshape(-1, 4)
    mask = (colors[:, 0] > colors[:, 1] + .001) | (colors[:, 2] > colors[:, 1] + .08)
    intensity = np.maximum(colors[mask, 0], colors[mask, 2]) / .72
    colors[mask, :3] = intensity[:, None] * np.array([.73, .75, .76])
    attr.data.foreach_set('color', colors.ravel())
    body.data.update()
    return int(mask.sum())


def load_shared_human(asset_path=None, *, expected_sha256=None):
    """Append only the human into the current scene; preserve other scene objects.

    An existing Human/Human.rig/Black shorts is an error, never silently deleted.
    External .blend files must be trusted. Embedded scripts are not run here.
    """
    import bpy
    path = resolve_asset(asset_path)
    digest = asset_sha256(path)
    if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
        raise ValueError('Shared human asset SHA-256 mismatch')
    if any(name in bpy.data.objects for name in OBJECT_TYPES):
        raise ValueError('Shared human already exists; use a fresh scene or reuse it')
    before = set(bpy.data.objects)
    try:
        with bpy.data.libraries.load(str(path), link=False) as (source, target):
            missing = set(OBJECT_TYPES) - set(source.objects)
            if missing:
                raise ValueError(f'Shared asset missing objects: {sorted(missing)}')
            target.objects = list(OBJECT_TYPES)
        objects = dict(zip(OBJECT_TYPES, target.objects))
        human = SharedHuman(objects['Human'], objects['Human.rig'], objects['Black shorts'])
        # Match the original body algorithm; garment contact still needs pose QA.
        body_mods = [m for m in human.h.modifiers if m.type == 'ARMATURE']
        for mod in human.shorts.modifiers:
            if mod.type == 'ARMATURE' and len(body_mods) == 1:
                mod.use_deform_preserve_volume = body_mods[0].use_deform_preserve_volume
        human.report = validate_human(human)
        human.report['cleared_role_vertices'] = clear_role_colors(human.h)
        for obj in objects.values():
            bpy.context.collection.objects.link(obj)
            obj.animation_data_clear()
        for pb in human.rig.pose.bones:
            pb.matrix_basis.identity()
        human.rig.data.pose_position = 'POSE'
        bpy.context.view_layer.update()
        human.report['asset_sha256'] = digest
        return human
    except Exception:
        for obj in set(bpy.data.objects) - before:
            bpy.data.objects.remove(obj, do_unlink=True)
        raise
