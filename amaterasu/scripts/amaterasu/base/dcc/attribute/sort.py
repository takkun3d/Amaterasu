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
"""Attribute reordering utilities for Maya.

This module provides functions to manipulate and reorder user-defined attributes
on Maya nodes
"""

from __future__ import annotations
from maya import cmds


def reorder_user_attributes(node: str, attr_names: list[str]) -> None:
    """Reorders user-defined attributes on a node.

    This function uses a known Maya hack: it deletes the attributes in reverse order
    and then undoes the deletions.

    WARNING: Because of this hack, it MUST NOT be wrapped in an undo chunk,
    and it will flush Maya's undo queue upon completion.

    Args:
        node (str): The name of the Maya node.
        attr_names (list[str]): The desired order of the attribute names.

    Raises:
        RuntimeError: If deleting or undoing fails.
    """
    attr_orders_reversed: list[str] = list(reversed(attr_names))
    for attr in attr_orders_reversed:
        cmds.deleteAttr(f"{node}.{attr}")

    for _ in range(len(attr_orders_reversed)):
        cmds.undo()

    cmds.flushUndo()
