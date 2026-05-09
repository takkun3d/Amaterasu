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
"""Tool for stocking and transferring attribute values in Maya.

This tool stocks the values of attributes and allows you to copy and paste
them across different nodes using search and replace functionality.
"""

from __future__ import annotations
from typing import Any, cast
import json
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Stocker"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)

MIME_TYPE: str = "application/x-amaterasu-stocker-data"


class Settings(framework.ToolSettings):
    """Settings for the Stocker tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        search (framework.Variant[str]): The saved search string.
        replace (framework.Variant[str]): The saved replace string.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    search: framework.Variant[str] = framework.Variant("")
    replace: framework.Variant[str] = framework.Variant("")


class StockerViewWidget(widgets.TreeWidget):
    """Tree view for Stocker utilizing the simplified QTreeWidget."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the StockerViewWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setHeaderLabels(["Node", "Attribute", "Value"])
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.set_placeholder_text(
            "Select attributes in Channel Box and click 'Copy'"
        )

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.__action_copy = QtGui.QAction("Copy to Clipboard", self)
        self.__action_copy.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        self.__action_copy.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.__action_copy.triggered.connect(self.copy_to_clipboard)
        self.addAction(self.__action_copy)

        self.__action_paste = QtGui.QAction("Paste from Clipboard", self)
        self.__action_paste.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        self.__action_paste.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.__action_paste.triggered.connect(self.paste_from_clipboard)
        self.addAction(self.__action_paste)

        self.__action_delete = QtGui.QAction("Delete Selected", self)
        self.__action_delete.setShortcut(QtGui.QKeySequence.StandardKey.Delete)
        self.__action_delete.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.__action_delete.triggered.connect(self.delete_selected_items)
        self.addAction(self.__action_delete)

        self.__context_menu = QtWidgets.QMenu(self)
        self.__context_menu.addAction(self.__action_copy)
        self.__context_menu.addAction(self.__action_paste)
        self.__context_menu.addSeparator()
        self.__context_menu.addAction(self.__action_delete)

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Shows the right-click context menu.

        Args:
            pos (QtCore.QPoint): The local position where the right-click occurred.
        """
        has_selection: bool = bool(self.selectedItems())
        self.__action_copy.setEnabled(has_selection)
        self.__action_delete.setEnabled(has_selection)

        clipboard: QtGui.QClipboard = QtWidgets.QApplication.clipboard()
        self.__action_paste.setEnabled(
            clipboard.mimeData().hasFormat(MIME_TYPE)
        )

        global_pos: QtCore.QPoint = self.viewport().mapToGlobal(pos)
        self.__context_menu.exec_(global_pos)

    def append_item(self, node_name: str, attr_name: str, value: Any) -> None:
        """Appends a new attribute item to the tree.

        Args:
            node_name (str): The name of the Maya node.
            attr_name (str): The name of the attribute.
            value (Any): The value of the attribute.
        """
        plug: str = f"{node_name}.{attr_name}"
        try:
            nice_name: str = cmds.attributeName(plug, long=True)
        except RuntimeError:
            nice_name = attr_name

        item = QtWidgets.QTreeWidgetItem([node_name, nice_name, str(value)])
        item.setData(1, QtCore.Qt.ItemDataRole.UserRole, attr_name)
        item.setData(2, QtCore.Qt.ItemDataRole.UserRole, type(value))
        self.addTopLevelItem(item)

    def get_item_data(
        self, item: QtWidgets.QTreeWidgetItem
    ) -> tuple[str, str, Any]:
        """Extracts node, attribute, and formatted value from a tree item.

        Args:
            item (QtWidgets.QTreeWidgetItem): The tree widget item to extract data from.

        Returns:
            tuple[str, str, Any]: A tuple containing the node name, attribute name,
                and its formatted value.
        """
        node_name: str = item.text(0)
        attr_name: str = item.data(1, QtCore.Qt.ItemDataRole.UserRole)
        attr_type: type = item.data(2, QtCore.Qt.ItemDataRole.UserRole)
        value_str: str = item.text(2)

        value: Any = value_str
        if attr_type is bool:
            value = value_str.lower() in ("true", "1")

        else:
            try:
                value = attr_type(value_str)

            except ValueError:
                pass

        return node_name, attr_name, value

    def get_export_data(self) -> list[list[Any]]:
        """Gets all items in the tree for JSON exporting.

        Returns:
            list[list[Any]]: A list containing all rows of data formatted for export.
        """
        items: list[QtWidgets.QTreeWidgetItem] = [
            self.topLevelItem(i) for i in range(self.topLevelItemCount())
        ]
        return [list(self.get_item_data(item)) for item in items]

    def load_import_data(self, datas: list[list[Any]]) -> None:
        """Loads items from imported JSON data.

        Args:
            datas (list[list[Any]]): A list of data rows to import and display.
        """
        for data in datas:
            if len(data) >= 3:
                self.append_item(data[0], data[1], data[2])

    @QtCore.Slot()
    def copy_to_clipboard(self) -> None:
        """Copies the selected items to the system clipboard as JSON."""
        items: list[QtWidgets.QTreeWidgetItem] = self.selectedItems() or [
            self.topLevelItem(i) for i in range(self.topLevelItemCount())
        ]
        data: list[tuple[str, str, Any]] = [
            self.get_item_data(item) for item in items
        ]

        mime_data = QtCore.QMimeData()
        mime_data.setData(
            MIME_TYPE, QtCore.QByteArray(json.dumps(data).encode("utf-8"))
        )
        QtWidgets.QApplication.clipboard().setMimeData(mime_data)

    @QtCore.Slot()
    def paste_from_clipboard(self) -> None:
        """Pastes items from the system clipboard JSON into the tree."""
        mime_data: QtCore.QMimeData = (
            QtWidgets.QApplication.clipboard().mimeData()
        )
        if not mime_data.hasFormat(MIME_TYPE):
            return

        json_bytes: QtCore.QByteArray = mime_data.data(MIME_TYPE)
        datas: Any = json.loads(bytes(json_bytes).decode("utf-8"))  # type: ignore
        for data in datas:
            self.append_item(data[0], data[1], data[2])

        mime_data.clear()

    @QtCore.Slot()
    def copy(self) -> None:
        """Copies attribute data from selected nodes in the Channel Box to the tree."""
        self.clear()
        plugs: list[str] = dcc.selection.get_selected_channel_box_plugs()
        for plug in plugs:
            node: str
            attr: str
            node, attr = plug.split(".", 1)
            value: Any = cmds.getAttr(plug)
            self.append_item(node, attr, value)

        if self.topLevelItemCount() != 0:
            return

        selection: list[str] = cmds.ls(selection=True)
        for node in selection:
            attrs: list[str] = cmds.listAttr(node) or []
            for attr in attrs:
                try:
                    plug = f"{node}.{attr}"
                    attr_type: str = cmds.getAttr(plug, type=True)
                    if attr_type in ("float3", "double3", "long3"):
                        continue

                    if cmds.getAttr(plug, channelBox=True) or cmds.getAttr(
                        plug, keyable=True
                    ):
                        value = cmds.getAttr(plug)
                        self.append_item(node, attr, value)

                except (RuntimeError, ValueError):
                    pass

    @QtCore.Slot(str, str)
    def paste(self, search: str = "", replace: str = "") -> None:
        """Pastes the tree's attribute values to the selected nodes in Maya.

        Args:
            search (str, optional): The string to search for in node names.
                Defaults to "".
            replace (str, optional): The string to replace the search string with.
                Defaults to "".
        """
        items: list[QtWidgets.QTreeWidgetItem] = self.selectedItems() or [
            self.topLevelItem(i) for i in range(self.topLevelItemCount())
        ]
        selection: list[str] = cmds.ls(selection=True)
        is_selection: bool = bool(selection)

        for item in items:
            node: str
            attr: str
            value: Any
            node, attr, value = self.get_item_data(item)

            target_nodes: list[str] = selection
            if not is_selection:
                target_node: str = node.replace(search, replace)
                if cmds.objExists(target_node):
                    target_nodes = [target_node]

            for dst_node in target_nodes:
                plug: str = f"{dst_node}.{attr}"
                try:
                    if cmds.attributeQuery(attr, node=dst_node, exists=True):
                        cmds.setAttr(plug, value)

                except RuntimeError:
                    _logger.error("Failed to set value. : %s", plug)


class Stock(QtWidgets.QWidget):
    """The main widget containing the Stocker tree view and controls."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the Stock widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        self.__viewer = StockerViewWidget(self)
        main_layout.addWidget(self.__viewer, 0, 0, 1, 2)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout, 1, 0, 1, 2)

        layout.addWidget(QtWidgets.QLabel("Find & Replace :", self))

        self.search = QtWidgets.QLineEdit(self)
        layout.addWidget(self.search)

        self.replace = QtWidgets.QLineEdit(self)
        layout.addWidget(self.replace)

        clear_button = QtWidgets.QPushButton("Clear", self)
        clear_button.clicked.connect(self.clear)
        layout.addWidget(clear_button)

        copy_button = QtWidgets.QPushButton("Copy", self)
        copy_button.clicked.connect(self.copy)
        main_layout.addWidget(copy_button, 3, 0)

        paste_button = QtWidgets.QPushButton("Paste", self)
        paste_button.clicked.connect(self.paste)
        main_layout.addWidget(paste_button, 3, 1)

    @QtCore.Slot()
    def clear(self) -> None:
        """Clears the search and replace line edits."""
        self.search.setText("")
        self.replace.setText("")

    @QtCore.Slot()
    def copy(self) -> None:
        """Triggers the copy action on the viewer."""
        self.__viewer.copy()

    @QtCore.Slot()
    @dcc.undo
    def paste(self) -> None:
        """Triggers the paste action on the viewer and applies undo chunk."""
        selection: list[str] = cmds.ls(selection=True)
        if self.search.text() or self.replace.text():
            cmds.select(clear=True)

        self.__viewer.paste(self.search.text(), self.replace.text())

        if selection:
            cmds.select(*selection)

    def viewer(self) -> StockerViewWidget:
        """Returns the internal tree viewer widget.

        Returns:
            StockerViewWidget: The internal tree view widget.
        """
        return self.__viewer


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Stocker tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow.

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
        self.__tab: widgets.TabWidget

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates custom menus for data import/export.

        Args:
            menu_bar (QtWidgets.QMenuBar): The main menu bar widget.
        """
        data_menu = QtWidgets.QMenu("Data", self)
        menu_bar.addMenu(data_menu)

        action_import = QtGui.QAction("Import JSON...", self)
        action_import.triggered.connect(self.import_json)
        data_menu.addAction(action_import)

        action_export = QtGui.QAction("Export JSON...", self)
        action_export.triggered.connect(self.export_json)
        data_menu.addAction(action_export)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__tab = widgets.TabWidget(
            self, default_tab_name="Stock", title=__product__
        )
        self.__tab.setDocumentMode(True)
        self.__tab.add_requested.connect(self.add_tab)

        self.add_tab("Stock")
        main_layout.addWidget(self.__tab)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.search.bind(
            setter=self.set_current_search_text,
            getter=self.current_search_text,
        )
        settings.replace.bind(
            setter=self.set_current_replace_text,
            getter=self.current_replace_text,
        )

    def current_search_text(self) -> str:
        """Gets the search text from the active tab.

        Returns:
            str: The current search text.
        """
        current: Stock = cast(Stock, self.__tab.currentWidget())
        return current.search.text()

    def set_current_search_text(self, value: str) -> None:
        """Sets the search text to the active tab.

        Args:
            value (str): The text to set.
        """
        current: Stock = cast(Stock, self.__tab.currentWidget())
        current.search.setText(value)

    def current_replace_text(self) -> str:
        """Gets the replace text from the active tab.

        Returns:
            str: The current replace text.
        """
        current: Stock = cast(Stock, self.__tab.currentWidget())
        return current.replace.text()

    def set_current_replace_text(self, value: str) -> None:
        """Sets the replace text to the active tab.

        Args:
            value (str): The text to set.
        """
        current: Stock = cast(Stock, self.__tab.currentWidget())
        current.replace.setText(value)

    def add_tab(self, label: str) -> None:
        """Adds a new Stock tab to the tool window.

        Args:
            label (str): The label for the new tab.
        """
        page_widget = Stock(self)
        self.__tab.add_custom_tab(page_widget, label)

        settings: Settings = self.tool_settings()
        page_widget.search.setText(settings.search.value())
        page_widget.replace.setText(settings.replace.value())

    @QtCore.Slot()
    def import_json(self) -> None:
        """Imports a JSON file into the current stock tab."""
        stock_widget: Stock = cast(Stock, self.__tab.currentWidget())
        if not stock_widget:
            _logger.warning("No active stock tab found.")
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)

            stock_widget.viewer().load_import_data(raw_list)

        except json.JSONDecodeError as e:
            _logger.error("Invalid JSON format in file %s: %s", file_path, e)

        except OSError as e:
            _logger.error("File access error %s: %s", file_path, e)

    @QtCore.Slot()
    def export_json(self) -> None:
        """Exports the current stock tab to a JSON file."""
        stock_widget: Stock = cast(Stock, self.__tab.currentWidget())
        if not stock_widget:
            _logger.warning("No active stock tab found.")
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            json_data: list[list[Any]] = stock_widget.viewer().get_export_data()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

        except OSError as e:
            _logger.error("File write error for %s: %s", file_path, e)

        except TypeError as e:
            _logger.error("JSON serialization error : %s", e)


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
