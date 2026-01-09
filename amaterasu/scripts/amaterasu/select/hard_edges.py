# ==============================================================================
#
# Select Hard Edges
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds, mel
from ..lib import utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Hard Edges'
__version__: str = '1.00'
__doc__ = 'Select hard edges.'
__copyright__ = 'Copyright(c) 2020-2024 @takkun3d. All Rights Reserved.'
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
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygon/edges to convert selection.')
        return

    mel.eval('SelectEdgeMask')
    edges: list[str] = utility.to_edge(selection)
    cmds.select(*edges)
    cmds.polySelectConstraint(mode=3, type=0x8000, smoothness=1, where=2)
    cmds.polySelectConstraint(mode=0)
    _logger.info('Done.')
