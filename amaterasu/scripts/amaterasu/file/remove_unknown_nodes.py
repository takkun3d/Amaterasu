# ==============================================================================
#
# Remove Unknown Nodes
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
__product__: str = 'Remove Unknown Nodes'
__version__: str = '1.01'
__doc__ = 'Remove unknown nodes from an open scene.'
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
    nodes: list[str] = cmds.ls(type='unknown')
    for node in nodes:
        try:
            cmds.lockNode(node, lock=False)
            cmds.delete(node)
            _logger.info('Delete node : %s', node)

        except RuntimeError:
            _logger.warning('Can not delete node : %s', node)

        except ValueError:
            # Ignore nodes deleted in conjunction.
            pass

    _logger.info('Done.')
