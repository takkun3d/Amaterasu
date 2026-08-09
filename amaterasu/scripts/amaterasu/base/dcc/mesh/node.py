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
"""Provides node utilities for Maya meshes."""

from __future__ import annotations
from maya import cmds


def get_polygon_transforms(
    nodes: list[str], result: list[str] | None = None
) -> list[str]:
    """Searches for polygon transform nodes within the given hierarchy.

    Args:
        nodes (list[str]): A list of node names to search.

    Returns:
        list[str]: A list of transform nodes that contain mesh shapes.
    """
    if not result:
        result = []

    for node in nodes:
        if cmds.objectType(node) != "transform":
            continue

        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            children: list[str] = (
                cmds.listRelatives(node, children=True, path=True) or []
            )
            if children:
                result = get_polygon_transforms(children, result)

        else:
            shape: str = shapes[0]
            if cmds.objectType(shape) == "mesh":
                result.append(node)

    return result
