# ==============================================================================
#
# Remove Node Editor Info
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
__product__: str = 'Remove Node Editor Info'
__version__: str = '1.00'
__doc__ = 'Remove Node Editor Info from an open scene.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
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
def main() -> None:
    '''Do it.'''
    nodes: list[str] = cmds.ls(type='nodeGraphEditorInfo')
    for node in nodes:
        # dst, src, dst, src ...
        connections: list[str] = (
            cmds.listConnections(node, connections=True, plugs=True) or []
        )
        for dst_plug, src_plug in zip(connections[::2], connections[1::2]):
            cmds.disconnectAttr(src_plug, dst_plug)

        cmds.delete(node)

    _logger.info('Done.')
