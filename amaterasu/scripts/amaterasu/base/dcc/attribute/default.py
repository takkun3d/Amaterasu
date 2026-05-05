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
"""Attribute querying utilities."""

from __future__ import annotations
from typing import Any
from maya import cmds


def get_default_value(node: str, attribute: str) -> Any | None:
    """Gets the default value of a specified attribute with accurate Python typing.

    Args:
        node (str): The name of the Maya node.
        attribute (str): The name of the attribute.

    Returns:
        Any | None: The correctly typed default value (bool, int, float, str, list),
                    or None if it cannot be queried.
    """
    try:
        values: Any = cmds.attributeQuery(
            attribute, node=node, listDefault=True
        )

        attr_type: str = cmds.attributeQuery(
            attribute, node=node, attributeType=True
        )  # type: ignore

        if not values:
            return None

        if attr_type == "bool":
            return bool(values[0])

        if attr_type in ("byte", "short", "long", "enum"):
            return int(values[0])

        if attr_type in ("float", "double", "doubleAngle", "doubleLinear"):
            return float(values[0])

        if attr_type == "string":
            return str(values[0])

        if attr_type in ("float2", "float3", "double2", "double3"):
            return [float(v) for v in values]

        if attr_type in ("short2", "short3", "long2", "long3"):
            return [int(v) for v in values]

        return values[0] if len(values) == 1 else values

    except RuntimeError:
        return None
