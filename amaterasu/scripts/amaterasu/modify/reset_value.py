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
"""Resets keyable attributes of selected nodes to their default values.

This tool iterates through the keyable, scalar attributes of the
currently selected nodes and resets them to their default states.
It safely ignores locked attributes and those driven by non-animation
connections.
"""

from __future__ import annotations
from typing import Any
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Reset Value"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def _reset_node(node: str) -> utils.Result:
    """Resets the attributes of a single node.

    Args:
        node (str): The name of the Maya node.

    Returns:
        utils.Result: A result object indicating success or
            containing error details.
    """
    result: utils.Result = utils.Result()
    attrs: list[str] = cmds.listAttr(node, keyable=True, scalar=True) or []
    for attr in attrs:
        plug: str = f"{node}.{attr}"
        try:
            if cmds.getAttr(plug, lock=True):
                continue

        except ValueError:
            continue

        # Skip if connected to a non-animation node
        connections: list[str] = (
            cmds.listConnections(plug, source=True, destination=False) or []
        )
        if connections:
            node_type: str = cmds.nodeType(connections[0])  # type: ignore
            if not node_type.startswith("animCurveT"):
                continue

        default_value: Any = dcc.attribute.get_default_value(node, attr)
        if default_value is None:
            continue

        current_value: Any = cmds.getAttr(plug)
        if current_value != default_value:
            try:
                cmds.setAttr(plug, default_value)
                result.add_info(
                    plug, f"Reset: {current_value} -> {default_value}"
                )

            except RuntimeError:
                result.add_failure(plug, "Failed to set default value")
                continue

    return result


def main() -> None:
    """Resets keyable attributes of selected nodes to their default values."""
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        _logger.error("Select node(s) to reset attribute value.")
        return

    result: utils.Result = utils.Result()
    for node in selection:
        r: utils.Result = _reset_node(node)
        result.merge(r)

    result.log(_logger)
