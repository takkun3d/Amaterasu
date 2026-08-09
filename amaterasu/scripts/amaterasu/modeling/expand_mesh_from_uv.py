# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Expands mesh geometry by mapping vertices based on UV layout coordinates."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Expand Mesh From UV"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


def expand_mesh_from_uv(
    node: str, auto_split_border: bool = True
) -> utils.DataResult[list[str]]:
    """Expands mesh geometry based on its UV layout coordinates.

    Args:
        node (str): The transform node to process.
        auto_split_border (bool, optional): Whether to automatically split
            vertices at UV borders before processing. Defaults to True.

    Returns:
        utils.DataResult[list[str]]: The result object containing the newly
            created node names as its value payload.
    """
    result: utils.DataResult[list[str]] = utils.DataResult([])
    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes or cmds.objectType(shapes[0]) != "mesh":
        result.add_failure(node, "Skipping non-mesh node.")
        return result

    # cmds.polySplitEdge can be unstable, so we split vertices instead.
    if auto_split_border:
        border_uvs: list[str] = dcc.mesh.to_border_uv(node)
        border_vertices: list[str] = dcc.mesh.to_vertex(border_uvs)
        if border_vertices:
            cmds.polySplitVertex(*border_vertices)

    edge_length_3d: float = dcc.mesh.edge_length_3d(f"{node}.e[0]")
    edge_length_2d: float = dcc.mesh.edge_length_2d(f"{node}.e[0]")
    ratio: float = edge_length_3d / edge_length_2d

    new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
    vertices: list[str] = dcc.mesh.to_vertex(new_node)
    for vertex in vertices:
        uvs: list[str] = dcc.mesh.to_uv(vertex)
        if len(uvs) != 1:
            cmds.delete(new_node)
            result.add_failure(node, "Vertex has an invalid UV count.")
            return result

        position: list[float] = cmds.polyEditUV(uvs[0], query=True)  # type: ignore
        cmds.move(
            position[0] * ratio,
            position[1] * ratio,
            0,
            vertex,
            localSpace=True,
        )

    result.set_value([new_node])
    return result


def main() -> None:
    """Executes the mesh expansion process based on the current selection."""
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select polygons to expand mesh from UV.")
        return

    result: utils.DataResult[list[str]] = utils.DataResult([])
    for node in selection:
        r: utils.DataResult[list[str]] = expand_mesh_from_uv(node)
        result.merge(r)

    if result.value():
        cmds.select(*result.value())

    result.log(_logger)
