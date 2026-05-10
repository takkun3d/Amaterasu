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
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
"""Unfreeze transformations algorithms and matrix calculations."""

from __future__ import annotations
import math
from maya import cmds
from maya.api import OpenMaya
from amaterasu.base import utils


def __get_mesh_fn(node: str) -> OpenMaya.MFnMesh:
    """Retrieves the OpenMaya.MFnMesh object for a given node.

    Args:
        node (str): The name of the mesh node.

    Returns:
        OpenMaya.MFnMesh: The function set for the specified mesh.
    """
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(node)
    return OpenMaya.MFnMesh(selection_list.getDagPath(0))


def __get_point(node: str) -> OpenMaya.MPoint | None:
    """Gets the world-space position of a given node or component.

    Supports both transforms and vertices by using cmds.xform.

    Args:
        node (str): The name of the node or component (e.g., vertex).

    Returns:
        OpenMaya.MPoint | None: The world-space position as an MPoint,
            or None if it fails.
    """
    try:
        # Use xform to support both vertices and transforms/locators
        pos: list[float] = cmds.xform(
            node, query=True, translation=True, worldSpace=True
        )  # type: ignore
        return OpenMaya.MPoint(pos[0], pos[1], pos[2])

    except RuntimeError:
        return None

    except TypeError:
        return None


def __get_matrix_4_points(
    mesh_fn: OpenMaya.MFnMesh,
    vtx_ids: tuple[int, int, int, int],
    space: int,
) -> OpenMaya.MMatrix:
    """Constructs an OpenMaya.MMatrix from four vertex positions.

    Args:
        mesh_fn (OpenMaya.MFnMesh): The function set of the mesh.
        vtx_ids (tuple[int, int, int, int]): A tuple of four vertex IDs.
        space (int): The coordinate space to query
            (e.g., OpenMaya.MSpace.kObject).

    Returns:
        OpenMaya.MMatrix: The resulting 4x4 transformation matrix.
    """
    points: list[OpenMaya.MPoint] = [
        mesh_fn.getPoint(i, space) for i in vtx_ids
    ]
    return OpenMaya.MMatrix(
        [
            [points[0].x, points[0].y, points[0].z, 1],
            [points[1].x, points[1].y, points[1].z, 1],
            [points[2].x, points[2].y, points[2].z, 1],
            [points[3].x, points[3].y, points[3].z, 1],
        ]
    )


def __get_matrix_3_points(
    mesh_fn: OpenMaya.MFnMesh,
    vtx_ids: tuple[int, int, int, OpenMaya.MPoint],
    space: int,
) -> OpenMaya.MMatrix:
    """Constructs an OpenMaya.MMatrix from three vertices and a calculated virtual point.

    Calculates a local normal to generate a fourth virtual point for matrix construction.

    Args:
        mesh_fn (OpenMaya.MFnMesh): The function set of the mesh.
        vtx_ids (tuple[int, int, int, OpenMaya.MPoint]): A tuple of three vertex IDs and a virtual point.
        space (int): The coordinate space to query.

    Returns:
        OpenMaya.MMatrix: The resulting 4x4 transformation matrix.
    """
    points: list[OpenMaya.MPoint] = [
        mesh_fn.getPoint(i, space) for i in vtx_ids[0:3]
    ]

    p_0: OpenMaya.MPoint = points[0]
    p_1: OpenMaya.MPoint = points[1]
    p_2: OpenMaya.MPoint = points[2]
    p_3: OpenMaya.MPoint = OpenMaya.MPoint()

    if space == OpenMaya.MSpace.kObject:
        # Use the virtual point stored in vtx_ids for Source
        p_3 = vtx_ids[3]
    else:
        # Recalculate virtual point for Destination to match local normal
        vector_ab: OpenMaya.MVector = (p_1 - p_0).normal()
        vector_ac: OpenMaya.MVector = (p_2 - p_0).normal()
        normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()
        p_3 = p_0 + normal

    return OpenMaya.MMatrix(
        [
            [p_0.x, p_0.y, p_0.z, 1],
            [p_1.x, p_1.y, p_1.z, 1],
            [p_2.x, p_2.y, p_2.z, 1],
            [p_3.x, p_3.y, p_3.z, 1],
        ]
    )


def __apply_matrix(
    dst: str,
    target_world_matrix: OpenMaya.MMatrix,
    pivots: list[float],
    rotate_order: int,
    rotate_axis: tuple[float, float, float],
    handle: tuple[float, float, float],
) -> None:
    """Applies a target world matrix to a destination node with proper decomposition.

    Handles inverse matrix application, freezing, and restoring pivot, rotate order,
    and handle data to accurately extract and set transformations.

    Args:
        dst (str): The destination node name.
        target_world_matrix (OpenMaya.MMatrix): The target matrix to apply.
        pivots (list[float]): The original rotate and scale pivots (6 floats).
        rotate_order (int): The original rotation order index.
        rotate_axis (tuple[float, float, float]): The original rotation axis.
        handle (tuple[float, float, float]): The original selection handle offsets.
    """
    # Apply Inverse Matrix
    inverse_matrix: OpenMaya.MMatrix = target_world_matrix.inverse()
    cmds.xform(dst, matrix=[v for v in inverse_matrix], worldSpace=True)  # type: ignore

    # Freeze And Reset Transformations.
    cmds.makeIdentity(dst, apply=True, translate=True, rotate=True, scale=True)
    cmds.makeIdentity(dst, apply=False, translate=True, rotate=True, scale=True)

    # Matrix Decomposition
    t_mtx: OpenMaya.MTransformationMatrix = OpenMaya.MTransformationMatrix(
        target_world_matrix
    )

    # Translate: Translate = Translation - Pivot + (Pivot * Target Matrix)
    translation: OpenMaya.MVector = t_mtx.translation(
        OpenMaya.MSpace.kTransform
    )
    pivot: OpenMaya.MVector = OpenMaya.MVector(pivots[0], pivots[1], pivots[2])
    transformed_pivot: OpenMaya.MVector = pivot * target_world_matrix
    translation = translation - pivot + transformed_pivot
    translate: list[float] = [
        translation.x,
        translation.y,
        translation.z,
    ]

    # Rotate: Reorder original rotate order.
    rotation: OpenMaya.MEulerRotation = t_mtx.rotation()
    rotation = rotation.reorderIt(rotate_order)
    rotate: list[float] = [
        math.degrees(rotation.x),
        math.degrees(rotation.y),
        math.degrees(rotation.z),
    ]

    scale: list[float] = t_mtx.scale(OpenMaya.MSpace.kTransform)
    shear: list[float] = t_mtx.shear(OpenMaya.MSpace.kTransform)

    # Restore node settings.
    cmds.xform(dst, rotatePivot=pivots[0:3], objectSpace=True)  # type: ignore
    cmds.xform(dst, scalePivot=pivots[3:6], objectSpace=True)  # type: ignore
    cmds.setAttr(f'{dst}.rotateOrder', rotate_order)
    cmds.setAttr(f'{dst}.rotateAxis', *rotate_axis)
    cmds.setAttr(f'{dst}.selectHandle', *handle)

    # Apply results.
    cmds.setAttr(f'{dst}.translate', *translate)
    cmds.setAttr(f'{dst}.rotate', *rotate)
    cmds.setAttr(f'{dst}.scale', *scale)
    cmds.setAttr(f'{dst}.shear', *shear)


def __find_best_stable_4_points(
    mesh_fn: OpenMaya.MFnMesh,
) -> tuple[int, int, int, int] | None:
    """Finds the four most stable vertices to minimize calculation errors.

    The algorithm searches for points that maximize distances from each other,
    forming the largest possible volume (tetrahedron) for stable matrix calculation.

    Args:
        mesh_fn (OpenMaya.MFnMesh): The function set of the mesh to analyze.

    Returns:
        tuple[int, int, int, int] | None: A tuple of four vertex indices,
            or None if validation fails.
    """
    # Check num of points.
    points: OpenMaya.MPointArray = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
    num_points: int = len(points)
    if num_points < 4:
        return None

    index_a: int = -1
    index_b: int = -1
    index_c: int = -1
    index_d: int = -1
    max_dist_square: float = -1.0

    # Find Point A: Furthest point from the first point.
    point_0: OpenMaya.MPoint = points[0]
    for i in range(num_points):
        distance_to: float = point_0.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_a = i

    # Find Point B: Furthest point from Point A.
    point_a: OpenMaya.MPoint = points[index_a]
    max_dist_square = -1.0
    for i in range(num_points):
        distance_to = point_a.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_b = i

    # Find Point C: Furthest point from Line Segment AB.
    point_b: OpenMaya.MPoint = points[index_b]
    max_dist_square = -1.0
    vector_ab: OpenMaya.MVector = (point_b - point_a).normal()
    for i in range(num_points):
        vec_ap: OpenMaya.MPoint = points[i] - point_a
        dist_sq: float = (vector_ab ^ vec_ap).length()
        if dist_sq > max_dist_square:
            max_dist_square = dist_sq
            index_c = i

    # Find Point D: Furthest point from Plane ABC.
    point_c: OpenMaya.MPoint = points[index_c]
    max_height: float = -1.0
    vector_ac: OpenMaya.MVector = (point_c - point_a).normal()
    normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()
    for i in range(num_points):
        vec_ap = points[i] - point_a
        height: float = abs(vec_ap * normal)
        if height > max_height:
            max_height = height
            index_d = i

    # Check max height.
    if max_height < 0.000001:
        return None

    # Check index.
    indexes: tuple[int, int, int, int] = (index_a, index_b, index_c, index_d)
    if len(indexes) != len(set(indexes)):
        return None

    return indexes


def __find_best_stable_3_points(
    mesh_fn: OpenMaya.MFnMesh,
) -> tuple[int, int, int, OpenMaya.MPoint] | None:
    """Finds the three most stable vertices and calculates a virtual normal point.

    The algorithm selects points to form the largest possible triangle and
    generates a fourth virtual point along its normal vector for matrix stability.

    Args:
        mesh_fn (OpenMaya.MFnMesh): The function set of the mesh to analyze.

    Returns:
        tuple[int, int, int, OpenMaya.MPoint] | None: A tuple of three vertex indices and the virtual point,
            or None if validation fails.
    """
    # Check num of points.
    points: OpenMaya.MPointArray = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
    num_points: int = len(points)
    if num_points < 3:
        return None

    index_a: int = -1
    index_b: int = -1
    index_c: int = -1
    max_dist_square: float = -1.0

    # Find Point A: Furthest point from the first point.
    point_0: OpenMaya.MPoint = points[0]
    for i in range(num_points):
        distance_to: float = point_0.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_a = i

    # Find Point B: Furthest point from Point A.
    point_a: OpenMaya.MPoint = points[index_a]
    max_dist_square = -1.0
    for i in range(num_points):
        distance_to = point_a.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_b = i

    # Find Point C: Furthest point from Line Segment AB.
    point_b: OpenMaya.MPoint = points[index_b]
    max_dist_square = -1.0
    vector_ab: OpenMaya.MVector = (point_b - point_a).normal()
    for i in range(num_points):
        vec_ap: OpenMaya.MPoint = points[i] - point_a
        dist_sq: float = (vector_ab ^ vec_ap).length()
        if dist_sq > max_dist_square:
            max_dist_square = dist_sq
            index_c = i

    # Find Point D: Furthest point from Plane ABC.
    point_c: OpenMaya.MPoint = points[index_c]
    vector_ac: OpenMaya.MVector = (point_c - point_a).normal()
    normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()

    point_d: OpenMaya.MPoint = point_a + normal

    # Check index.
    indexes: tuple[int, int, int] = (index_a, index_b, index_c)
    if len(indexes) != len(set(indexes)):
        return None

    return (index_a, index_b, index_c, point_d)


def apply_affine_transformation(src: str, dsts: list[str]) -> utils.Result:
    """Applies an affine (solid) transformation to restore frozen models.

    Uses a 4-point matrix matching algorithm between the source and destination meshes.

    Args:
        src (str): The reference source node.
        dsts (list[str]): A list of destination nodes to unfreeze.

    Returns:
        utils.Result: The execution result containing info or failure logs.
    """

    result: utils.Result = utils.Result()
    src_fn: OpenMaya.MFnMesh = __get_mesh_fn(src)
    vtx_ids: tuple[int, int, int, int] | None = __find_best_stable_4_points(
        src_fn
    )
    if not vtx_ids:
        result.set_error(f"Failed to find valid points for calculation: {src}")
        return result

    # Get Source Transform Informations
    pivots: list[float] = cmds.xform(
        src, query=True, pivots=True, objectSpace=True
    )  # type: ignore

    src_inverse_mtx: OpenMaya.MMatrix = __get_matrix_4_points(
        src_fn, vtx_ids, OpenMaya.MSpace.kObject
    ).inverse()

    rotate_order: int = cmds.getAttr(f'{src}.rotateOrder')
    rotate_axis: tuple[float, float, float] = cmds.getAttr(f'{src}.rotateAxis')[
        0
    ]
    handle: tuple[float, float, float] = cmds.getAttr(f'{src}.selectHandle')[0]

    # Process targets
    for dst in dsts:
        dst_fn: OpenMaya.MFnMesh = __get_mesh_fn(dst)
        if src_fn.numVertices != dst_fn.numVertices:
            result.add_failure(dst, "Topology Mismatch")
            continue

        # Reset
        cmds.makeIdentity(
            dst, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            dst, apply=False, translate=True, rotate=True, scale=True
        )

        # Calculate Affine Matrix (Local -> World)
        dst_matrix: OpenMaya.MMatrix = __get_matrix_4_points(
            dst_fn, vtx_ids, OpenMaya.MSpace.kWorld
        )

        # Calculate the Target World Matrix
        target_world_matrix: OpenMaya.MMatrix = src_inverse_mtx * dst_matrix

        # Apply using common function
        __apply_matrix(
            dst,
            target_world_matrix,
            pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return result


def apply_triangle_transformation(src: str, dsts: list[str]) -> utils.Result:
    """Applies a planar (triangle) transformation to restore frozen models.

    Uses a 3-point and calculated normal vector matching algorithm between
    the source and destination meshes.

    Args:
        src (str): The reference source node.
        dsts (list[str]): A list of destination nodes to unfreeze.

    Returns:
        utils.Result: The execution result containing info or failure logs.
    """
    result: utils.Result = utils.Result()
    src_fn: OpenMaya.MFnMesh = __get_mesh_fn(src)
    vtx_ids: tuple[int, int, int, OpenMaya.MPoint] | None = (
        __find_best_stable_3_points(src_fn)
    )
    if not vtx_ids:
        result.set_error(f"Failed to find valid points for calculation: {src}")
        return result

    # Get Source Transform Informations
    pivots: list[float] = cmds.xform(
        src, query=True, pivots=True, objectSpace=True
    )  # type: ignore

    src_inverse_mtx: OpenMaya.MMatrix = __get_matrix_3_points(
        src_fn, vtx_ids, OpenMaya.MSpace.kObject
    ).inverse()

    rotate_order: int = cmds.getAttr(f'{src}.rotateOrder')
    rotate_axis: tuple[float, float, float] = cmds.getAttr(f'{src}.rotateAxis')[
        0
    ]
    handle: tuple[float, float, float] = cmds.getAttr(f'{src}.selectHandle')[0]

    # Process targets
    for dst in dsts:
        dst_fn: OpenMaya.MFnMesh = __get_mesh_fn(dst)
        if src_fn.numVertices != dst_fn.numVertices:
            result.add_failure(dst, "Topology Mismatch")
            continue

        # Reset
        cmds.makeIdentity(
            dst, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            dst, apply=False, translate=True, rotate=True, scale=True
        )

        # Calculate Affine Matrix (Local -> World)
        dst_matrix: OpenMaya.MMatrix = __get_matrix_3_points(
            dst_fn, vtx_ids, OpenMaya.MSpace.kWorld
        )

        # Calculate the Target World Matrix
        target_world_matrix: OpenMaya.MMatrix = src_inverse_mtx * dst_matrix

        # Apply using common function
        __apply_matrix(
            dst,
            target_world_matrix,
            pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return result


def apply_align_to_components(
    pivot_node: str, aim_node: str, up_node: str, dsts: list[str]
) -> utils.Result:
    """Applies a manual alignment transformation using Pivot, Aim, and Up components.

    Aligns the X-axis to the Aim target and the Y-axis to the Up target relative to the Pivot.

    Args:
        pivot_node (str): The node or component representing the origin pivot.
        aim_node (str): The node or component representing the X+ aim target.
        up_node (str): The node or component representing the Y+ up target.
        dsts (list[str]): A list of destination nodes to align.

    Returns:
        utils.Result: The execution result containing info or failure logs.
    """
    result: utils.Result = utils.Result()

    # Get Coordinates
    p: OpenMaya.MPoint | None = __get_point(pivot_node)
    a: OpenMaya.MPoint | None = __get_point(aim_node)
    u: OpenMaya.MPoint | None = __get_point(up_node)

    if not p:
        result.set_error(f'Failed to get coordinates from selections : {p}')
        return result

    if not a:
        result.set_error(f'Failed to get coordinates from selections : {a}')
        return result

    if not u:
        result.set_error('Failed to get coordinates from selections : {u}')
        return result

    # Process targets
    for dst in dsts:

        # Reset
        cmds.makeIdentity(
            dst, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            dst, apply=False, translate=True, rotate=True, scale=True
        )

        # Construct Matrix (Aim=X, Up=Y)
        vec_x: OpenMaya.MVector = (a - p).normal()
        vec_up_temp: OpenMaya.MVector = (u - p).normal()
        vec_z: OpenMaya.MVector = (vec_x ^ vec_up_temp).normal()
        vec_y: OpenMaya.MVector = (vec_z ^ vec_x).normal()

        target_world_matrix = OpenMaya.MMatrix(
            [
                [vec_x.x, vec_x.y, vec_x.z, 0],
                [vec_y.x, vec_y.y, vec_y.z, 0],
                [vec_z.x, vec_z.y, vec_z.z, 0],
                [p.x, p.y, p.z, 1],
            ]
        )

        # Get current node settings to preserve them
        rotate_order: int = cmds.getAttr(f'{dst}.rotateOrder')
        rotate_axis: tuple[float, float, float] = cmds.getAttr(
            f'{dst}.rotateAxis'
        )[0]
        handle: tuple[float, float, float] = cmds.getAttr(
            f'{dst}.selectHandle'
        )[0]

        # Resetting the Local Pivot to 0,0,0.
        zero_pivots: list[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        __apply_matrix(
            dst,
            target_world_matrix,
            zero_pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return result
