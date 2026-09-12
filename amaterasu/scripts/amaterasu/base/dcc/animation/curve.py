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
"""Animation utilities for the DCC base package.

This module provides functions to query and manipulate animation curves
and keyframes within Maya.
"""

from __future__ import annotations
from maya import cmds

ANIM_CURVES: list[str] = [
    "animCurveTL",
    "animCurveTA",
    "animCurveTU",
    "animCurveTT",
]


def get_anim_curves(node: str) -> list[str]:
    """Retrieves a list of animation curves connected to the given node.

    Args:
        node (str): The name of the Maya node to check for connections.

    Returns:
        list[str]: A list of connected animation curve names. Returns an empty
            list if no animation curves are found.
    """
    result: list[str] = []
    connections: list[str] = (
        cmds.listConnections(node, source=True, destination=False) or []
    )
    if not connections:
        return []

    for connection in connections:
        if cmds.nodeType(connection) in ANIM_CURVES:
            result.append(connection)

    return result


def get_anim_curve(node: str, attr: str) -> str:
    """Retrieves the animation curve connected to a specific attribute.

    Args:
        node (str): The name of the Maya node.
        attr (str): The name of the attribute on the node.

    Returns:
        str: The name of the connected animation curve, or an empty string
            if no curve is connected.
    """
    connections: list[str] = (
        cmds.listConnections(f"{node}.{attr}", source=True, destination=False)
        or []
    )
    if not connections:
        return ""

    if cmds.nodeType(connections[0]) in ANIM_CURVES:
        return connections[0]

    return ""
