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
"""Tool for managing instance nodes in Autodesk Maya.

This module provides a UI to find, select, un-instance (convert to object),
and delete instance nodes within the Maya scene.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Instance Manager"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Instance Manager tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Instance Manager tool."""

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
        self.resize(400, 300)
        self.__tree: widgets.TreeWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__tree = widgets.TreeWidget(self)
        self.__tree.setHeaderLabels(["Instance Nodes"])
        self.__tree.setAlternatingRowColors(True)
        self.__tree.setRootIsDecorated(False)
        self.__tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.__tree.itemSelectionChanged.connect(self.select_nodes)
        layout.addWidget(self.__tree)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Instance to Object"
        )
        button.clicked.connect(self.instance_to_object)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Delete")
        button.clicked.connect(self.delete_instance)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Update")
        button.clicked.connect(self.update_view)
        btn_layout.addWidget(button)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        self.update_view()

    @QtCore.Slot()
    def update_view(self) -> None:
        """Updates the tree view with current instance nodes in the scene."""
        self.__tree.clear()
        instance_list: list[str] = dcc.scene.find_instance_nodes()
        for instance in instance_list:
            item = QtWidgets.QTreeWidgetItem([instance])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, instance)
            self.__tree.addTopLevelItem(item)

    @QtCore.Slot()
    @dcc.undo
    def select_nodes(self) -> None:
        """Selects the corresponding Maya nodes when items are selected in the tree."""
        nodes: list[str] = self.__node_list()
        if not nodes:
            cmds.select(clear=True)
        else:
            cmds.select(*nodes)

    @QtCore.Slot()
    @dcc.undo
    def instance_to_object(self) -> None:
        """Converts selected instance nodes into independent objects."""
        result: utils.Result = utils.Result()
        items: list[QtWidgets.QTreeWidgetItem] = self.__tree.selectedItems()
        for item in items:
            node: str = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            r: utils.Result = dcc.instance.to_object(node)
            if r.status() == utils.ResultStatus.SUCCESS:
                index: int = self.__tree.indexOfTopLevelItem(item)
                if index >= 0:
                    self.__tree.takeTopLevelItem(index)

            result.merge(r)

        result.log(_logger, "Converted instances to objects.")

    @QtCore.Slot()
    @dcc.undo
    def delete_instance(self) -> None:
        """Deletes the selected instance nodes."""
        result: utils.Result = utils.Result()
        items: list[QtWidgets.QTreeWidgetItem] = self.__tree.selectedItems()
        for item in items:
            node: str = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            r: utils.Result = dcc.instance.delete(node)
            if r.status() == utils.ResultStatus.SUCCESS:
                index: int = self.__tree.indexOfTopLevelItem(item)
                if index >= 0:
                    self.__tree.takeTopLevelItem(index)

            result.merge(r)

        result.log(_logger, "Deleted instances.")

    def __node_list(self) -> list[str]:
        """Extracts the node paths from the currently selected tree items.

        Returns:
            list[str]: A list of selected node paths.
        """
        return [
            i.data(0, QtCore.Qt.ItemDataRole.UserRole)
            for i in self.__tree.selectedItems()
        ]


def main(unique_id: str = "") -> None:
    """Entry point for launching the Instance Manager tool window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
