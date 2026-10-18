"""Opt-in decimated pose preview. Never a collision-safety certificate."""
import math
import time
from shared_human import validate_vertex_weights


def create_shared_proxy(human, ratio=0.01, name='Human.low_proxy'):
    """Copy the shared body's rest mesh and decimate before its live armature.

    The proxy uses Blender's decimation weight interpolation and the SAME rig
    and skinning method. Its surface does not enclose the original body.
    Initially hidden in viewport and render; explicitly show it for preview.
    No scene visibility or animation on the source is changed.
    """
    import bpy
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not math.isfinite(ratio) or not 0 < ratio <= 1:
        raise ValueError('ratio must be finite and greater than zero, at most one')
    if not name or name in bpy.data.objects:
        raise ValueError('Proxy name must be nonempty and unused')
    if bpy.context.mode != 'OBJECT':
        raise ValueError('Create the proxy in Object mode')
    source = human.h
    arms = [m for m in source.modifiers if m.type == 'ARMATURE']
    if len(arms) != 1 or arms[0].object != human.rig:
        raise ValueError('Source must use exactly the shared Human.rig')
    if source.data.shape_keys or any(m.type != 'ARMATURE' for m in source.modifiers):
        raise ValueError('Proxy requires the baked shared body with only its armature modifier')
    started = time.perf_counter()
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    proxy = None
    mesh = None
    try:
        proxy = source.copy()
        mesh = source.data.copy()
        proxy.data = mesh
        proxy.name = name
        bpy.context.collection.objects.link(proxy)
        proxy.animation_data_clear()
        proxy.hide_set(False)
        proxy.hide_viewport = False
        arm = next(m for m in proxy.modifiers if m.type == 'ARMATURE')
        arm.show_viewport = False
        arm.show_render = False
        decimate = proxy.modifiers.new('Experimental rest mesh decimation', 'DECIMATE')
        decimate.ratio = ratio
        decimate.use_collapse_triangulate = True
        proxy.modifiers.move(len(proxy.modifiers) - 1, 0)
        bpy.ops.object.select_all(action='DESELECT')
        proxy.select_set(True)
        bpy.context.view_layer.objects.active = proxy
        bpy.ops.object.modifier_apply(modifier=decimate.name)
        arm.show_viewport = arms[0].show_viewport
        arm.show_render = arms[0].show_render
        if arm.object != human.rig or arm.use_deform_preserve_volume != arms[0].use_deform_preserve_volume:
            raise ValueError('Proxy skinning differs from source')
        weighted = validate_vertex_weights(proxy, human.rig)
        proxy.hide_render = True
        proxy.hide_set(True)
        return proxy, {
            'build_seconds': time.perf_counter() - started,
            'source_vertices': len(source.data.vertices),
            'proxy_vertices': len(proxy.data.vertices),
            'proxy_polygons': len(proxy.data.polygons),
            'weighted_vertices': weighted,
            'ratio': ratio, 'shared_armature': human.rig.name,
            'preserve_volume': arm.use_deform_preserve_volume,
            'weight_transfer': 'Blender rest-mesh decimation interpolation',
            'purpose': 'pose_preview_only', 'collision_certificate': False,
        }
    except Exception:
        if proxy is not None:
            bpy.data.objects.remove(proxy, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        raise
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
