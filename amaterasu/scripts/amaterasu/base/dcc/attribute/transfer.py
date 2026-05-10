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
"""Utilities for transferring user-defined attributes."""

from __future__ import annotations
from typing import Any
import dataclasses
from maya import cmds
from amaterasu.base import utils


@dataclasses.dataclass
class TransferBuffer:
    """A data class representing a Maya user-defined attribute.

    Attributes:
        name (str): The long name of the attribute.
        nice_name (str): The nice name (display name) of the attribute.
        attr_type (str): The type of the attribute
            (e.g., 'string', 'enum', 'float').
        value (Any): The current value of the attribute.
        default_value (Any): The default value of the attribute.
        enum_value (str): A colon-separated string of enum names, if applicable.
        color (bool): True if the attribute is used as a color, False otherwise.
        parent_attr (str): The name of the parent attribute,
            if this is a child attribute.
        keyable (bool): True if the attribute is keyable.
        channelbox (bool): True if the attribute is displayed in the channel box.
        minimum (float | None): The minimum allowed value, or None if not set.
        maximum (float | None): The maximum allowed value, or None if not set.
    """

    name: str
    nice_name: str
    attr_type: str
    value: Any
    default_value: Any
    enum_value: str
    color: bool
    parent_attr: str
    keyable: bool
    channelbox: bool
    minimum: float | None
    maximum: float | None

    def to_dict(self) -> dict[str, Any]:
        """Converts the AttributeData instance to a JSON-serializable dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the attribute data.
        """
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransferBuffer:
        """Creates an AttributeData instance from a dictionary.

        Args:
            data (dict[str, Any]): The dictionary containing attribute data.

        Returns:
            AttributeData: A new instance populated with the dictionary data.
        """
        return cls(**data)


def extract_transfer_buffers(node: str) -> list[TransferBuffer]:
    """Extracts all user-defined attributes from a specified Maya node.

    Args:
        node (str): The name of the Maya node to query.

    Returns:
        list[AttributeData]: A list of AttributeData objects representing
            the user-defined attributes on the node.
    """
    attrs: list[str] = cmds.listAttr(node, userDefined=True) or []
    data_list: list[TransferBuffer] = []

    for attr in attrs:
        plug: str = f"{node}.{attr}"
        attr_type: str = cmds.getAttr(plug, type=True)

        nice_name: str = cmds.attributeQuery(attr, node=node, niceName=True)  # type: ignore

        value: Any = cmds.getAttr(plug)
        if attr_type in ("float3", "double3") and isinstance(value, list):
            value = value[0]  # unwraps [(x, y, z)]

        default_value: Any = None
        if attr_type != "string":
            default_value = cmds.attributeQuery(
                attr, node=node, listDefault=True
            )[
                0
            ]  # type: ignore

        enum_value: str = ""
        if attr_type == "enum":
            enum_value = cmds.attributeQuery(attr, node=node, listEnum=True)[0]  # type: ignore

        color: bool = cmds.attributeQuery(attr, node=node, usedAsColor=True)  # type: ignore

        check_parent: list[str] = cmds.attributeQuery(
            attr, node=node, listParent=True
        )  # type: ignore
        parent_attr: str = check_parent[0] if check_parent else ""

        keyable: bool = cmds.getAttr(plug, keyable=True)
        channelbox: bool = cmds.getAttr(plug, channelBox=True)

        has_min: bool = cmds.attributeQuery(attr, node=node, minExists=True)  # type: ignore
        minimum: float | None = (
            cmds.attributeQuery(attr, node=node, minimum=True)[0]  # type: ignore
            if (attr_type in ("long", "float") and has_min)
            else None
        )

        has_max: bool = cmds.attributeQuery(attr, node=node, maxExists=True)  # type: ignore
        maximum: float | None = (
            cmds.attributeQuery(attr, node=node, maximum=True)[0]  # type: ignore
            if (attr_type in ("long", "float") and has_max)
            else None
        )

        data_list.append(
            TransferBuffer(
                name=attr,
                nice_name=nice_name,
                attr_type=attr_type,
                value=value,
                default_value=default_value,
                enum_value=enum_value,
                color=color,
                parent_attr=parent_attr,
                keyable=keyable,
                channelbox=channelbox,
                minimum=minimum,
                maximum=maximum,
            )
        )
    return data_list


def apply_transfer_buffer(
    node: str, datas: list[TransferBuffer]
) -> utils.Result:
    """Applies a list of TransferBuffer objects to a destination Maya node.

    This function uses a two-step approach:
    1. Creates all attributes first to ensure compound children exist.
    2. Sets values, keyable states, and channel box visibility.

    Args:
        node (str): The name of the destination Maya node.
        datas (list[TransferBuffer]): A list of attribute data buffers to apply.

    Returns:
        utils.Result: An object containing the execution result.
    """
    result: utils.Result = utils.Result()

    for data in datas:
        add_kwargs: dict[str, Any] = {}
        if data.parent_attr:
            add_kwargs["parent"] = data.parent_attr

        is_compound: bool = data.attr_type in ("float3", "double3", "long3")
        if not is_compound:
            if data.default_value is not None:
                add_kwargs["defaultValue"] = data.default_value

            if data.minimum is not None:
                add_kwargs["minValue"] = data.minimum

            if data.maximum is not None:
                add_kwargs["maxValue"] = data.maximum

        if data.color:
            add_kwargs["usedAsColor"] = data.color

        add_kwargs["longName"] = data.name
        add_kwargs["niceName"] = data.nice_name

        plug: str = f"{node}.{data.name}"
        try:
            if not cmds.attributeQuery(data.name, node=node, exists=True):
                if data.attr_type == "enum":
                    cmds.addAttr(
                        node,
                        attributeType="enum",
                        enumName=data.enum_value,
                        **add_kwargs,
                    )
                elif data.attr_type == "string":
                    cmds.addAttr(
                        node,
                        dataType=data.attr_type,
                        **add_kwargs,
                    )
                else:
                    cmds.addAttr(
                        node,
                        attributeType=data.attr_type,
                        **add_kwargs,
                    )

            else:
                result.add_failure(plug, "Attribute already exists.")
                continue

        except RuntimeError as e:
            result.add_failure(plug, f"AddAttr Error: {e}")
            continue

    for data in datas:
        plug = f"{node}.{data.name}"
        is_compound = data.attr_type in ("float3", "double3", "long3")

        cmds.setAttr(
            plug,
            edit=True,
            keyable=data.keyable,
            channelBox=data.channelbox,
        )

        if not is_compound:
            if data.attr_type == "string":
                cmds.setAttr(plug, data.value, type="string")

            else:
                cmds.setAttr(plug, data.value)

    return result
