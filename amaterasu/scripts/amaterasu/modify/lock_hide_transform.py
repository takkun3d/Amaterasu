# ==============================================================================
#
# Lock & Hide Transform
#
# ==============================================================================
from __future__ import annotations
import logging
import itertools
from maya import cmds

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Lock & Hide Transform'
__version__: str = '1.00'
__doc__ = 'Lock and hide transform attributes.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

TRANS_TAGS: tuple[str, str, str] = ('t', 'r', 's')
AXIS_TAGS: tuple[str, str, str] = ('x', 'y', 'z')

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
def lock(nodes: list[str], is_visible: bool = True) -> bool:
    '''Lock and hide transform attributes.'''
    for node in nodes:
        for channel, axis in itertools.product(TRANS_TAGS, AXIS_TAGS):
            cmds.setAttr(f'{node}.{channel}{axis}', lock=True, keyable=False)
        if is_visible:
            cmds.setAttr(f'{node}.v', lock=True, keyable=False)
    return True


def unlock(nodes: list[str], is_visible: bool = True) -> bool:
    '''Unlock and show transform attributes.'''
    for node in nodes:
        for channel, axis in itertools.product(TRANS_TAGS, AXIS_TAGS):
            cmds.setAttr(f'{node}.{channel}{axis}', lock=False, keyable=True)
        if is_visible:
            cmds.setAttr(f'{node}.v', lock=False, keyable=True)
    return True


def main(is_lock: bool = True) -> None:
    '''Lock and hide transform attributes from selection.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        if is_lock:
            _logger.error('Select node to lock and hide attribute.')
        else:
            _logger.error('Select node to unlock and show attribute.')
        return

    if is_lock:
        lock(selection)
    else:
        unlock(selection)
    _logger.info('Done.')
