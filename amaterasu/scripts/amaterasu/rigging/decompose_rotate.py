# ==============================================================================
#
# Decompose Rotate
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from ..display import drawing_color
from ..modify import history_visibility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Decompose Rotate'
__version__: str = '1.10'
__doc__ = 'Decomposes the rotation of selected objects into separate X, Y, Z Euler angles.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

OP_CROSS_PRODUCT: int = 2
OP_GREATER_THAN: int = 2
OP_LESS_THAN: int = 4


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Plane:
    XY: int = 0
    YZ: int = 1
    XZ: int = 2
    name: tuple[str, str, str] = ('XY', 'YZ', 'XZ')
    vector: list[tuple[float, float, float]] = [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    ]
    axis: list[tuple[float, float, float]] = [
        (1, 1, 0),
        (0, 1, 1),
        (1, 0, 1),
    ]
    axis_attr: tuple[str, str, str] = ('Z', 'X', 'Y')
    index_color: tuple[float, float, float] = (13, 14, 6)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def create_plane_control(
    base_name: str, plane: int, src_transform: str, parent: str = ''
) -> str:
    '''Creates a rig control for a specific rotation plane (XY, YZ, or XZ).'''
    plane_name: str = Plane.name[plane]
    vector: tuple[float, float, float] = Plane.vector[plane]
    axis: tuple[float, float, float] = Plane.axis[plane]
    axis_attr: str = Plane.axis_attr[plane]
    index_color: float = Plane.index_color[plane]

    # Rotate Vector ------------------------------------------------------------
    rotate_vector: str = cmds.createNode(
        'rotateVector', name=f'{base_name}Vector{plane_name}_rv'
    )
    cmds.setAttr(f'{rotate_vector}.input', *vector, type='double3')
    cmds.connectAttr(f'{src_transform}.rotate', f'{rotate_vector}.rotate')
    cmds.connectAttr(
        f'{src_transform}.rotateOrder', f'{rotate_vector}.rotateOrder'
    )

    # Axis Filter --------------------------------------------------------------
    axis_filter: str = cmds.createNode(
        'multiplyDivide', name=f'{base_name}AxisFilter{plane_name}_md'
    )
    cmds.setAttr(f'{axis_filter}.input2', *axis, type='double3')
    cmds.connectAttr(f'{rotate_vector}.output', f'{axis_filter}.input1')

    # Angle --------------------------------------------------------------------
    angle: str = cmds.createNode(
        'angleBetween', name=f'{base_name}Angle{plane_name}_ab'
    )
    cmds.setAttr(f'{angle}.vector1', *vector, type='double3')
    cmds.connectAttr(f'{axis_filter}.output', f'{angle}.vector2')

    # Cross Product ------------------------------------------------------------
    cross: str = cmds.createNode(
        'vectorProduct', name=f'{base_name}Cross{plane_name}_vp'
    )
    cmds.setAttr(f'{cross}.operation', OP_CROSS_PRODUCT)
    cmds.setAttr(f'{cross}.input1', *vector, type='double3')
    cmds.connectAttr(f'{axis_filter}.output', f'{cross}.input2')

    # Direction ----------------------------------------------------------------
    direction: str = cmds.createNode(
        'condition', name=f'{base_name}Direction{plane_name}_condition'
    )
    cmds.setAttr(f'{direction}.operation', OP_GREATER_THAN)
    cmds.setAttr(f'{direction}.colorIfTrue', 1, 0, 0, type='double3')
    cmds.setAttr(f'{direction}.colorIfFalse', -1, 0, 0, type='double3')
    cmds.connectAttr(f'{cross}.output{axis_attr}', f'{direction}.firstTerm')

    # Filtering 0 --------------------------------------------------------------
    filtering_0: str = cmds.createNode(
        'condition', name=f'{base_name}Filtering0{plane_name}_condition'
    )
    cmds.setAttr(f'{filtering_0}.operation', OP_LESS_THAN)
    cmds.setAttr(f'{filtering_0}.secondTerm', 0.001)
    cmds.setAttr(f'{filtering_0}.colorIfTrue', 1, 0, 0, type='double3')
    cmds.setAttr(f'{filtering_0}.colorIfFalse', -1, 0, 0, type='double3')
    cmds.connectAttr(f'{angle}.angle', f'{filtering_0}.firstTerm')
    cmds.connectAttr(f'{direction}.outColorR', f'{filtering_0}.colorIfFalseR')

    # Filtering 180 ------------------------------------------------------------
    filtering_180: str = cmds.createNode(
        'condition', name=f'{base_name}Filtering180{plane_name}_condition'
    )
    cmds.setAttr(f'{filtering_180}.operation', OP_GREATER_THAN)
    cmds.setAttr(f'{filtering_180}.secondTerm', 179.999)
    cmds.setAttr(f'{filtering_180}.colorIfTrue', 1, 0, 0, type='double3')
    cmds.setAttr(f'{filtering_180}.colorIfFalse', -1, 0, 0, type='double3')
    cmds.connectAttr(f'{angle}.angle', f'{filtering_180}.firstTerm')
    cmds.connectAttr(
        f'{filtering_0}.outColorR', f'{filtering_180}.colorIfFalseR'
    )

    # Rotate -------------------------------------------------------------------
    rotate: str = cmds.createNode(
        'multiplyDivide', name=f'{base_name}Rotate{plane_name}_md'
    )
    cmds.connectAttr(f'{filtering_180}.outColorR', f'{rotate}.input1X')
    cmds.connectAttr(f'{angle}.angle', f'{rotate}.input2X')

    # Locator ------------------------------------------------------------------
    locator: str = cmds.spaceLocator(name=f'{base_name}{plane_name}_loc')[0]
    if parent:
        locator = cmds.parent(locator, parent)[0]
        cmds.setAttr(f'{locator}.translate', 0, 0, 0, type='double3')
        cmds.setAttr(f'{locator}.rotate', 0, 0, 0, type='double3')
        cmds.setAttr(f'{locator}.scale', 1, 1, 1, type='double3')

    shape_size: list[float] = [i * 5 for i in vector]
    cmds.setAttr(f'{locator}.localPosition', *shape_size, type='double3')
    cmds.setAttr(f'{locator}.localScale', *shape_size, type='double3')
    cmds.connectAttr(f'{rotate}.outputX', f'{locator}.rotate{axis_attr}')
    drawing_color.apply(0, index_color, None, True, [locator])
    history_visibility.main([locator], 0)

    return locator


def create_offset_control(base_name: str, src_transform: str) -> str:
    '''Creates an offset group.'''

    # Create a matrix without rotation -----------------------------------------
    offset_cmtx: str = cmds.createNode(
        'composeMatrix', name=f'{base_name}Offset_composeMtx'
    )
    cmds.connectAttr(
        f'{src_transform}.translate', f'{offset_cmtx}.inputTranslate'
    )
    cmds.connectAttr(f'{src_transform}.scale', f'{offset_cmtx}.inputScale')
    cmds.connectAttr(
        f'{src_transform}.rotateOrder', f'{offset_cmtx}.inputRotateOrder'
    )

    # Create a matrix with joint orient ----------------------------------------
    orient_cmtx: str = ''
    if cmds.objectType(src_transform) == 'joint':
        orient_cmtx = cmds.createNode(
            'composeMatrix', name=f'{base_name}Orient_composeMtx'
        )
        cmds.connectAttr(
            f'{src_transform}.jointOrient', f'{orient_cmtx}.inputRotate'
        )
        cmds.connectAttr(
            f'{src_transform}.rotateOrder', f'{orient_cmtx}.inputRotateOrder'
        )

    # Multiply matrices --------------------------------------------------------
    offset_mmtx: str = cmds.createNode(
        'multMatrix', name=f'{base_name}Offset_multMtx'
    )
    matrix_index: int = 0
    if orient_cmtx:
        cmds.connectAttr(
            f'{orient_cmtx}.outputMatrix',
            f'{offset_mmtx}.matrixIn[{matrix_index}]',
        )
        matrix_index += 1

    cmds.connectAttr(
        f'{offset_cmtx}.outputMatrix', f'{offset_mmtx}.matrixIn[{matrix_index}]'
    )

    # Decompose ----------------------------------------------------------------
    offset_dmtx: str = cmds.createNode(
        'decomposeMatrix', name=f'{base_name}Offset_decomposeMtx'
    )
    cmds.connectAttr(f'{offset_mmtx}.matrixSum', f'{offset_dmtx}.inputMatrix')

    # Offset Transform ---------------------------------------------------------
    parents: list[str] = (
        cmds.listRelatives(src_transform, parent=True, path=True) or []
    )
    parent: str = parents[0] if parents else '|'

    offset_transform: str = cmds.createNode(
        'transform', name=f'{base_name}Plane_offset', parent=parent
    )
    cmds.connectAttr(
        f'{offset_dmtx}.outputTranslate', f'{offset_transform}.translate'
    )
    cmds.connectAttr(
        f'{offset_dmtx}.outputRotate', f'{offset_transform}.rotate'
    )
    cmds.connectAttr(f'{offset_dmtx}.outputScale', f'{offset_transform}.scale')
    cmds.connectAttr(f'{offset_dmtx}.outputShear', f'{offset_transform}.shear')
    history_visibility.main([offset_transform], 0)

    return offset_transform


def main(nodes: list[str] | None = None) -> None:
    '''Runs the main process on the currently selected nodes.'''
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error('Select a Transform or Joint to decompose the rotation.')
        return

    for node in nodes:
        base_name: str = node.split('|')[-1]
        base_name = base_name.split('_')[0]

        offset_transform: str = create_offset_control(base_name, node)
        create_plane_control(base_name, Plane.XY, node, offset_transform)
        create_plane_control(base_name, Plane.YZ, node, offset_transform)
        create_plane_control(base_name, Plane.XZ, node, offset_transform)

    _logger.info('Done.')
