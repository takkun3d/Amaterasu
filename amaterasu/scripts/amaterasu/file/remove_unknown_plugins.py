# ==============================================================================
#
# Remove Unknown Plugins
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
__product__: str = 'Remove Unknown Plugins'
__version__: str = '1.01'
__doc__ = 'Remove unknown plugins from an open scene.'
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
    unknown_plugins: list[str] = cmds.unknownPlugin(query=True, list=True) or []
    for plugin in unknown_plugins:
        cmds.unknownPlugin(plugin, remove=True)
        _logger.info('Remove plugin : %s', plugin)

    _logger.info('Done.')
