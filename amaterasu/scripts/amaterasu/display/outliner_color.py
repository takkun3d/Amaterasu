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
"""Provides a user interface for managing Maya Outliner colors.

This module contains the UI tool for setting and clearing custom
RGB colors on selected nodes in the Maya Outliner.
"""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Outliner Color"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Outliner Color tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        rgb (framework.Variant[list[float]]): The saved RGB color.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    rgb: framework.Variant[list[float]] = framework.Variant([1.0, 0.0, 0.0])


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Outliner Color tool.

    This window provides a user interface with a color picker, palette,
    and action buttons to apply or remove outliner colors.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(200, 50)
        self.__rgb_color: widgets.ColorSelectButton

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
                custom UI elements should be added.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        rgb_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(rgb_layout)

        self.__rgb_color = widgets.ColorSelectButton(self)
        self.__rgb_color.setFixedSize(70, 20)
        rgb_layout.addWidget(self.__rgb_color)
        rgb_layout.addStretch(True)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Remove", self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.remove_rgb_color_callback)
        rgb_layout.addWidget(button)

        button = QtWidgets.QPushButton("Apply", self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.apply_rgb_color_callback)
        rgb_layout.addWidget(button)

        palette: widgets.ColorPalette = widgets.ColorPalette(None, 8, self)
        palette.clicked.connect(self.__rgb_color.set_color)
        main_layout.addWidget(palette)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.rgb.bind(
            setter=self.__rgb_color.set_color,
            getter=self.__rgb_color.color,
        )

    @dcc.undo
    def remove_rgb_color_callback(self) -> None:
        """Callback to remove the outliner color from selected nodes."""
        self.save_settings()
        result: utils.Result = dcc.node.clear_outliner_color()
        result.log(_logger)

    @dcc.undo
    def apply_rgb_color_callback(self) -> None:
        """Callback to apply the selected RGB color to selected nodes."""
        self.save_settings()
        result: utils.Result = dcc.node.set_outliner_color(
            self.__rgb_color.color()
        )
        result.log(_logger)


def main(unique_id: str = "") -> None:
    """Shows the Outliner Color tool window.

    Args:
        unique_id (str, optional): Unique ID for the tool window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
