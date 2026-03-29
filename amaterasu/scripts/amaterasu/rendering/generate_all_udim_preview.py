# ==============================================================================
#
# Generate All UDIM Preview
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
__product__: str = 'Generate All UDIM Preview'
__version__: str = '1.00'
__doc__ = 'Generate all udim preview.'
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
def apply(nodes: list[str]) -> None:
    '''Generate udim preview.'''
    for node in nodes:
        if cmds.getAttr(f'{node}.uvTilingMode') == 0:
            continue

        if cmds.getAttr(f'{node}.uvTileProxyQuality') == 0:
            continue

        cmds.ogs(regenerateUVTilePreview=node)
        _logger.info('Update : %s.', node)


def main() -> None:
    '''Generate all udim preview.'''
    apply(cmds.ls(type='file'))
    _logger.info('Done.')
