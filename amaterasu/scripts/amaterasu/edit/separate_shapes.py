# ==============================================================================
#
# Separate Shapes
#
# ==============================================================================
from __future__ import annotations
from typing import Any
from maya import cmds
from ..lib import logger


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Separate Shapes'
__version__: str = '1.00'
__doc__ = 'Separate Shapes from selection.'
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
def apply(source_nodes: list[str]) -> bool:
    '''Separate shapes.'''
    result: list[bool] = []
    for source_node in source_nodes:
        shapes: list[str] | None = cmds.listRelatives(
            source_node, shapes=True, path=True
        )
        if not shapes:
            _logger.warning('Does not exists shape : %s', source_node)
            result.append(False)
            continue

        if len(source_node) <= 1:
            _logger.warning('There is only one shape : %s', source_node)
            result.append(False)
            continue

        parent_nodes: list[str] | None = cmds.listRelatives(
            source_node, parent=True, shapes=False, path=True
        )
        parent_node: str = '|'
        if parent_nodes and len(parent_nodes) >= 1:
            parent_node = parent_nodes[0]

        for shape in shapes[1:]:
            transform: str = cmds.createNode(
                'transform', name=shape.replace('Shape', ''), parent=parent_node
            )
            matrix: Any = cmds.xform(
                source_node, query=True, matrix=True, worldSpace=True
            )
            cmds.xform(transform, matrix=matrix, worldSpace=True)
            cmds.parent(shape, transform, addObject=True, shape=True)
            cmds.parent(shape, removeObject=True, shape=True)

        result.append(True)

    return all(result)


def main() -> None:
    '''Do it.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select objects to separate shapes.')
        return

    result: bool = apply(selection)
    if result:
        _logger.info('Done.')
