# ==============================================================================
#
# Replace Shapes
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Replace Shapes'
__version__: str = '1.00'
__doc__ = 'Replace Shapes from selected nodes.'
__copyright__ = 'Copyright(c) 20xx @takkun3d. All Rights Reserved.'
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
def apply(source_node: str, destination_nodes: list[str]) -> bool:
    '''Replace shapes.'''
    source_shapes: list[str] = (
        cmds.listRelatives(source_node, shapes=True, path=True) or []
    )
    if not source_shapes:
        _logger.error('Does not exists shapes : %s', source_node)
        return False

    for destination_node in destination_nodes:
        source_dummy: str = cmds.duplicate(source_node, returnRootsOnly=True)[0]
        source_shapes = cmds.listRelatives(source_dummy, shapes=True, path=True)
        old_shapes: list[str] = (
            cmds.listRelatives(destination_node, shapes=True, path=True) or []
        )

        for shape in source_shapes:
            cmds.parent(shape, destination_node, addObject=True, shape=True)

        cmds.parent(source_dummy, removeObject=True)
        if old_shapes:
            cmds.delete(*old_shapes)

    return True


def main() -> None:
    '''Dot it.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select objects to replace shape.')
        return

    if len(selection) < 2:
        _logger.error('Select least 2 objects to replace shape.')

    result: bool = apply(selection[-1], selection[:-1])
    if result:
        _logger.info('Done.')
