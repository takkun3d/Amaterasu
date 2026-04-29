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


def _apply_color_override(
    node: str,
    enabled: bool = True,
    index: int | None = None,
    rgb: list[float] | None = None,
    force_layer: bool = True,
) -> None:
    """Internal function to handle Maya display override attributes.

    This function performs the actual attribute changes on the node.
    """
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
        return

    if rgb is not None:
        cmds.setAttr(f"{node}.overrideRGBColors", 1)
        cmds.setAttr(f"{node}.overrideColorRGB", *rgb, type="double3")

    elif index is not None:
        cmds.setAttr(f"{node}.overrideRGBColors", 0)
        cmds.setAttr(f"{node}.overrideColor", index)


def set_index_color(
    index: int, nodes: list[str] | None = None, force_layer: bool = True
) -> None:
    """Apply an index-based color override to nodes.

    Args:
        index (int): Color index (1-31). If 0, overrides are disabled.
        nodes (list[str] | None): Target nodes. Defaults to current selection.
        force_layer (bool): Whether to disconnect from display layers.
    """
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        return

    enabled: bool = index != 0
    for node in targets:
        _apply_color_override(
            node, enabled=enabled, index=index, force_layer=force_layer
        )


def set_rgb_color(
    rgb: list[float],
    nodes: list[str] | None = None,
    force_layer: bool = True,
) -> None:
    """Apply an RGB-based color override to nodes.

    Args:
        rgb (list[float]): RGB values as [r, g, b] (0.0 to 1.0).
        nodes (list[str] | None): Target nodes. Defaults to current selection.
        force_layer (bool): Whether to disconnect from display layers.
    """
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        return

    for node in targets:
        _apply_color_override(
            node, enabled=True, rgb=rgb, force_layer=force_layer
        )


def clear_color(nodes: list[str] | None = None) -> None:
    """Disable color overrides on nodes.

    Args:
        nodes (list[str] | None): Target nodes. Defaults to current selection.
    """
    targets: list[str] = nodes if nodes is not None else cmds.ls(selection=True)
    if not targets:
        return

    for node in targets:
        _apply_color_override(node, enabled=False)
