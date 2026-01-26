# ==============================================================================
#
# Utlity
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# ==============================================================================
from __future__ import annotations
from typing import Any
import math
import re
import os
import platform
import subprocess
import getpass
from maya import cmds


# ==============================================================================
#
# Variables
#
# ==============================================================================
__doc__ = 'Ulitity for supporting maya.cmds and math.'

ANIM_CURVE_TYPES: tuple[str, str, str, str] = (
    'animCurveTA',
    'animCurveTL',
    'animCurveTT',
    'animCurveTU',
)

# ==============================================================================
#
# Classes
#
# ==============================================================================


# ==============================================================================
#
# Functions
#
# ==============================================================================


# ==============================================================================
# IO
# ==============================================================================
def open_directory(path: str) -> int:
    '''Open directory'''
    if not os.path.exists(path):
        return -1

    os_name: str = platform.system()
    if os_name != 'Windows':
        return -2

    path = path.replace('/', '\\')
    with subprocess.Popen(f'explorer "{path}"'):
        pass

    return 1


def user_name() -> str:
    '''Return current user name.'''
    try:
        return cmds.button('AdlSdkFixedCtrl', query=True, label=True)
    except RuntimeError:
        return getpass.getuser()


# ==============================================================================
# python
# ==============================================================================
def str_to_bool(value: str) -> bool:
    '''Return bool value from str value.'''
    if value in ('False', 'false', '0', 'no', 'off'):
        return False

    if value[0] == '-':
        return False

    return True


# ==============================================================================
# math
# ==============================================================================
class Vector:
    '''Vector'''

    def __init__(self, value: list[float]) -> None:
        '''Initialize.'''
        self.__x = value[0]
        self.__y = value[1]
        self.__z = value[2]

    def x(self) -> float:
        '''Return x value.'''
        return self.__x

    def y(self) -> float:
        '''Return y value.'''
        return self.__y

    def z(self) -> float:
        '''Return z value.'''
        return self.__z

    def set_x(self, value: float) -> None:
        '''Set x value.'''
        self.__x = value

    def set_y(self, value: float) -> None:
        '''Set y value.'''
        self.__y = value

    def set_z(self, value: float) -> None:
        '''Set z value.'''
        self.__z = value

    def vector(self, vec: Vector) -> Vector:
        '''Vector'''
        return Vector(
            [self.x() - vec.x(), self.y() - vec.y(), self.z() - vec.z()]
        )

    def length(self, vec: Vector) -> float:
        '''Vector length.'''
        return math.pow(
            (
                ((self.x() - vec.x()) * (self.x() - vec.x()))
                + ((self.y() - vec.y()) * (self.y() - vec.y()))
                + ((self.z() - vec.z()) * (self.z() - vec.z()))
            ),
            0.5,
        )

    def as_float3(self) -> list[float]:
        '''Return float list.'''
        return [self.x(), self.y(), self.z()]

    def __add__(self, vec: Vector) -> Vector:
        '''Vector + Vector'''
        return Vector(
            [self.x() + vec.x(), self.y() + vec.y(), self.z() + vec.z()]
        )

    def __sub__(self, vec: Vector) -> Vector:
        '''Vector - Vector'''
        return Vector(
            [self.x() - vec.x(), self.y() - vec.y(), self.z() - vec.z()]
        )

    def __mul__(self, value: Vector | int | float) -> Vector:
        '''Vector * Vector'''
        if isinstance(value, (int, float)):
            return Vector(
                [self.x() * value, self.y() * value, self.z() * value]
            )
        elif isinstance(value, Vector):
            return Vector(
                [self.x() * self.x(), self.y() * self.y(), self.z() * self.z()]
            )
        else:
            raise ValueError()

    def __div__(self, value: Vector | int | float) -> Vector:
        '''Vector / Vector'''
        if isinstance(value, (int, float)):
            return Vector(
                [self.x() / value, self.y() / value, self.z() / value]
            )
        elif isinstance(value, Vector):
            return Vector(
                [self.x() / self.x(), self.y() / self.y(), self.z() / self.z()]
            )
        else:
            raise ValueError()

    def __str__(self) -> str:
        '''return str from Vector to str.'''
        return f'{self.x()}, {self.y()}, {self.z()}'


def cross_product(a: list[float], b: list[float]) -> list[float]:
    '''Vector cross product'''
    result: list[float] = [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
    return result


def dot_product(a: list[float], b: list[float]) -> float:
    '''Vector dot profuct'''
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vector_length(v: list[float]) -> float:
    '''Return vector length'''
    return math.pow((v[0] * v[0]) + (v[1] * v[1]) + (v[2] * v[2]), 0.5)


def distance(p1: list[float], p2: list[float]) -> float:
    '''Return distance from p1 to p2.'''
    return math.sqrt(
        math.pow((p2[0] - p1[0]), 2)
        + math.pow((p2[1] - p1[1]), 2)
        + math.pow((p2[2] - p1[2]), 2)
    )


def distance_each_axis(p1: list[float], p2: list[float]) -> list[float]:
    '''Return distance each axis from p1 to p2.'''
    x: float = math.sqrt(math.pow((p2[0] - p1[0]), 2))
    y: float = math.sqrt(math.pow((p2[1] - p1[1]), 2))
    z: float = math.sqrt(math.pow((p2[2] - p1[2]), 2))
    return [x, y, z]


def angle(a: list[float], b: list[float]) -> float:
    '''Return angle from a and b.'''
    length_a: float = vector_length(a)
    length_b: float = vector_length(b)
    cos_sita: float = dot_product(a, b) / (length_a * length_b)
    sita: float = math.acos(cos_sita)  # * 180 / math.pi
    return sita


def rotate_normal_x(normal: list[float], rotate_x: float) -> list[float]:
    '''Rotate normal to x.'''
    rx: float = math.radians(rotate_x)
    normal = [
        normal[0],
        normal[1] * math.cos(rx) - normal[2] * math.sin(rx),
        normal[1] * math.sin(rx) + normal[2] * math.cos(rx),
    ]
    return normal


def rotate_normal_y(normal: list[float], rotate_y: float) -> list[float]:
    '''Rotate normal to y.'''
    ry: float = math.radians(rotate_y)
    normal = [
        normal[2] * math.sin(ry) + normal[0] * math.cos(ry),
        normal[1],
        normal[2] * math.cos(ry) - normal[0] * math.sin(ry),
    ]
    return normal


def rotate_normal_z(normal: list[float], rotate_z: float) -> list[float]:
    '''Rotate normal to z.'''
    rz: float = math.radians(rotate_z)
    normal = [
        normal[0] * math.cos(rz) - normal[1] * math.sin(rz),
        normal[0] * math.sin(rz) + normal[1] * math.cos(rz),
        normal[2],
    ]
    return normal


def rotate_normal(normal: list[float], rotate: list[float]) -> list[float]:
    '''Rotate normal.'''
    normal = rotate_normal_x(normal, rotate[0])
    normal = rotate_normal_y(normal, rotate[1])
    normal = rotate_normal_z(normal, rotate[2])
    return normal


# ==============================================================================
# maya.cmds
# ==============================================================================
def get_edge_type(edge: str) -> str:
    '''Return string of edge type.'''
    return cmds.polyInfo(edge, edgeToVertex=True)[0][-5:-1]


def is_hard_edge(edge: str) -> bool:
    '''Returns whether it is a hard edge.'''
    return get_edge_type(edge) == 'Hard'


def is_soft_edge(edge: str) -> bool:
    '''Returns whether it is a soft edge.'''
    return get_edge_type(edge) != 'Hard'


def face_normals(face: str) -> list[float]:
    '''Return face normals.'''
    temp: list[str] = cmds.polyInfo(face, faceNormals=True)[0].split(' ')
    return [float(temp[-3]), float(temp[-2]), float(temp[-1])]


def component_id(component: str) -> list[str]:
    '''Return component ids from string of dag path.'''
    ids: list[str] = re.findall('\\[[0-9]+\\]', component)
    for i, _ in enumerate(ids):
        ids[i] = ids[i].replace('[', '').replace(']', '')

    return ids


def to_each_geometry(components: list[str]) -> dict[str, list[str]]:
    '''Return dict of each geometry.'''
    result: dict[str, list[str]] = {}
    components = to_flatten(components)
    for component in components:
        temp: list[str] = component.split('.')
        if (temp[0] in result) is False:
            result[temp[0]] = []

        result[temp[0]].append(component)
    return result


def to_flatten(components: list[str] | str) -> list[str]:
    '''Return flattens list of objects.'''
    if isinstance(components, str):
        components = [components]
    return cmds.ls(*components, flatten=True)


def to_vertex(components: list[str] | str) -> list[str]:
    '''Convert to list of vertex.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromFace=True,
        fromEdge=True,
        fromUV=True,
        fromVertexFace=True,
        toVertex=True,
    )
    return to_flatten(components)


def to_vertex_face(components: list[str] | str) -> list[str]:
    '''Convert to list of vertex face.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromEdge=True,
        fromFace=True,
        fromUV=True,
        toVertexFace=True,
    )
    return to_flatten(components)


def to_edge(components: list[str] | str) -> list[str]:
    '''Convert to list of edge.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromFace=True,
        fromUV=True,
        fromVertexFace=True,
        toEdge=True,
    )
    return to_flatten(components)


def to_contained_edge(components: list[str] | str) -> list[str]:
    '''Convert to list of contained edge.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromFace=True,
        fromUV=True,
        fromVertexFace=True,
        toEdge=True,
        internal=True,
    )
    return to_flatten(components)


def to_border_edge(components: list[str] | str) -> list[str]:
    '''Convert to list of border edge.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        border=True,
        fromVertex=True,
        fromFace=True,
        fromUV=True,
        fromVertexFace=True,
        toEdge=True,
    )
    return to_flatten(components)


def to_face(components: list[str] | str) -> list[str]:
    '''Convert to list of face.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromEdge=True,
        fromUV=True,
        fromVertexFace=True,
        toFace=True,
    )
    return to_flatten(components)


def to_uv(components: list[str] | str) -> list[str]:
    '''Convert to list of uv.'''
    if isinstance(components, str):
        components = [components]
    components = cmds.polyListComponentConversion(
        *components,
        fromVertex=True,
        fromEdge=True,
        fromFace=True,
        fromVertexFace=True,
        fromUV=True,
        toUV=True,
    )
    return to_flatten(components)


def to_uv_shell(components: list[str] | str) -> list[str]:
    '''Convert to list of uv shell.'''
    if isinstance(components, str):
        components = [components]

    cmds.select(*to_uv(components))
    cmds.polySelectConstraint(mode=2, shell=True)
    cmds.polySelectConstraint(border=False, mode=0, shell=False)
    uvs = cmds.ls(selection=True, flatten=True)
    cmds.select(*components)
    return uvs


def to_border_uv(components: list[str] | str) -> list[str]:
    '''Convert to list of border uv.'''
    if isinstance(components, str):
        components = [components]

    cmds.select(*to_uv(components))
    cmds.polySelectConstraint(type=0)
    cmds.polySelectConstraint(shell=True, border=False, mode=2)
    cmds.polySelectConstraint(type=0x0010, shell=False, border=True, mode=2)
    cmds.polySelectConstraint(type=0x0010, shell=True, border=False, mode=0)
    cmds.polySelectConstraint(shell=False, border=False, mode=0)  # Reset
    uvs = cmds.ls(selection=True)
    cmds.select(*components)
    return uvs


# def to_uv_shell_list(transformNode: list[str]) -> list[list[str]]:
#     '''
#     Reference
#     https://groups.google.com/forum/#!topic/python_inside_maya/W4NXutgFl60
#     '''
#     shape  = cmds.listRelatives(transformNode, s=True, pa=True)[0]
#     mObject = OpenMaya.MObject()
#     selectionList = OpenMaya.MSelectionList()
#     selectionList.add(shape)
#     selectionList.getDependNode(0, mObject)

#     meshFn = OpenMaya.MFnMesh(mObject)

#     scriptUtil = OpenMaya.MScriptUtil()
#     numUvShellsPtr = scriptUtil.asUintPtr()
#     uvShellIDs = OpenMaya.MIntArray()

#     meshFn.getUvShellsIds(uvShellIDs, numUvShellsPtr)

#     numUvShells = OpenMaya.MScriptUtil(numUvShellsPtr).asUint()
#     shells = [[]] * numUvShells
#     for i in range(uvShellIDs.length()):
#         shells[uvShellIDs[i]].append(f'{transformNode}.map[{i}]')

#     return shells


def poly_component_id(path: str) -> list[str] | str:
    '''Return component id from dag path.'''
    if re.search('\.vtxFace', path):
        buffer: list[str] = path.split('.vtxFace')[-1].split('][')
        id1 = re.search('([0-9]+)', buffer[0]).group(0)
        id2 = re.search('([0-9]+)', buffer[1]).group(0)
        return [id1, id2]

    elif re.search('\.uv', path):
        buffer = path.split('.uv')[-1].split('][')
        id1 = re.sub('\[', '', buffer[0])
        id2 = re.sub('\]', '', buffer[1])
        return [id1, id2]

    elif re.search('\.u', path):
        buffer = path.split('.u')[-1].split(']')
        id: str = re.sub('\[', '', buffer[0])
        return id

    elif re.search('\.vtx', path):
        buffer = path.split('.vtx')[-1].split(']')
        id = re.sub('\[', '', buffer[0])
        return id

    elif re.search('\.v', path):
        buffer = path.split('.v')[-1].split(']')
        id = re.sub('\[', '', buffer[0])
        return id

    id = re.search('([0-9]+)', path.split('.')[-1]).group(0)
    return id


def is_static_value(
    node: str, attr: str, check_value: bool, value: Any
) -> bool:
    '''is static value'''
    default: Any = get_default_value(node, attr)

    current: Any = value
    if not check_value:
        current = cmds.getAttr(f'{node}.{attr}')

    if isinstance(current, list) and len(current) == 1:
        current = current[0]

    result: bool = default == current
    return result


def get_default_value(node: str, attr: str) -> Any:
    '''Return default value'''
    default: Any = cmds.attributeQuery(attr, node=node, listDefault=True)
    if isinstance(default, list) and len(default) == 1:
        default = default[0]

    return default


def extract_namespace(node: str) -> str:
    '''return namespace from node name.'''
    namespace: str = ''
    temp: list[str] = node.split(':')
    if len(temp) != 1:
        namespace = ':'.join(temp[:-1]) + ':'
    return namespace


def extract_namespaces(nodes: list[str]) -> list[str]:
    '''return namespace list from nodes.'''
    result: list[str] = list(set([extract_namespace(n) for n in nodes]))
    if result == ['']:
        return []

    return result


def list_to_per_namespace(nodes: list[str]) -> dict[str, list[str]]:
    '''return node list per namespace.'''
    result: dict[str, list[str]] = {}
    for node in nodes:
        namespace: str = extract_namespace(node)
        if namespace not in result:
            result[namespace] = []
        result[namespace].append(node)

    return result


def has_animation(node: str, attr: str = '') -> bool:
    '''return has animation.'''
    plug: str = node
    if attr:
        plug += '.' + attr

    return bool(cmds.keyframe(plug, query=True, keyframeCount=True))


def get_fps() -> int:
    '''Return fps.'''
    unit = cmds.currentUnit(query=True, time=True)
    fps = 0

    if unit == 'game':
        fps = 15

    elif unit == 'film':
        fps = 24

    elif unit == 'pal':
        fps = 25

    elif unit == 'ntsc':
        fps = 30

    elif unit == 'show':
        fps = 48

    elif unit == 'palf':
        fps = 50

    elif unit == 'ntscf':
        fps = 60

    elif unit == '2fps':
        fps = 2

    elif unit == '3fps':
        fps = 3

    elif unit == '4fps':
        fps = 4

    elif unit == '5fps':
        fps = 5

    elif unit == '6fps':
        fps = 6

    elif unit == '8fps':
        fps = 8

    elif unit == '10fps':
        fps = 10

    elif unit == '12fps':
        fps = 12

    elif unit == '16fps':
        fps = 16

    elif unit == '20fps':
        fps = 20

    elif unit == '40fps':
        fps = 40

    elif unit == '75fps':
        fps = 75

    elif unit == '80fps':
        fps = 80

    elif unit == '100fps':
        fps = 100

    elif unit == '120fps':
        fps = 120

    elif unit == '125fps':
        fps = 125

    elif unit == '150fps':
        fps = 150

    elif unit == '200fps':
        fps = 200

    elif unit == '240fps':
        fps = 240

    elif unit == '250fps':
        fps = 250

    elif unit == '300fps':
        fps = 300

    elif unit == '375fps':
        fps = 375

    elif unit == '400fps':
        fps = 400

    elif unit == '500fps':
        fps = 500

    elif unit == '600fps':
        fps = 600

    elif unit == '750fps':
        fps = 750

    elif unit == '1200fps':
        fps = 1200

    elif unit == '1500fps':
        fps = 1500

    elif unit == '3000fps':
        fps = 3000

    elif unit == '6000fps':
        fps = 6000

    return fps


def set_fps(value: int) -> None:
    '''Set fps'''
    if value == 15:
        unit = 'game'

    elif value == 24:
        unit = 'film'

    elif value == 25:
        unit = 'pal'

    elif value == 30:
        unit = 'ntsc'

    elif value == 48:
        unit = 'show'

    elif value == 50:
        unit = 'palf'

    elif value == 60:
        unit = 'ntscf'

    else:
        unit = f'{value}fps'

    cmds.currentUnit(time=unit)


def get_anim_curves(node: str) -> list[str]:
    '''Return anim curve list from node.'''
    result: list[str] = []
    connections: list[str] = (
        cmds.listConnections(node, source=True, destination=False) or []
    )
    if not connections:
        return []

    for connection in connections:
        node_type: str = cmds.nodeType(connection)
        if node_type in [
            'animCurveTL',
            'animCurveTA',
            'animCurveTU',
            'animCurveTT',
        ]:
            result.append(connection)

    return result


def get_anim_curve(node: str, attr: str) -> str:
    '''Return anim curve from plug.'''
    connections: list[str] = (
        cmds.listConnections(f'{node}.{attr}', source=True, destination=False)
        or []
    )
    if not connections:
        return ''

    node_type: str = cmds.nodeType(connections[0])
    if node_type in [
        'animCurveTL',
        'animCurveTA',
        'animCurveTU',
        'animCurveTT',
    ]:
        return connections[0]

    return ''


def unused_influences(skin_cluster: str) -> list[str]:
    infls: list[str] = cmds.skinCluster(
        skin_cluster, query=True, influence=True
    )
    wtinfs: list[str] = cmds.skinCluster(
        skin_cluster, query=True, weightedInfluence=True
    )

    unused_infls: list[str] = []
    for infl in infls:
        if infl not in wtinfs:
            unused_infls.append(infl)

    return unused_infls


def find_related_skin_cluster(skin_object: str) -> str:
    '''Find skin cluster.'''
    skin_shape = None
    skin_shape_with_path = None
    hidden_shape = None
    hidden_shape_with_path = None

    cp_test = cmds.ls(skin_object, typ='controlPoint')
    if len(cp_test):
        skin_shape = cp_test[0]

    else:
        rels = cmds.listRelatives(skin_object)
        for r in rels:
            cp_test = cmds.ls(f'{skin_object}|{r}', type='controlPoint')
            if len(cp_test) == 0:
                continue

            io = cmds.getAttr(f'{skin_object}|{r}.io')
            if io:
                continue

            visible = cmds.getAttr(f'{skin_object}|{r}.v')
            if not visible:
                hidden_shape = r
                hidden_shape_with_path = f'{skin_object}|{r}'
                continue

            skin_shape = r
            skin_shape_with_path = f'{skin_object}|{r}'
            break

    if len(skin_shape) == 0:
        if len(hidden_shape) == 0:
            return ''

        else:
            skin_shape = hidden_shape
            skin_shape_with_path = hidden_shape_with_path

    clusters = cmds.ls(type='skinCluster')
    for c in clusters:
        geom: list[str] = cmds.skinCluster(c, query=True, geometry=True)
        for g in geom:
            if g == skin_shape or g == skin_shape_with_path:
                return c

    return ''


def is_surface_shader(node: str) -> bool:
    '''Return is surface shader'''
    node_type: str = cmds.nodeType(node)
    return cmds.getClassification(node_type, satisfies='shader/surface')


def surface_shader(node: str) -> list[str]:
    '''Return surface shaders from specificed node.'''
    all_nodes: list[str] = cmds.listHistory(node, future=True)
    shading_group: list[str] = cmds.ls(*all_nodes, type='shadingEngine')
    return shading_group
