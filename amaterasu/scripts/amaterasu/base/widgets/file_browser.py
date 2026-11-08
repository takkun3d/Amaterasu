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
"""Provides file browsing functionality for the Amaterasu toolset."""

from __future__ import annotations
from typing import Any, Callable
import os
import shutil
import functools
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc
from amaterasu.base.widgets.icon_button import IconButton


class IconProvider(QtWidgets.QFileIconProvider):
    """Custom icon provider for file browser."""

    def icon(self, file_info: QtCore.QFileInfo) -> QtGui.QIcon:  # type: ignore
        """Returns the appropriate QIcon for a given file.

        Args:
            file_info (QtCore.QFileInfo): File information object.

        Returns:
            QtGui.QIcon: The icon representing the file.
        """
        file_path: str = file_info.filePath()
        if file_path.endswith((".jpg", ".png")):
            pixmap: QtGui.QPixmap = QtGui.QPixmap()
            pixmap.load(file_path)
            return QtGui.QIcon(pixmap)

        return super().icon(file_info)


class FileBrowserItem(QtGui.QStandardItem):
    """Represents an item within the file browser."""

    thumbnail_filename: str = "thumbnail.jpg"
    no_image: str = "a_no_image.png"

    def __init__(self, data_path: str) -> None:
        """Initializes the FileBrowserItem.

        Args:
            data_path (str): The absolute path to the data.
        """
        super().__init__()
        self.__data_path: str = ""
        self.__name: str = ""
        self.__icon_path: str = ""
        self.__extension: str = ""

        if data_path:
            self.set_data_path(data_path)

    def data_path(self) -> str:
        """Gets the data path.

        Returns:
            str: The absolute path of the data.
        """
        return self.__data_path

    def set_data_path(self, path: str) -> None:
        """Sets the data path and updates internal item properties.

        Args:
            path (str): The absolute path to set.
        """
        base_name: str = os.path.basename(path)
        base_name, extension = os.path.splitext(base_name)
        extension: str = extension[1:]

        self.__data_path = path
        self.__name = base_name
        self.__extension = extension
        self.__icon_path = os.path.join(
            self.__data_path, self.thumbnail_filename
        )
        self.setText(f"[{self.__extension}] {self.__name}")

        if os.path.exists(self.__icon_path):
            self.setIcon(QtGui.QIcon(self.__icon_path))
        else:
            self.setIcon(QtGui.QIcon(dcc.get_icon_path(self.no_image)))

    def icon_path(self) -> str:
        """Gets the icon path.

        Returns:
            str: The absolute path to the thumbnail icon.
        """
        return self.__icon_path

    def name(self) -> str:
        """Gets the base name of the item.

        Returns:
            str: The item's base name without extension.
        """
        return self.__name

    def extension(self) -> str:
        """Gets the extension of the item.

        Returns:
            str: The item's file extension.
        """
        return self.__extension


class FileBrowser(QtWidgets.QWidget):
    """Outline style file browser widget."""

    item_selected = QtCore.Signal(FileBrowserItem)
    folder_tree_filter: str = r"^([^.]+)$"

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
    ) -> None:
        """Initializes the FileBrowser widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Window.
        """
        super().__init__(parent, flag)
        self.__filter_text: str = ""
        self.__current_path: str = ""
        self.__current_item: FileBrowserItem | None = None
        self.__action_list: list[Any] = []

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        path_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(path_layout)

        self.__root_dir: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__root_dir.setEnabled(False)
        self.__root_dir.textChanged.connect(self.on_home_directory_changed)
        path_layout.addWidget(self.__root_dir)

        self.__edit_root_dir: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Edit", self
        )
        self.__edit_root_dir.setCheckable(True)
        self.__edit_root_dir.setChecked(False)
        self.__edit_root_dir.clicked.connect(self.on_root_dir_edited)
        path_layout.addWidget(self.__edit_root_dir)

        # Outline View
        outline_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        outline_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(
            outline_widget
        )
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(2)

        outline_header_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        outline_header_layout.setContentsMargins(0, 0, 0, 0)
        outline_header_layout.setSpacing(2)
        outline_header_layout.addStretch(True)
        outline_layout.addLayout(outline_header_layout)

        button: IconButton = IconButton(self)
        button.set_icon(dcc.get_icon_path("a_create_folder.png"))
        button.clicked.connect(self.create_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(dcc.get_icon_path("a_rename.png"))
        button.clicked.connect(self.rename_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(dcc.get_icon_path("a_trash.png"))
        button.clicked.connect(self.remove_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        self.__outline_model = QtWidgets.QFileSystemModel(self)
        self.__outline_model.setFilter(
            QtCore.QDir.Filter.NoDotAndDotDot | QtCore.QDir.Filter.Dirs
        )

        self.__outline_proxy_model = QtCore.QSortFilterProxyModel()
        self.__outline_proxy_model.setSourceModel(self.__outline_model)
        self.__outline_proxy_model.setFilterRegularExpression(
            self.folder_tree_filter
        )

        self.__outline_viewer: QtWidgets.QTreeView = QtWidgets.QTreeView(self)
        self.__outline_viewer.setHeaderHidden(True)
        self.__outline_viewer.setModel(self.__outline_proxy_model)
        self.__outline_viewer.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.__outline_viewer.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__outline_viewer.customContextMenuRequested.connect(
            self.show_outline_context_menu
        )

        for i in range(1, self.__outline_viewer.header().count()):
            self.__outline_viewer.header().hideSection(i)

        self.__outline_viewer.selectionModel().currentChanged.connect(
            self.on_directory_changed
        )
        self.__outline_viewer.clicked.connect(self.on_outline_clicked)
        outline_layout.addWidget(self.__outline_viewer)

        outline_footer_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        outline_footer_layout.setContentsMargins(0, 0, 0, 0)
        outline_footer_layout.setSpacing(2)
        outline_layout.addLayout(outline_footer_layout)

        # File View
        file_viewer_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        file_viewer_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(
            file_viewer_widget
        )
        file_viewer_layout.setContentsMargins(0, 0, 0, 0)
        file_viewer_layout.setSpacing(2)

        self.__file_viewer_header_layout = QtWidgets.QHBoxLayout()
        self.__file_viewer_header_layout.setContentsMargins(0, 0, 0, 0)
        self.__file_viewer_header_layout.setSpacing(2)
        self.__file_viewer_header_layout.addStretch(True)
        file_viewer_layout.addLayout(self.__file_viewer_header_layout)

        button = IconButton(self)
        button.set_icon(dcc.get_icon_path("a_rename.png"))
        button.clicked.connect(self.rename_item)
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(dcc.get_icon_path("a_trash.png"))
        button.clicked.connect(self.remove_item)
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.addWidget(button)

        self.__file_model: QtGui.QStandardItemModel = QtGui.QStandardItemModel()
        self.__file_proxy_model = QtCore.QSortFilterProxyModel()
        self.__file_proxy_model.setSourceModel(self.__file_model)

        self.__file_viewer: QtWidgets.QListView = QtWidgets.QListView(self)
        self.__file_viewer.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.__file_viewer.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.__file_viewer.setModel(self.__file_proxy_model)
        self.__file_viewer.setDragEnabled(False)
        self.__file_viewer.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.__file_viewer.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__file_viewer.customContextMenuRequested.connect(
            self.show_file_viewer_context_menu
        )
        self.__file_viewer.selectionModel().currentChanged.connect(
            self.on_item_changed
        )
        self.__file_viewer.clicked.connect(self.on_view_clicked)
        file_viewer_layout.addWidget(self.__file_viewer, True)

        file_viewer_footer_layout = QtWidgets.QHBoxLayout()
        file_viewer_footer_layout.setContentsMargins(0, 0, 0, 0)
        file_viewer_footer_layout.setSpacing(2)
        file_viewer_layout.addLayout(file_viewer_footer_layout)

        self.__file_viewer_filter: QtWidgets.QLineEdit = QtWidgets.QLineEdit(
            self
        )
        self.__file_viewer_filter.textChanged.connect(self.set_filter)
        file_viewer_footer_layout.addWidget(self.__file_viewer_filter)

        self.__file_viewer_icon_size: QtWidgets.QSlider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal, self
        )
        self.__file_viewer_icon_size.setRange(0, 100)
        self.__file_viewer_icon_size.setValue(50)
        self.__file_viewer_icon_size.setMaximumWidth(100)
        self.__file_viewer_icon_size.sliderMoved.connect(self.set_icon_size)
        file_viewer_footer_layout.addWidget(self.__file_viewer_icon_size)

        # Splitter
        self.__splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(self)
        self.__splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.__splitter.addWidget(outline_widget)
        self.__splitter.addWidget(file_viewer_widget)
        self.__splitter.setSizes([200, 980, 1])
        # self.__splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.__splitter)

        self.__option_widget: QtWidgets.QWidget | None = None

    def on_root_dir_edited(self, enabled: bool) -> None:
        """Toggles the enabled state of the root directory edit line.

        Args:
            enabled (bool): Whether the line edit should be enabled.
        """
        self.__root_dir.setEnabled(enabled)
        self.__edit_root_dir.setText("Lock" if enabled else "Edit")

    def show_outline_context_menu(self, position: QtCore.QPoint) -> None:
        """Shows the context menu on the outline view.

        Args:
            position (QtCore.QPoint): The local cursor position.
        """
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self)

        action: QtGui.QAction = menu.addAction(
            QtGui.QIcon(dcc.get_icon_path("a_create_folder.png")),
            "New Folder",
        )
        action.triggered.connect(self.create_folder)

        if self.__outline_viewer.selectionModel().hasSelection():
            action = menu.addAction(
                QtGui.QIcon(dcc.get_icon_path("a_rename.png")),
                "Rename Folder",
            )
            action.triggered.connect(self.rename_folder)

            action = menu.addAction(
                QtGui.QIcon(dcc.get_icon_path("a_trash.png")),
                "Delete Folder",
            )
            action.triggered.connect(self.remove_folder)

        menu.exec_(self.mapToGlobal(position))

    def show_file_viewer_context_menu(self, position: QtCore.QPoint) -> None:
        """Shows the context menu on the file view.

        Args:
            position (QtCore.QPoint): The local cursor position.
        """
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self)

        for action_data in self.__action_list:
            action: QtGui.QAction = menu.addAction(
                QtGui.QIcon(dcc.get_icon_path(action_data[1])),
                action_data[0],
            )
            action.triggered.connect(action_data[2])

        if self.__file_viewer.selectionModel().hasSelection():
            action = menu.addAction(
                QtGui.QIcon(dcc.get_icon_path("a_rename.png")),
                "Rename Item",
            )
            action.triggered.connect(self.rename_item)

            action = menu.addAction(
                QtGui.QIcon(dcc.get_icon_path("a_trash.png")),
                "Delete Item",
            )
            action.triggered.connect(self.remove_item)

        menu.exec_(self.mapToGlobal(position))

    def root_path(self) -> str:
        """Gets the current root path.

        Returns:
            str: The root path string.
        """
        return self.__root_dir.text()

    def set_root_path(self, path: str) -> None:
        """Sets the root path string in the UI.

        Args:
            path (str): The root directory path.
        """
        self.__root_dir.setText(path)

    def outline_viewer(self) -> QtWidgets.QTreeView:
        """Gets the outline tree viewer widget.

        Returns:
            QtWidgets.QTreeView: The outline viewer.
        """
        return self.__outline_viewer

    def file_viewer(self) -> QtWidgets.QListView:
        """Gets the file list viewer widget.

        Returns:
            QtWidgets.QListView: The file viewer.
        """
        return self.__file_viewer

    def option_widget(self) -> QtWidgets.QWidget | None:
        """Gets the dynamically added option widget.

        Returns:
            QtWidgets.QWidget | None: The option widget if attached.
        """
        return self.__option_widget

    def splitter_widget(self) -> QtWidgets.QSplitter:
        """Gets the main layout splitter widget.

        Returns:
            QtWidgets.QSplitter: The layout splitter.
        """
        return self.__splitter

    def add_option_widget(self, widget: QtWidgets.QWidget) -> None:
        """Adds or replaces the option widget on the splitter.

        Args:
            widget (QtWidgets.QWidget): The widget to add to the layout.
        """
        self.__splitter.addWidget(widget)
        self.__option_widget = widget

    def add_file_view_button(
        self, index: int, label: str, icon_name: str, func: Callable[..., Any]
    ) -> IconButton:
        """Adds a custom button to the header of the file view.

        The current path is passed to the argument when the function
        is executed: `func(current_path)`.

        Args:
            index (int): Insertion index in the layout.
            label (str): Label for the context menu action.
            icon_name (str): The filename of the icon.
            func (Callable[..., Any]): The callback function to execute.

        Returns:
            IconButton: The instantiated button widget.
        """
        button: IconButton = IconButton(self)
        button.set_icon(dcc.get_icon_path(icon_name))
        button.clicked.connect(
            functools.partial(self.on_custom_button_clicked, func)
        )
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.insertWidget(index, button)

        self.__action_list.insert(index, [label, icon_name, func])
        return button

    def on_custom_button_clicked(self, func: Callable[..., Any]) -> None:
        """Executes a custom header button callback.

        Args:
            func (Callable[..., Any]): The target function.
        """
        func(self.__current_path)

    def on_home_directory_changed(self, file_path: str) -> None:
        """Updates internal viewers when the home directory text changes.

        Args:
            file_path (str): The new home directory path.
        """
        self.__current_path = file_path
        self.__outline_viewer.setRootIndex(
            self.__outline_proxy_model.mapFromSource(
                self.__outline_model.setRootPath(file_path)
            )
        )

    def on_outline_clicked(self, _: QtCore.QModelIndex) -> None:
        """Handles click events on the outline tree view.

        Args:
            selected (QtCore.QModelIndex): The selected item index.
        """
        if not self.__outline_viewer.selectionModel().hasSelection():
            self.__outline_viewer.selectionModel().clear()

    def on_view_clicked(self, _: QtCore.QModelIndex) -> None:
        """Handles click events on the file list view.

        Args:
            selected (QtCore.QModelIndex): The selected item index.
        """
        if not self.__file_viewer.selectionModel().hasSelection():
            self.__file_viewer.selectionModel().clear()

    def on_directory_changed(
        self, selected: QtCore.QModelIndex, _: QtCore.QModelIndex
    ) -> None:
        """Updates the file view when a directory in the outline is selected.

        Args:
            selected (QtCore.QModelIndex): The newly selected index.
            deselected (QtCore.QModelIndex): The previously selected index.
        """
        selected_src: QtCore.QModelIndex = (
            self.__outline_proxy_model.mapToSource(selected)
        )
        file_path: str = self.__outline_model.filePath(selected_src)

        if file_path == "":
            file_path = self.__outline_model.rootPath()

        self.change_directory(file_path)

    def change_directory(self, current_path: str) -> None:
        """Refreshes the file model based on the provided directory path.

        Args:
            current_path (str): The directory path to display.
        """
        self.__file_model.clear()

        try:
            for path in os.listdir(current_path):
                full_path: str = os.path.join(current_path, path)
                if not os.path.isdir(full_path):
                    continue

                _, ext = os.path.splitext(path)
                if ext == "":
                    continue

                self.add_item(full_path)

        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to load directory {current_path}: {e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return

        self.__current_path = current_path

    def on_item_changed(
        self, selected: QtCore.QModelIndex, _: QtCore.QModelIndex
    ) -> None:
        """Emits signals and updates selection state when a file item changes.

        Args:
            selected (QtCore.QModelIndex): The newly selected index.
            deselected (QtCore.QModelIndex): The previously selected index.
        """
        if not selected.isValid():
            self.item_selected.emit(FileBrowserItem(""))
            self.__current_item = None
            return

        selected_src: QtCore.QModelIndex = self.__file_proxy_model.mapToSource(
            selected
        )
        item: FileBrowserItem = self.__file_model.itemFromIndex(selected_src)  # type: ignore
        self.item_selected.emit(item)
        self.__current_item = item

    def add_item(self, path: str) -> None:
        """Adds a new FileBrowserItem to the file view model.

        Args:
            path (str): The path of the item to add.
        """
        for row in range(self.__file_model.rowCount()):
            index: QtCore.QModelIndex = self.__file_model.index(row, 0)
            item: FileBrowserItem = self.__file_model.itemFromIndex(index)  # type: ignore
            if path == item.data_path():
                item.set_data_path(path)
                return

        item = FileBrowserItem(path)
        self.__file_model.appendRow(item)

    def filter(self) -> str:
        """Gets the current filter text from the file viewer.

        Returns:
            str: The active filter string.
        """
        return self.__filter_text

    def set_filter_text(self, filter_text: str) -> None:
        """Sets the filter text in the UI widget.

        Args:
            filter_text (str): The text to apply.
        """
        self.__file_viewer_filter.setText(filter_text)
        self.set_filter(filter_text)

    def set_filter(self, filter_text: str) -> None:
        """Applies the string filter to the proxy model.

        Args:
            filter_text (str): The regex pattern or text filter.
        """
        self.__filter_text = filter_text
        self.__file_proxy_model.setFilterRegularExpression(filter_text)

    def icon_size(self) -> int:
        """Gets the current icon size rendering dimension.

        Returns:
            int: Icon width in pixels.
        """
        return self.__file_viewer.iconSize().width()

    def set_icon_size(self, icon_size: int) -> None:
        """Updates the icon rendering dimension in the file viewer.

        Args:
            icon_size (int): Icon width and height in pixels.
        """
        self.__file_viewer.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.__file_viewer.setGridSize(
            QtCore.QSize(icon_size + 12, icon_size + 12)
        )

    def set_icon_range(self, value: int, min_size: int, max_size: int) -> None:
        """Sets the allowed range and default value for the icon size slider.

        Args:
            value (int): The current value to set.
            min_size (int): Minimum permissible icon size.
            max_size (int): Maximum permissible icon size.
        """
        self.__file_viewer_icon_size.setRange(min_size, max_size)
        self.__file_viewer_icon_size.setValue(value)
        self.set_icon_size(value)

    def create_folder(self) -> None:
        """Creates a new folder via a dialog prompt."""
        source_path: str = self.__current_path
        folder_name, result = QtWidgets.QInputDialog.getText(
            self,
            "Create folder",
            f"Location :\n{source_path}\n\n New folder name :",
            QtWidgets.QLineEdit.EchoMode.Normal,
        )
        if not result or folder_name == "":
            return

        try:
            full_path: str = os.path.join(source_path, folder_name)
            os.mkdir(full_path)

        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to create folder.\n{e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return

        if self.__outline_model.rootPath() == source_path:
            self.__outline_viewer.selectionModel().clear()

    def rename_folder(self) -> bool:
        """Renames the currently selected folder via a dialog prompt.

        Returns:
            bool: True if renamed successfully, False otherwise.
        """
        source_path = self.__current_path
        if self.__outline_model.rootPath() == self.__current_path:
            return False

        split_path: tuple[str, str] = os.path.split(source_path)
        folder_name, result = QtWidgets.QInputDialog.getText(
            self,
            "Rename folder",
            "New folder name :",
            QtWidgets.QLineEdit.EchoMode.Normal,
            split_path[-1],
        )
        if not result or folder_name == "" or folder_name == split_path[-1]:
            return False

        try:
            dirname: str = os.path.dirname(source_path)
            new_path: str = os.path.join(dirname, folder_name)
            os.rename(source_path, new_path)
        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to rename folder.\n\n{e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False

        self.__file_viewer.selectionModel().clear()
        self.__outline_viewer.selectionModel().clear()
        return True

    def remove_folder(self) -> bool:
        """Removes the currently selected folder.

        Returns:
            bool: True if removed successfully, False otherwise.
        """
        if self.root_path() == self.__current_path:
            return False

        result: QtWidgets.QMessageBox.StandardButton = (
            QtWidgets.QMessageBox.question(
                self,
                "Remove folder",
                f"Are you sure you want to delete?\n{self.__current_path}",
            )
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return False

        try:
            shutil.rmtree(self.__current_path)

        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to remove folder.\n\n{e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False

        self.__file_viewer.selectionModel().clear()
        self.__outline_viewer.selectionModel().clear()
        return True

    def rename_item(self) -> bool:
        """Renames the currently selected item in the file viewer.

        Returns:
            bool: True if renamed successfully, False otherwise.
        """
        if not self.__current_item:
            return False

        source_path: str = self.__current_item.data_path()
        base_name: str = os.path.basename(source_path)
        base_name, extension = os.path.splitext(base_name)
        extension: str = extension[1:]

        folder_name, result = QtWidgets.QInputDialog.getText(
            self,
            "Rename item",
            f"New {extension} item name :",
            QtWidgets.QLineEdit.EchoMode.Normal,
            base_name,
        )
        if not result or folder_name == "" or folder_name == base_name:
            return False

        source_item: FileBrowserItem = self.__current_item
        try:
            dirname: str = os.path.dirname(source_path)
            new_path: str = os.path.join(dirname, f"{folder_name}.{extension}")
            os.rename(source_path, new_path)

        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to rename folder.\n\n{e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False

        source_item.set_data_path(new_path)
        self.__file_viewer.selectionModel().clear()
        return True

    def remove_item(self) -> bool:
        """Removes the currently selected item in the file viewer.

        Returns:
            bool: True if removed successfully, False otherwise.
        """
        if not self.__current_item:
            return False

        source_path: str = self.__current_item.data_path()
        result: QtWidgets.QMessageBox.StandardButton = (
            QtWidgets.QMessageBox.question(
                self,
                "Remove item",
                f"Are you sure you want to delete?\n{source_path}",
            )
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return False

        try:
            shutil.rmtree(source_path)

        except OSError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to remove folder.\n\n{e}",
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            return False

        self.__file_model.removeRow(self.__current_item.row())
        self.__file_viewer.selectionModel().clear()
        return True
