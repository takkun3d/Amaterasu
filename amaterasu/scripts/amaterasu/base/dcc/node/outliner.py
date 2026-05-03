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
"""Provides utilities for managing Maya Outliner colors.

This module contains functions to set or clear custom RGB colors
for nodes displayed in the Maya Outliner. It handles attribute
modifications and safely catches runtime errors.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def set_outliner_color(
    rgb: list[float],
    nodes: list[str] | None = None,
) -> utils.Result:
    """Applies an RGB color to the specified nodes in the Outliner.

    This function enables the 'useOutlinerColor' attribute and sets the
    'outlinerColor' attribute for the given nodes. If no nodes are
    provided, it defaults to the current selection.

    Args:
        rgb (list[float]): The RGB color values as a list of three floats
            (e.g., [1.0, 0.0, 0.0] for red).
        nodes (list[str] | None, optional): A list of Maya node names to
            process. Defaults to None, which uses the current selection.

    Returns:
        utils.Result: An object containing the success or failure states
            of the operation.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        result.set_error("Select object to set outliner color.")
        return result

    for node in nodes:
        try:
            cmds.setAttr(f"{node}.useOutlinerColor", 1)
            cmds.setAttr(f"{node}.outlinerColor", *rgb, type="double3")

        except RuntimeError as e:
            reason: str = str(e).split(":", maxsplit=1)[-1].strip()
            result.add_failure(node, reason)

    return result


def clear_outliner_color(nodes: list[str] | None = None) -> utils.Result:
    """Clears the Outliner color override from the specified nodes.

    This function disables the 'useOutlinerColor' attribute for the given
    nodes, reverting them to their default Outliner appearance. If no
    nodes are provided, it defaults to the current selection.

    Args:
        nodes (list[str] | None, optional): A list of Maya node names to
            process. Defaults to None, which uses the current selection.

    Returns:
        utils.Result: An object containing the success or failure states
            of the operation.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        result.set_error("Select object to clear outliner color.")
        return result

    for node in nodes:
        try:
            cmds.setAttr(f"{node}.useOutlinerColor", 0)

        except RuntimeError as e:
            reason: str = str(e).split(":", maxsplit=1)[-1].strip()
            result.add_failure(node, reason)

    return result


def sort(nodes: list[str], sort_order: int = 2) -> utils.Result:
    """Sorts nodes in the outliner based on the specified order.

    Args:
        nodes (list[str]): The nodes to sort.
        sort_order (int, optional): The sorting method.
            0 for Ascending, 1 for Descending, 2 for Selection order.
            Defaults to 2.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    if sort_order == 0:
        nodes = sorted(nodes)

    elif sort_order == 1:
        nodes = sorted(nodes, reverse=True)

    for node in nodes:
        try:
            cmds.reorder(node, back=True)

        except RuntimeError as e:
            result.add_failure(node, str(e))

    return result
