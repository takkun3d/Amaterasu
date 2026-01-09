# ==============================================================================
#
# Duplicate Face
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from ..lib import utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Duplicate Face'
__version__: str = '1.00'
__doc__ = 'Duplicate face from selected face.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
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
def apply(faces: list[str]) -> list[str]:
    '''Duplicate face.'''
    result: list[str] = []
    selection_each_geo: dict[str, list[str]] = utility.to_each_geometry(faces)
    for node in selection_each_geo:
        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        keep_faces: list[str] = []
        for face in selection_each_geo[node]:
            component: str = face.split('.')[-1]
            keep_faces.append(f'{new_node}.{component}')

        cmds.select(f'{new_node}.f[*]')
        cmds.select(*keep_faces, deselect=True)
        delete_faces: list[str] = cmds.ls(selection=True)
        if delete_faces:
            cmds.delete(*delete_faces)
            result.append(new_node)
        else:
            cmds.delete(new_node)

    if result:
        cmds.select(*result)

    return result


def main() -> None:
    '''Duplicate face from selected face.'''
    selection: list[str] = cmds.filterExpand(selectionMask=34)
    if not selection:
        _logger.error('Select polygon faces to duplicate.')
        return

    apply(selection)
    _logger.info('Done.')
