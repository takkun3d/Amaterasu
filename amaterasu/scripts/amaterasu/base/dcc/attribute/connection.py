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
"""Provides utilities for breaking attribute connections in Maya.

This module contains functions to safely disconnect incoming connections
for specific transform and visibility attributes of Maya nodes.
"""

from __future__ import annotations
from maya import cmds


def __break_connections(dst_plug: str) -> None:
    """Breaks the incoming connection to the specified destination plug.

    Args:
        dst_plug (str): The destination plug to disconnect (e.g., 'node.tx').
    """
    if not cmds.connectionInfo(dst_plug, isDestination=True):
        return

    src_plug: str = cmds.connectionInfo(dst_plug, sourceFromDestination=True)  # type: ignore
    cmds.disconnectAttr(src_plug, dst_plug)


def break_transform_connections(
    nodes: list[str],
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Breaks incoming connections for specified transform attributes.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        translate (bool, optional): If True, breaks translate connections.
            Defaults to False.
        rotate (bool, optional): If True, breaks rotate connections.
            Defaults to False.
        scale (bool, optional): If True, breaks scale connections.
            Defaults to False.
        visibility (bool, optional): If True, breaks visibility connections.
            Defaults to False.
    """
    for node in nodes:
        for attr, flag in zip(["t", "r", "s"], [translate, rotate, scale]):
            if not flag:
                continue

            for axis in ["x", "y", "z"]:
                __break_connections(f"{node}.{attr}{axis}")

        if visibility:
            __break_connections(f"{node}.v")
