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
"""Rounds off the time of keyframes on selected nodes.

This module provides functionality to round the keyframe times of animation
curves connected to selected nodes. It supports targeting only the selected
nodes or their entire hierarchy.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Round Off Time"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Round Off Time tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        hierarchy (framework.Variant[int]): Mode for applying the keyframe.
            0 for 'Selected', 1 for 'Below'.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    hierarchy: framework.Variant[int] = framework.Variant(1)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Round Off Time tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): A unique ID for restoring window
                states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        hierarchy_combo: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        hierarchy_combo.addItems(["Selected", "Below"])
        main_layout.addRow(widgets.FormLabel("Hierarchy"), hierarchy_combo)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.hierarchy.bind(
            setter=hierarchy_combo.setCurrentIndex,
            getter=hierarchy_combo.currentIndex,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(nodes: list[str]) -> bool:
    """Rounds off keyframe times on the animation curves of the given nodes.

    Args:
        nodes (list[str]): A list of Maya node names to process.

    Returns:
        bool: True if the operation was successful.
    """
    for node in nodes:
        connected_curves: list[str] = dcc.animation.get_anim_curves(node)
        for curve in connected_curves:
            times: list[float] = cmds.keyframe(
                curve, query=True, timeChange=True
            )  # type: ignore
            for time in times:
                if int(time) == time:
                    continue

                cmds.setKeyframe(curve, insert=True, time=round(time))
                cmds.cutKey(curve, time=(time, time))

    return True


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the keyframe round-off based on the current UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to
            use. If None, it initializes settings from the module name and
            reads them from the file. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True, long=True) or []
    if not selection:
        _logger.error("Select node(s) to round off keyframe time.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    if settings.hierarchy.value():
        selection = dcc.node.get_children(selection)

    result: bool = apply(selection)
    if result:
        _logger.info("Done.")
