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
"""Provides utilities for combining and managing Maya shape nodes.

This module contains functions to extract shape nodes from multiple
source transforms and consolidate them under a single target transform.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def combine(parent_node: str, source_nodes: list[str]) -> utils.Result:
    """Combines shapes from multiple source transforms into a single target.

    Args:
        parent_node (str): The target transform node to receive the shapes.
        source_nodes (list[str]): Source transforms whose shapes will be moved.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    for source_node in source_nodes:
        shapes: list[str] = (
            cmds.listRelatives(source_node, shapes=True, path=True) or []
        )
        if not shapes:
            result.add_failure(source_node, "No shapes found to combine")
            continue

        try:
            for shape in shapes:
                cmds.parent(shape, parent_node, addObject=True, shape=True)

            cmds.parent(source_node, removeObject=True)

        except RuntimeError as e:
            result.add_failure(source_node, str(e))

    return result
