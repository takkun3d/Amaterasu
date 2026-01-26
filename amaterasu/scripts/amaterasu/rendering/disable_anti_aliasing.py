# ==============================================================================
#
# Disable anti-aliasing for Maya Software
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
__product__: str = 'Disable anti-aliasing'
__version__: str = '1.00'
__doc__ = 'Sets Maya Software anti-aliasing to disabled.'
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
    cmds.setAttr(
        'defaultRenderGlobals.currentRenderer',
        'mayaSoftware',
        type='string',
    )
    try:
        cmds.addAttr(
            'defaultRenderGlobals',
            cachedInternally=True,
            longName='useZBuffer',
            defaultValue=1,
            minValue=0,
            maxValue=1,
            attributeType='bool',
        )
    except RuntimeError:
        cmds.setAttr('defaultRenderGlobals.useZBuffer', 1)

    cmds.setAttr('defaultRenderGlobals.jitterFinalColor', 0)
    cmds.setAttr('defaultRenderQuality.edgeAntiAliasing', 0)
    cmds.setAttr('defaultRenderQuality.shadingSamples', 2)
    cmds.setAttr('defaultRenderQuality.maxShadingSamples', 8)
    cmds.setAttr('defaultRenderQuality.useMultiPixelFilter', 0)
    cmds.setAttr('defaultRenderQuality.enableRaytracing', 0)
    cmds.setAttr('defaultRenderQuality.reflections', 10)
    cmds.setAttr('defaultRenderQuality.refractions', 10)
    cmds.setAttr('defaultRenderQuality.shadows', 0)

    _logger.info('Done.')
