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
"""Tool for managing external files linked to Maya nodes.

This module provides a UI to browse, copy, repath, and manage string
replacements for external file dependencies (textures, references, etc.).
"""

from __future__ import annotations
from typing import Any
import os
import re
import shutil
import functools
from maya import cmds
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets, system

__product__: str = "File Manager"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)

FOLDER_VIEW_ICON: str = "view/a_folder.png"
FOLDER_ICON: str = "a_folder.png"
BAD_ICON: str = "a_warning.png"
COPY_ICON: str = "a_copy.png"
COPY_TO_ICON: str = "a_copy_file.png"
REPATH_ICON: str = "a_repath.png"
REPLACE_STRING_ICON: str = "a_rename.png"
RENAME_ICON: str = "a_edit_file.png"
EXPLORER_ICON: str = "a_folder.png"
ATTR_EDITOR_ICON: str = "a_attribute.png"

QSS: str = """
#PreviewImage {
    background-color : rgba(0, 0, 0, 0.2);
    border-radius: 5px;
}
NodeListView {
    outline: none;
}
NodeListView::item {
    padding: 4px;
    border-bottom: 1px solid #3a3a3a;
}
NodeListView::item:hover {
    background-color: #3d3d3d;
}
NodeListView::item:selected {
    background-color: #5285a6;
    color: white;
}
NodeListView::item:selected:!active {
    background-color: #405060;
}
QHeaderView::section {
    background-color: #555555;
    padding: 4px;
    border: 1px solid #2b2b2b;
}
QHeaderView::down-arrow, QHeaderView::up-arrow {
    width: 12px;
    height: 12px;
}
QToolButton#missingBtn {
    border: 1px solid #555555;
    border-radius: 3px;
}
QToolButton#missingBtn:checked {
    background-color: #8b3a3a;
    border: 1px solid #cc5555;
    border-radius: 3px;
}
"""


class Settings(framework.ToolSettings):
    """Settings for the File Manager tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        splitter_state (framework.Variant[str]): Saved splitter ratio.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    splitter_state: framework.Variant[str] = framework.Variant("")


class CopyToDialog(QtWidgets.QDialog):
    """Dialog for copying files to a new directory."""

    def __init__(
        self,
        file_list: list[dcc.asset.AssetFile],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the Copy To dialog.

        Args:
            file_list (list[dcc.asset.AssetFile]): The list of files to copy.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__file_list: list[dcc.asset.AssetFile] = file_list
        self.setWindowTitle("Copy To")
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(self)

        project: str = dcc.project.get_workspace()
        source_images: str = os.path.normpath(
            os.path.join(project, "sourceImages")
        )

        self.__dst_dir: widgets.BrowseWidget = widgets.BrowseWidget(self)
        self.__dst_dir.set_icon(FOLDER_ICON)
        self.__dst_dir.set_text(source_images)
        self.__dst_dir.clicked.connect(self.show_file_dialog)
        main_layout.addRow(widgets.FormLabel("To"), self.__dst_dir)

        self.__new_dir: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("New Directory"), self.__new_dir)

        self.__is_delete: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Delete Original File", self
        )
        main_layout.addRow("", self.__is_delete)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply_copy)
        main_layout.addRow(button)

    def show_file_dialog(self) -> None:
        """Opens a file dialog to select a directory."""
        current_dir: str = os.path.dirname(self.__dst_dir.text())
        result: str = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Copy to",
            current_dir,
        )
        if result:
            self.__dst_dir.set_text(os.path.normpath(result))

    @dcc.undo
    def apply_copy(self) -> None:
        """Executes the copy operation."""
        dst: str = self.__dst_dir.text()
        new_dir: str = self.__new_dir.text()
        if new_dir:
            dst = os.path.join(dst, new_dir)

        if not os.path.exists(dst):
            try:
                os.makedirs(dst)

            except IOError:
                _logger.error("Failed to create directory : %s", dst)
                return

        progress: QtWidgets.QProgressDialog = QtWidgets.QProgressDialog(
            "Copy...",
            "Cancel",
            0,
            len(self.__file_list),
            self,
        )
        progress.show()

        result: utils.Result = utils.Result()
        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                break

            file_list: list[str] = [file.file_name()] + file.sequence()
            is_update: bool = True
            for src in file_list:
                base_name: str = os.path.basename(src)
                dst_path: str = os.path.join(dst, base_name)

                if src == dst_path:
                    continue

                try:
                    shutil.copyfile(src.split("{")[0], dst_path.split("{")[0])

                except IOError:
                    result.add_failure(src, "Failed to copy file")
                    continue

                if is_update:
                    file.change_file_path(dst_path)
                    is_update = False

            if self.__is_delete.isChecked():
                for src in file_list:
                    try:
                        os.remove(src)

                    except IOError:
                        result.add_failure(src, "Failed to delete source file")
                        continue

        result.log(_logger)
        progress.close()
        self.setResult(1)
        self.accept()


class RepathDialog(QtWidgets.QDialog):
    """Dialog for repathing existing files."""

    def __init__(
        self,
        file_list: list[dcc.asset.AssetFile],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the Repath dialog.

        Args:
            file_list (list[dcc.asset.AssetFile]): The list of files to repath.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__file_list: list[dcc.asset.AssetFile] = file_list
        self.setWindowTitle("Repath")
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(self)

        project: str = dcc.project.get_workspace()
        source_images: str = os.path.normpath(
            os.path.join(project, "sourceImages")
        )

        self.__dst_dir: widgets.BrowseWidget = widgets.BrowseWidget(self)
        self.__dst_dir.set_icon(FOLDER_ICON)
        self.__dst_dir.set_text(source_images)
        self.__dst_dir.clicked.connect(self.show_file_dialog)
        main_layout.addRow(widgets.FormLabel("Repath"), self.__dst_dir)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply_repath)
        main_layout.addRow(button)

    def show_file_dialog(self) -> None:
        """Opens a file dialog to select a directory."""
        current_dir: str = os.path.dirname(self.__dst_dir.text())
        result: str = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Repath to",
            current_dir,
        )
        if result:
            self.__dst_dir.set_text(os.path.normpath(result))

    def apply_repath(self) -> None:
        """Executes the repath operation."""
        dst: str = self.__dst_dir.text()

        progress: QtWidgets.QProgressDialog = QtWidgets.QProgressDialog(
            "Repath...", "Cancel", 0, len(self.__file_list), self
        )
        progress.show()

        result: utils.Result = utils.Result()
        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                break

            src: str = file.file_name()
            dst_path: str = os.path.join(dst, file.base_name())

            if src == dst_path:
                continue

            if not os.path.exists(dst_path.split("{")[0]):
                result.add_failure(
                    dst_path, "Destination path does not exists."
                )
                continue

            file.change_file_path(dst_path)

        result.log(_logger)
        progress.close()
        self.setResult(1)
        self.accept()


class ReplaceStringDialog(QtWidgets.QDialog):
    """Dialog for replacing strings in file paths."""

    def __init__(
        self,
        file_list: list[dcc.asset.AssetFile],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the Replace String dialog.

        Args:
            file_list (list[dcc.asset.AssetFile]): The list of files to modify.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__file_list: list[dcc.asset.AssetFile] = file_list
        self.setWindowTitle("Replace String")
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(self)

        self.__affected: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.__affected.addItems(["Directory Path", "Full Path", "File Name"])
        self.__affected.setCurrentIndex(1)
        main_layout.addRow(
            widgets.FormLabel("Affected String"), self.__affected
        )

        self.__search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Search String"), self.__search)

        self.__replace: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Replace String"), self.__replace)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply_replace_string)
        main_layout.addRow(button)

    def apply_replace_string(self) -> None:
        """Executes the string replacement."""
        affected_string: int = self.__affected.currentIndex()
        search: str = self.__search.text().replace("\\", "/")
        replace: str = self.__replace.text().replace("\\", "/")

        progress: QtWidgets.QProgressDialog = QtWidgets.QProgressDialog(
            "Replace strings...", "Cancel", 0, len(self.__file_list), self
        )
        progress.show()

        result: utils.Result = utils.Result()
        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                break

            if affected_string == 0:
                dst: str = file.dir_name()
                dst = re.sub(search, replace, dst)
                dst_path: str = os.path.join(dst, file.base_name())

            elif affected_string == 1:
                dst = file.file_name()
                dst_path = re.sub(search, replace, dst)

            else:
                dst = file.base_name()
                dst = re.sub(search, replace, dst)
                dst_path = os.path.join(file.dir_name(), dst)

            src: str = file.file_name()
            if src == dst_path:
                result.add_failure(src, "The result is same path")
                continue

            if not os.path.exists(dst_path.split("{")[0]):
                result.add_failure(src, "Destination path does not exists.")
                continue

            file.change_file_path(dst_path)

        result.log(_logger)
        progress.close()
        self.setResult(1)
        self.accept()


class RenameDialog(QtWidgets.QDialog):
    """Dialog for renaming a single file and repathing its Maya node."""

    def __init__(
        self,
        target_file: dcc.asset.AssetFile,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the Rename dialog.

        Args:
            target_file (dcc.asset.AssetFile): The target file to rename.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__file: dcc.asset.AssetFile = target_file
        self.setWindowTitle("Rename File")
        self.resize(400, 50)
        self.setModal(True)

        main_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout(self)

        self.__new_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__new_name.setText(self.__file.base_name())
        main_layout.addRow(widgets.FormLabel("New File Name"), self.__new_name)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply_rename)
        main_layout.addRow(button)

    @dcc.undo
    def apply_rename(self) -> None:
        """Executes the rename operation on OS and updates Maya node."""
        new_name: str = self.__new_name.text().strip()
        if not new_name or new_name == self.__file.base_name():
            self.reject()
            return

        old_path: str = self.__file.file_name()
        new_path: str = os.path.join(self.__file.dir_name(), new_name).replace(
            "\\", "/"
        )

        if os.path.exists(new_path):
            _logger.error("Destination file already exists: %s", new_path)
            return

        try:
            os.rename(old_path, new_path)

        except OSError as e:
            _logger.error("Failed to rename file: %s", e)
            return

        self.__file.change_file_path(new_path)
        self.setResult(1)
        self.accept()


class FileInfoPanel(QtWidgets.QWidget):
    """Panel displaying detailed OS information for a specific file or folder.

    Attributes:
        clicked_copy_to (QtCore.Signal): Emitted when the Copy To button is clicked.
        clicked_repath (QtCore.Signal): Emitted when the Repath button is clicked.
        clicked_rename (QtCore.Signal): Emitted when the Rename button is clicked.
    """

    clicked_copy_to = QtCore.Signal()
    clicked_repath = QtCore.Signal()
    clicked_rename = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the panel.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__current_files: list[dcc.asset.AssetFile] = []
        self.__current_dir: str = ""

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__preview: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.__preview.setObjectName("PreviewImage")
        self.__preview.setFixedSize(256, 256)
        self.__preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.__preview)

        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.__location: widgets.BrowseWidget = widgets.BrowseWidget(self)
        self.__location.set_icon(COPY_ICON)
        self.__location.set_read_only(True)
        self.__location.clicked.connect(self.copy_file_path)
        form_layout.addRow(widgets.FormLabel("Location"), self.__location)

        self.__accessed: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__accessed.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel("Accessed"), self.__accessed)

        self.__modified: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__modified.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel("Modified"), self.__modified)

        self.__changed: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__changed.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel("Changed"), self.__changed)

        self.__edit_size: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.__edit_size.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel("Size"), self.__edit_size)

        main_layout.addStretch(True)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(2)
        main_layout.addLayout(button_layout)

        button_layout.addStretch(True)

        self.__copy_to: widgets.IconButton = widgets.IconButton(self)
        self.__copy_to.set_icon(COPY_TO_ICON)
        self.__copy_to.setToolTip("Copy to another folder.")
        self.__copy_to.clicked.connect(self.show_copy_to_window)
        button_layout.addWidget(self.__copy_to)

        self.__repath: widgets.IconButton = widgets.IconButton(self)
        self.__repath.set_icon(REPATH_ICON)
        self.__repath.setToolTip("Reconnect the file path.")
        self.__repath.clicked.connect(self.show_repath_window)
        button_layout.addWidget(self.__repath)

        self.__replace: widgets.IconButton = widgets.IconButton(self)
        self.__replace.set_icon(REPLACE_STRING_ICON)
        self.__replace.setToolTip("Replace strings in the path.")
        self.__replace.clicked.connect(self.show_replace_string_window)
        button_layout.addWidget(self.__replace)

        self.__rename: widgets.IconButton = widgets.IconButton(self)
        self.__rename.set_icon(RENAME_ICON)
        self.__rename.setToolTip("Rename the file.")
        self.__rename.clicked.connect(self.show_rename_window)
        button_layout.addWidget(self.__rename)

        self.__open_dir: widgets.IconButton = widgets.IconButton(self)
        self.__open_dir.set_icon(EXPLORER_ICON)
        self.__open_dir.setToolTip("Open the folder.")
        self.__open_dir.clicked.connect(self.open_directory)
        button_layout.addWidget(self.__open_dir)

        self.__attr_editor: widgets.IconButton = widgets.IconButton(self)
        self.__attr_editor.set_icon(ATTR_EDITOR_ICON)
        self.__attr_editor.setToolTip("Open the node in the Attribute Editor.")
        self.__attr_editor.clicked.connect(self.show_attribute_editor)
        button_layout.addWidget(self.__attr_editor)

        self.set_selection(None)

    @QtCore.Slot()
    def copy_file_path(self) -> None:
        """Copies the current file path to the clipboard."""
        clipboard: QtGui.QClipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.__location.text())

    @QtCore.Slot(object)
    def set_selection(self, data: Any) -> None:
        """Sets the active selection (File or Folder) and updates the UI.

        Args:
            data (Any): The selected file data tuple or AssetFile node.
        """
        if not data:
            self.__current_files = []
            self.__current_dir = ""
            self.__preview.clear()
            self.__preview.setText("No selection")
            self.__location.set_text("")
            self.__accessed.clear()
            self.__modified.clear()
            self.__changed.clear()
            self.__edit_size.clear()
            self.setEnabled(False)
            return

        self.setEnabled(True)

        if isinstance(data, dcc.asset.AssetFile):
            self.__current_files = [data]
            self.__current_dir = data.dir_name()
            self.__attr_editor.setEnabled(True)
            self.__rename.setEnabled(True)

            image: QtGui.QPixmap = QtGui.QPixmap(data.file_name())
            if not image.isNull():
                image = image.scaled(
                    256,
                    256,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.FastTransformation,
                )
                self.__preview.setPixmap(image)

            else:
                self.__preview.clear()
                self.__preview.setText("No Image")

            self.__location.set_text(data.file_name())
            self.__accessed.setText(data.date_accessed())
            self.__modified.setText(data.date_modified())
            self.__changed.setText(data.date_changed())
            self.__edit_size.setText(data.file_size_string())

        elif isinstance(data, tuple) and len(data) == 2:
            dir_path, files = data
            self.__current_files = files
            self.__current_dir = dir_path
            self.__attr_editor.setEnabled(False)
            self.__rename.setEnabled(False)

            icon_path: str = dcc.get_icon_path(FOLDER_ICON)
            image = QtGui.QPixmap(icon_path)
            image = image.scaled(
                256,
                256,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.FastTransformation,
            )
            self.__preview.setPixmap(image)
            self.__location.set_text(dir_path)
            if os.path.exists(dir_path):
                self.__accessed.setText(
                    dcc.asset.format_time(os.path.getatime(dir_path))
                )
                self.__modified.setText(
                    dcc.asset.format_time(os.path.getmtime(dir_path))
                )
                self.__changed.setText(
                    dcc.asset.format_time(os.path.getctime(dir_path))
                )

            else:
                self.__accessed.setText("")
                self.__modified.setText("")
                self.__changed.setText("")

            total_bytes: float = 0
            for f in files:
                if f.is_valid:
                    total_bytes += os.path.getsize(f.file_name)

            self.__edit_size.setText(dcc.asset.format_size(total_bytes))

    def open_directory(self) -> None:
        """Opens the directory using the base utility."""
        if not os.path.exists(self.__current_dir):
            return

        system.open_directory(self.__current_dir)

    def show_attribute_editor(self) -> None:
        """Opens the Attribute Editor for the current node."""
        if not self.__current_files:
            return

        dcc.show_attribute_editor(self.__current_files[0].node())

    def show_rename_window(self) -> None:
        """Shows the rename dialog."""
        if not self.__current_files:
            return

        app: RenameDialog = RenameDialog(self.__current_files[0], self)
        if app.exec_():
            self.clicked_rename.emit()

    def show_copy_to_window(self) -> None:
        """Shows the copy to dialog."""
        if not self.__current_files:
            return

        app: CopyToDialog = CopyToDialog(self.__current_files, self)
        if app.exec_():
            self.clicked_copy_to.emit()

    def show_repath_window(self) -> None:
        """Shows the repath dialog."""
        if not self.__current_files:
            return

        app: RepathDialog = RepathDialog(self.__current_files, self)
        if app.exec_():
            self.clicked_repath.emit()

    def show_replace_string_window(self) -> None:
        """Shows the replace string dialog."""
        if not self.__current_files:
            return

        app: ReplaceStringDialog = ReplaceStringDialog(
            self.__current_files, self
        )
        if app.exec_():
            self.clicked_repath.emit()


class NodeListView(QtWidgets.QTreeView):
    """View component displaying the grouped external files.

    Attributes:
        file_selected (QtCore.Signal): Emitted when a file or folder is selected.
            Passes the selected `dcc.asset.AssetFile` object or a tuple of `(dir_name, files)`.
    """

    file_selected = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the view.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__node_type: str = ""
        self.__missing_only: bool = False

        self.__model: QtGui.QStandardItemModel = QtGui.QStandardItemModel(
            0, 2, self
        )
        self.__model.setHeaderData(
            0,
            QtCore.Qt.Orientation.Horizontal,
            "Node Name",
        )
        self.__model.setHeaderData(
            1,
            QtCore.Qt.Orientation.Horizontal,
            "File Name",
        )

        self.__proxy_model = QtCore.QSortFilterProxyModel(self)
        self.__proxy_model.setDynamicSortFilter(True)
        self.__proxy_model.setSourceModel(self.__model)
        self.__proxy_model.setFilterKeyColumn(-1)
        self.__proxy_model.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive
        )
        self.__proxy_model.setRecursiveFilteringEnabled(True)

        self.__selection_model: QtCore.QItemSelectionModel = (
            QtCore.QItemSelectionModel(self.__proxy_model)
        )
        self.setModel(self.__proxy_model)
        self.setSelectionModel(self.__selection_model)
        self.setSelectionMode(
            QtWidgets.QTreeView.SelectionMode.ExtendedSelection
        )
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
        self.setAlternatingRowColors(True)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(
            0,
            QtWidgets.QHeaderView.ResizeMode.Interactive,
        )
        self.setColumnWidth(0, 180)

        self.customContextMenuRequested.connect(self.context_menu)
        self.__selection_model.selectionChanged.connect(self.change_item)

        self.__file_list: dict[str, list[dcc.asset.AssetFile]] = {}

    def context_menu(self, point: QtCore.QPoint) -> None:
        """Shows context menu at specific position.

        Args:
            point (QtCore.QPoint): The point at which to spawn the context menu.
        """
        item_selection: QtCore.QItemSelection = (
            self.__proxy_model.mapSelectionToSource(
                self.__selection_model.selection()
            )
        )
        indexs: list[QtCore.QModelIndex] = item_selection.indexes()
        if not indexs:
            return

        dir_names: list[str] = []
        files: list[dcc.asset.AssetFile] = []
        for index in indexs:
            temp: Any = self.__model.itemFromIndex(index).data()
            if isinstance(temp, str):
                dir_names.append(temp)
                files.extend(self.__file_list[temp])

            elif isinstance(temp, dcc.asset.AssetFile):
                dir_names.append(temp.dir_name())
                files.append(temp)

        dir_names = list(set(dir_names))
        if not files:
            return

        menu = QtWidgets.QMenu(self)

        action: QtGui.QAction = QtGui.QAction("Copy To", self)
        action.triggered.connect(
            functools.partial(self.open_dialog, CopyToDialog, files)
        )
        menu.addAction(action)

        action = QtGui.QAction("Repath", self)
        action.triggered.connect(
            functools.partial(self.open_dialog, RepathDialog, files)
        )
        menu.addAction(action)

        action = QtGui.QAction("Replace String", self)
        action.triggered.connect(
            functools.partial(self.open_dialog, ReplaceStringDialog, files)
        )
        menu.addAction(action)

        menu.addSeparator()

        action = QtGui.QAction("Explorer", self)
        action.triggered.connect(
            functools.partial(self.open_directory, dir_names)
        )
        menu.addAction(action)

        menu.exec_(self.mapToGlobal(point))

    @QtCore.Slot(str)
    def set_node_type(self, node_type: str) -> None:
        """Sets the current node type to filter by.

        Args:
            node_type (str): The node type string.
        """
        self.__node_type = node_type
        self.update_ui()

    @QtCore.Slot(bool)
    def set_missing_only(self, checked: bool) -> None:
        """Sets whether to show only missing files and updates the view.

        Args:
            checked (bool): True to filter only missing files, False otherwise.
        """
        self.__missing_only = checked
        self.update_ui()

    def update_ui(self) -> None:
        """Updates the items inside the tree view."""
        self.__model.removeRows(0, self.__model.rowCount())
        if not self.__node_type:
            return

        self.__file_list = {}
        nodes: list[dcc.asset.AssetFile] = dcc.asset.get_external_nodes(
            self.__node_type
        )

        for file in nodes:
            dir_name: str = file.dir_name()
            if dir_name not in self.__file_list:
                self.__file_list[dir_name] = []

            self.__file_list[dir_name].append(file)

        file_list: list[dcc.asset.AssetFile]
        for dir_name, file_list in self.__file_list.items():
            if self.__missing_only:
                file_list = [f for f in file_list if not f.is_valid()]

            if not file_list:
                continue

            group_node: QtGui.QStandardItem = QtGui.QStandardItem()
            group_node.setEditable(False)
            group_node.setText(dir_name)
            group_node.setData(dir_name)
            group_node.setIcon(QtGui.QIcon(dcc.get_icon_path(FOLDER_VIEW_ICON)))

            group_file: QtGui.QStandardItem = QtGui.QStandardItem("")
            group_file.setEditable(False)
            group_file.setData(dir_name)

            self.__model.appendRow([group_node, group_file])

            for file in file_list:
                item_node: QtGui.QStandardItem = QtGui.QStandardItem()
                item_node.setEditable(False)
                item_node.setText(file.node())
                item_node.setData(file)

                if not file.is_valid():
                    item_node.setIcon(QtGui.QIcon(dcc.get_icon_path(BAD_ICON)))

                else:
                    item_node.setIcon(
                        QtWidgets.QFileIconProvider().icon(
                            QtCore.QFileInfo(file.file_name())
                        )
                    )

                item_file: QtGui.QStandardItem = QtGui.QStandardItem()
                item_file.setEditable(False)
                item_file.setText(file.display_short_file_name())
                item_file.setData(file)

                group_node.appendRow([item_node, item_file])

        self.expandAll()

        for row in range(self.__proxy_model.rowCount()):
            self.setFirstColumnSpanned(row, QtCore.QModelIndex(), True)

        self.file_selected.emit(None)

    @dcc.undo
    def change_item(
        self,
        selected: QtCore.QItemSelection,
        deselected: QtCore.QItemSelection,
    ) -> None:
        """Handles selection changes and emits the selected file node or folder data.

        Args:
            selected (QtCore.QItemSelection): The newly selected items.
            deselected (QtCore.QItemSelection): The newly deselected items.
        """
        item_selection: QtCore.QItemSelection = (
            self.__proxy_model.mapSelectionToSource(
                self.__selection_model.selection()
            )
        )
        indexs: list[QtCore.QModelIndex] = item_selection.indexes()
        if not indexs:
            self.file_selected.emit(None)
            return

        item: QtGui.QStandardItem = self.__model.itemFromIndex(indexs[0])
        data: str | dcc.asset.AssetFile = item.data()
        if isinstance(data, dcc.asset.AssetFile):
            self.file_selected.emit(data)
            cmds.select(data.node())

        elif isinstance(data, str):
            files: list[dcc.asset.AssetFile] = self.__file_list.get(data, [])
            self.file_selected.emit((data, files))

    def set_filter(self, filter_text: str) -> None:
        """Sets the filter string to the proxy model.

        Args:
            filter_text (str): The text to filter the items by.
        """
        self.__proxy_model.setFilterWildcard(f"*{filter_text}*")

    def open_dialog(self, dialog_class: type, target: list[Any]) -> None:
        """Opens a specific tool dialog.

        Args:
            dialog_class (type): The class of the dialog to open.
            target (list[Any]): The target files to pass into the dialog.
        """
        app: QtWidgets.QDialog = dialog_class(target, self)
        result: int = app.exec_()
        if result:
            self.update_ui()

    def open_directory(self, paths: list[str]) -> None:
        """Opens the OS directory.

        Args:
            paths (list[str]): A list of directory paths to open.
        """
        for path in paths:
            system.open_directory(path)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the File Manager tool."""

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
            unique_id (str, optional): A unique ID for the window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(700, 450)
        self.setStyleSheet(QSS)

        self.__node_list_view: NodeListView
        self.__file_info_panel: FileInfoPanel
        self.__category_combo: QtWidgets.QComboBox
        self.__splitter: QtWidgets.QSplitter

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, self
        )
        main_layout.addWidget(self.__splitter)

        left_widget: QtWidgets.QWidget = QtWidgets.QWidget(self.__splitter)
        self.__splitter.addWidget(left_widget)

        left_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        sub_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        left_layout.addLayout(sub_layout)

        self.__category_combo = QtWidgets.QComboBox(left_widget)
        for category_name, _ in dcc.asset.SUPPORTED_NODE_TYPES:
            self.__category_combo.addItem(category_name)

        self.__category_combo.currentIndexChanged.connect(self.change_category)
        sub_layout.addWidget(self.__category_combo)

        filter_str: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        filter_str.setPlaceholderText("Filter by name...")
        filter_str.textChanged.connect(self.change_filter)
        sub_layout.addWidget(filter_str)

        missing: QtWidgets.QToolButton = QtWidgets.QToolButton(left_widget)
        missing.setObjectName("missingBtn")
        missing.setIcon(QtGui.QIcon(dcc.get_icon_path(BAD_ICON)))
        missing.setCheckable(True)
        missing.setToolTip("Show missing files only")
        missing.toggled.connect(self.missing_filter_change_callback)
        sub_layout.addWidget(missing)

        self.__node_list_view = NodeListView(left_widget)
        left_layout.addWidget(self.__node_list_view)

        self.__file_info_panel = FileInfoPanel(self.__splitter)
        self.__splitter.addWidget(self.__file_info_panel)
        self.__splitter.setSizes([350, 350])

        self.__node_list_view.file_selected.connect(
            self.__file_info_panel.set_selection
        )

        self.__file_info_panel.clicked_copy_to.connect(self.update_view)
        self.__file_info_panel.clicked_repath.connect(self.update_view)
        self.__file_info_panel.clicked_rename.connect(self.update_view)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.splitter_state.bind(
            setter=self.__splitter.restoreState,
            getter=self.__splitter.saveState,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        self.change_category(0)

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates custom menus for view options.

        Args:
            menu_bar (QtWidgets.QMenuBar): The menu bar to append menus to.
        """
        view_menu: QtWidgets.QMenu = QtWidgets.QMenu("View", self)
        menu_bar.addMenu(view_menu)

        action: QtGui.QAction = view_menu.addAction("Update")
        action.triggered.connect(self.update_view)

    @QtCore.Slot(int)
    def change_category(self, index: int) -> None:
        """Handles category combo box changes.

        Args:
            index (int): The selected index in the combo box.
        """
        if index < 0:
            return

        node_type: str = dcc.asset.SUPPORTED_NODE_TYPES[index][1]
        self.__node_list_view.set_node_type(node_type)

    @QtCore.Slot()
    def update_view(self) -> None:
        """Updates the tree view."""
        self.__node_list_view.update_ui()

    @QtCore.Slot(str)
    def change_filter(self, filter_text: str) -> None:
        """Passes the filter text to the view.

        Args:
            filter_text (str): The text to filter the files by.
        """
        self.__node_list_view.set_filter(filter_text)

    @QtCore.Slot(bool)
    def missing_filter_change_callback(self, checked: bool) -> None:
        """Passes the missing filter state to the view.

        Args:
            checked (bool): True to filter only missing files, False otherwise.
        """
        self.__node_list_view.set_missing_only(checked)


def main(unique_id: str = "") -> None:
    """Entry point for launching the File Manager tool window.

    Args:
        unique_id (str, optional): A unique ID for restoring window states.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
