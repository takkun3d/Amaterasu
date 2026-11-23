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
"""Inserts a zero-out offset group above the selected transforms."""

from __future__ import annotations

from maya import cmds

from amaterasu.base import utils

__product__: str = "Insert Space"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig or dcc.node).
def extract_base_name(node: str) -> str:
    """Extracts the short base name from a DAG path or namespaced node.

    Args:
        node (str): The full or partial node name.

    Returns:
        str: The extracted base name prefix.
    """
    short_name: str = node.split("|")[-1].split(":")[-1]
    return short_name.split("_")[0]


def insert_space(node: str) -> str:
    """Inserts a zero-out space null node above the specified transform.

    Args:
        node (str): The target transform node name.

    Returns:
        str: The name of the created space null node.
    """
    parents: list[str] = (
        cmds.listRelatives(node, parent=True, fullPath=True) or []
    )
    parent_node: str = parents[0] if parents else ""
    base_name: str = extract_base_name(node)

    space_node: str = cmds.createNode(
        "transform", name=f"{base_name}Space_null"
    )
    cmds.matchTransform(
        space_node, node, position=True, rotation=True, scale=True, pivots=True
    )
    if parent_node:
        space_node = cmds.parent(space_node, parent_node)[0]

    node = cmds.parent(node, space_node)[0]

    # TODO: Consider moving to amaterasu.base (e.g., dcc.rig or dcc.node). ???
    for attr in ("translate", "rotate"):
        cmds.setAttr(f"{node}.{attr}", 0.0, 0.0, 0.0, type="double3")
    cmds.setAttr(f"{node}.scale", 1.0, 1.0, 1.0, type="double3")

    return space_node


def main() -> None:
    """Runs the main process on the currently selected transform nodes."""
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select transform node(s) to insert a space group.")
        return

    result: list[str] = []
    for node in selection:
        space: str = insert_space(node)
        result.append(space)

    if result:
        cmds.select(*result)

    _logger.info("Done.")
