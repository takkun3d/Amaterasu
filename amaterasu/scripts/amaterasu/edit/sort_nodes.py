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
"""Sorts selected nodes in the Maya outliner."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Sort Nodes"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Sort Nodes tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        sort_order (framework.Variant[int]): The sorting method
            (0: Ascend, 1: Descend, 2: Selected).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    sort_order: framework.Variant[int] = framework.Variant(2)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Sort Nodes tool.

    This window provides a UI for selecting the sort order and applying
    the sort operation to the selected nodes in the Maya outliner.
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
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the window
                instance. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI
                elements to.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        sort_order: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        sort_order.addItems(["Ascend", "Descend", "Selected"])
        main_layout.addRow(widgets.FormLabel("Sort Order"), sort_order)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.sort_order.bind(
            setter=sort_order.setCurrentIndex,
            getter=sort_order.currentIndex,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by applying the configured settings."""
        self.save_settings()
        main()


def option(unique_id: str = "") -> None:
    """Shows the tool's option window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the sort nodes operation on the current selection.

    If no settings are provided, it automatically reads the saved settings
    from the disk before executing.

    Args:
        settings (Settings | None, optional): The settings instance to use for
            the sort operation. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select objects to sort nodes in the outliner.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: utils.Result = dcc.node.sort(
        selection,
        settings.sort_order.value(),
    )
    result.log(_logger)
