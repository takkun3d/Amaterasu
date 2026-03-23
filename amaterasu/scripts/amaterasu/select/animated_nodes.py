# ==============================================================================
#
# Select Animated Nodes
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
__product__: str = 'Select Animated Nodes'
__version__: str = '1.00'
__doc__ = 'Select animated nodes.'
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
    selection: set[str] = set(cmds.ls(selection=True))
    result: set[str] = set([])

    anim_curves: list[str] = cmds.ls(
        type=['animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU']
    )
    for anim_curve in anim_curves:
        connections: list[str] = cmds.listConnections(anim_curve)
        if not connections:
            continue

        for node in connections:
            result.add(node)

    if selection:
        result = selection & result

    if result:
        cmds.select(*list(result))
        _logger.info('Done.')

    else:
        _logger.warning('Does not exists animed node.')
