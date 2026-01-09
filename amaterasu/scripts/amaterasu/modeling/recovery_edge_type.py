# ==============================================================================
#
# Recovery Edge Type
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
__product__: str = 'Recovery Edge Type'
__version__: str = '1.10'
__doc__ = 'Set hard or soft edge from normals.'
__copyright__ = 'Copyright(c) 2017-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

CALC_PRECISION: int = 5


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
def apply(nodes: list[str]) -> bool:
    '''Set hard or soft edge.'''
    for node in nodes:
        edges: list[str] = utility.to_edge(node)
        if not edges:
            _logger.error('Failed to get polygon edges: %s', node)
            continue

        soft_edges: list[str] = []
        hard_edges: list[str] = []
        for edge in edges:
            normals: list[list[float]] = []
            vertex_faces: list[str] = utility.to_vertex_face(edge)
            for vertex_face in vertex_faces:
                normal: list[float] = list(
                    cmds.polyNormalPerVertex(
                        vertex_face, query=True, normalXYZ=True
                    )
                )
                normal[0] = round(normal[0], CALC_PRECISION)
                normal[1] = round(normal[1], CALC_PRECISION)
                normal[2] = round(normal[2], CALC_PRECISION)
                if normal not in normals:
                    normals.append(normal)

            if len(normals) < 2:
                soft_edges.append(edge)
            else:
                hard_edges.append(edge)

        if soft_edges:
            cmds.polySoftEdge(*soft_edges, angle=180)

        if hard_edges:
            cmds.polySoftEdge(*hard_edges, angle=0)

    cmds.select(*nodes)
    return True


def main() -> None:
    '''Set hard or soft edge from normals.'''
    selection: list[str] = cmds.ls(selection=True, flatten=True)
    if not selection:
        _logger.error('Select polygon node to recovery edge type.')
        return

    apply(selection)
    _logger.info('Done.')
