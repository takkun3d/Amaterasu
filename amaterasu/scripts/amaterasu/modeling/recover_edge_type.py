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
"""Sets hard or soft edges based on vertex normals.

This module evaluates the vertex normals of selected polygon meshes.
It checks the angle between normals of adjacent faces at each edge
to correctly determine and apply hard or soft edge properties.
"""

from __future__ import annotations
from maya.api import OpenMaya
from maya import cmds
from amaterasu.base import utils

__product__: str = "Recover Edge Type"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

ANGLE_TOLERANCE: float = 0.01


def apply(nodes: list[str]) -> bool:
    """Sets hard or soft edges based on vertex normal equivalence.

    Args:
        nodes (list[str]): A list of polygon node names to process.

    Returns:
        bool: True if the operation completes successfully, False otherwise.
    """
    if not nodes:
        return False

    selection_list: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    for node in nodes:
        selection_list.add(node)
        dag_path: OpenMaya.MDagPath = selection_list.getDagPath(0)
        selection_list.clear()

        edge_iter: OpenMaya.MItMeshEdge = OpenMaya.MItMeshEdge(dag_path)
        mesh_fn: OpenMaya.MFnMesh = OpenMaya.MFnMesh(dag_path)
        node_name: str = dag_path.partialPathName()
        soft_edges: list[str] = []
        hard_edges: list[str] = []

        while not edge_iter.isDone():
            connected_faces: OpenMaya.MIntArray = edge_iter.getConnectedFaces()
            if len(connected_faces) < 2:
                edge_iter.next()
                continue

            v0: int = edge_iter.vertexId(0)
            v1: int = edge_iter.vertexId(1)
            is_hard: bool = False
            for vertex_id in (v0, v1):
                normal_f0: OpenMaya.MVector = mesh_fn.getFaceVertexNormal(
                    connected_faces[0],
                    vertex_id,
                    OpenMaya.MSpace.kObject,
                )
                normal_f1: OpenMaya.MVector = mesh_fn.getFaceVertexNormal(
                    connected_faces[1],
                    vertex_id,
                    OpenMaya.MSpace.kObject,
                )

                angle: float = normal_f0.angle(normal_f1)
                if angle > ANGLE_TOLERANCE:
                    is_hard = True
                    break

            edge_name: str = f"{node_name}.e[{edge_iter.index()}]"
            if is_hard:
                hard_edges.append(edge_name)

            else:
                soft_edges.append(edge_name)

            edge_iter.next()

        if soft_edges:
            cmds.polySoftEdge(soft_edges, angle=180)  # type: ignore

        if hard_edges:
            cmds.polySoftEdge(hard_edges, angle=0)  # type: ignore

    cmds.select(*nodes, replace=True)
    return True


def main() -> None:
    """Executes the edge recovery process for the current selection."""
    selection: list[str] = cmds.ls(selection=True, transforms=True)
    if not selection:
        _logger.error("Select polygon nodes to recover edge types.")
        return

    apply(selection)
    _logger.info("Done.")
