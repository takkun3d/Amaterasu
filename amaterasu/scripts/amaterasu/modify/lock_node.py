# ==============================================================================
#
# Lock Node
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
__product__: str = 'Lock Node'
__version__: str = '1.01'
__doc__ = 'Lock or unlock the selected node.'
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
def lock(nodes: list[str] | None = None) -> None:
    '''Lock the selected nodes.'''
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error('Select node(s) to lock state.')
        return

    main(nodes, True)
    _logger.info('Done.')


def unlock(nodes: list[str] | None = None) -> None:
    '''Unlock the selected nodes.'''
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error('Select node(s) to unlock state.')
        return

    main(nodes, False)
    _logger.info('Done.')


def main(nodes: list[str] | None = None, is_lock: bool = True) -> None:
    '''Lock or unlock the selected node.'''
    if nodes:
        cmds.lockNode(*nodes, lock=is_lock)
