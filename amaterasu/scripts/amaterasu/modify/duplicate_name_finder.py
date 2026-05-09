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
"""Tool for finding and managing nodes with duplicate names in Maya.

This module provides a user interface to list, select, and intuitively rename
nodes that share the same short name but have different absolute DAG paths.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__ = "Duplicate Name Finder"
__version__: str = "1.00"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Duplicate Name Finder tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Duplicate Name Finder tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
            unique_id (str, optional): A unique identifier for the window instance.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 500)
        self.__tree: widgets.TreeWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__tree = widgets.TreeWidget(self)
        self.__tree.setHeaderLabels(["Duplicate Nodes"])
        self.__tree.setAlternatingRowColors(True)
        self.__tree.itemChanged.connect(self.item_changed)
        self.__tree.itemSelectionChanged.connect(self.selection_changed)
        layout.addWidget(self.__tree)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Update / Search")
        button.clicked.connect(self.update_view)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Expand All")
        button.clicked.connect(self.__tree.expandAll)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Collapse All")
        button.clicked.connect(self.__tree.collapseAll)
        btn_layout.addWidget(button)

        self.tool_settings().window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    @QtCore.Slot()
    def update_view(self) -> None:
        """Updates the tree view with current duplicate nodes in the scene.

        Finds all nodes with non-unique short names and populates the tree,
        grouping them by their shared short names.
        """
        self.__tree.clear()
        duplicate_nodes: list[str] = dcc.scene.find_duplicate_name_nodes()
        groups: dict[str, QtWidgets.QTreeWidgetItem] = {}

        for node in duplicate_nodes:
            short_name: str = node.split("|")[-1]
            if short_name not in groups:
                parent = QtWidgets.QTreeWidgetItem([short_name])
                self.__tree.addTopLevelItem(parent)
                groups[short_name] = parent

            child = QtWidgets.QTreeWidgetItem([node])
            child.setData(0, QtCore.Qt.ItemDataRole.UserRole, node)
            child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            groups[short_name].addChild(child)

        if not duplicate_nodes:
            _logger.info("No duplicate names found! Scene is clean.")

    @QtCore.Slot(QtWidgets.QTreeWidgetItem, int)
    @dcc.undo
    def item_changed(
        self, item: QtWidgets.QTreeWidgetItem, column: int
    ) -> None:
        """Handles the event when a tree item's text is edited.

        Attempts to rename the underlying Maya node to the new text.
        If the rename fails, it reverts the text back to the original node name.

        Args:
            item (QtWidgets.QTreeWidgetItem): The tree item that was edited.
            column (int): The column index that was edited.
        """
        self.__tree.blockSignals(True)
        old_path: str = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        new_short_name: str = item.text(0).split("|")[-1]
        try:
            new_path: str = cmds.rename(old_path, new_short_name)
            item.setText(0, new_path)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, new_path)

        except RuntimeError:
            item.setText(0, old_path)

        self.__tree.blockSignals(False)

    @QtCore.Slot()
    def selection_changed(self) -> None:
        """Selects the corresponding Maya nodes when items are selected in the tree."""
        nodes: list[str] = [
            i.data(0, QtCore.Qt.ItemDataRole.UserRole)
            for i in self.__tree.selectedItems()
            if i.parent()
        ]
        if nodes:
            cmds.select(*nodes)


def main(unique_id: str = "") -> None:
    """Entry point for launching the Duplicate Name Finder tool window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
