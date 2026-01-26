# ==============================================================================
#
# Stocker
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import json
import itertools

try:
    from PySide2.QtCore import (
        Qt,
        Slot,
        QMimeData,
        QByteArray,
        QItemSelectionModel,
        QModelIndex,
    )
    from PySide2.QtGui import (
        QStandardItemModel,
        QStandardItem,
        QKeyEvent,
        QKeySequence,
        QClipboard,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QTreeView,
        QApplication,
        QGridLayout,
        QHBoxLayout,
        QPushButton,
        QVBoxLayout,
        QLineEdit,
        QLabel,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            Qt,
            Slot,
            QMimeData,
            QByteArray,
            QItemSelectionModel,
            QModelIndex,
        )
        from PySide6.QtGui import (
            QStandardItemModel,
            QStandardItem,
            QKeyEvent,
            QKeySequence,
            QClipboard,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QTreeView,
            QApplication,
            QGridLayout,
            QHBoxLayout,
            QPushButton,
            QVBoxLayout,
            QLineEdit,
            QLabel,
        )
from maya import cmds, mel
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Stocker'
__version__: str = '1.10'
__doc__ = 'This tool stocks the values of attributes and can be copy and paste.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

MIME_TYPE: str = 'application/x-amaterasu-stocker-data'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    search: parser.Variant[str] = parser.Variant('_L_')
    replace: parser.Variant[str] = parser.Variant('_R_')


class ClipboardData(QMimeData):
    '''Clipboad data as json'''

    def set_json_data(self, mime_type: str, json_data: list[Any]) -> None:
        '''Set json from data.'''
        json_byte_data: bytes = bytes(json.dumps(json_data), 'utf-8')
        self.setData(mime_type, QByteArray(json_byte_data))


class StockerItemModel(QStandardItemModel):
    '''Item model for Stocker.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 3, parent)
        self.setHeaderData(0, Qt.Horizontal, 'Node')
        self.setHeaderData(1, Qt.Horizontal, 'Attribute')
        self.setHeaderData(2, Qt.Horizontal, 'Value')

    def append_item(self, node_name: str, attr_name: str, value: Any) -> None:
        '''Apend data to item model.'''
        plug: str = f'{node_name}.{attr_name}'
        node_item: QStandardItem = QStandardItem()
        node_item.setText(node_name)
        node_item.setEditable(False)

        attr_item: QStandardItem = QStandardItem()
        try:
            attr_item.setData(cmds.attributeName(plug, long=True))
            attr_item.setText(cmds.attributeName(plug, long=True))
        except RuntimeError:
            attr_item.setData(attr_name)
            attr_item.setText(attr_name)

        value_item: QStandardItem = QStandardItem()
        value_item.setData(type(value))
        value_item.setText(str(value))
        self.appendRow([node_item, attr_item, value_item])

    def row_data(self, index: int) -> tuple[str, str, Any]:
        '''Return row data from item model.'''
        node_name: str = self.item(index, 0).text()
        attr_name: str = self.item(index, 1).text()
        data_type: Any = self.item(index, 2).data()
        value: Any = self.item(index, 2).text()
        if data_type is bool:
            value = utility.str_to_bool(value)
        else:
            value = data_type(value)

        return (node_name, attr_name, value)


class StockerViewWidget(QTreeView):
    '''Tree view for Stocker.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize'''
        super().__init__(parent)
        model: StockerItemModel = StockerItemModel(self)
        selection_model: QItemSelectionModel = QItemSelectionModel()
        self.setModel(model)
        self.setSelectionModel(selection_model)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)

    # override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        '''keyPressEvent[override]'''
        if event.matches(QKeySequence.Copy):
            self.copy_to_clipboard()
        elif event.matches(QKeySequence.Paste):
            self.paste_from_clipboard()
        elif event.key() == Qt.Key_Delete:
            self.remove_selected_item()
        else:
            super().keyPressEvent(event)

    def copy_to_clipboard(self) -> None:
        '''Copy data to clipboard.'''
        data: list[Any] = []
        model: StockerItemModel = self.model()
        selection_model: QItemSelectionModel = self.selectionModel()
        indexes: list[QModelIndex] = selection_model.selectedIndexes()
        if not indexes:
            row: int = model.rowCount()
            indexes = []
            for i in range(row):
                indexes.append(model.index(i, 0))

        for index in indexes:
            if index.column() != 0:
                continue
            data.append(model.row_data(index.row()))

        mime_data: ClipboardData = ClipboardData()
        mime_data.set_json_data(MIME_TYPE, data)

        clipboard: QClipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)

    def paste_from_clipboard(self) -> None:
        '''Paste data from clipboard'''
        clipboard: QClipboard = QApplication.clipboard()
        mime_data: QMimeData = clipboard.mimeData()
        if not mime_data.hasFormat(MIME_TYPE):
            return

        data_bytes: QByteArray = mime_data.data(MIME_TYPE)
        datas: list[Any] = json.loads(str(data_bytes.data(), 'utf-8'))
        model: StockerItemModel = self.model()
        for data in datas:
            model.append_item(data[0], data[1], data[2])

    def remove_selected_item(self) -> None:
        '''Remove data from selected rows.'''
        model: StockerItemModel = self.model()
        selection_model: QItemSelectionModel = self.selectionModel()
        while True:
            indexes: list[QModelIndex] = selection_model.selectedIndexes()
            if not indexes:
                break

            model.removeRow(indexes[0].row())
            if len(indexes) == 1:
                selection_model.clear()

    @Slot()
    def copy(self) -> None:
        '''Copy data from selected attribute in Channel Box.'''

        def append_item(
            model: StockerItemModel, nodes: list[str], attrs: list[str]
        ) -> None:
            if not nodes or not attrs:
                return

            for node, attr in itertools.product(nodes, attrs):
                value: Any = cmds.getAttr(f'{node}.{attr}')
                model.append_item(node, attr, value)

        model: StockerItemModel = self.model()
        model.removeRows(0, model.rowCount())

        cb_name: str = mel.eval('$gChannelBoxName=$gChannelBoxName;')
        append_item(
            model,
            cmds.channelBox(cb_name, query=True, mainObjectList=True),
            cmds.channelBox(cb_name, query=True, selectedMainAttributes=True),
        )
        append_item(
            model,
            cmds.channelBox(cb_name, query=True, shapeObjectList=True),
            cmds.channelBox(cb_name, query=True, selectedShapeAttributes=True),
        )
        append_item(
            model,
            cmds.channelBox(cb_name, query=True, historyObjectList=True),
            cmds.channelBox(
                cb_name, query=True, selectedHistoryAttributes=True
            ),
        )
        append_item(
            model,
            cmds.channelBox(cb_name, query=True, outputObjectList=True),
            cmds.channelBox(cb_name, query=True, selectedOutputAttributes=True),
        )

        if model.rowCount() != 0:
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            return

        for node in selection:
            attrs: list[str] = cmds.listAttr(node) or []
            result: list[str] = []
            for attr in attrs:
                try:
                    plug: str = f'{node}.{attr}'
                    is_cb: bool = cmds.getAttr(plug, channelBox=True)
                    is_key: bool = cmds.getAttr(plug, keyable=True)
                    if is_cb or is_key:
                        result.append(attr)
                except RuntimeError:
                    pass
                except ValueError:
                    pass

            append_item(model, [node], result)

    @Slot(str, str)
    def paste(self, search: str = '', replace: str = '') -> None:
        '''Paste value to selected node from Stocker.'''
        model: StockerItemModel = self.model()
        selection_model: QItemSelectionModel = self.selectionModel()
        indexes: list[QModelIndex] = selection_model.selectedIndexes()
        if not indexes:
            row: int = model.rowCount()
            indexes = []
            for i in range(row):
                indexes.append(model.index(i, 0))

        selection: list[str] = cmds.ls(selection=True)
        is_selection: bool = True if selection else False
        for index in indexes:
            if index.column() != 0:
                continue

            node, attr, value = model.row_data(index.row())
            if not is_selection:  # and cmds.objExists(node):
                node = node.replace(search, replace)
                selection = [node]

            for dst_node in selection:
                plug: str = f'{dst_node}.{attr}'
                if not cmds.attributeQuery(attr, node=dst_node, exists=True):
                    _logger.error('Does not exists plug. : %s', plug)
                    continue

                try:
                    cmds.setAttr(plug, value)
                except RuntimeError:
                    _logger.error('Failed to set value. : %s', plug)
                    continue


class Stock(QWidget):
    '''Stock widget for Stocker'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize'''
        super().__init__(parent, flag)
        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__viewer: StockerViewWidget = StockerViewWidget(self)
        main_layout.addWidget(self.__viewer, 0, 0, 1, 2)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout, 1, 0, 1, 2)

        layout.addWidget(QLabel('Search & Replace :', self), False)

        self.__search = QLineEdit(self)
        layout.addWidget(self.__search)

        self.__replace = QLineEdit(self)
        layout.addWidget(self.__replace)

        clear_button: QPushButton = QPushButton('Clear', self)
        clear_button.clicked.connect(self.clear_callback)
        layout.addWidget(clear_button)

        copy_button: QPushButton = QPushButton('Copy', self)
        copy_button.clicked.connect(self.copy_callback)
        main_layout.addWidget(copy_button, 3, 0)

        paste_button: QPushButton = QPushButton('Paste', self)
        paste_button.clicked.connect(self.paste_callback)
        main_layout.addWidget(paste_button, 3, 1)

    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__search.setText(settings.search.value())
        self.__replace.setText(settings.replace.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.search.set_value(self.__search.text())
        settings.replace.set_value(self.__replace.text())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    def search(self) -> QLineEdit:
        '''Return search widget.'''
        return self.__search

    def replace(self) -> QLineEdit:
        '''Return replace widget.'''
        return self.__replace

    @Slot()
    def clear_callback(self) -> None:
        '''Clear search and replace'''
        self.__search.setText('')
        self.__replace.setText('')

    @widgets.undo
    def copy_callback(self) -> None:
        '''Copy Callback'''
        self.__viewer.copy()

    @widgets.undo
    def paste_callback(self) -> None:
        '''Paste Callback'''
        self.save_settings()
        selection: list[str] = cmds.ls(selection=True)
        if self.__search.text() or self.__replace.text():
            cmds.select(clear=True)

        self.__viewer.paste(self.__search.text(), self.__replace.text())
        if selection:
            cmds.select(*selection)


class StockerTab(widgets.TabWidget):
    '''Tab for Stocker.'''

    default_tab_name = 'Stock'
    title = __product__

    # override
    def add_tab(self, label: str = '') -> None:
        '''Add tab[override]'''
        if not label:
            label = StockerTab.default_tab_name

        stock: Stock = Stock(self)
        stock.load_settings()
        self.addTab(stock, label)
        self.setCurrentIndex(self.count() - 1)


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

        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        tab: StockerTab = StockerTab(self)
        tab.setDocumentMode(True)
        tab.add_tab()
        main_layout.addWidget(tab)

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


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
