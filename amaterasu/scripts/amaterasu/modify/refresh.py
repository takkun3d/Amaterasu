# ==============================================================================
#
# Refresh Scene
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
__product__: str = 'Refresh Scene'
__version__: str = '1.00'
__doc__ = 'Recalculate the nodes in the scene.'
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
def main() -> None:
    '''Do it.'''
    result: int = cmds.dgdirty(allPlugs=True)
    cmds.refresh(force=True)
    _logger.info('Done. : %s', result)
