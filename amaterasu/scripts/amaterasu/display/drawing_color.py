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
import functools
import hashlib
import colorsys
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Drawing Color"
__version__: str = "1.30"
__copyright__ = (
    "Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License."
)
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
    """Settings for tool."""

    window_geo: framework.Variant[str] = framework.Variant("")
    last_tab_index: framework.Variant[int] = framework.Variant(0)
    rgb: framework.Variant[list[float]] = framework.Variant([0.0, 0.275, 0.098])
    preset_name: framework.Variant[str] = framework.Variant("Soft Pastel")
    h_min: framework.Variant[float] = framework.Variant(0.0)
    h_max: framework.Variant[float] = framework.Variant(1.0)
    s_min: framework.Variant[float] = framework.Variant(0.2)
    s_max: framework.Variant[float] = framework.Variant(0.45)
    v_min: framework.Variant[float] = framework.Variant(0.85)
    v_max: framework.Variant[float] = framework.Variant(1.0)


class IndexColorWidget(QtWidgets.QWidget):
    """Widget for manual index color selection.

    Provides a grid of Maya index colors and a trash button for removing colors.
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

        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        row: int = -1
        col: int = -1
        for i in range(32):
            col += 1
            if not i % 8:
                row += 1
                col = 0

            if i == 0:
                trash_button: widgets.IconButton = widgets.IconButton(self)
                trash_button.set_icon(dcc.get_icon_path(TRASH))
                trash_button.setFixedSize(QtCore.QSize(24, 24))
                trash_button.clicked.connect(functools.partial(self.apply, i))
                main_layout.addWidget(trash_button, row, col)

            else:
                color: list[float] = cmds.colorIndex(
                    i, query=True
                )  # type: ignore
                button: widgets.ColorButton = widgets.ColorButton(self)
                button.set_color(color[0], color[1], color[2])
                button.setFixedSize(QtCore.QSize(24, 24))
                button.clicked.connect(functools.partial(self.apply, i))
                main_layout.addWidget(button, row, col)

        main_layout.setRowStretch(row + 1, 1)
        main_layout.setColumnStretch(8, 1)

    @dcc.undo
    def apply(self, index: int) -> None:
        """Apply the selected index color to the current selection.

        Args:
            index (int): The color index (0-31) to apply.
        """
        self.applied.emit()
        result: bool = apply(0, index)
        if result:
            _logger.info("Done.")


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
        palette.clicked.connect(self.__set_color_from_palette)
        layout.addRow(palette)

    def __set_color_from_palette(self, color: list[float]) -> None:
        """Set the RGB color to the ColorSelectButton from the clicked palette.

        Args:
            color (list[float]): The RGB color values as a list of floats.
        """
        self.__rgb_color.set_color(*color)

    @dcc.undo
    def remove_rgb_color_callback(self) -> None:
        """Callback to remove RGB color overrides from selected nodes."""
        self.applied.emit()
        result: bool = apply(1, 0)
        if result:
            _logger.info("Done.")

    @dcc.undo
    def apply_rgb_color_callback(self) -> None:
        """Callback to apply the selected RGB color override to
        selected nodes."""
        self.applied.emit()
        result: bool = apply(1, 0, self.__rgb_color.color())
        if result:
            _logger.info("Done.")

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
        self.__rgb_color.set_color(*color)


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
        result: bool = apply(1, 0)
        if result:
            _logger.info("Done.")

    @dcc.undo
    def apply_auto_colorize_callback(self) -> None:
        """Callback to apply UUID-based automatic HSV coloring to
        selected nodes."""
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            _logger.warning('Select objects to colorize.')
            return

        self.applied.emit()

        result: bool = apply_auto_color(
            selection,
            self.__hue.low_value() / 100.0,
            self.__hue.high_value() / 100.0,
            self.__saturation.low_value() / 100.0,
            self.__saturation.high_value() / 100.0,
            self.__value.low_value() / 100.0,
            self.__value.high_value() / 100.0,
        )
        if result:
            _logger.info("Applied colors to %s nodes.", len(selection))

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

    def hsv_ranges(self) -> dict[str, tuple[float, float]]:
        """Get current HSV slider ranges (0.0 - 1.0).

        Returns:
            dict[str, tuple[float, float]]: A dictionary containing
                the min and max
                values for hue ('h'), saturation ('s'), and value ('v').
        """
        return {
            "h": (
                self.__hue.low_value() / 100.0,
                self.__hue.high_value() / 100.0,
            ),
            "s": (
                self.__saturation.low_value() / 100.0,
                self.__saturation.high_value() / 100.0,
            ),
            "v": (
                self.__value.low_value() / 100.0,
                self.__value.high_value() / 100.0,
            ),
        }

    def set_hsv_ranges(
        self,
        h: tuple[float, float],
        s: tuple[float, float],
        v: tuple[float, float],
    ) -> None:
        """Set HSV slider ranges (0.0 - 1.0).

        Args:
            h (tuple[float, float]): Hue range as (min, max).
            s (tuple[float, float]): Saturation range as (min, max).
            v (tuple[float, float]): Value range as (min, max).
        """
        self.__hue.set_values(int(h[0] * 100), int(h[1] * 100))
        self.__saturation.set_values(int(s[0] * 100), int(s[1] * 100))
        self.__value.set_values(int(v[0] * 100), int(v[1] * 100))


class MainWindow(framework.ToolWindow):
    """Tool main window."""

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
        """Create the tool-specific user interface."""
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

    def load_settings(self) -> None:
        """Load UI settings from the configuration file."""
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(utils.ascii_to_qt(settings.window_geo.value()))
        self.__tabs.setCurrentIndex(settings.last_tab_index.value())
        self.__rgb_widget.set_color(settings.rgb.value())
        self.__auto_widget.set_preset_name(settings.preset_name.value())
        self.__auto_widget.set_hsv_ranges(
            (settings.h_min.value(), settings.h_max.value()),
            (settings.s_min.value(), settings.s_max.value()),
            (settings.v_min.value(), settings.v_max.value()),
        )

    def save_settings(self) -> None:
        """Save UI settings to the configuration file."""
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(utils.qt_to_ascii(self.saveGeometry()))
        settings.last_tab_index.set_value(self.__tabs.currentIndex())
        settings.rgb.set_value(self.__rgb_widget.color())
        settings.preset_name.set_value(self.__auto_widget.preset_name())

        hsv: dict[str, tuple[float, float]] = self.__auto_widget.hsv_ranges()
        settings.h_min.set_value(hsv["h"][0])
        settings.h_max.set_value(hsv["h"][1])
        settings.s_min.set_value(hsv["s"][0])
        settings.s_max.set_value(hsv["s"][1])
        settings.v_min.set_value(hsv["v"][0])
        settings.v_max.set_value(hsv["v"][1])
        settings.write()

    def reset_settings(self) -> None:
        """Reset UI settings to their default values."""
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    def about(self) -> None:
        """Show the about dialog with tool information."""
        framework.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )


def apply_auto_color(
    transforms: list[str],
    h_min: float,
    h_max: float,
    s_min: float,
    s_max: float,
    v_min: float,
    v_max: float,
) -> bool:
    """Generate and apply unique colors to the given transforms based on UUID.

    Args:
        transforms (list[str]): List of transform node names to colorize.
        h_min (float): Minimum hue value (0.0 - 1.0).
        h_max (float): Maximum hue value (0.0 - 1.0).
        s_min (float): Minimum saturation value (0.0 - 1.0).
        s_max (float): Maximum saturation value (0.0 - 1.0).
        v_min (float): Minimum brightness value (0.0 - 1.0).
        v_max (float): Maximum brightness value (0.0 - 1.0).

    Returns:
        bool: True if colors were successfully applied.
    """
    for node in transforms:
        uuids: list[str] = cmds.ls(node, uuid=True)
        if not uuids:
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

        r: float
        g: float
        b: float
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        cmds.setAttr(f"{node}.overrideEnabled", 1)
        cmds.setAttr(f"{node}.overrideRGBColors", 1)
        cmds.setAttr(f"{node}.overrideColorRGB", r, g, b)

    return True


def apply(
    mode: int,
    index: int = 0,
    rgb: list[float] | None = None,
    force_layer: bool = True,
    selection: list[str] | None = None,
) -> bool:
    """Apply display color to selected nodes.

    Args:
        mode (int): 0 for Index Color mode, 1 for RGB Color mode.
        index (int, optional): The color index (0-31).
            Defaults to 0.
        rgb (list[float] | None, optional): The RGB color values.
            Defaults to None.
        force_layer (bool, optional): Whether to disconnect existing
            display layers.
            Defaults to True.
        selection (list[str] | None, optional): List of nodes to colorize.
            If None, uses current selection. Defaults to None.

    Returns:
        bool: True if successful, False if an error occurred or no objects
            were selected.
    """
    if not selection:
        selection = cmds.ls(selection=True)

    if not selection:
        _logger.error("Select object to set wireframe color.")
        return False

    if index >= 32:
        _logger.error("Color index is maximum value of 31.")
        return False

    if index <= -1:
        _logger.error("Color index is minimum value of 0.")
        return False

    for node in selection:
        if force_layer:
            plugs: list[str] = cmds.listConnections(
                f"{node}.drawOverride",
                type="displayLayer",
                source=True,
                destination=False,
                plugs=True,
            )
            if plugs:
                cmds.disconnectAttr(plugs[0], f"{node}.drawOverride")

        # Index Color
        if mode == 0:
            if index == 0:
                cmds.setAttr(f"{node}.overrideEnabled", 0)
            else:
                cmds.setAttr(f"{node}.overrideEnabled", 1)
                cmds.setAttr(f"{node}.overrideRGBColors", 0)
                cmds.setAttr(f"{node}.overrideColor", index)

        # RGB Color
        else:
            if rgb is None:
                cmds.setAttr(f"{node}.overrideEnabled", 0)
            else:
                cmds.setAttr(f"{node}.overrideEnabled", 1)
                cmds.setAttr(f"{node}.overrideRGBColors", 1)
                cmds.setAttr(f"{node}.overrideColorRGB", *rgb, type="double3")

    return True


def main(unique_id: str = "") -> None:
    """Show the tool window.

    Args:
        unique_id (str, optional): Unique ID for the tool window instance.
        Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
