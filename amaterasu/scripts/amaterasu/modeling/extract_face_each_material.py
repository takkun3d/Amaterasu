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
"""Extract face each material from selected polygon."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils, dcc

__product__: str = "Extract Face Each Material"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


def extract_faces_by_material(node: str) -> utils.Result:
    """Extracts faces from a polygon mesh grouped by their assigned materials.

    Identifies all shading engines assigned to the mesh, separates the faces
    based on their material assignments, and performs extraction for each
    material group.

    Args:
        node: The name of the polygon mesh node to process.

    Returns:
        A utils.Result object containing the status of the extraction process.
    """
    result: utils.Result = utils.Result()
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

    for shading_group in shading_groups[1:]:
        extract_faces: list[str] = []
        faces: list[str] = dcc.mesh.to_face(node)
        for face in faces:
            if cmds.sets(face, isMember=shading_group):
                extract_faces.append(face)

        new_node: list[str] = dcc.mesh.extract_faces(extract_faces)
        if not new_node:
            continue

        cmds.sets(new_node[0], edit=True, forceElement=shading_group)

    cmds.sets(node, edit=True, forceElement=shading_groups[0])
    return result


def main() -> None:
    """Entry point for extracting faces by material based on selection.

    Validates the user selection and iterates through nodes to perform the
    extraction process. Logs the final result.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select polygon meshes to extract faces by material.")
        return

    result: utils.Result = utils.Result()
    for node in selection:
        r: utils.Result = extract_faces_by_material(node)
        result.merge(r)

    cmds.select(*selection)
    result.log(_logger)
