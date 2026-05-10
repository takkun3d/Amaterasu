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
"""Provides utilities for separating Maya shape nodes.

This module contains functions to split multiple shape nodes that are
parented under a single transform into their own individual transform
nodes, while perfectly preserving their world-space transformations.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def separate(source_nodes: list[str]) -> utils.Result:
    """Separates multiple shapes under a transform into individual transforms.

    Args:
        source_nodes (list[str]): Transforms containing multiple shapes.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    for source_node in source_nodes:
        shapes: list[str] = (
            cmds.listRelatives(source_node, shapes=True, path=True) or []
        )
        if not shapes:
            result.add_failure(source_node, "No shapes found")
            continue
        if len(shapes) <= 1:
            result.add_failure(source_node, "Contains only one shape, skipping")
            continue

        try:
            parent_nodes: list[str] = (
                cmds.listRelatives(
                    source_node, parent=True, shapes=False, path=True
                )
                or []
            )
            parent_node: str = parent_nodes[0] if parent_nodes else "|"

            for shape in shapes[1:]:
                transform: str = cmds.createNode(
                    "transform",
                    name=shape.replace("Shape", ""),
                    parent=parent_node,
                )
                matrix: list[float] = cmds.xform(
                    source_node, query=True, matrix=True, worldSpace=True
                )  # type: ignore
                cmds.xform(
                    transform, matrix=matrix, worldSpace=True  # type: ignore
                )
                cmds.parent(shape, transform, addObject=True, shape=True)
                cmds.parent(shape, removeObject=True, shape=True)

        except RuntimeError as e:
            result.add_failure(source_node, str(e))

    return result
