# ==============================================================================
#
# Insert Space
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
__product__: str = 'Insert Space'
__version__: str = '1.00'
__doc__ = 'Inserts a zero-out offset group above the selected transforms.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def insert_node(node: str) -> str:
    '''Inserts a space null node for the specified transform.'''

    parents: list[str] = (
        cmds.listRelatives(node, parent=True, fullPath=True) or []
    )
    parent_node: str = parents[0] if parents else ''
    base_name: str = node.split('|')[-1]
    base_name = base_name.split('_')[0]

    new_node: str = cmds.group(empty=True, name=f'{base_name}Space_null')
    cmds.matchTransform(
        new_node, node, position=True, rotation=True, scale=True, pivots=True
    )
    if parent_node:
        new_node = cmds.parent(new_node, parent_node)[0]

    node = cmds.parent(node, new_node)[0]
    for attr in ['translate', 'rotate']:
        cmds.setAttr(f'{node}.{attr}', 0, 0, 0, type='double3')
    cmds.setAttr(f'{node}.scale', 1, 1, 1, type='double3')

    return new_node


def main() -> None:
    '''Runs the main process on the currently selected nodes.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select transform(s) to insert space.')
        return

    for node in selection:
        insert_node(node)

    _logger.info('Done.')
