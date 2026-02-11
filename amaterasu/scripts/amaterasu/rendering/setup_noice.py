# ==============================================================================
#
# Setup Noice
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from mtoa import core


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Setup Noice'
__version__: str = '1.00'
__doc__ = 'Sets up Arnold render settings for Noice denoising.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

PLUGIN_NAME: str = 'mtoa'

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
    '''Executes the Setup Noice tool.'''
    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)
        if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
            _logger.error('Failed to load Arnold plugin.')
            return

    render_options: str = 'defaultArnoldRenderOptions'
    driver: str = 'defaultArnoldDriver'
    if not cmds.objExists(render_options):
        core.createOptions()
        _logger.info('Create Arnold Options.')

    cmds.setAttr(f'{render_options}.outputVarianceAOVs', 1)
    cmds.setAttr(f'{render_options}.renderDevice', 0)
    cmds.setAttr(f'{driver}.mergeAOVs', 1)
    cmds.setAttr(f'{driver}.aiTranslator', 'exr', type='string')
    cmds.setAttr(f'{driver}.exrCompression', 3)
    _logger.info('Done.')
