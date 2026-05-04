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
"""Selects each Nth edges."""

from __future__ import annotations
from maya import cmds, mel
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Select Each Nth Edges"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Select Each Nth Edges tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        nth (framework.Variant[int]): The skip interval.
        mode (framework.Variant[int]): The selection mode
            (0: Loop, 1: Ring, 2: Both).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    nth: framework.Variant[int] = framework.Variant(1)
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

        nth: QtWidgets.QSpinBox = QtWidgets.QSpinBox(parent)
        nth.setRange(1, 99)
        nth.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel("N th"), nth)

        mode: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        mode.addItems(["Loop", "Ring", "Both"])
        main_layout.addRow(widgets.FormLabel("Mode"), mode)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.nth.bind(
            setter=nth.setValue,
            getter=nth.value,
        )
        settings.mode.bind(
            setter=mode.setCurrentIndex,
            getter=mode.currentIndex,
        )

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
    """Executes the select each nth edges operation.

    Args:
        settings (Settings | None, optional): The tool settings to apply.
            If None, the default settings will be loaded. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        _logger.error("Select polygon edges to execute.")
        return

    edges: list[str] = dcc.mesh.to_edge(selection)
    if not edges:
        _logger.error("Select polygon edges to execute.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result_edges: list[str] = dcc.mesh.get_nth_edges(
        edges,
        settings.nth.value(),
        settings.mode.value(),
    )

    if not result_edges:
        _logger.info("There were no matching nth edges.")
        return

    mel.eval("SelectEdgeMask")
    cmds.select(*result_edges, replace=True)
    _logger.info("Done.")
