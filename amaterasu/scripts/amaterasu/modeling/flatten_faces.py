# ==============================================================================
#
# Flatten Faces
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
__product__: str = 'Flatten Faces'
__version__: str = '1.00'
__doc__ = 'Flatten faces from selected it.'
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
def apply(faces: list[str]) -> None:
    '''Flatten faces.'''
    faces_each_geo: dict[str, list[str]] = utility.to_each_geometry(faces)
    for node in faces_each_geo:
        face_number: int = len(faces_each_geo[node])
        bounding_box: list[float] = cmds.xform(
            faces_each_geo[node], query=True, objectSpace=True, boundingBox=True
        )
        center_pivot: list[float] = [
            (bounding_box[0] + bounding_box[3]) * 0.5,
            (bounding_box[1] + bounding_box[4]) * 0.5,
            (bounding_box[2] + bounding_box[5]) * 0.5,
        ]
        face_vector: list[float] = [0.0, 0.0, 0.0]
        for face in faces_each_geo[node]:
            vector: list[float] = utility.face_normals(face)
            face_vector[0] += vector[0] / face_number
            face_vector[1] += vector[1] / face_number
            face_vector[2] += vector[2] / face_number

        center_distance: float = (
            face_vector[0] * center_pivot[0]
            + face_vector[1] * center_pivot[1]
            + face_vector[2] * center_pivot[2]
        )
        for face in faces_each_geo[node]:
            vertexes = utility.to_vertex(face)
            for vertex in vertexes:
                value: list[float] = [0.0, 0.0, 0.0]
                position: list[float] = cmds.pointPosition(vertex, local=True)
                offset: float = (
                    center_distance
                    - (face_vector[0] * position[0])
                    - (face_vector[1] * position[1])
                    - (face_vector[2] * position[2])
                )
                length: float = (
                    (face_vector[0] * face_vector[0])
                    + (face_vector[1] * face_vector[1])
                    + (face_vector[2] * face_vector[2])
                )
                if length != 0:
                    value = [
                        position[0] + (offset / length * face_vector[0]),
                        position[1] + (offset / length * face_vector[1]),
                        position[2] + (offset / length * face_vector[2]),
                    ]

                cmds.move(
                    value[0],
                    value[1],
                    value[2],
                    vertex,
                    absolute=True,
                    objectSpace=True,
                )


def main() -> None:
    '''Flatten faces from selected it.'''
    selection: list[str] = cmds.filterExpand(selectionMask=34)
    if not selection:
        _logger.error('Select polygon faces to flat.')
        return

    apply(selection)
    _logger.info('Done.')
