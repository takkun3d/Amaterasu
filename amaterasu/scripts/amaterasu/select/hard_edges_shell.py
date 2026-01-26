# ==============================================================================
#
# Select Hard Edges Shell
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
__product__: str = 'Select Hard Edges Shell'
__version__: str = '1.00'
__doc__ = 'Select hard edges shell.'
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
    faces: list[str] = cmds.filterExpand(selectionMask=34)
    if not faces:
        vertexes: list[str] = cmds.filterExpand(selectionMask=31)
        if vertexes:
            faces = utility.to_face(vertexes)

        edges = cmds.filterExpand(selectionMask=32)
        if edges:
            faces = utility.to_face(edges)

    if not faces:
        _logger.error('Select vertex/edge/face to convert hard edges shell.')
        return

    result: list[str] = []
    while True:
        edges = utility.to_edge(faces)
        soft_edges: list[str] = [
            edge for edge in edges if utility.is_soft_edge(edge)
        ]
        faces = utility.to_face(soft_edges)
        if result == faces:
            break

        result = faces

    cmds.select(*result)
    _logger.info('Done.')
