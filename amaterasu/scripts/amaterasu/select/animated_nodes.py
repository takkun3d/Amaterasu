# ==============================================================================
#
# Select Animated Nodes
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
__product__: str = 'Select Animated Nodes'
__version__: str = '1.00'
__doc__ = 'Select animated nodes.'
__copyright__ = 'Copyright(c) 2019-2014 @takkun3d. All Rights Reserved.'
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
        logging.info('Done.')

    else:
        logging.info('Does not exists animed node.')
