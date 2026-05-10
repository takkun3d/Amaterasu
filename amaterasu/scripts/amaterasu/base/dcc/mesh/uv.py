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
"""Provides UV-related utilities for Maya meshes."""

from __future__ import annotations
from maya.api import OpenMaya


def get_inverted_uv_faces(faces: list[str]) -> list[str]:
    """Finds faces with inverted UVs based on tangent/binormal cross products.

    Args:
        faces (list[str]): A list of face components to evaluate.

    Returns:
        list[str]: A list of faces that have inverted UVs.
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
        if not dag_path.hasFn(OpenMaya.MFn.kMesh):
            continue

        node_name: str = dag_path.partialPathName()
        fn_mesh: OpenMaya.MFnMesh = OpenMaya.MFnMesh(dag_path)
        it_poly: OpenMaya.MItMeshPolygon = OpenMaya.MItMeshPolygon(
            dag_path, component
        )
        while not it_poly.isDone():
            face_idx: int = it_poly.index()
            if not it_poly.hasUVs():
                it_poly.next()
                continue

            vertex_ids: list[int] = it_poly.getVertices()
            first_vertex_id: int = vertex_ids[0]

            normal: OpenMaya.MVector = fn_mesh.getPolygonNormal(
                face_idx,
                OpenMaya.MSpace.kObject,
            )
            tangent: OpenMaya.MVector = fn_mesh.getFaceVertexTangent(
                face_idx,
                first_vertex_id,
                OpenMaya.MSpace.kObject,
            )
            binormal: OpenMaya.MVector = fn_mesh.getFaceVertexBinormal(
                face_idx,
                first_vertex_id,
                OpenMaya.MSpace.kObject,
            )
            cross: OpenMaya.MVector = tangent ^ binormal
            dot: float = normal * cross
            if dot < 0:
                result_faces.append(f"{node_name}.f[{face_idx}]")

            it_poly.next()

    return result_faces
