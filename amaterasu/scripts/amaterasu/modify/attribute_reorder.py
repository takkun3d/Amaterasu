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
"""Reorders the user-defined attributes on the selected node."""

from __future__ import annotations
from maya import cmds

from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Attribute Reorder"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

LIST_VIEW_QSS: str = """
QListWidget {
    outline: none;
}
QListWidget::item {
    padding: 3px;
    border-bottom: 1px solid #3a3a3a;
}
QListWidget::item:hover {
    background-color: #4a4a4a;
}
"""


class Settings(framework.ToolSettings):
    """Settings for the Attribute Reorder tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Attribute Reorder tool."""

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
            unique_id (str, optional): A unique identifier for the window instance.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 300)
        self.__node: QtWidgets.QLineEdit
        self.__list: widgets.ListWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__node = QtWidgets.QLineEdit(self)
        self.__node.setEnabled(False)
        main_layout.addWidget(self.__node, 0, 0, 1, 2)

        self.__list = widgets.ListWidget(self)
        self.__list.set_placeholder_text("Select a node and click 'Analyze'")
        self.__list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.__list.setDragEnabled(True)
        self.__list.setAcceptDrops(True)
        self.__list.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove
        )
        self.__list.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.__list.setStyleSheet(LIST_VIEW_QSS)
        main_layout.addWidget(self.__list, 1, 0, 1, 2)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Analyze", self)
        button.clicked.connect(self.analyze)
        main_layout.addWidget(button, 2, 0)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button, 2, 1)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    def analyze(self) -> None:
        """Analyzes the selected node and populates the list with its user-defined attributes."""
        self.__node.clear()
        self.__list.clear()

        selection: list[str] = cmds.ls(selection=True) or []
        if not selection:
            _logger.warning("Select a node to reorder attributes.")
            return

        if len(selection) > 1:
            _logger.warning("Please select only one node.")
            return

        node: str = selection[0]
        attributes: list[str] = cmds.listAttr(node, userDefined=True) or []
        if not attributes:
            _logger.warning(
                "The selected node '%s' has no user-defined attributes.",
                node,
            )
            return

        attributes = [f":: {attr}" for attr in attributes]
        self.__node.setText(node)
        self.__list.addItems(attributes)

    def apply(self) -> None:
        """Applies the new attribute order to the node."""
        node: str = self.__node.text()
        if not node:
            return

        order: list[str] = [
            self.__list.item(i).text().removeprefix(":: ")
            for i in range(self.__list.count())
        ]
        answer: int = QtWidgets.QMessageBox.warning(
            self,
            __product__,
            "This action relies on Maya's Undo queue and cannot be undone once completed.\n"
            "Maya's Undo history will be flushed.\n\nDo you want to continue?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if answer == QtWidgets.QMessageBox.StandardButton.No:
            return

        self.save_settings()

        result: utils.Result = _execute_reorder(node, order)
        result.log(_logger)


def _execute_reorder(node: str, attr_orders: list[str]) -> utils.Result:
    """Wraps the core reordering logic with Result logging.

    Args:
        node (str): The name of the Maya node.
        attr_orders (list[str]): The desired order of the attribute names.

    Returns:
        utils.Result: An object containing execution details and error logs.
    """
    result: utils.Result = utils.Result()

    try:
        dcc.attribute.reorder_user_attributes(node, attr_orders)

    except RuntimeError as e:
        result.add_failure(node, f"Failed to reorder attributes: {e}")

    return result


def main(unique_id: str = "") -> None:
    """Shows the tool's option window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
