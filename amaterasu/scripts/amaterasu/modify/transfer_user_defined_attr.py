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
"""Tool for transferring and managing user-defined attributes in Maya.

This module provides a UI tool to copy user-defined attributes from one node
and paste them to others. It supports maintaining multiple attribute 'stocks'
via tabs and exporting/importing these stocks as JSON files.
"""

from __future__ import annotations
from typing import Any
import json
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Transfer User Defined Attr"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

MIME_TYPE: str = "application/x-amaterasu-tuda-data"


class Settings(framework.ToolSettings):
    """Settings for the Transfer User Defined Attr tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class AttributePage(QtWidgets.QWidget):
    """A single page widget holding a list of stored attributes."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the AttributePage widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.__list: widgets.ListWidget = widgets.ListWidget(self)
        self.__list.set_placeholder_text("Select a node and click 'Copy'")
        self.__list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.__list.setAlternatingRowColors(True)
        self.__list.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.__list)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Copy", self)
        button.clicked.connect(self.copy_from_maya)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Paste", self)
        button.clicked.connect(self.paste_to_maya)
        btn_layout.addWidget(button)

        self.__context_menu: QtWidgets.QMenu = QtWidgets.QMenu(self.__list)
        self.__action_copy: QtGui.QAction = QtGui.QAction(
            "Copy to Clipboard", self
        )
        self.__action_copy.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        self.__action_copy.triggered.connect(self.copy_to_clipboard)
        self.__list.addAction(self.__action_copy)
        self.__context_menu.addAction(self.__action_copy)

        self.__action_paste: QtGui.QAction = QtGui.QAction(
            "Paste from Clipboard", self
        )
        self.__action_paste.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        self.__action_paste.triggered.connect(self.paste_from_clipboard)
        self.__list.addAction(self.__action_paste)
        self.__context_menu.addAction(self.__action_paste)

        self.__context_menu.addSeparator()

        self.__action_delete: QtGui.QAction = QtGui.QAction(
            "Delete Selected", self
        )
        self.__action_delete.setShortcut(QtGui.QKeySequence.StandardKey.Delete)
        self.__action_delete.triggered.connect(self.__list.delete_selected_item)
        self.__list.addAction(self.__action_delete)
        self.__context_menu.addAction(self.__action_delete)

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Shows the right-click context menu for the list.

        Args:
            pos (QtCore.QPoint): The local position where the right-click occurred.
        """
        has_selection: bool = bool(self.__list.selectedItems())
        self.__action_copy.setEnabled(has_selection)
        self.__action_delete.setEnabled(has_selection)

        clipboard: QtGui.QClipboard = QtWidgets.QApplication.clipboard()
        mime_data: QtCore.QMimeData = clipboard.mimeData()
        has_clipboard_data: bool = mime_data.hasFormat(MIME_TYPE)
        self.__action_paste.setEnabled(has_clipboard_data)

        global_pos: QtCore.QPoint = self.__list.mapToGlobal(pos)
        self.__context_menu.exec_(global_pos)

    def _add_list_item(self, data: dcc.attribute.TransferBuffer) -> None:
        """Helper to create a list item containing hidden AttributeData.

        Args:
            data (dcc.attribute.AttributeData): The attribute data object.
        """
        item = QtWidgets.QListWidgetItem(f"{data.name}  [{data.attr_type}]")
        item.setData(QtCore.Qt.ItemDataRole.UserRole, data)
        self.__list.addItem(item)

    @QtCore.Slot()
    def copy_from_maya(self) -> None:
        """Copies user-defined attributes from the selected Maya node into the UI list."""
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.warning("Select a node to copy attributes from.")
            return

        self.__list.clear()
        attrs_data: list[dcc.attribute.TransferBuffer] = (
            dcc.attribute.extract_transfer_buffers(selection[0])
        )
        for data in attrs_data:
            self._add_list_item(data)

    @dcc.undo
    def paste_to_maya(self) -> None:
        """Pastes the selected attributes from the UI list to the selected Maya nodes."""
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.warning("Select node(s) to paste attributes to.")
            return

        items: list[
            QtWidgets.QListWidgetItem
        ] = self.__list.selectedItems() or [
            self.__list.item(i) for i in range(self.__list.count())
        ]
        if not items:
            return

        datas: list[dcc.attribute.TransferBuffer] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
        ]
        result: utils.Result = utils.Result()
        for node in selection:
            r: utils.Result = dcc.attribute.apply_transfer_buffer(node, datas)
            result.merge(r)

        result.log(_logger)

    def get_export_data(self) -> list[dict[str, Any]]:
        """Gets all attributes in the list as dictionaries for exporting.

        Returns:
            list[dict[str, Any]]: A list of dictionaries representing the attribute data.
        """
        items: list[QtWidgets.QListWidgetItem] = [
            self.__list.item(i) for i in range(self.__list.count())
        ]
        return [
            item.data(QtCore.Qt.ItemDataRole.UserRole).to_dict()
            for item in items
        ]

    def load_import_data(self, raw_list: list[dict[str, Any]]) -> None:
        """Loads attributes from a list of dictionaries.

        Args:
            raw_list (list[dict[str, Any]]): A list of dictionaries representing the attribute data.
        """
        for raw_dict in raw_list:
            data: dcc.attribute.TransferBuffer = (
                dcc.attribute.TransferBuffer.from_dict(raw_dict)
            )
            self._add_list_item(data)

    @QtCore.Slot()
    def copy_to_clipboard(self) -> None:
        """Copies selected items to the system clipboard as JSON."""
        items: list[
            QtWidgets.QListWidgetItem
        ] = self.__list.selectedItems() or [
            self.__list.item(i) for i in range(self.__list.count())
        ]
        json_data: list[Any] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole).to_dict()
            for item in items
        ]

        mime_data = QtCore.QMimeData()
        mime_data.setData(
            MIME_TYPE, QtCore.QByteArray(json.dumps(json_data).encode("utf-8"))
        )
        QtWidgets.QApplication.clipboard().setMimeData(mime_data)

    @QtCore.Slot()
    def paste_from_clipboard(self) -> None:
        """Pastes JSON attributes from the system clipboard into the UI list."""
        mime_data: QtCore.QMimeData = (
            QtWidgets.QApplication.clipboard().mimeData()
        )
        if not mime_data.hasFormat(MIME_TYPE):
            return

        json_bytes: QtCore.QByteArray = mime_data.data(MIME_TYPE)
        raw_list: Any = json.loads(bytes(json_bytes).decode("utf-8"))  # type: ignore
        self.load_import_data(raw_list)
        mime_data.clear()


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Transfer User Defined Attr tool."""

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
        self.resize(350, 450)
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
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__tab = widgets.TabWidget(
            self, default_tab_name="Buffer", title=__product__
        )
        self.__tab.setDocumentMode(True)
        self.__tab.add_requested.connect(self.add_tab)
        self.add_tab("Buffer")
        main_layout.addWidget(self.__tab)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    def add_tab(self, label: str) -> None:
        """Adds a new Stock tab to the tool window.

        Args:
            label (str): The label for the new tab.
        """
        page_widget = AttributePage(self)
        self.__tab.add_custom_tab(page_widget, label)

    @QtCore.Slot()
    def import_json(self) -> None:
        """Imports a JSON file into the current stock tab."""
        current_tab: QtWidgets.QWidget = self.__tab.currentWidget()
        if not isinstance(current_tab, AttributePage):
            _logger.warning("No active stock tab found.")
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list: Any = json.load(f)

            current_tab.load_import_data(raw_list)

        except json.JSONDecodeError as e:
            _logger.error("Invalid JSON format in file %s: %s", file_path, e)

        except OSError as e:
            _logger.error("File access error '%s': %s", file_path, e)

    @QtCore.Slot()
    def export_json(self) -> None:
        """Exports the current stock tab to a JSON file."""
        current_tab: QtWidgets.QWidget = self.__tab.currentWidget()
        if not isinstance(current_tab, AttributePage):
            _logger.warning("No active stock tab found.")
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            json_data: list[dict[str, Any]] = current_tab.get_export_data()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

        except OSError as e:
            _logger.error("File write error for %s: %s", file_path, e)

        except TypeError as e:
            _logger.error("JSON serialization error: %s", e)


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
