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
"""Selects stacked nodes in the scene."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Select Stacked Nodes"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Select Stacked Nodes tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        mode (framework.Variant[int]): The selection mode (0: ALL, 1: 1-Last).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    mode: framework.Variant[int] = framework.Variant(1)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the tool."""

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
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique string identifier for the window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget for the UI layout.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        mode: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        mode.addItems(["ALL", "1-Last"])
        main_layout.addRow(widgets.FormLabel("Mode"), mode)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.mode.bind(
            setter=mode.setCurrentIndex,
            getter=mode.currentIndex,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by applying the configured settings."""
        self.save_settings()
        main(self.tool_settings())


def option(unique_id: str = "") -> None:
    """Shows the tool's option window.

    Args:
        unique_id (str, optional): A unique string identifier for the window.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the select stacked nodes operation.

    Args:
        settings (Settings | None, optional): The tool settings to apply.
            If None, the default settings will be loaded. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        selection = cmds.ls(transforms=True)

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    nodes: list[str] = dcc.space.get_stacked_nodes(
        selection, settings.mode.value()
    )
    if not nodes:
        cmds.select(clear=True)
        _logger.info("There were no stacked nodes in this scene.")
        return

    cmds.select(*nodes, replace=True)
    _logger.info("Done.")
