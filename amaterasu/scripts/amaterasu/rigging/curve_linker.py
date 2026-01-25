# ==============================================================================
#
# Curve Linker
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from ..modify import history_visibility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Curve Linker'
__version__: str = '1.00'
__doc__ = 'Create a CV curve that follows a controller.'
__copyright__ = 'Copyright(c) 2026 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


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
def apply(nodes: list[str]) -> str:
    '''Create a CV curve that follows a controller.'''

    def base_name(node_name: str) -> str:
        '''Return base name.'''
        name: str = node_name.split('|')[-1]
        name = name.split('_')[0]
        return name

    start_name: str = base_name(nodes[0])
    end_name: str = base_name(nodes[-1])

    point_num: int = len(nodes)
    points: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * point_num
    knot: list[float] = [x for x in range(point_num)]
    curve: str = cmds.curve(
        degree=1,
        point=points,
        knot=knot,
        name=f'{start_name}To{end_name.title()}_crv',
    )
    temp_shape: str = cmds.listRelatives(curve, shapes=True, path=True)[0]
    curve_shape: str = curve.split('|')[-1]
    curve_shape = cmds.rename(temp_shape, f'{curve_shape}Shape')

    for i, node in enumerate(nodes):
        node_name: str = base_name(node)

        mult_mtx: str = cmds.createNode(
            'multMatrix', name=f'{node_name}_multMtx'
        )
        cmds.connectAttr(f'{node}.worldMatrix[0]', f'{mult_mtx}.matrixIn[0]')
        cmds.connectAttr(
            f'{curve}.worldInverseMatrix[0]', f'{mult_mtx}.matrixIn[1]'
        )

        decompose_mtx: str = cmds.createNode(
            'decomposeMatrix', name=f'{node_name}_decomposeMtx'
        )
        cmds.connectAttr(
            f'{mult_mtx}.matrixSum', f'{decompose_mtx}.inputMatrix'
        )
        cmds.connectAttr(
            f'{decompose_mtx}.outputTranslate',
            f'{curve_shape}.controlPoints[{i}]',
        )

    history_visibility.main([curve, curve_shape], False)
    return curve


def main() -> None:
    '''Do it'''
    selection: list[str] = cmds.ls(selection=True, transforms=True)
    if not selection or len(selection) < 2:
        _logger.error('Select two or more transforms to create a curve.')
        return

    apply(selection)
    _logger.info('Done.')
