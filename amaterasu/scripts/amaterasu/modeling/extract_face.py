# ==============================================================================
#
# Extract Face
#
# ==============================================================================
from __future__ import annotations
from maya import cmds
from ..lib import logger, utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Extract Face'
__version__: str = '1.00'
__doc__ = 'Extract Face from selected face.'
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
def apply(faces: list[str]) -> list[str]:
    '''Extract Face.'''
    result: list[str] = []
    selection_each_geo: dict[str, list[str]] = utility.to_each_geometry(faces)
    for node in selection_each_geo:
        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        keep_faces: list[str] = []
        delete_faces: list[str] = []
        for face in selection_each_geo[node]:
            component: str = face.split('.')[-1]
            keep_faces.append(f'{new_node}.{component}')
            delete_faces.append(face)

        cmds.select(f'{new_node}.f[*]')
        cmds.select(*keep_faces, deselect=True)
        delete_faces += cmds.ls(selection=True)

        if delete_faces:
            cmds.delete(*delete_faces)
            result.append(new_node)
        else:
            cmds.delete(new_node)

    if result:
        cmds.select(*result)

    return result


def main() -> None:
    '''Extract Face from selected face.'''
    selection: list[str] = cmds.filterExpand(selectionMask=34)
    if not selection:
        _logger.error('Select polygon faces to extract.')
        return

    apply(selection)
    _logger.info('Done.')
