"""
Headless Blender `bpy` API Emulation & Verification Harness.

Allows `blender/generate_from_motion_spec.py` to execute and be unit-tested
in standard Python environments when the native `blender` binary is not installed,
recording every created Object, Mesh, Armature, Bone, Constraint, Material, Light,
Camera, and Keyframe channel.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


class _NodeInput:
    def __init__(self, default_value=None):
        self.default_value = default_value


class _BSDFNode:
    def __init__(self):
        self.inputs = {
            "Base Color": _NodeInput((0.8, 0.8, 0.8, 1.0)),
            "Metallic": _NodeInput(0.0),
            "Roughness": _NodeInput(0.5),
            "Emission Strength": _NodeInput(0.0),
        }


class _NodeTree:
    def __init__(self):
        self.nodes = {"Principled BSDF": _BSDFNode()}


class MockMaterial:
    def __init__(self, name: str):
        self.name = name
        self.use_nodes = False
        self.diffuse_color = (0.8, 0.8, 0.8, 1.0)
        self.node_tree = _NodeTree()


class MockConstraint:
    def __init__(self, ctype: str):
        self.type = ctype
        self.name = ctype
        self.target = None


class MockConstraintList(list):
    def new(self, type: str):
        c = MockConstraint(type)
        self.append(c)
        return c


class MockEditBone:
    def __init__(self, name: str):
        self.name = name
        self.head = (0.0, 0.0, 0.0)
        self.tail = (0.0, 0.0, 0.1)
        self.parent: Optional[MockEditBone] = None


class MockEditBones(dict):
    def new(self, name: str) -> MockEditBone:
        eb = MockEditBone(name)
        self[name] = eb
        return eb


class MockPoseBone:
    def __init__(self, name: str, owner_obj: "MockObject"):
        self.name = name
        self.rotation_mode = "XYZ"
        self.location = (0.0, 0.0, 0.0)
        self.rotation_euler = (0.0, 0.0, 0.0)
        self.constraints = MockConstraintList()
        self._owner = owner_obj

    def keyframe_insert(self, data_path: str, frame: int):
        key = f"pose.bones['{self.name}'].{data_path}"
        self._owner._keyframes.setdefault(key, []).append((frame, getattr(self, data_path, None)))


class MockPose:
    def __init__(self, bones_dict: Dict[str, MockPoseBone]):
        self.bones = bones_dict


class MockArmatureData:
    def __init__(self, name: str):
        self.name = name
        self.edit_bones = MockEditBones()
        self.bones: List[MockEditBone] = []


class MockMeshData:
    def __init__(self, name: str):
        self.name = name
        self.materials: List[MockMaterial] = []


class MockLightData:
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
        self.energy = 100.0


class MockCameraData:
    def __init__(self, name: str):
        self.name = name
        self.lens = 50.0


class MockObject:
    def __init__(self, name: str, data=None):
        self.name = name
        self.data = data
        self.location = (0.0, 0.0, 0.0)
        self.rotation_euler = (0.0, 0.0, 0.0)
        self.scale = (1.0, 1.0, 1.0)
        self.parent: Optional[MockObject] = None
        self.pose: Optional[MockPose] = None
        self._keyframes: Dict[str, list] = {}

    def keyframe_insert(self, data_path: str, frame: int):
        val = getattr(self, data_path, None)
        self._keyframes.setdefault(data_path, []).append((frame, val))


class _NamedCollection(list):
    def __init__(self, factory):
        super().__init__()
        self._factory = factory

    def new(self, *args, **kwargs):
        item = self._factory(*args, **kwargs)
        self.append(item)
        return item

    def get(self, name: str):
        for item in self:
            if getattr(item, "name", None) == name:
                return item
        return None


class _MockData:
    def __init__(self):
        self.reset()

    def reset(self):
        self.objects = _NamedCollection(lambda name, data=None, object_data=None: MockObject(name, data or object_data))
        self.materials = _NamedCollection(lambda name: MockMaterial(name))
        self.armatures = _NamedCollection(lambda name: MockArmatureData(name))
        self.lights = _NamedCollection(lambda name, type="AREA": MockLightData(name, type))
        self.cameras = _NamedCollection(lambda name: MockCameraData(name))


data = _MockData()


class _RenderSettings:
    def __init__(self):
        self.fps = 24
        self.resolution_x = 1080
        self.resolution_y = 1080
        self.filepath = "/tmp/frame_"


class _Scene:
    def __init__(self):
        self.render = _RenderSettings()
        self.frame_start = 1
        self.frame_end = 100
        self.camera: Optional[MockObject] = None


class _CollectionObjects:
    def link(self, obj: MockObject):
        if obj not in data.objects:
            data.objects.append(obj)


class _Collection:
    def __init__(self):
        self.objects = _CollectionObjects()


class _ViewLayerObjects:
    def __init__(self):
        self.active: Optional[MockObject] = None


class _ViewLayer:
    def __init__(self):
        self.objects = _ViewLayerObjects()


class _MockContext:
    def __init__(self):
        self.scene = _Scene()
        self.collection = _Collection()
        self.view_layer = _ViewLayer()
        self.object: Optional[MockObject] = None


context = _MockContext()


class _OpsMesh:
    @staticmethod
    def _spawn(prefix: str, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
        mesh_data = MockMeshData(f"{prefix}_Mesh")
        obj = MockObject(prefix, mesh_data)
        obj.location = tuple(location)
        obj.rotation_euler = tuple(rotation)
        data.objects.append(obj)
        context.object = obj
        context.view_layer.objects.active = obj
        return {"FINISHED"}

    @staticmethod
    def primitive_cylinder_add(radius=1.0, depth=2.0, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
        return _OpsMesh._spawn("Cylinder", location, rotation)

    @staticmethod
    def primitive_uv_sphere_add(radius=1.0, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
        return _OpsMesh._spawn("Sphere", location, rotation)

    @staticmethod
    def primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
        return _OpsMesh._spawn("Cube", location, rotation)


class _OpsObject:
    @staticmethod
    def select_all(action="SELECT"):
        return {"FINISHED"}

    @staticmethod
    def delete(use_global=False):
        data.objects.clear()
        return {"FINISHED"}

    @staticmethod
    def mode_set(mode="OBJECT"):
        act = context.view_layer.objects.active
        if mode == "OBJECT" and act and isinstance(act.data, MockArmatureData):
            act.data.bones = list(act.data.edit_bones.values())
            act.pose = MockPose({b.name: MockPoseBone(b.name, act) for b in act.data.bones})
        return {"FINISHED"}


class _OpsWM:
    @staticmethod
    def save_as_mainfile(filepath: str):
        return {"FINISHED"}


class _OpsExportScene:
    @staticmethod
    def gltf(filepath: str, export_format: str = "GLB"):
        return {"FINISHED"}


class _OpsRender:
    @staticmethod
    def render(animation: bool = False):
        return {"FINISHED"}


class _MockOps:
    mesh = _OpsMesh()
    object = _OpsObject()
    wm = _OpsWM()
    export_scene = _OpsExportScene()
    render = _OpsRender()


ops = _MockOps()
