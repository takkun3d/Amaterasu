# ==============================================================================
#
# History Visibility
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
__product__: str = 'History Visibility'
__version__: str = '1.00'
__doc__ = 'Toggles the visibility of history in the Channel Box.'
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
def show(nodes: list[str] | None = None) -> None:
    '''Shows the history in the Channel Box.'''
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error('Select node(s) to show the history in Channel Box.')
        return

    main(nodes, 2)
    cmds.select(*nodes, replace=True)  # Updates the Channel Box information.
    _logger.info('Done.')


def hide(nodes: list[str] | None = None) -> None:
    '''Hides the history in the Channel Box.'''
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error('Select node(s) to hide the history in Channel Box.')
        return

    main(nodes, 0)
    cmds.select(*nodes, replace=True)  # Updates the Channel Box information.
    _logger.info('Done.')


def main(nodes: list[str] | None = None, visibility: int = 0) -> None:
    '''Toggles the visibility of history in the Channel Box.'''
    if not nodes:
        nodes = []

    for node in nodes:
        histories: list[str] = cmds.listHistory(node, leaf=False) or []
        for history in histories:
            cmds.setAttr(f'{history}.isHistoricallyInteresting', visibility)
