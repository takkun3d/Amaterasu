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
"""Provides edge-related utilities for Maya meshes."""

from __future__ import annotations
from maya import cmds


def get_crease_edges(edges: list[str]) -> list[str]:
    """Finds edges that have a crease value greater than 0.0.

    Args:
        edges (list[str]): A list of edge components to evaluate.

    Returns:
        list[str]: A list of edges with crease values.
    """
    if not edges:
        return []

    crease_values: list[float] = cmds.polyCrease(edges, query=True, value=True)  # type: ignore
    crease_edges: list[str] = [
        edges[i] for i, val in enumerate(crease_values) if val > 0.0
    ]

    return crease_edges
