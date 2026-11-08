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
from typing import Any
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


def promote_attribute(
    ctrl_node: str,
    target_plug: str,
    custom_name: str = "",
    default_value: Any | None = None,
) -> str:
    """Promotes a target attribute onto a controller node and connects it.

    This function reads the configuration (min, max, default, enum values, etc.)
    of a target attribute and creates a matching attribute on the control node.
    It then establishes a connection from the new control attribute to the target.

    Args:
        ctrl_node (str): The Maya node where the new attribute will be created.
        target_plug (str): The target attribute plug to promote and connect to
            (e.g., 'cameraShape1.focalLength').
        custom_name (str, optional): An optional custom long name for the promoted
            attribute. If empty, the target's attribute name is used. Defaults to "".
        default_value (Any | None, optional): An optional initial value to set.
            If None, it copies the current value of the target plug. Defaults to None.

    Returns:
        str: The full plug path of the newly promoted attribute on the controller node
            (e.g., 'ctrl_node.focalLength').
    """
    target_node: str
    target_attr: str
    target_node, target_attr = target_plug.split(".", 1)
    ctrl_attr: str = custom_name if custom_name else target_attr
    ctrl_plug: str = f"{ctrl_node}.{ctrl_attr}"

    if not cmds.attributeQuery(ctrl_attr, node=ctrl_node, exists=True):
        attr_type: str = cmds.getAttr(target_plug, type=True)
        kwargs: dict[str, Any] = {"longName": ctrl_attr, "keyable": True}

        if not custom_name:
            kwargs["niceName"] = cmds.attributeQuery(
                target_attr, node=target_node, niceName=True
            )

        if cmds.attributeQuery(target_attr, node=target_node, minExists=True):
            kwargs["minValue"] = cmds.attributeQuery(
                target_attr, node=target_node, minimum=True
            )[0]  # type: ignore

        if cmds.attributeQuery(target_attr, node=target_node, maxExists=True):
            kwargs["maxValue"] = cmds.attributeQuery(
                target_attr, node=target_node, maximum=True
            )[0]  # type: ignore

        default_vals: list[Any] = cmds.attributeQuery(
            target_attr, node=target_node, listDefault=True
        )  # type: ignore
        if default_vals is not None:
            kwargs["defaultValue"] = default_vals[0]

        if attr_type == "enum":
            kwargs["attributeType"] = "enum"
            enums: list[str] = cmds.attributeQuery(
                target_attr, node=target_node, listEnum=True
            )  # type: ignore
            if enums:
                kwargs["enumName"] = enums[0]
        elif attr_type in ["string", "matrix", "mesh", "nurbsCurve"]:
            kwargs["dataType"] = attr_type
        else:
            kwargs["attributeType"] = attr_type

        cmds.addAttr(ctrl_node, **kwargs)
        if default_value is None:
            cmds.setAttr(ctrl_plug, cmds.getAttr(target_plug))
        else:
            cmds.setAttr(ctrl_plug, default_value)

    if not cmds.isConnected(ctrl_plug, target_plug):
        cmds.connectAttr(ctrl_plug, target_plug, force=True)

    return ctrl_plug
