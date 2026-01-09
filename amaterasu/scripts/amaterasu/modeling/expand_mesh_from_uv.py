# ==============================================================================
#
# Expand Mesh from UV
#
# ==============================================================================
from __future__ import annotations
import logging
import math
from maya import cmds
from ..lib import utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Expand Mesh From UV'
__version__: str = '1.11'
__doc__ = 'Duplicate face from selected face.'
__copyright__ = 'Copyright(c) 2017-2025 @takkun3d. All Rights Reserved.'
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
def edge_length_3d(edge: str) -> float:
    '''Return edge length in 3d.'''
    vertexes: list[str] = utility.to_vertex(edge)
    position: list[float] = cmds.xform(
        vertexes, query=True, translation=True, worldSpace=True
    )
    x: float = math.pow(position[3] - position[0], 2)
    y: float = math.pow(position[4] - position[1], 2)
    z: float = math.pow(position[5] - position[2], 2)
    return math.sqrt(x + y + z)


def edge_length_2d(edge: str) -> float:
    '''Return edge length in 2d.'''
    uvs: list[str] = utility.to_uv(edge)
    position: list[float] = cmds.polyEditUV(uvs, query=True)
    return math.sqrt(
        math.pow(position[2] - position[0], 2)
        + math.pow(position[3] - position[1], 2)
    )


def uv_center(node: str) -> list[float]:
    '''Return uv center position.'''
    bb2d: list[list[float]] = cmds.polyEvaluate(node, boundingBox2d=True)
    return [(bb2d[0][1] + bb2d[0][0]) / 2, (bb2d[1][1] + bb2d[1][0]) / 2]


def apply(nodes: list[str], auto_split_border: bool = True) -> bool:
    '''Expand Mesh from UV.'''
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes or cmds.objectType(shapes[0]) != 'mesh':
            _logger.warning('Can not be processed : %s', node)
            continue

        ratio: float = edge_length_3d(f'{node}.e[0]') / edge_length_2d(
            f'{node}.e[0]'
        )

        if auto_split_border:
            border_uv: list[str] = utility.to_border_uv(node)
            border_vertex: list[str] = utility.to_vertex(border_uv)
            if border_vertex:
                cmds.polySplitVertex(*border_vertex)

        duplicate_nodes: list[str] = cmds.duplicate(node, returnRootsOnly=True)
        if not duplicate_nodes:
            continue

        new_node: str = duplicate_nodes[0]

        vertexes: list[str] = utility.to_vertex(new_node)
        for vertex in vertexes:
            uvs: list[str] = utility.to_uv(vertex)
            if len(uvs) != 1:
                _logger.error('Vertex has more than one uvs : %s', node)
                cmds.delete(new_node)
                break

            position: list[float] = cmds.polyEditUV(uvs[0], query=True)
            cmds.move(
                position[0] * ratio,
                position[1] * ratio,
                0,
                vertex,
                localSpace=True,
            )

    if nodes:
        cmds.select(*nodes)

    return True


# -------------------------------------------------------------------------------
# Main Functions
# -------------------------------------------------------------------------------
def main() -> None:
    '''Expand Mesh from selected nodes.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygons to expand mesh from UV.')
        return

    result: bool = apply(selection)
    if result:
        _logger.info('Done.')
