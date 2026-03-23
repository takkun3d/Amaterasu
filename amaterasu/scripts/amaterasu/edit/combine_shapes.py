# ==============================================================================
#
# Combine Shapes
#
# ==============================================================================
from __future__ import annotations
from maya import cmds
from ..lib import logger


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Combine Shapes'
__version__: str = '1.00'
__doc__ = 'Combine Shapes from selected node.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


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
def apply(parent_node: str, source_nodes: list[str]) -> bool:
    '''Combine shape.'''
    result: list[bool] = []
    for source_node in source_nodes:
        shapes: list[str] | None = cmds.listRelatives(
            source_node, shapes=True, path=True
        )
        if not shapes:
            _logger.warning('Does not exists shape : %s', source_node)
            result.append(False)
            continue

        for shape in shapes:
            cmds.parent(shape, parent_node, addObject=True, shape=True)

        cmds.parent(source_node, removeObject=True)
        result.append(True)

    return all(result)


def main() -> None:
    '''Dot it.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select objects to combine shape.')
        return

    if len(selection) < 2:
        _logger.error('Select least 2 objects to combine shape.')

    result: bool = apply(selection[-1], selection[0:-1])
    if result:
        _logger.info('Done.')
