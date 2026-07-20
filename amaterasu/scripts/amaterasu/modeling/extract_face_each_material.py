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
"""Extracts faces from selected polygons for each assigned material."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils, dcc

__product__: str = "Extract Face Each Material"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


def extract_faces_by_material(node: str) -> utils.DataResult[list[str]]:
    """Extracts faces from a polygon mesh grouped by their assigned materials.

    Identifies all shading engines assigned to the mesh, separates the faces
    based on their material assignments, and performs extraction for each
    material group.

    Args:
        node (str): The name of the polygon mesh node to process.

    Returns:
        utils.DataResult[list[str]]: The result object containing the newly
            created node names as its value payload.
    """
    result: utils.DataResult[list[str]] = utils.DataResult([])
    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        result.add_failure(node, "No shape found.")
        return result

    shape: str = shapes[0]
    shading_groups: list[str] = (
        cmds.listConnections(
            shape, source=True, destination=False, type="shadingEngine"
        )
        or []
    )
    shading_groups = list(set(shading_groups))
    if not shading_groups or len(shading_groups) == 1:
        result.add_failure(node, "Only one material assigned, skipping.")
        return result

    new_nodes: list[str] = [node]
    for shading_group in shading_groups[1:]:
        # extract_faces: list[str] = []
        # faces: list[str] = dcc.mesh.to_face(node)
        # for face in faces:
        #     if cmds.sets(face, isMember=shading_group):
        #         extract_faces.append(face)
        members: list[str] = cmds.sets(shading_group, query=True) or []  # type: ignore
        extract_faces: list[str] = cmds.ls(*members, flatten=True)
        extract_faces = [f for f in extract_faces if f.startswith(f"{node}.f[")]

        new_node: list[str] = dcc.mesh.extract_faces(extract_faces)
        if not new_node:
            continue

        cmds.sets(new_node[0], edit=True, forceElement=shading_group)
        new_nodes.append(new_node[0])

    cmds.sets(node, edit=True, forceElement=shading_groups[0])
    result.set_value(new_nodes)
    return result


def main() -> None:
    """Entry point for extracting faces by material based on selection.

    Validates the user selection and iterates through nodes to perform the
    extraction process. Logs the final result.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select polygon meshes to extract faces by material.")
        return

    result: utils.DataResult[list[str]] = utils.DataResult([])
    for node in selection:
        r: utils.DataResult[list[str]] = extract_faces_by_material(node)
        result.merge(r)

    if result.value():
        cmds.select(*result.value())

    result.log(_logger)
