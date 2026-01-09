# ==============================================================================
#
# Extract Face Each Material
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from . import extract_face
from ..lib import utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Extract Face Each Material'
__version__: str = '1.10'
__doc__ = 'Extract face each material from selected polygon.'
__copyright__ = 'Copyright(c) 2013-2024 @takkun3d. All Rights Reserved.'
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
    '''Extract face each material from selected polygon.'''
    selection: list[str] = cmds.ls(selection=True, objectsOnly=True)
    if not selection:
        _logger.error('Select polygon to extract face each material.')
        return

    result: list[str] = []
    for node in selection:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            _logger.warning('Does not exists shape : %s', node)
            continue

        shape: str = shapes[0]
        shading_groups: list[str] = cmds.listConnections(
            shape, source=True, destination=False, type='shadingEngine'
        )
        shading_groups = list(set(shading_groups))
        if not shading_groups:
            _logger.warning('Material is not assigned : %s', node)
            continue

        if len(shading_groups) == 1:
            continue

        for shading_group in shading_groups[1:]:
            extract_faces: list[str] = []
            faces = utility.to_face(node)
            for face in faces:
                if cmds.sets(face, isMember=shading_group):
                    extract_faces.append(face)

            temp_result: list[str] = extract_face.apply(extract_faces)
            if not temp_result:
                continue

            result.append(temp_result[0])
            cmds.sets(temp_result[0], edit=True, forceElement=shading_group)

        cmds.sets(node, edit=True, forceElement=shading_groups[0])
        result.append(node)

    if result:
        cmds.select(*result)

    _logger.info('Done.')
