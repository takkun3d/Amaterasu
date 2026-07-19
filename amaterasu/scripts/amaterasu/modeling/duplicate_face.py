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
"""Duplicate face from selected face."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Duplicate Face"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def apply(faces: list[str]) -> list[str]:
    """Duplicates specified polygon faces as a new mesh.

    This function groups selected faces by their parent geometry, duplicates
    the original mesh, and removes all faces except for those specified in
    the input list.

    Args:
        faces: A list of face component strings (e.g., ["pCube1.f[0]"]).

    Returns:
        A list of new mesh names created during the operation.
    """
    result: list[str] = []
    grouped_faces: dict[str, list[str]] = dcc.mesh.group_by_node(faces)
    for node, face_list in grouped_faces.items():
        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        keep_faces: list[str] = [
            f"{new_node}.{f.split('.')[-1]}" for f in face_list
        ]

        cmds.select(f"{new_node}.f[*]")
        cmds.select(*keep_faces, deselect=True)

        targets_to_delete: list[str] = cmds.ls(selection=True)
        if targets_to_delete:
            cmds.delete(*targets_to_delete)
            result.append(new_node)

        else:
            cmds.delete(new_node)

    if result:
        cmds.select(*result)

    return result


def main() -> None:
    """Entry point to duplicate faces based on the current selection.

    Validates that polygon faces are selected before triggering the apply
    process.
    """
    selection: list[str] = cmds.filterExpand(selectionMask=34) or []
    if not selection:
        _logger.error("Select polygon faces to duplicate.")
        return

    apply(selection)
    _logger.info("Done.")
