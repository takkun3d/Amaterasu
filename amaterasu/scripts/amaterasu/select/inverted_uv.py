# ==============================================================================
#
# Select Inverted UV
#
# ==============================================================================
from __future__ import annotations
from maya import OpenMaya
from ..lib import logger

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Inverted UV'
__version__: str = '1.00'
__doc__ = 'Select inverted uv.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main() -> None:
    '''Do it.'''
    selection: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(selection)
    if selection.length() == 0:
        _logger.error('Select polygon to pick out inverted uvs.')
        return

    select_iter: OpenMaya.MItSelectionList = OpenMaya.MItSelectionList(
        selection
    )
    result: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    while not select_iter.isDone():
        dag_path: OpenMaya.MDagPath = OpenMaya.MDagPath()
        component: OpenMaya.MObject = OpenMaya.MObject()
        select_iter.getDagPath(dag_path, component)

        # TODO: Check if it's a mesh
        fn_mesh: OpenMaya.MFnMesh = OpenMaya.MFnMesh(dag_path)
        poly_iter: OpenMaya.MItMeshPolygon = OpenMaya.MItMeshPolygon(
            dag_path, component
        )
        while not poly_iter.isDone():
            normal: OpenMaya.MVector = OpenMaya.MVector()
            fn_mesh.getPolygonNormal(poly_iter.index(), normal)

            tangents: OpenMaya.MFloatVectorArray = OpenMaya.MFloatVectorArray()
            fn_mesh.getFaceVertexTangents(poly_iter.index(), tangents)
            tangent: OpenMaya.MFloatVector = tangents[0]

            binormals: OpenMaya.MFloatVectorArray = OpenMaya.MFloatVectorArray()
            fn_mesh.getFaceVertexBinormals(poly_iter.index(), binormals)
            binormal: OpenMaya.MFloatVector = binormals[0]

            cross: OpenMaya.MFloatVector = tangent ^ binormal
            dot: float = OpenMaya.MFloatVector(normal) * cross

            if dot < 0:
                result.add(dag_path, poly_iter.currentItem())

            poly_iter.next()

        select_iter.next()

    OpenMaya.MGlobal.setActiveSelectionList(result)
    _logger.info('Done.')
