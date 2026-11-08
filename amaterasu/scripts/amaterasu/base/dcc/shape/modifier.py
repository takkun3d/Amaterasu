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
"""Provides utilities for modifying Maya shape evaluation history.

This module contains functions to intercept and modify the geometry of shapes
via Dependency Graph (DG) nodes, such as injecting offset matrices directly
into a curve's drawing pipeline without moving its parent transform.
"""

from __future__ import annotations

from maya import cmds


def insert_transform_geometry(node: str, matrix_plug: str) -> list[str]:
    """Inserts a transformGeometry node into the curve shape's evaluation history.

    This function duplicates the existing shape to use as an intermediate origin,
    and injects a `transformGeometry` node before the final shape generation.
    This allows scaling and offset matrices to be applied directly to the shape's
    visual geometry without affecting the actual transform node's matrix, keeping
    the manipulator gizmos and pivots independent of the shape's orientation.

    Args:
        node (str): The name of the transform node containing the curve shapes.
        matrix_plug (str): The attribute plug (e.g., 'node.outMatrix' or
            'multMatrix.matrixSum') to connect to the transformGeometry's
            transform attribute.

    Returns:
        list[str]: A list of the newly created transformGeometry node names.
    """
    shapes: list[str] = (
        cmds.listRelatives(node, shapes=True, fullPath=True) or []
    )
    valid_shapes: list[str] = [
        s for s in shapes if not cmds.getAttr(f"{s}.intermediateObject")
    ]
    result: list[str] = []
    for shape in valid_shapes:
        shape_name: str = shape.split("|")[-1]
        org_shape: str = cmds.createNode("nurbsCurve")
        cmds.connectAttr(f"{shape}.local", f"{org_shape}.create")
        cmds.refresh()
        cmds.disconnectAttr(f"{shape}.local", f"{org_shape}.create")

        org_shape = cmds.rename(org_shape, f"{shape_name}Org")
        org_trans: str = cmds.listRelatives(org_shape, parent=True, path=True)[
            0
        ]

        org_shape = cmds.parent(org_shape, node, shape=True, relative=True)[0]
        cmds.delete(org_trans)
        cmds.setAttr(f"{org_shape}.intermediateObject", True)

        tg_node: str = cmds.createNode(
            "transformGeometry", name=f"{shape_name}_tg"
        )
        cmds.connectAttr(f"{org_shape}.local", f"{tg_node}.inputGeometry")
        cmds.connectAttr(f"{tg_node}.outputGeometry", f"{shape}.create")
        cmds.connectAttr(matrix_plug, f"{tg_node}.transform")
        result.append(tg_node)

    return result
