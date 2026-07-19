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
import re
from maya import cmds


def to_vertex(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to a vertex list.

    Args:
        sources: The nodes or components to convert (e.g., 'pCube1.f[0]').

    Returns:
        A list of flattened vertex components (e.g., ['pCube1.vtx[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    vertices: list[str] = cmds.polyListComponentConversion(
        *sources, toVertex=True
    )
    return cmds.filterExpand(*vertices, selectionMask=31) or []


def to_edge(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to an edge list.

    Args:
        sources: The nodes or components to convert (e.g., 'pCube1.f[0]').

    Returns:
        A list of flattened edge components (e.g., ['pCube1.e[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    edges: list[str] = cmds.polyListComponentConversion(*sources, toEdge=True)
    return cmds.filterExpand(*edges, selectionMask=32) or []


def to_contained_edge(sources: list[str] | str) -> list[str]:
    """Converts the given nodes or components to a list of internal edges.

    Args:
        sources: The nodes or components to convert (e.g., 'pCube1.f[0]').

    Returns:
        A list of flattened internal edge components (e.g., ['pCube1.e[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    edges: list[str] = cmds.polyListComponentConversion(
        *sources, toEdge=True, internal=True
    )
    return cmds.filterExpand(*edges, selectionMask=32) or []


def to_face(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to a face list.

    Args:
        sources: The nodes or components to convert (e.g., 'pCube1.e[0]').

    Returns:
        A list of flattened face components (e.g., ['pCube1.f[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    faces: list[str] = cmds.polyListComponentConversion(*sources, toFace=True)
    return cmds.filterExpand(*faces, selectionMask=34) or []


def to_uv(sources: str | list[str]) -> list[str]:
    """Converts the given nodes or components to a UV list.

    Args:
        sources: The nodes or components to convert (e.g., 'pCube1.f[0]').

    Returns:
        A list of flattened UV components (e.g., ['pCube1.map[0]', ...]).
    """
    if not sources:
        return []

    if isinstance(sources, str):
        sources = [sources]

    uvs: list[str] = cmds.polyListComponentConversion(*sources, toUV=True)
    return cmds.filterExpand(*uvs, selectionMask=35) or []


def to_border_uv(sources: list[str] | str) -> list[str]:
    """Converts the given nodes or components to a border UV list.

    Args:
        sources: The nodes or components to evaluate for border UVs.

    Returns:
        A list of flattened border UV components.
    """
    if isinstance(sources, str):
        sources = [sources]

    cmds.select(*to_uv(sources))
    cmds.polySelectConstraint(type=0)
    cmds.polySelectConstraint(shell=True, border=False, mode=2)
    cmds.polySelectConstraint(type=0x0010, shell=False, border=True, mode=2)
    cmds.polySelectConstraint(type=0x0010, shell=True, border=False, mode=0)
    cmds.polySelectConstraint(shell=False, border=False, mode=0)  # Reset
    uvs: list[str] = cmds.ls(selection=True)
    cmds.select(*sources)
    return uvs


def to_uv_border_edges(node: str) -> list[str]:
    """Retrieves edge names that exist on UV borders.

    Args:
        node: The mesh node to analyze.

    Returns:
        A list of edge names (e.g., 'mesh.e[0]') that lie on UV borders.
    """
    uv_border_edges: list[str] = []
    edges: list[str] = cmds.ls(f"{node}.e[*]", flatten=True)
    for edge in edges:
        uv_nodes: list[str] = cmds.polyListComponentConversion(edge, toUV=True)
        uvs: list[str] = cmds.filterExpand(*uv_nodes, selectionMask=35)
        if uvs and len(uvs) > 2:
            uv_border_edges.append(edge)

    return uv_border_edges


def group_by_node(components: list[str]) -> dict[str, list[str]]:
    """Groups a list of components by their parent node.

    Args:
        components: A list of component strings (e.g., ['pCube1.e[0]']).

    Returns:
        A dictionary mapping node names to their lists of components.
    """
    result: dict[str, list[str]] = {}
    components = cmds.ls(*components, flatten=True)
    for comp in components:
        node: str = comp.split(".")[0]
        result.setdefault(node, []).append(comp)
    return result


def get_index(component: str) -> int:
    """Extracts the integer index from a component string.

    Args:
        component: A component string (e.g., 'pCube1.e[10]').

    Returns:
        The extracted index, or -1 if no index is found.
    """
    match: re.Match[str] | None = re.search(r"\[(\d+)\]", component)
    return int(match.group(1)) if match else -1
