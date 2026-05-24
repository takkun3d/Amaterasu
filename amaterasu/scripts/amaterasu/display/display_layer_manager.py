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
"""Provides utilities for importing and exporting Maya display layers to JSON."""

from __future__ import annotations
from typing import Any
import json
from maya import cmds
from amaterasu.base.qt import QtWidgets
from amaterasu.base import dcc, utils

__product__: str = "Display Layer Manager"
__version__: str = "1.00"
_logger: utils.Logger = utils.get_logger(__product__)


def import_json(file_path: str | None = None) -> None:
    """Imports display layers from a JSON file.

    If no file path is provided, a file dialog will prompt the user to select one.
    Existing layers with the same name will be skipped.

    Args:
        file_path (str | None, optional): The absolute path to the JSON file.
            Defaults to None.
    """
    if not file_path:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Load Layer Data", "", "JSON (*.json)"
        )
        if not file_path:
            return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            layer_data: Any = json.load(f)

    except IOError:
        _logger.error("Failed to read the file: %s", file_path)
        return

    except json.JSONDecodeError:
        _logger.error("Failed to decode JSON: %s", file_path)
        return

    result: utils.Result = utils.Result()
    for layer_name, data in layer_data.items():
        if not cmds.objExists(layer_name):
            cmds.createDisplayLayer(name=layer_name, empty=True)

        else:
            original_name: str = layer_name
            layer_name = cmds.createDisplayLayer(
                name=f"{layer_name}#", empty=True
            )
            result.add_failure(
                original_name, f"Already exists. Created as: {layer_name}"
            )

        members: list[str] = []
        for member in data.get("members", []):
            if cmds.objExists(member):
                members.append(member)

            else:
                result.add_failure(
                    f"{layer_name}: {member}", "Object not found in scene."
                )

        cmds.setAttr(f"{layer_name}.color", data.get("color", 0))
        cmds.setAttr(f"{layer_name}.displayType", data.get("displayType", 0))
        cmds.setAttr(f"{layer_name}.visibility", data.get("visibility", True))
        cmds.setAttr(
            f"{layer_name}.overrideRGBColors", data.get("overrideRGBColors", 0)
        )
        cmds.setAttr(
            f"{layer_name}.overrideColorRGB",
            *data.get("overrideColorRGB", [0.0, 0.0, 0.0]),
            type="double3",
        )
        cmds.setAttr(
            f"{layer_name}.overrideColorA", data.get("overrideColorA", 1.0)
        )
        cmds.setAttr(
            f"{layer_name}.hideOnPlayback", data.get("hideOnPlayback", False)
        )
        if members:
            cmds.editDisplayLayerMembers(layer_name, *members)

    result.log(_logger)


def export_json(
    selection: list[str] | None = None, file_path: str | None = None
) -> None:
    """Exports specified display layers to a JSON file.

    If no selection is provided, it attempts to get the currently selected
    display layers from the Layer Editor. If no file path is provided,
    a file dialog will prompt the user to specify a save location.

    Args:
        selection (list[str] | None, optional): A list of display layer names to export.
            Defaults to None.
        file_path (str | None, optional): The absolute path to save the JSON file.
            Defaults to None.
    """
    if selection is None:
        selection = dcc.selection.get_selected_display_layers()

    if not selection:
        _logger.warning("No display layers selected for export.")
        return

    if file_path is None:
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save Layer Data", "", "JSON (*.json)"
        )
        if not file_path:
            return

    selection.reverse()
    layer_data: dict[str, Any] = {}
    for layer in selection:
        members: list[str] = (
            cmds.editDisplayLayerMembers(layer, query=True, fullNames=True)
            or []  # type : ignore
        )
        color_rgb: list[list[float]] = cmds.getAttr(f"{layer}.overrideColorRGB")
        color_rgb_value: list[float] = (
            color_rgb[0] if color_rgb else [0.0, 0.0, 0.0]
        )
        layer_data[layer] = {
            "members": members,
            "color": cmds.getAttr(f"{layer}.color"),
            "displayType": cmds.getAttr(f"{layer}.displayType"),
            "visibility": cmds.getAttr(f"{layer}.visibility"),
            "overrideRGBColors": cmds.getAttr(f"{layer}.overrideRGBColors"),
            "overrideColorRGB": color_rgb_value,
            "overrideColorA": cmds.getAttr(f"{layer}.overrideColorA"),
            "hideOnPlayback": cmds.getAttr(f"{layer}.hideOnPlayback"),
        }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(layer_data, f, indent=4, ensure_ascii=False)

    except IOError:
        _logger.error("Failed to write to the file: %s", file_path)
        return

    except TypeError:
        _logger.error("Failed to encode data to JSON.")
        return

    _logger.info("Done.")
