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
"""Decomposes the rotation of selected objects into separate X, Y, Z angles."""

from __future__ import annotations

from dataclasses import dataclass

from maya import cmds

from amaterasu.base import dcc, utils

__product__: str = "Decompose Rotate"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)

OP_CROSS_PRODUCT: int = 2
OP_GREATER_THAN: int = 2
OP_LESS_THAN: int = 4


@dataclass(frozen=True)
class Plane:
    """Configuration values for a rotation decomposition plane.

    Attributes:
        name (str): The plane identifier (e.g., "XY", "YZ", "XZ").
        vector (tuple[float, float, float]): The reference base vector.
        axis (tuple[float, float, float]): The axis mask applied to the
            rotated vector.
        axis_attr (str): The rotation axis attribute name ("X", "Y", or "Z").
        index_color (int): The Maya viewport wireframe color index.
    """

    name: str
    vector: tuple[float, float, float]
    axis: tuple[float, float, float]
    axis_attr: str
    index_color: int


PLANES: tuple[Plane, ...] = (
    Plane("XY", (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), "Z", 13),
    Plane("YZ", (0.0, 1.0, 0.0), (0.0, 1.0, 1.0), "X", 14),
    Plane("XZ", (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), "Y", 6),
)


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig or dcc.node).
def extract_base_name(node: str) -> str:
    """Extracts the short base name from a DAG path or namespaced node.

    Args:
        node (str): The full or partial node name.

    Returns:
        str: The extracted base name prefix.
    """
    short_name: str = node.split("|")[-1].split(":")[-1]
    return short_name.split("_")[0]


def create_plane_control(
    base_name: str,
    plane: Plane,
    src_transform: str,
    parent: str = "",
) -> str:
    """Creates a rig control for a specific rotation plane (XY, YZ, or XZ).

    Args:
        base_name (str): The naming prefix for created nodes.
        plane (Plane): The plane specification defining axes and color.
        src_transform (str): The source transform or joint node name.
        parent (str, optional): The parent node for the created locator.
            Defaults to "".

    Returns:
        str: The name of the created locator node.
    """
    plane_name: str = plane.name
    vector: tuple[float, float, float] = plane.vector
    axis: tuple[float, float, float] = plane.axis
    axis_attr: str = plane.axis_attr
    index_color: int = plane.index_color

    rotate_vector: str = cmds.createNode(
        "rotateVector", name=f"{base_name}Vector{plane_name}_rv"
    )
    cmds.setAttr(f"{rotate_vector}.input", *vector, type="double3")
    cmds.connectAttr(f"{src_transform}.rotate", f"{rotate_vector}.rotate")
    cmds.connectAttr(
        f"{src_transform}.rotateOrder", f"{rotate_vector}.rotateOrder"
    )

    axis_filter: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}AxisFilter{plane_name}_md"
    )
    cmds.setAttr(f"{axis_filter}.input2", *axis, type="double3")
    cmds.connectAttr(f"{rotate_vector}.output", f"{axis_filter}.input1")

    angle: str = cmds.createNode(
        "angleBetween", name=f"{base_name}Angle{plane_name}_ab"
    )
    cmds.setAttr(f"{angle}.vector1", *vector, type="double3")
    cmds.connectAttr(f"{axis_filter}.output", f"{angle}.vector2")

    cross: str = cmds.createNode(
        "vectorProduct", name=f"{base_name}Cross{plane_name}_vp"
    )
    cmds.setAttr(f"{cross}.operation", OP_CROSS_PRODUCT)
    cmds.setAttr(f"{cross}.input1", *vector, type="double3")
    cmds.connectAttr(f"{axis_filter}.output", f"{cross}.input2")

    direction: str = cmds.createNode(
        "condition", name=f"{base_name}Direction{plane_name}_condition"
    )
    cmds.setAttr(f"{direction}.operation", OP_GREATER_THAN)
    cmds.setAttr(f"{direction}.colorIfTrue", 1, 0, 0, type="double3")
    cmds.setAttr(f"{direction}.colorIfFalse", -1, 0, 0, type="double3")
    cmds.connectAttr(f"{cross}.output{axis_attr}", f"{direction}.firstTerm")

    filtering_0: str = cmds.createNode(
        "condition", name=f"{base_name}Filtering0{plane_name}_condition"
    )
    cmds.setAttr(f"{filtering_0}.operation", OP_LESS_THAN)
    cmds.setAttr(f"{filtering_0}.secondTerm", 0.001)
    cmds.setAttr(f"{filtering_0}.colorIfTrue", 1, 0, 0, type="double3")
    cmds.setAttr(f"{filtering_0}.colorIfFalse", -1, 0, 0, type="double3")
    cmds.connectAttr(f"{angle}.angle", f"{filtering_0}.firstTerm")
    cmds.connectAttr(f"{direction}.outColorR", f"{filtering_0}.colorIfFalseR")

    filtering_180: str = cmds.createNode(
        "condition", name=f"{base_name}Filtering180{plane_name}_condition"
    )
    cmds.setAttr(f"{filtering_180}.operation", OP_GREATER_THAN)
    cmds.setAttr(f"{filtering_180}.secondTerm", 179.999)
    cmds.setAttr(f"{filtering_180}.colorIfTrue", 1, 0, 0, type="double3")
    cmds.setAttr(f"{filtering_180}.colorIfFalse", -1, 0, 0, type="double3")
    cmds.connectAttr(f"{angle}.angle", f"{filtering_180}.firstTerm")
    cmds.connectAttr(
        f"{filtering_0}.outColorR", f"{filtering_180}.colorIfFalseR"
    )

    rotate: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}Rotate{plane_name}_md"
    )
    cmds.connectAttr(f"{filtering_180}.outColorR", f"{rotate}.input1X")
    cmds.connectAttr(f"{angle}.angle", f"{rotate}.input2X")

    locator: str = cmds.spaceLocator(name=f"{base_name}{plane_name}_loc")[0]  # type: ignore
    if parent:
        locator = cmds.parent(locator, parent)[0]
        cmds.setAttr(f"{locator}.translate", 0, 0, 0, type="double3")
        cmds.setAttr(f"{locator}.rotate", 0, 0, 0, type="double3")
        cmds.setAttr(f"{locator}.scale", 1, 1, 1, type="double3")

    shape_size: list[float] = [i * 5.0 for i in vector]
    cmds.setAttr(f"{locator}.localPosition", *shape_size, type="double3")
    cmds.setAttr(f"{locator}.localScale", *shape_size, type="double3")
    cmds.connectAttr(f"{rotate}.outputX", f"{locator}.rotate{axis_attr}")
    dcc.node.set_drawing_index_color(index_color, [locator])
    dcc.node.hide_history([locator])

    return locator


def create_offset_control(base_name: str, src_transform: str) -> str:
    """Creates an offset transform group matching position and joint orient.

    Args:
        base_name (str): The naming prefix for created nodes.
        src_transform (str): The source transform or joint node name.

    Returns:
        str: The name of the created offset transform node.
    """

    offset_cmtx: str = cmds.createNode(
        "composeMatrix", name=f"{base_name}Offset_composeMtx"
    )
    cmds.connectAttr(
        f"{src_transform}.translate", f"{offset_cmtx}.inputTranslate"
    )
    cmds.connectAttr(f"{src_transform}.scale", f"{offset_cmtx}.inputScale")
    cmds.connectAttr(
        f"{src_transform}.rotateOrder", f"{offset_cmtx}.inputRotateOrder"
    )

    orient_cmtx: str = ""
    if cmds.objectType(src_transform) == "joint":
        orient_cmtx = cmds.createNode(
            "composeMatrix", name=f"{base_name}Orient_composeMtx"
        )
        cmds.connectAttr(
            f"{src_transform}.jointOrient", f"{orient_cmtx}.inputRotate"
        )
        cmds.connectAttr(
            f"{src_transform}.rotateOrder", f"{orient_cmtx}.inputRotateOrder"
        )

    offset_mmtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}Offset_multMtx"
    )
    matrix_index: int = 0
    if orient_cmtx:
        cmds.connectAttr(
            f"{orient_cmtx}.outputMatrix",
            f"{offset_mmtx}.matrixIn[{matrix_index}]",
        )
        matrix_index += 1

    cmds.connectAttr(
        f"{offset_cmtx}.outputMatrix",
        f"{offset_mmtx}.matrixIn[{matrix_index}]",
    )

    offset_dmtx: str = cmds.createNode(
        "decomposeMatrix", name=f"{base_name}Offset_decomposeMtx"
    )
    cmds.connectAttr(f"{offset_mmtx}.matrixSum", f"{offset_dmtx}.inputMatrix")

    parents: list[str] = (
        cmds.listRelatives(src_transform, parent=True, path=True) or []
    )
    parent: str = parents[0] if parents else "|"

    offset_transform: str = cmds.createNode(
        "transform", name=f"{base_name}Plane_offset", parent=parent
    )
    cmds.connectAttr(
        f"{offset_dmtx}.outputTranslate", f"{offset_transform}.translate"
    )
    cmds.connectAttr(
        f"{offset_dmtx}.outputRotate", f"{offset_transform}.rotate"
    )
    cmds.connectAttr(f"{offset_dmtx}.outputScale", f"{offset_transform}.scale")
    cmds.connectAttr(f"{offset_dmtx}.outputShear", f"{offset_transform}.shear")
    dcc.node.hide_history([offset_transform])

    return offset_transform


def main(nodes: list[str] | None = None) -> None:
    """Runs the rotation decomposition setup on the specified or selected nodes.

    Args:
        nodes (list[str] | None, optional): Target transform or joint nodes.
            Uses the current Maya selection if None. Defaults to None.
    """
    if not nodes:
        nodes = cmds.ls(selection=True)

    if not nodes:
        _logger.error("Select a transform or joint to decompose its rotation.")
        return

    for node in nodes:
        base_name: str = extract_base_name(node)
        offset_transform: str = create_offset_control(base_name, node)
        for plane in PLANES:
            create_plane_control(base_name, plane, node, offset_transform)

    _logger.info("Done.")
