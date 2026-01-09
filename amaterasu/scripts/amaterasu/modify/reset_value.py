# ==============================================================================
#
# Reset Value
#
# ==============================================================================
from __future__ import annotations
from typing import Any
import logging
from maya import cmds
from ..lib import utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Reset Value'
__version__: str = '1.00'
__doc__ = 'Resets keyable attributes of selected nodes to their default values.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
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
def apply(node: str) -> bool:
    '''Do it'''
    attrs: list[str] = cmds.listAttr(node, keyable=True, scalar=True) or []
    for attr in attrs:
        plug: str = f'{node}.{attr}'

        try:
            if cmds.getAttr(plug, lock=True):
                continue

        except ValueError:
            continue

        connections: list[str] = cmds.listConnections(
            plug, source=True, destination=False
        )
        if connections:
            if cmds.nodeType(connections[0]) not in [
                'animCurveTL',
                'animCurveTA',
                'animCurveTU',
                'animCurveTT',
            ]:
                continue

        default_value: Any = utility.get_default_value(node, attr)
        current_value: Any = cmds.getAttr(plug)
        if default_value is None:
            continue

        if current_value != default_value:
            try:
                cmds.setAttr(plug, default_value)

            except RuntimeError:
                return False

    return True


def main() -> None:
    '''Resets keyable attributes of selected nodes to their default values.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select nodes to reset attribute value.')
        return

    for node in selection:
        result: bool = apply(node)
        if not result:
            _logger.error('Failed to reset attribute : %s', node)

    _logger.info('Done.')
