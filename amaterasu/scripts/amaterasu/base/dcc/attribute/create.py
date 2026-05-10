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
"""Attribute creation utilities for Maya."""

from __future__ import annotations
from typing import Any
from maya import cmds

VECTOR_ATTR_TYPE: tuple[str, str, str] = ("X", "Y", "Z")
COLOR_ATTR_TYPE: tuple[str, str, str] = ("R", "G", "B")


def add_integer(
    node: str,
    name: str,
    min_val: int | None = None,
    max_val: int | None = None,
    default_val: int | None = None,
    **kwargs: Any,
) -> None:
    """Adds an integer (long) attribute to the specified node.

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the attribute to add.
        min_val (int | None, optional): The minimum value of the attribute.
            Defaults to None.
        max_val (int | None, optional): The maximum value of the attribute.
            Defaults to None.
        default_val (int | None, optional): The default value of the attribute.
            Defaults to None.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    flags: dict[str, Any] = {"attributeType": "long"}
    if min_val is not None:
        flags["minValue"] = min_val

    if max_val is not None:
        flags["maxValue"] = max_val

    if default_val is not None:
        flags["defaultValue"] = default_val

    cmds.addAttr(node, longName=name, **flags)
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)


def add_float(
    node: str,
    name: str,
    min_val: float | None = None,
    max_val: float | None = None,
    default_val: float | None = None,
    **kwargs: Any,
) -> None:
    """Adds a float (double) attribute to the specified node.

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the attribute to add.
        min_val (float | None, optional): The minimum value of the attribute.
            Defaults to None.
        max_val (float | None, optional): The maximum value of the attribute.
            Defaults to None.
        default_val (float | None, optional): The default value of the attribute.
            Defaults to None.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    flags: dict[str, Any] = {"attributeType": "double"}
    if min_val is not None:
        flags["minValue"] = min_val

    if max_val is not None:
        flags["maxValue"] = max_val

    if default_val is not None:
        flags["defaultValue"] = default_val

    cmds.addAttr(node, longName=name, **flags)
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)


def add_string(
    node: str, name: str, default_val: str = "", **kwargs: Any
) -> None:
    """Adds a string attribute to the specified node.

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the attribute to add.
        default_val (str, optional): The default string value. Defaults to "".
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    cmds.addAttr(node, longName=name, dataType="string")
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)

    if default_val:
        cmds.setAttr(f"{node}.{name}", default_val, type="string")


def add_boolean(
    node: str, name: str, default_val: bool = False, **kwargs: Any
) -> None:
    """Adds a boolean attribute to the specified node.

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the attribute to add.
        default_val (bool, optional): The default boolean value.
            Defaults to False.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    cmds.addAttr(node, longName=name, attributeType="bool")
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)

    cmds.setAttr(f"{node}.{name}", default_val)


def add_enum(
    node: str, name: str, enum_names: str, default_val: int = 0, **kwargs: Any
) -> None:
    """Adds an enum attribute to the specified node.

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the attribute to add.
        enum_names (str): A colon-separated string of enum values
            (e.g., "Red:Green:Blue").
        default_val (int, optional): The default index of the enum.
            Defaults to 0.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    cmds.addAttr(node, longName=name, attributeType="enum", enumName=enum_names)
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)

    if default_val:
        cmds.setAttr(f"{node}.{name}", default_val)


def add_vector(node: str, name: str, **kwargs: Any) -> None:
    """Adds a vector (double3) attribute to the specified node.

    Creates a parent double3 attribute and three child double attributes (X, Y, Z).

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the base vector attribute.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    cmds.addAttr(node, longName=name, attributeType="double3")
    for xyz in VECTOR_ATTR_TYPE:
        cmds.addAttr(
            node, longName=f"{name}{xyz}", parent=name, attributeType="double"
        )

    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)

    for xyz in VECTOR_ATTR_TYPE:
        if kwargs:
            cmds.setAttr(f"{node}.{name}{xyz}", edit=True, **kwargs)


def add_color(node: str, name: str, **kwargs: Any) -> None:
    """Adds a color (float3) attribute to the specified node.

    Creates a parent float3 attribute used as color and three child float attributes (R, G, B).

    Args:
        node (str): The name of the Maya node.
        name (str): The long name of the base color attribute.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., keyable=True).
    """
    cmds.addAttr(node, longName=name, attributeType="float3", usedAsColor=True)
    for rgb in COLOR_ATTR_TYPE:
        cmds.addAttr(
            node, longName=f"{name}{rgb}", parent=name, attributeType="float"
        )

    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)

    for rgb in COLOR_ATTR_TYPE:
        if kwargs:
            cmds.setAttr(f"{node}.{name}{rgb}", edit=True, **kwargs)


def add_separator(node: str, name: str, **kwargs: Any) -> None:
    """Adds a visual separator (border) attribute to the specified node.

    Uses a locked enum attribute with a formatted niceName to act as a UI separator
    in the Channel Box.

    Args:
        node (str): The name of the Maya node.
        name (str): The name to display in the enum definition.
            Spaces and slashes are replaced with underscores.
        **kwargs (Any): Additional keyword arguments passed to `cmds.setAttr`
            (e.g., channelBox=True).
    """
    name = name.replace(" ", "_").replace("/", "_")
    cmds.addAttr(
        node,
        longName=name,
        attributeType="enum",
        enumName=f"{name}:",
        niceName="--------------------",
        minValue=0,
        maxValue=0,
    )
    if kwargs:
        cmds.setAttr(f"{node}.{name}", edit=True, **kwargs)
