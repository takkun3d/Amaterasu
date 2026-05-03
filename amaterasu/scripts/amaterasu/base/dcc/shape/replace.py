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
"""Provides utilities for replacing Maya shape nodes.

This module contains functions to duplicate shape nodes from a source
transform and transfer them to multiple destination transforms,
effectively replacing their existing shapes.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def replace(source_node: str, destination_nodes: list[str]) -> utils.Result:
    """Replaces shapes of destination transforms with shapes from a source.

    Args:
        source_node (str): The transform node containing the new shapes.
        destination_nodes (list[str]): The transforms whose shapes will be replaced.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    source_shapes: list[str] = (
        cmds.listRelatives(source_node, shapes=True, path=True) or []
    )
    if not source_shapes:
        result.set_error(f"No shapes found in source node: {source_node}")
        return result

    for destination_node in destination_nodes:
        try:
            source_dummy: str = cmds.duplicate(
                source_node, returnRootsOnly=True
            )[0]
            dummy_shapes: list[str] = (
                cmds.listRelatives(source_dummy, shapes=True, path=True) or []
            )
            old_shapes: list[str] = (
                cmds.listRelatives(destination_node, shapes=True, path=True)
                or []
            )

            for shape in dummy_shapes:
                cmds.parent(shape, destination_node, addObject=True, shape=True)

            cmds.parent(source_dummy, removeObject=True)

            if old_shapes:
                cmds.delete(*old_shapes)

        except RuntimeError as e:
            result.add_failure(destination_node, str(e))

    return result
