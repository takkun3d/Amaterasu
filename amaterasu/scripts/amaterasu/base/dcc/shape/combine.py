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


def combine(parent_node: str, source_nodes: list[str]) -> bool:
    """Combines shapes from multiple source transforms into a single target.

    This function iterates through the provided source nodes, extracts their
    shape nodes, and reparents them under the specified parent node. After
    the shapes are successfully transferred, the original source transforms
    are removed.

    Args:
        parent_node (str): The name of the target transform node that will
            receive the shapes.
        source_nodes (list[str]): A list of source transform nodes whose
            shapes will be extracted and moved.

    Returns:
        bool: True if the shapes were successfully combined.
    """
    for source_node in source_nodes:
        shapes: list[str] = (
            cmds.listRelatives(source_node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        for shape in shapes:
            cmds.parent(shape, parent_node, addObject=True, shape=True)

        cmds.parent(source_node, removeObject=True)

    return True
