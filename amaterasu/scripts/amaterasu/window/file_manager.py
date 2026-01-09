# ==============================================================================
#
# File Manager
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import os
import time
import re
import shutil
from functools import partial

try:
    from PySide2.QtCore import (
        QObject,
        Qt,
        Signal,
        Slot,
        QModelIndex,
        QAbstractItemModel,
        QSortFilterProxyModel,
        QSize,
        QPoint,
        QItemSelectionModel,
        QItemSelection,
        QFileInfo,
    )
    from PySide2.QtGui import (
        QFont,
        QStandardItemModel,
        QStandardItem,
        QCursor,
        QPixmap,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QFormLayout,
        QGridLayout,
        QToolButton,
        QLabel,
        QLineEdit,
        QPushButton,
        QMenuBar,
        QDialog,
        QCheckBox,
        QProgressDialog,
        QComboBox,
        QTreeView,
        QMenu,
        QAction,
        QFileIconProvider,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            QObject,
            Qt,
            Signal,
            Slot,
            QModelIndex,
            QAbstractItemModel,
            QSortFilterProxyModel,
            QSize,
            QPoint,
            QItemSelectionModel,
            QItemSelection,
            QFileInfo,
        )
        from PySide6.QtGui import (
            QFont,
            QStandardItemModel,
            QStandardItem,
            QCursor,
            QPixmap,
            QAction,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QFormLayout,
            QGridLayout,
            QToolButton,
            QLabel,
            QLineEdit,
            QPushButton,
            QMenuBar,
            QDialog,
            QCheckBox,
            QProgressDialog,
            QComboBox,
            QTreeView,
            QMenu,
            QFileIconProvider,
        )
from maya import cmds, mel
from ..lib import parser, widgets, utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'File Manager'
__version__: str = '1.21'
__doc__ = 'Manage external files.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

FOLDER_ICON: str = 'view/a_folder.png'
BAD_ICON: str = 'view/a_close.png'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class File:
    '''Manage file object.'''

    category: list[list[str]] = [
        ['File', 'file'],
        ['Image Plane', 'imagePlane'],
        ['Reference', 'reference'],
    ]

    def __init__(self, node: str) -> None:
        self.__node: str = node
        self.__file_name: str = ''
        self.__node_type: str = cmds.objectType(node)

        if self.__node_type == 'file':
            self.__file_name = cmds.getAttr(f'{node}.fileTextureName')

        elif self.__node_type == 'reference':
            self.__file_name = cmds.referenceQuery(node, filename=True)

        elif self.__node_type == 'imagePlane':
            self.__file_name = cmds.getAttr(f'{node}.imageName')

        self.__display_file_name: str = self.base_name()
        if self.__file_name:
            self.__sequence: list[str] = []
            temp = self.__file_name.split('.')
            if temp[-2].isdigit():
                padding: int = len(temp[-2])
                start = int(temp[-2])
                format_str: str = self.__file_name.replace(
                    temp[-2], f'%%0{padding}i'
                )
                while True:
                    start += 1
                    file_name: str = format_str % start
                    if not os.path.exists(file_name):
                        break
                    self.__sequence.append(file_name)

                if len(self.__sequence) > 1:
                    format_str = '[' + ('#' * padding) + ']'
                    self.__display_file_name = self.__file_name.replace(
                        temp[-2], format_str
                    )

    def change_file_path(self, file_name: str) -> None:
        '''Change file path'''
        self.__filename = file_name
        if self.__node_type == 'file':
            plug: str = f'{self.node()}.fileTextureName'
            cmds.setAttr(plug, file_name, type='string')

        elif self.__node_type == 'reference':
            cmds.file(file_name, loadReference=self.node())

        elif self.__node_type == 'imagePlane':
            plug = f'{self.node()}.imageName'
            cmds.setAttr(plug, file_name, type='string')

    def node(self) -> str:
        '''Return node name.'''
        return self.__node

    def node_type(self) -> str:
        '''Return node type.'''
        return self.__node_type

    def file_name(self) -> str:
        '''Return file name.'''
        return self.__file_name.replace('\\', '/')

    def display_file_name(self) -> str:
        '''Return display file name.'''
        return self.__display_file_name

    def display_short_file_name(self) -> str:
        '''Return display short name.'''
        return os.path.basename(self.display_file_name())

    def sequence(self) -> list[str]:
        '''Return list of sequence files.'''
        return self.__sequence

    def base_name(self) -> str:
        '''Return base file name.'''
        return os.path.basename(self.file_name())

    def dir_name(self) -> str:
        '''Return directory name.'''
        return os.path.dirname(self.file_name())

    def is_valid(self) -> bool:
        '''Return valid'''
        return os.path.exists(self.file_name().split('{')[0])

    def date_accessed(self) -> float:
        ''''''
        if not self.is_valid():
            return 0
        return os.path.getatime(self.file_name())

    def date_accessed_string(self) -> str:
        ''''''
        return self.time_to_string(self.date_accessed())

    def date_modified(self) -> float:
        ''''''
        if not self.is_valid():
            return 0
        return os.path.getmtime(self.file_name())

    def date_modified_string(self) -> str:
        ''''''
        return self.time_to_string(self.date_modified())

    def date_changed(self) -> float:
        ''''''
        if not self.is_valid():
            return 0
        return os.path.getctime(self.file_name())

    def date_changed_string(self) -> str:
        ''''''
        return self.time_to_string(self.date_changed())

    def file_size(self) -> int:
        '''Return file size.'''
        if not self.is_valid():
            return 0
        return os.path.getsize(self.file_name())

    def file_size_string(self) -> str:
        ''''''
        bytes_: float = float(self.file_size())
        if bytes_ >= 1099511627776:
            terabytes: float = bytes_ / 1099511627776
            size: str = f'{terabytes:0.2f} TB'

        elif bytes_ >= 1073741824:
            gigabytes: float = bytes_ / 1073741824
            size = f'{gigabytes:0.2f} GB'

        elif bytes_ >= 1048576:
            megabytes: float = bytes_ / 1048576
            size = f'{megabytes:0.2f} MB' % megabytes

        elif bytes_ >= 1024:
            kilobytes: float = bytes_ / 1024
            size = f'{kilobytes:0.2f} KB'

        else:
            size = f'{bytes_:0.2f} byte'

        return size

    def ext(self) -> str:
        '''Return extension.'''
        filename = self.file_name()
        return filename.split('.')[-1]

    def time_to_string(self, sec: float) -> str:
        '''Convert time value to formated string.'''
        try:
            t: time.struct_time = time.gmtime(sec)
            return time.strftime('%b, %d, %Y, %H:%M %p', t)
        except Exception:
            return ''


class SortFilterProxyModel(QSortFilterProxyModel):
    '''Sort Filter Proxy Model.'''

    def __init__(self, parent: QObject | None = None) -> None:
        '''Initialize model'''
        super().__init__(parent)
        self.__filter: str = ''

    # override
    def filterAcceptsRow(
        self, sourceRow: int, sourceParent: QModelIndex
    ) -> bool:
        '''fiter accepts row[override]'''
        if not sourceParent.isValid():
            return True

        index: QModelIndex = self.sourceModel().index(
            sourceRow, 0, sourceParent
        )
        item: QAbstractItemModel = self.sourceModel().itemFromIndex(index)
        if not item:
            return False

        data: str = item.text()
        # result: bool = bool(self.filterRegExp().indexIn(data, 0) + 1)
        match: re.Match[str] | None = re.match(self.__filter, data)
        if match:
            return True
        return False

    def set_filter(self, filter: str) -> None:
        '''Set filter string.'''
        self.__filter = filter
        self.invalidate()


class FileItem(QWidget):
    '''File Item Widget'''

    icon_clicked = Signal()

    def __init__(self, file: File, parent: QWidget | None = None) -> None:
        '''Initialize Widget.'''
        super().__init__(parent)
        self.__file: File = file

        main_layout: QHBoxLayout = QHBoxLayout(self)

        titleFont = QFont()
        titleFont.setPointSize(16)
        titleFont.setBold(True)

        thumbnail = QToolButton(self)
        thumbnail.setFixedWidth(64)
        thumbnail.setFixedHeight(64)
        thumbnail.setIconSize(QSize(64, 64))
        thumbnail.clicked.connect(self.thumbnail_callback)
        main_layout.addWidget(thumbnail, 0, Qt.AlignTop)

        layout = QVBoxLayout()
        main_layout.addLayout(layout)

        node_name_label = QLabel(self.__file.node(), self)
        node_name_label.setFont(titleFont)
        layout.addWidget(node_name_label)

        file_path_label = QLabel(self.__file.base_name(), self)
        layout.addWidget(file_path_label)

        valid_label = QLabel('', self)
        if not self.__file.is_valid():
            valid_label.setText('File does not exists.')
            valid_label.setStyleSheet('QLabel{background:darkred}')
        layout.addWidget(valid_label)

    def thumbnail_callback(self) -> None:
        '''Emit signal when clicked thumbnail button.'''
        self.icon_clicked.emit()


class FileInfoWindow(QWidget):
    '''File Info Window'''

    id: str = f'{__name__}.fileInfo'
    copy_to_callback: Signal = Signal()
    repath_callback: Signal = Signal()

    def __init__(self, file: File, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.__file: File = file
        self.setWindowTitle(self.__file.node())
        self.setWindowFlag(Qt.Window)
        self.resize(520, 150)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ======================================================================
        # Menu
        # ======================================================================
        menu_bar: QMenuBar = QMenuBar(self)
        main_layout.addWidget(menu_bar)

        menu = menu_bar.addMenu('Tool')
        action = menu.addAction('Open Directory')
        action.triggered.connect(
            partial(open_directory, self.__file.dir_name())
        )
        action = menu.addAction('Attribute Editor')
        action.triggered.connect(
            partial(show_attribute_editor, self.__file.node())
        )

        # ======================================================================
        # Widget
        # ======================================================================

        sub_layout: QGridLayout = QGridLayout()
        sub_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.addLayout(sub_layout)

        form_layout: QFormLayout = QFormLayout()
        sub_layout.addLayout(form_layout, 0, 0)

        image: QPixmap = QPixmap(file.file_name())
        image = image.scaled(
            128, 128, Qt.KeepAspectRatio, Qt.FastTransformation
        )
        preview: QLabel = QLabel(self)
        preview.setPixmap(image)
        sub_layout.addWidget(preview, 0, 1)

        edit: QLineEdit = QLineEdit(self)
        edit.setText(self.__file.file_name())
        edit.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel('Location'), edit)

        edit = QLineEdit(self)
        edit.setText(self.__file.date_accessed_string())
        edit.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel('Date Accessed'), edit)

        edit = QLineEdit(self)
        edit.setText(self.__file.date_modified_string())
        edit.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel('Date Modified'), edit)

        edit = QLineEdit(self)
        edit.setText(self.__file.date_changed_string())
        edit.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel('Date Changed'), edit)

        edit = QLineEdit(self)
        edit.setText(self.__file.file_size_string())
        edit.setReadOnly(True)
        form_layout.addRow(widgets.FormLabel('Size'), edit)

        button_layout: QHBoxLayout = QHBoxLayout()
        sub_layout.addLayout(button_layout, 1, 0, 1, 2)

        button: QPushButton = QPushButton('Copy To', self)
        button.clicked.connect(self.copy_to_window)
        button_layout.addWidget(button)

        button = QPushButton('Repath', self)
        button.clicked.connect(self.repath_window)
        button_layout.addWidget(button)

        button = QPushButton('Replace String', self)
        button.clicked.connect(self.replace_string_window)
        button_layout.addWidget(button)
        main_layout.addStretch()

    def copy_to_window(self) -> None:
        '''Show copy to window.'''
        app: CopyToDialog = CopyToDialog([self.__file], self)
        result = app.exec_()
        if result:
            self.close()
            self.copy_to_callback.emit()

    def repath_window(self) -> None:
        '''Show repath window.'''
        app: RepathDialog = RepathDialog([self.__file], self)
        result = app.exec_()
        if result:
            self.close()
            self.repath_callback.emit()

    def replace_string_window(self) -> None:
        '''Show replace string window.'''
        app: ReplaceStringDialog = ReplaceStringDialog([self.__file], self)
        result = app.exec_()
        if result:
            self.close()
            self.repath_callback.emit()


class CopyToDialog(QDialog):
    def __init__(
        self, file_list: list[File], parent: QWidget | None = None
    ) -> None:
        '''Initialize dialog.'''
        super().__init__(parent)

        self.__file_list: list[File] = file_list

        self.setWindowTitle('Copy To')
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QFormLayout = QFormLayout(self)

        project: str = cmds.workspace(query=True, rootDirectory=True)
        source_images: str = os.path.join(
            project, 'sourceImages'
        )  # cmds.workspace('sourceImages', q=True, fre=True)

        self.__dst_dir: QLineEdit = QLineEdit(self)
        self.__dst_dir.setText(os.path.normpath(source_images))
        main_layout.addRow(widgets.FormLabel('To'), self.__dst_dir)

        self.__new_dir: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('New Directory'), self.__new_dir)

        self.__is_delete: QCheckBox = QCheckBox('Delete Original File', self)
        main_layout.addRow('', self.__is_delete)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.dotIt)
        main_layout.addRow(button)

    @widgets.undo
    def dotIt(self) -> None:
        '''Do it.'''
        dst: str = self.__dst_dir.text()
        new_dir: str = self.__new_dir.text()
        if new_dir:
            dst = os.path.join(dst, new_dir)

        if not os.path.exists(dst):
            try:
                os.makedirs(dst)

            except IOError:
                _logger.error('Failed to create directory : %s', dst)
                return

        progress: QProgressDialog = QProgressDialog(
            'Copy...', 'Cancel', 0, len(self.__file_list), self
        )
        progress.show()

        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                _logger.info('Canceled.')
                break

            file_list: list[str] = [file.file_name()] + file.sequence()
            is_update: bool = True
            for src in file_list:
                base_name: str = os.path.basename(src)
                dst_path: str = os.path.join(dst, base_name)

                if src == dst_path:
                    continue

                # TODO : Confirm override.
                try:
                    shutil.copyfile(src.split('{')[0], dst_path.split('{')[0])

                except IOError:
                    _logger.error('Failed to copy file : %s', src)
                    continue

                if is_update:
                    file.change_file_path(dst_path)
                    is_update = False

            if self.__is_delete.isChecked():
                for src in file_list:
                    try:
                        os.remove(src)

                    except IOError:
                        _logger.error('Failed to delete source file. : %s', src)
                        continue

        _logger.info('Done')
        progress.close()
        self.close()
        self.setResult(True)


class RepathDialog(QDialog):
    '''Repath Dialog'''

    def __init__(
        self, file_list: list[File], parent: QWidget | None = None
    ) -> None:
        '''Initialize dialog.'''
        super().__init__(parent)
        self.__file_list: list[File] = file_list

        self.setWindowTitle('Repath')
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QFormLayout = QFormLayout(self)

        project: str = cmds.workspace(query=True, rootDirectory=True)
        sourceImages: str = os.path.join(
            project, 'sourceImages'
        )  # cmds.workspace('sourceImages', q=True, fre=True)

        self.__dst_dir: QLineEdit = QLineEdit()
        self.__dst_dir.setText(os.path.normpath(sourceImages))
        main_layout.addRow(widgets.FormLabel('Repath'), self.__dst_dir)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.doIt)
        main_layout.addRow(button)

    @widgets.undo
    def doIt(self) -> None:
        '''Do it'''
        dst: str = self.__dst_dir.text()

        progress: QProgressDialog = QProgressDialog(
            'Repath...', 'Cancel', 0, len(self.__file_list), self
        )
        progress.show()

        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                _logger.info('Canceled.')
                break

            src: str = file.file_name()
            dst_path: str = os.path.join(dst, file.base_name())

            if src == dst_path:
                continue

            if not os.path.exists(dst_path.split('{')[0]):
                _logger.error('Destination path does not exists.')
                continue

            file.change_file_path(dst_path)

        _logger.info('Done')
        progress.close()
        self.close()
        self.setResult(True)


class ReplaceStringDialog(QDialog):
    '''Replace string dialog.'''

    def __init__(
        self, file_list: list[File], parent: QWidget | None = None
    ) -> None:
        '''Initialize dialog.'''
        super().__init__(parent)
        self.__file_list: list[File] = file_list

        self.setWindowTitle('Replace String')
        self.resize(420, 50)
        self.setModal(True)

        main_layout: QFormLayout = QFormLayout(self)

        self.__affected: QComboBox = QComboBox(self)
        self.__affected.addItem('Directory Path')
        self.__affected.addItem('Full Path')
        self.__affected.addItem('File Name')
        self.__affected.setCurrentIndex(1)
        main_layout.addRow(
            widgets.FormLabel('Affected String'), self.__affected
        )

        self.__search: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Search String'), self.__search)

        self.__replace: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Replace String'), self.__replace)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.dotIt)
        main_layout.addRow(button)

    @widgets.undo
    def dotIt(self) -> None:
        '''Do it'''
        affected_string: int = self.__affected.currentIndex()
        search: str = self.__search.text().replace('\\', '/')
        replace: str = self.__replace.text().replace('\\', '/')

        progress: QProgressDialog = QProgressDialog(
            'Replace strings...', 'Cancel', 0, len(self.__file_list), self
        )
        progress.show()

        for file in self.__file_list:
            progress.setValue(progress.value() + 1)
            if progress.wasCanceled():
                _logger.info('Canceled.')
                break

            # Directory Path
            if affected_string == 0:
                dst: str = file.dir_name()
                dst = re.sub(search, replace, dst)
                dst_path: str = os.path.join(dst, file.base_name())

            # Full Path
            elif affected_string == 1:
                dst = file.file_name()
                dst_path = re.sub(search, replace, dst)

            # File Name
            else:
                dst = file.base_name()
                dst = re.sub(search, replace, dst)
                dst_path = os.path.join(file.dir_name(), dst)

            # dst_path = os.path.normpath(dstPath)
            # src = os.path.normpath(fileInfo.filename())
            src: str = file.file_name()
            if src == dst_path:
                _logger.warning(
                    'The result is same path. : %s > %s', src, dst_path
                )
                continue

            if not os.path.exists(dst_path.split('{')[0]):
                _logger.error('Destination path does not exists.')
                continue

            _logger.info('%s : %s > %s', file.node(), src, dst_path)
            file.change_file_path(dst_path)

        _logger.info('Done')
        progress.close()
        self.close()
        self.setResult(True)


class NodeListView(QTreeView):
    '''Node List View'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.__node_type: str = ''

        self.__model: QStandardItemModel = QStandardItemModel(0, 1, self)
        self.__model.setHeaderData(0, Qt.Horizontal, 'Node')

        self.__proxy_model: SortFilterProxyModel = SortFilterProxyModel()
        self.__proxy_model.setDynamicSortFilter(True)
        self.__proxy_model.setSourceModel(self.__model)

        self.__selection_model: QItemSelectionModel = QItemSelectionModel(
            self.__proxy_model
        )
        self.setModel(self.__proxy_model)
        self.setSelectionModel(self.__selection_model)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.setAlternatingRowColors(True)
        self.setIconSize(QSize(16, 16))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.doubleClicked.connect(self.file_view)
        self.clicked.connect(self.select_node)

        self.__file_list: dict[str, list[Any]] = {}

    def context_menu(self, point: QPoint) -> None:
        '''Show context menu to specific position.'''
        item_selection: QItemSelection = (
            self.__proxy_model.mapSelectionToSource(
                self.__selection_model.selection()
            )
        )
        indexs: list[QModelIndex] = item_selection.indexes()
        if not indexs:
            return

        dir_names: list[str] = []
        files: list[Any] = []
        for index in indexs:
            temp: Any = self.__model.itemFromIndex(index).data()
            if isinstance(temp, str):
                dir_names.append(temp)
                files.extend(self.__file_list[temp])

            elif isinstance(temp, File):
                dir_names.append(temp.dir_name())
                files.append(temp)

        dir_names = list(set(dir_names))
        if len(files) <= 0:
            return

        menu = QMenu(self)

        action = QAction('Copy To', self)
        action.triggered.connect(partial(self.open_dialog, CopyToDialog, files))
        menu.addAction(action)

        action = QAction('Repath', self)
        action.triggered.connect(partial(self.open_dialog, RepathDialog, files))
        menu.addAction(action)

        action = QAction('Replace String', self)
        action.triggered.connect(
            partial(self.open_dialog, ReplaceStringDialog, files)
        )
        menu.addAction(action)

        action = QAction('Explorer', self)
        action.triggered.connect(partial(self.open_directory, dir_names))
        menu.addAction(action)

        menu.exec_(self.mapToGlobal(point))

    def set_node_type(self, node_type: str) -> None:
        '''Set node type'''
        self.__node_type = node_type
        self.update_ui()

    def update_ui(self) -> None:
        '''Update widgets.'''
        self.__model.removeRows(0, self.__model.rowCount())
        if not self.__node_type:
            return

        # TODO : to OpenMaya?
        self.__file_list = {}
        nodes: list[str] = cmds.ls(type=self.__node_type)
        for node in nodes:
            if node == 'sharedReferenceNode':
                continue

            node = node.split('->')[-1]
            file: File = File(node)
            if not file.file_name():
                continue

            dir_name: str = file.dir_name()
            if dir_name not in self.__file_list:
                self.__file_list[dir_name] = []

            self.__file_list[dir_name].append(file)

        for dir_name, file_list in self.__file_list.items():
            group: QStandardItem = QStandardItem()
            group.setEditable(False)
            group.setText(dir_name)
            group.setData(dir_name)
            group.setIcon(widgets.icon_from_file_name(FOLDER_ICON))
            self.__model.appendRow(group)

            for file in file_list:
                displayText = (
                    f'{file.node()} : {file.display_short_file_name()}'
                )

                item: QStandardItem = QStandardItem()
                item.setEditable(False)
                item.setText(displayText)
                item.setData(file)
                if not file.is_valid():
                    item.setIcon(widgets.icon_from_file_name(BAD_ICON))
                else:
                    item.setIcon(
                        QFileIconProvider().icon(QFileInfo(file.file_name()))
                    )
                group.setChild(group.rowCount(), item)

        self.collapseAll()

    def file_view(self, index: QModelIndex) -> None:
        '''Show file info view.'''
        item_selection: QItemSelection = (
            self.__proxy_model.mapSelectionToSource(
                self.__selection_model.selection()
            )
        )
        indexs: list[QModelIndex] = item_selection.indexes()
        if not indexs:
            return

        file = self.__model.itemFromIndex(indexs[0]).data()
        if not isinstance(file, File):
            return

        app = FileInfoWindow(file, self)
        app.copy_to_callback.connect(self.update)
        app.repath_callback.connect(self.update)
        app.move(QCursor.pos())
        app.show()

    def set_filter(self, filter: str) -> None:
        '''Set filter to model.'''
        self.__proxy_model.set_filter(filter)

    @widgets.undo
    def select_node(self, index: QModelIndex) -> None:
        '''select node.'''
        item_selection: QItemSelection = (
            self.__proxy_model.mapSelectionToSource(
                self.__selection_model.selection()
            )
        )
        indexs: list[QModelIndex] = item_selection.indexes()
        if not indexs:
            return

        file = self.__model.itemFromIndex(indexs[0]).data()
        if isinstance(file, File):
            cmds.select(file.node())

    def open_dialog(self, dialog: Any, target: list[Any]) -> None:
        '''Show specific dialog.'''
        app = dialog(target, self)
        result = app.exec_()
        if result:
            self.update_ui()

    def open_directory(self, paths: list[str]) -> None:
        '''Open directory.'''
        for path in paths:
            open_directory(path)


class Category(QComboBox):
    changed_category: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)

        for category in File.category:
            self.addItem(category[0])

        self.setCurrentIndex(-1)
        self.currentIndexChanged[int].connect(self.change_category)

    @Slot(int)
    def change_category(self, index: int) -> None:
        '''change categoery callback'''
        node_type: str = File.category[index][1]
        self.changed_category.emit(node_type)


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        # ======================================================================
        # Widget
        # ======================================================================
        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sub_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(sub_layout)

        category: Category = Category(self)
        sub_layout.addWidget(category)

        filter_edit: QLineEdit = QLineEdit(self)
        filter_edit.textChanged[str].connect(self.filter_change_callback)
        sub_layout.addWidget(filter_edit)

        self.__node_list_view: NodeListView = NodeListView(self)
        category.changed_category[str].connect(
            self.__node_list_view.set_node_type
        )
        category.setCurrentIndex(0)
        main_layout.addWidget(self.__node_list_view)

        # ======================================================================
        # Menu
        # ======================================================================
        menu_bar = self.menu_bar()
        view_menu = menu_bar.addMenu('View')
        menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)
        action = view_menu.addAction('Update')
        action.triggered.connect(self.update_view)

        self.update_view()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )

    def update_view(self) -> None:
        '''Update view.'''
        self.__node_list_view.update_ui()

    def filter_change_callback(self, filter: str) -> None:
        '''Update filter'''
        # regExp = QtCore.QRegExp(filter)
        # self.__nodeListView.model().setFilterRegExp(regExp)
        self.__node_list_view.set_filter(filter)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def open_directory(path: str) -> None:
    '''Open directory.'''
    result: int = utility.open_directory(path)
    if result == -2:
        _logger.error('Not supported os.')
    elif result == -1:
        _logger.error('Does not exists path : %s', path)
    else:
        _logger.info('Done.')


def show_attribute_editor(node: str) -> None:
    '''Show attribute editor.'''
    cmds.select(node)
    mel.eval('ShowAttributeEditorOrChannelBox')


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
