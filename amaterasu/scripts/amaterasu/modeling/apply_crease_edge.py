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
"""Tool for applying crease values to hard edges on polygon meshes.

This module provides a UI and functions to automatically detect hard edges
from selected polygon components and apply crease values to them.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils

__product__: str = "Apply Crease Edge"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Apply Crease Edge tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        crease_value (framework.Variant[float]): Saved crease value.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    crease_value: framework.Variant[float] = framework.Variant(2.0)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Apply Crease Edge tool."""

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
            unique_id (str, optional): A unique ID for restoring window states.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(300, 80)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(parent)

        crease: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        crease.setRange(0.0, 2.0)
        crease.setSingleStep(0.1)
        main_layout.addRow("Crease Value", crease)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.crease_value.bind(
            setter=crease.setValue,
            getter=crease.value,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the main tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def set_crease_from_edge_type(edges: list[str], crease_value: float) -> bool:
    """Applies crease values to the given edges based on their hardness.

    Hard edges will receive the specified crease value, while soft edges
    will have their crease value removed (set to 0).

    Args:
        edges (list[str]): A list of polygon edge names to process.
        crease_value (float): The crease value to apply to hard edges.

    Returns:
        bool: True if the operation was successful.
    """
    all_hard_edges: set[str] = set(dcc.mesh.get_hard_edges(edges))
    components: dict[str, list[str]] = dcc.mesh.group_by_node(edges)
    for _, node_edges in components.items():
        node_edges_set: set[str] = set(node_edges)
        set_crease_edges: list[str] = list(node_edges_set & all_hard_edges)
        remove_crease_edges: list[str] = list(node_edges_set - all_hard_edges)
        if set_crease_edges:
            cmds.polyCrease(
                *set_crease_edges, value=crease_value, createHistory=False
            )

        if remove_crease_edges:
            cmds.polyCrease(*remove_crease_edges, value=0, createHistory=False)

    return True


def option(unique_id: str = "") -> None:
    """Entry point for launching the tool window.

    Args:
        unique_id (str, optional): A unique ID for restoring window states.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Gathers current selection and applies crease settings.

    If no edges are selected, it attempts to convert the current
    selection to edges. It then calls the core crease application logic.

    Args:
        settings (Settings | None, optional): Tool settings instance.
            If None, the default settings will be acquired and read.
            Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    edges: list[str] = cmds.filterExpand(selectionMask=32) or []
    if not edges:
        selection = cmds.ls(selection=True, flatten=True) or []
        if not selection:
            _logger.error("Select objects or components to set crease.")
            return

        edges = dcc.mesh.to_edge(selection)
        if not edges:
            _logger.error("Failed to get polygon edges.")
            cmds.select(*selection)
            return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = set_crease_from_edge_type(
        edges, settings.crease_value.value()
    )
    if result:
        _logger.info("Done.")

    cmds.select(*selection)
