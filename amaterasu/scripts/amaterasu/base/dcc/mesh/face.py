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
"""Provides face-related utilities for Maya meshes."""

from __future__ import annotations
from maya.api import OpenMaya
from maya import cmds
from amaterasu.base.dcc.mesh import component


def get_hard_edge_shells(faces: list[str]) -> list[str]:
    """Expands the given faces to their hard edge boundaries
        using OpenMaya for extreme speed.

    Args:
        faces (list[str]): A list of face components to start from.

    Returns:
        list[str]: A list of faces within the hard edge shell.
    """
    if not faces:
        return []

    sel_list: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    for f in faces:
        sel_list.add(f)

    result_faces: list[str] = []
    for i in range(sel_list.length()):
        dag_path: OpenMaya.MDagPath
        component: OpenMaya.MObject
        dag_path, component = sel_list.getComponent(i)

        if (
            component.isNull()
            or component.apiType() != OpenMaya.MFn.kMeshPolygonComponent
        ):
            continue

        node_name: str = dag_path.partialPathName()
        it_poly: OpenMaya.MItMeshPolygon = OpenMaya.MItMeshPolygon(dag_path)
        it_edge: OpenMaya.MItMeshEdge = OpenMaya.MItMeshEdge(dag_path)
        fn_comp: OpenMaya.MFnSingleIndexedComponent = (
            OpenMaya.MFnSingleIndexedComponent(component)
        )

        start_faces: list[int] = fn_comp.getElements()
        stack: list[int] = list(start_faces)
        visited: set[int] = set(start_faces)
        while stack:
            current_face: int = stack.pop()
            result_faces.append(f"{node_name}.f[{current_face}]")

            it_poly.setIndex(current_face)
            for edge_id in it_poly.getEdges():
                it_edge.setIndex(edge_id)
                if not it_edge.isSmooth:
                    continue

                for next_face in it_edge.getConnectedFaces():
                    if next_face not in visited:
                        visited.add(next_face)
                        stack.append(next_face)

    return result_faces


def duplicate_faces(faces: list[str]) -> list[str]:
    """Duplicates specified polygon faces as a new mesh.

    This function groups selected faces by their parent geometry, duplicates
    the original mesh, and removes all faces except for those specified in
    the input list.

    Args:
        faces: A list of face component strings (e.g., ["pCube1.f[0]"]).

    Returns:
        A list of new mesh names created during the operation.
    """
    result: list[str] = []
    grouped_faces: dict[str, list[str]] = component.group_by_node(faces)
    for node, face_list in grouped_faces.items():
        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        keep_faces: list[str] = [
            f"{new_node}.{f.split('.')[-1]}" for f in face_list
        ]

        cmds.select(f"{new_node}.f[*]")
        cmds.select(*keep_faces, deselect=True)

        targets_to_delete: list[str] = cmds.ls(selection=True)
        if targets_to_delete:
            cmds.delete(*targets_to_delete)
            result.append(new_node)

        else:
            cmds.delete(new_node)

    if result:
        cmds.select(*result)

    return result


def extract_faces(faces: list[str]) -> list[str]:
    """Extracts specified polygon faces into a new mesh.

    Groups selected faces by their parent geometry, duplicates the mesh,
    and removes the extracted faces from the original geometry while
    cleaning up the new mesh to retain only the extracted components.

    Args:
        faces: A list of face component strings (e.g., ["pCube1.f[0]"]).

    Returns:
        A list of new mesh names created during the operation.
    """
    result: list[str] = []
    grouped_faces: dict[str, list[str]] = component.group_by_node(faces)
    for node, face_list in grouped_faces.items():
        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        keep_faces: list[str] = [
            f"{new_node}.{f.split('.')[-1]}" for f in face_list
        ]
        cmds.select(f"{new_node}.f[*]")
        cmds.select(*keep_faces, deselect=True)

        targets_to_delete: list[str] = cmds.ls(selection=True)
        if targets_to_delete:
            cmds.delete(*targets_to_delete)

        cmds.delete(*face_list)
        result.append(new_node)

    if result:
        cmds.select(*result)

    return result
