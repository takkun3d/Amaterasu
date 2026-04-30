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
"""Set drawing color to selected nodes.

This module provides tools and a user interface to apply index-based or
RGB-based drawing overrides to Maya transform nodes. It includes manual
color assignment features as well as a UUID-based automatic colorization
system for improved viewport visibility.
"""

from __future__ import annotations
import hashlib
import colorsys
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Drawing Color"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)

TRASH: str = "a_trash.png"
PRESETS: dict[str, list[float]] = {
    "Soft Pastel": [0.0, 1.0, 0.2, 0.45, 0.85, 1.0],
    "Rainbow": [0.0, 1.0, 0.4, 0.8, 0.7, 1.0],
    "Neon Vivid": [0.0, 1.0, 0.8, 1.0, 0.9, 1.0],
    "Dark Chic": [0.0, 1.0, 0.3, 0.7, 0.2, 0.45],
    "Cyberpunk": [0.5, 0.9, 0.7, 1.0, 0.8, 1.0],
    "Warm": [0.0, 0.15, 0.6, 0.9, 0.7, 1.0],
    "Cool": [0.5, 0.65, 0.5, 0.8, 0.7, 1.0],
    "Earth": [0.05, 0.35, 0.3, 0.6, 0.3, 0.6],
    "Berry": [0.85, 1.0, 0.5, 0.8, 0.7, 0.9],
    "Citrus": [0.1, 0.3, 0.6, 0.9, 0.8, 1.0],
    "Monotone": [0.0, 1.0, 0.0, 0.0, 0.1, 0.9],
    "Sepia": [0.08, 0.12, 0.4, 0.6, 0.4, 0.7],
    "Mint Teal": [0.45, 0.55, 0.5, 0.8, 0.7, 1.0],
    "Luxury Gold": [0.10, 0.16, 0.6, 1.0, 0.7, 1.0],
    "Matcha Latte": [0.20, 0.32, 0.3, 0.6, 0.6, 0.9],
}


class Settings(framework.ToolSettings):
    """Settings for the Drawing Color tool.

    This class manages the persistent settings for the tool's UI, ensuring
    that user preferences like window geometry, selected colors, and auto-color
    ranges are saved and restored across sessions.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        last_tab_index (framework.Variant[int]): The index of the last opened tab.
        rgb (framework.Variant[list[float]]): The last applied RGB color.
        preset_name (framework.Variant[str]): The name of the selected auto-color preset.
        h_range (framework.Variant[list[float]]): The hue slider range as [min, max].
        s_range (framework.Variant[list[float]]): The saturation slider range as [min, max].
        v_range (framework.Variant[list[float]]): The value slider range as [min, max].
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    last_tab_index: framework.Variant[int] = framework.Variant(0)
    rgb: framework.Variant[list[float]] = framework.Variant([0.0, 0.275, 0.098])
    preset_name: framework.Variant[str] = framework.Variant("Soft Pastel")
    h_range: framework.Variant[list[float]] = framework.Variant([0.0, 1.0])
    s_range: framework.Variant[list[float]] = framework.Variant([0.2, 0.45])
    v_range: framework.Variant[list[float]] = framework.Variant([0.85, 1.0])


class IndexColorWidget(QtWidgets.QWidget):
    """Widget for manual index color selection.

    Uses the generic IndexColorPalette to provide a grid of Maya index colors
    and handles the application logic for the drawing color tool.
    """

    applied: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the IndexColorWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__palette = widgets.IndexColorPalette(self)
        self.__palette.index_selected.connect(self.apply)
        main_layout.addWidget(self.__palette)

    @dcc.undo
    def apply(self, index: int) -> None:
        """Apply the selected index color to the current selection.

        Args:
            index (int): The color index (0-31) to apply.
        """
        self.applied.emit()
        result: utils.Result = dcc.node.set_index_color(index)
        result.log(_logger)


class RGBColorWidget(QtWidgets.QWidget):
    """Widget for manual RGB color selection.

    Provides a color picker, color palette, and apply/remove buttons.
    """

    applied: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the RGBColorWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        layout: widgets.FormLayout = widgets.FormLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        rgb_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addRow(rgb_layout)

        self.__rgb_color: widgets.ColorSelectButton = widgets.ColorSelectButton(
            self
        )
        self.__rgb_color.setFixedSize(70, 20)
        rgb_layout.addWidget(self.__rgb_color)
        rgb_layout.addStretch(True)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.apply_rgb_color_callback)
        rgb_layout.addWidget(button)

        button = QtWidgets.QPushButton("Remove", self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.remove_rgb_color_callback)
        rgb_layout.addWidget(button)

        palette: widgets.ColorPalette = widgets.ColorPalette(None, 8, self)
        palette.clicked.connect(self.__rgb_color.set_color)
        layout.addRow(palette)

    @dcc.undo
    def remove_rgb_color_callback(self) -> None:
        """Callback to remove RGB color overrides from selected nodes."""
        self.applied.emit()
        result: utils.Result = dcc.node.clear_color()
        result.log(_logger)

    @dcc.undo
    def apply_rgb_color_callback(self) -> None:
        """Callback to apply the selected RGB color override to
        selected nodes."""
        self.applied.emit()
        result: utils.Result = dcc.node.set_rgb_color(self.__rgb_color.color())
        result.log(_logger)

    def color(self) -> list[float]:
        """Get the current RGB color.

        Returns:
            list[float]: The current RGB color as a list of floats.
        """
        return self.__rgb_color.color()

    def set_color(self, color: list[float]) -> None:
        """Set the RGB color.

        Args:
            color (list[float]): The RGB color to set.
        """
        self.__rgb_color.set_color(color)


class AutoColorizeWidget(QtWidgets.QWidget):
    """Widget for UUID-based automatic coloring.

    Provides HSV range sliders and presets to generate random but
    consistent colors.
    """

    applied: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the AutoColorizeWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        layout: widgets.FormLayout = widgets.FormLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.__preset: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        for presets_name in PRESETS:
            self.__preset.addItem(presets_name)

        self.__preset.currentIndexChanged.connect(self.preset_changed)
        layout.addRow(widgets.FormLabel('Presets'), self.__preset)

        self.__hue: widgets.RangeSlider = widgets.RangeSlider(self)
        self.__hue.set_range(0, 100)
        self.__hue.set_bar_color((220, 90, 90))
        layout.addRow(widgets.FormLabel('Hue'), self.__hue)

        self.__saturation: widgets.RangeSlider = widgets.RangeSlider(self)
        self.__saturation.set_range(0, 100)
        self.__saturation.set_bar_color((90, 220, 130))
        layout.addRow(widgets.FormLabel('Saturation'), self.__saturation)

        self.__value: widgets.RangeSlider = widgets.RangeSlider(self)
        self.__value.set_range(0, 100)
        self.__value.set_bar_color((90, 150, 220))
        layout.addRow(widgets.FormLabel('Value'), self.__value)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addRow(button_layout)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply_auto_colorize_callback)
        button_layout.addWidget(button)

        button = QtWidgets.QPushButton("Reset", self)
        button.clicked.connect(self.remove_color_callback)
        button_layout.addWidget(button)

    @QtCore.Slot()
    def preset_changed(self) -> None:
        """Update HSV sliders when a different preset is selected from
        the combo box."""
        preset_name: str = self.__preset.currentText()
        if preset_name not in PRESETS:
            return

        h_min: float
        h_max: float
        s_min: float
        s_max: float
        v_min: float
        v_max: float
        h_min, h_max, s_min, s_max, v_min, v_max = PRESETS[preset_name]
        self.__hue.set_values(int(h_min * 100), int(h_max * 100))
        self.__saturation.set_values(int(s_min * 100), int(s_max * 100))
        self.__value.set_values(int(v_min * 100), int(v_max * 100))

    @dcc.undo
    def remove_color_callback(self) -> None:
        """Callback to remove color overrides from selected nodes."""
        self.applied.emit()
        result: utils.Result = dcc.node.clear_color()
        result.log(_logger)

    @dcc.undo
    def apply_auto_colorize_callback(self) -> None:
        """Callback to apply UUID-based automatic HSV coloring to
        selected nodes."""

        self.applied.emit()
        hue: list[float] = [
            self.__hue.low_value() / 100.0,
            self.__hue.high_value() / 100.0,
        ]
        saturation: list[float] = [
            self.__saturation.low_value() / 100.0,
            self.__saturation.high_value() / 100.0,
        ]
        value: list[float] = [
            self.__value.low_value() / 100.0,
            self.__value.high_value() / 100.0,
        ]
        result: utils.Result = apply_auto_color(hue, saturation, value)
        result.log(_logger)

    def preset_name(self) -> str:
        """Get current preset name.

        Returns:
            str: The current preset name.
        """
        return self.__preset.currentText()

    def set_preset_name(self, name: str) -> None:
        """Set current preset by name.

        Args:
            name (str): The preset name to set.
        """
        idx: int = self.__preset.findText(name)
        if idx >= 0:
            self.__preset.setCurrentIndex(idx)
            self.preset_changed()

    def hue_range(self) -> list[float]:
        """Get the current hue range.

        Returns:
            list[float]: The hue range as [min, max] between 0.0 and 1.0.
        """
        return [
            self.__hue.low_value() / 100.0,
            self.__hue.high_value() / 100.0,
        ]

    def set_hue_range(self, v: list[float]) -> None:
        """Set the hue range.

        Args:
            v (list[float]): The hue range as [min, max] between 0.0 and 1.0.
        """
        self.__hue.set_values(int(v[0] * 100), int(v[1] * 100))

    def saturation_range(self) -> list[float]:
        """Get the current saturation range.

        Returns:
            list[float]: The saturation range as [min, max] between 0.0 and 1.0.
        """
        return [
            self.__saturation.low_value() / 100.0,
            self.__saturation.high_value() / 100.0,
        ]

    def set_saturation_range(self, v: list[float]) -> None:
        """Set the saturation range.

        Args:
            v (list[float]): The saturation range as [min, max] between 0.0 and 1.0.
        """
        self.__saturation.set_values(int(v[0] * 100), int(v[1] * 100))

    def value_range(self) -> list[float]:
        """Get the current value (brightness) range.

        Returns:
            list[float]: The value range as [min, max] between 0.0 and 1.0.
        """
        return [
            self.__value.low_value() / 100.0,
            self.__value.high_value() / 100.0,
        ]

    def set_value_range(self, v: list[float]) -> None:
        """Set the value (brightness) range.

        Args:
            v (list[float]): The value range as [min, max] between 0.0 and 1.0.
        """
        self.__value.set_values(int(v[0] * 100), int(v[1] * 100))


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Drawing Color tool.

    This window integrates various color override utilities into a unified
    interface. It manages color selection tabs (Index, RGB, Auto) and
    synchronizes the UI state with persistent tool settings.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initialize the MainWindow widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): Unique ID for the window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(250, 220)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Construct the user interface and bind settings.

        This method initializes the main layout, creates the tab widget containing
        different color override tools, and establishes data bindings between
        the UI components and the tool's persistent settings.

        Args:
            parent (QtWidgets.QWidget): The central container widget provided
                by the framework where all UI elements should be added.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(self)
        main_layout.addWidget(self.__tabs)

        self.__index_widget: IndexColorWidget = IndexColorWidget(self)
        self.__index_widget.applied.connect(self.save_settings)
        self.__tabs.addTab(self.__index_widget, "Index")

        self.__rgb_widget: RGBColorWidget = RGBColorWidget(self)
        self.__rgb_widget.applied.connect(self.save_settings)
        self.__tabs.addTab(self.__rgb_widget, "RGB")

        self.__auto_widget: AutoColorizeWidget = AutoColorizeWidget(self)
        self.__auto_widget.applied.connect(self.save_settings)
        self.__tabs.addTab(self.__auto_widget, "Auto")

        # self.__tabs.currentChanged.connect(self.save_settings)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.last_tab_index.bind(
            setter=self.__tabs.setCurrentIndex,
            getter=self.__tabs.currentIndex,
        )
        settings.rgb.bind(
            setter=self.__rgb_widget.set_color,
            getter=self.__rgb_widget.color,
        )
        settings.preset_name.bind(
            setter=self.__auto_widget.set_preset_name,
            getter=self.__auto_widget.preset_name,
        )
        settings.h_range.bind(
            setter=self.__auto_widget.set_hue_range,
            getter=self.__auto_widget.hue_range,
        )
        settings.s_range.bind(
            setter=self.__auto_widget.set_saturation_range,
            getter=self.__auto_widget.saturation_range,
        )
        settings.v_range.bind(
            setter=self.__auto_widget.set_value_range,
            getter=self.__auto_widget.value_range,
        )


def apply_auto_color(
    h_range: list[float],
    s_range: list[float],
    v_range: list[float],
    nodes: list[str] | None = None,
) -> utils.Result:
    """Generate and apply unique colors to the given transforms based on UUID.

    Args:
        h_range (list[float]): Hue min and max (0.0 - 1.0).
        s_range (list[float]): Saturation min and max (0.0 - 1.0).
        v_range (list[float]): Brightness min and max (0.0 - 1.0).
        nodes (list[str] | None): List of node names to colorize.

    Returns:
        utils.Result: An object containing the merged results of the operation.
    """
    result: utils.Result = utils.Result()
    h_min, h_max = h_range
    s_min, s_max = s_range
    v_min, v_max = v_range

    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        result.set_error("Select nodes to set drawing color.")
        return result

    for node in nodes:
        uuids: list[str] = cmds.ls(node, uuid=True)
        if not uuids:
            result.add_failure(node, "Failed to get UUID.")
            continue

        uuid_str: str = uuids[0]
        long_name: str = cmds.ls(node, long=True)[0]
        unique_string: str = f"{long_name}_{uuid_str}"

        hash_obj: hashlib._Hash = hashlib.sha256(unique_string.encode('utf-8'))
        hash_int = int(hash_obj.hexdigest(), 16)

        h: float = h_min + ((hash_int % 10000) / 10000.0) * (h_max - h_min)
        s: float = s_min + (((hash_int // 10000) % 100) / 100.0) * (
            s_max - s_min
        )
        v: float = v_min + (((hash_int // 1000000) % 100) / 100.0) * (
            v_max - v_min
        )

        color: list[float] = list(colorsys.hsv_to_rgb(h, s, v))
        r: utils.Result = dcc.node.set_rgb_color(color, nodes=[node])
        result.merge(r)

    return result


# TODO: Remove this function once perspective_guide and decompose_rotate are updated.
def apply(
    mode: int,
    index: int = 0,
    rgb: list[float] | None = None,
    force_layer: bool = True,
    selection: list[str] | None = None,
) -> bool:
    """Deprecated: Use amaterasu.base.dcc.node.color instead."""
    if mode == 0:
        if index == 0:
            dcc.node.clear_color(nodes=selection)
        else:
            dcc.node.set_index_color(
                index, nodes=selection, force_layer=force_layer
            )
    else:
        if rgb is None:
            dcc.node.clear_color(nodes=selection)
        else:
            dcc.node.set_rgb_color(
                rgb, nodes=selection, force_layer=force_layer
            )
    return True


def main(unique_id: str = "") -> None:
    """Show the tool window.

    Args:
        unique_id (str, optional): Unique ID for the tool window instance.
        Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
