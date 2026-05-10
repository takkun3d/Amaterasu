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
"""Node color override utilities for Maya.

This module provides centralized functions to manage display color overrides
for Maya nodes. It supports both index-based and RGB-based color assignments,
and automatically handles the disconnection of display layers to ensure
overrides are properly applied.

By encapsulating these Maya-specific commands, this module allows higher-level
Amaterasu tools and UI components to safely interact with node colors without
duplicating business logic.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def _apply_color_override(
    node: str,
    enabled: bool = True,
    index: int | None = None,
    rgb: list[float] | None = None,
    force_layer: bool = True,
) -> utils.Result:
    """Internal function to handle Maya display override attributes.

    This function performs the actual attribute changes on the node.

    Args:
        node (str): The target node name.
        enabled (bool, optional): Whether to enable color overrides.
            Defaults to True.
        index (int | None, optional): Color index to apply (1-31).
            Defaults to None.
        rgb (list[float] | None, optional): RGB color as [r, g, b].
            Defaults to None.
        force_layer (bool, optional): Whether to disconnect from display layers.
            Defaults to True.

    Returns:
        utils.Result: An object tracking the success or failure of the operation.
    """
    result: utils.Result = utils.Result()
    try:
        if force_layer:
            plugs: list[str] = cmds.listConnections(
                f"{node}.drawOverride",
                type="displayLayer",
                source=True,
                destination=False,
                plugs=True,
            )
            if plugs:
                for plug in plugs:
                    cmds.disconnectAttr(plug, f"{node}.drawOverride")

        cmds.setAttr(f"{node}.overrideEnabled", 1 if enabled else 0)
        if not enabled:
            cmds.setAttr(f"{node}.overrideRGBColors", 0)
            cmds.setAttr(f"{node}.overrideColor", 0)
            return result

        if rgb is not None:
            cmds.setAttr(f"{node}.overrideRGBColors", 1)
            cmds.setAttr(f"{node}.overrideColorRGB", *rgb, type="double3")

        elif index is not None:
            cmds.setAttr(f"{node}.overrideRGBColors", 0)
            cmds.setAttr(f"{node}.overrideColor", index)

    except RuntimeError as e:
        reason: str = str(e).split(":", maxsplit=1)[-1].strip()
        result.add_failure(node, reason)

    return result


def set_drawing_index_color(
    index: int, nodes: list[str] | None = None, force_layer: bool = True
) -> utils.Result:
    """Apply an index-based color override to nodes.

    Args:
        index (int): Color index (1-31). If 0, overrides are disabled.
        nodes (list[str] | None): Target nodes. Defaults to current selection.
        force_layer (bool): Whether to disconnect from display layers.

    Returns:
        utils.Result: An object containing the merged results of the operation.
    """
    result: utils.Result = utils.Result()
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        result.set_error("Select nodes to set drawing color.")
        return result

    enabled: bool = index != 0
    for node in targets:
        r: utils.Result = _apply_color_override(
            node, enabled=enabled, index=index, force_layer=force_layer
        )
        result.merge(r)

    return result


def set_drawing_rgb_color(
    rgb: list[float],
    nodes: list[str] | None = None,
    force_layer: bool = True,
) -> utils.Result:
    """Apply an RGB-based color override to nodes.

    Args:
        rgb (list[float]): RGB values as [r, g, b] (0.0 to 1.0).
        nodes (list[str] | None): Target nodes. Defaults to current selection.
        force_layer (bool): Whether to disconnect from display layers.

    Returns:
        utils.Result: An object containing the merged results of the operation.
    """
    result: utils.Result = utils.Result()
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        result.set_error("Select nodes to set drawing color.")
        return result

    for node in targets:
        r: utils.Result = _apply_color_override(
            node, enabled=True, rgb=rgb, force_layer=force_layer
        )
        result.merge(r)

    return result


def clear_drawing_color(nodes: list[str] | None = None) -> utils.Result:
    """Disable color overrides on nodes.

    Args:
        nodes (list[str] | None): Target nodes. Defaults to current selection.

    Returns:
        utils.Result: An object containing the merged results of the operation.
    """
    result: utils.Result = utils.Result()
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        result.set_error("Select nodes to set drawing color.")
        return result

    for node in targets:
        r: utils.Result = _apply_color_override(node, enabled=False)
        result.merge(r)

    return result
