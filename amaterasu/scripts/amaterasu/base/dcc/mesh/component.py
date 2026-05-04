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
"""Provides component conversion utilities for Maya meshes."""

from __future__ import annotations
from maya import cmds


def to_edge(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to an edge list.

    Args:
        nodes_or_components (str | list[str]): The nodes or components to convert.

    Returns:
        list[str]: A flat list of edge components (e.g., ['pCube1.e[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    edges: list[str] = cmds.polyListComponentConversion(*sources, toEdge=True)
    return cmds.filterExpand(*edges, selectionMask=32) or []


def to_face(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to a face list.

    Args:
        nodes_or_components (str | list[str]): The nodes or components to convert.

    Returns:
        list[str]: A flat list of face components.
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    faces: list[str] = cmds.polyListComponentConversion(*sources, toFace=True)
    return cmds.filterExpand(*faces, selectionMask=34) or []
