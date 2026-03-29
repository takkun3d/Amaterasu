# ==============================================================================
#
# Transfer User Defined Attr
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import json

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
        QPushButton,
        QVBoxLayout,
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
            QPushButton,
            QVBoxLayout,
        )
from maya import cmds
from ..lib import logger, parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Transfer User Defined Attr'
__version__: str = '1.10'
__doc__ = 'This tool transfer user defined attribute from specific nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

MIME_TYPE: str = 'application/x-amaterasu-tuda-data'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class ClipboardData(QMimeData):
    '''Clipboad data as json'''

    def set_json_data(self, mime_type: str, json_data: list[Any]) -> None:
        '''Set json from data.'''
        json_byte_data: bytes = bytes(json.dumps(json_data), 'utf-8')
        self.setData(mime_type, QByteArray(json_byte_data))


class StockerItemModel(QStandardItemModel):
    '''Item model for Stocker.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        headers: list[str] = [
            'Name',
            'Type',
            'Value',
            'Default',
            'Enum',
            'Color',
            'Parent',
            'Keyable',
            'ChannelBox',
            'Min Value',
            'Max Value',
        ]
        super().__init__(0, len(headers), parent)
        for i, header in enumerate(headers):
            self.setHeaderData(i, Qt.Horizontal, header)

    def append_item_from_node(self, node_name: str) -> None:
        '''Append item from specific node.'''
        user_defined_attrs: list[str] = (
            cmds.listAttr(node_name, userDefined=True) or []
        )
        if not user_defined_attrs:
            return

        for user_defined_attr in user_defined_attrs:
            plug: str = f'{node_name}.{user_defined_attr}'
            attr_type: str = cmds.getAttr(plug, type=True)

            value: Any = cmds.getAttr(plug)
            if attr_type in ('float3', 'double3'):
                value = value[0]

            default_value: Any = ''
            if attr_type != 'string':
                default_value = cmds.attributeQuery(
                    user_defined_attr, node=node_name, listDefault=True
                )[0]

            enum_value: str = ''
            if attr_type == 'enum':
                enum_value = cmds.attributeQuery(
                    user_defined_attr, node=node_name, listEnum=True
                )[0]

            color: bool = cmds.attributeQuery(
                user_defined_attr, node=node_name, usedAsColor=True
            )
            check_parent: list[str] | None = cmds.attributeQuery(
                user_defined_attr, node=node_name, listParent=True
            )
            parent_attr: str = ''
            if check_parent:
                parent_attr = check_parent[0]

            keyable: bool = cmds.getAttr(plug, keyable=True)
            channelbox: bool = cmds.getAttr(plug, channelBox=True)

            has_min: bool = cmds.attributeQuery(
                user_defined_attr, node=node_name, minExists=True
            )
            minimum: int | float | None = None
            if attr_type in ('long', 'float') and has_min:
                minimum = cmds.attributeQuery(
                    user_defined_attr, node=node_name, minimum=True
                )[0]

            has_max: bool = cmds.attributeQuery(
                user_defined_attr, node=node_name, maxExists=True
            )
            maximum: int | float | None = None
            if attr_type in ('long', 'float') and has_max:
                maximum = cmds.attributeQuery(
                    user_defined_attr, node=node_name, maximum=True
                )[0]

            self.append_item(
                user_defined_attr,
                attr_type,
                value,
                default_value,
                enum_value,
                color,
                parent_attr,
                keyable,
                channelbox,
                minimum,
                maximum,
            )

    def append_item(
        self,
        attr_name: str,
        attr_type: str,
        value: Any,
        default_value: Any,
        enum_value: str,
        color: bool,
        parent_attr: str,
        keyable: bool,
        channelbox: bool,
        minimum: int | float | None,
        maximum: int | float | None,
    ) -> None:
        '''Append data to item model.'''

        attr_item: QStandardItem = QStandardItem()
        attr_item.setData(attr_name)
        attr_item.setText(attr_name)

        attr_type_item: QStandardItem = QStandardItem()
        attr_type_item.setData(attr_type)
        attr_type_item.setText(attr_type)
        attr_type_item.setEditable(False)

        value_item: QStandardItem = QStandardItem()
        value_item.setData(value)
        value_item.setText(f'{value}')
        value_item.setEditable(False)
        if attr_type == 'enum':
            value_item.setText(enum_value.split(':')[value])

        defalut_value_item: QStandardItem = QStandardItem()
        defalut_value_item.setData(default_value)
        defalut_value_item.setText(f'{default_value}')
        defalut_value_item.setEditable(False)

        enum_value_item: QStandardItem = QStandardItem()
        enum_value_item.setData(enum_value)
        enum_value_item.setText(enum_value)
        enum_value_item.setEditable(False)

        color_item: QStandardItem = QStandardItem()
        color_item.setData(color)
        color_item.setText(f'{color}' if color else '')
        color_item.setEditable(False)

        parent_attr_item: QStandardItem = QStandardItem()
        parent_attr_item.setData(parent_attr)
        parent_attr_item.setText(parent_attr)
        parent_attr_item.setEditable(False)

        keyable_item: QStandardItem = QStandardItem()
        keyable_item.setData(keyable)
        keyable_item.setText(f'{keyable}' if keyable else '')
        keyable_item.setEditable(False)

        channelbox_item: QStandardItem = QStandardItem()
        channelbox_item.setData(channelbox)
        channelbox_item.setText(f'{channelbox}' if channelbox else '')
        channelbox_item.setEditable(False)

        minimum_item: QStandardItem = QStandardItem()
        minimum_item.setData(minimum)
        minimum_item.setText(f'{minimum}' if minimum is not None else '')
        minimum_item.setEditable(False)

        maximum_item: QStandardItem = QStandardItem()
        maximum_item.setData(maximum)
        maximum_item.setText(f'{maximum}' if maximum is not None else '')
        maximum_item.setEditable(False)

        self.appendRow(
            [
                attr_item,
                attr_type_item,
                value_item,
                defalut_value_item,
                enum_value_item,
                color_item,
                parent_attr_item,
                keyable_item,
                channelbox_item,
                minimum_item,
                maximum_item,
            ]
        )

    def row_data(self, index: int) -> tuple[
        str,
        str,
        Any,
        Any,
        str,
        bool,
        str,
        bool,
        bool,
        int | float | None,
        int | float | None,
    ]:
        '''Return row data from item model.'''
        return (
            self.item(index, 0).data(),  # Name
            self.item(index, 1).data(),  # Type
            self.item(index, 2).data(),  # Value
            self.item(index, 3).data(),  # Default
            self.item(index, 4).data(),  # Enum
            self.item(index, 5).data(),  # Color
            self.item(index, 6).data(),  # Parent
            self.item(index, 7).data(),  # Keyable
            self.item(index, 8).data(),  # Channel Box
            self.item(index, 9).data(),  # Min Value
            self.item(index, 10).data(),  # Max Value
        )


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
            model.append_item(*data)

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
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            return

        model: StockerItemModel = self.model()
        model.removeRows(0, model.rowCount())
        model.append_item_from_node(selection[0])

    @Slot()
    def paste(self) -> None:
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

        # ======================================================================
        # Add attributes
        # ======================================================================
        for node in selection:
            for index in indexes:
                if index.column() != 0:
                    continue

                (
                    attr_name,
                    attr_type,
                    value,
                    default_value,
                    enum_value,
                    color,
                    parent_attr,
                    keyable,
                    channelbox,
                    minimum,
                    maximum,
                ) = model.row_data(index.row())

                add_option: dict[str, Any] = {}
                if parent_attr:
                    add_option['parent'] = parent_attr
                if default_value:
                    add_option['defaultValue'] = default_value
                if minimum is not None:
                    add_option['minValue'] = minimum
                if maximum is not None:
                    add_option['maxValue'] = maximum
                if color:
                    add_option['usedAsColor'] = color

                try:
                    if attr_type == 'enum':
                        cmds.addAttr(
                            node,
                            longName=attr_name,
                            attributeType='enum',
                            enumName=enum_value,
                            **add_option,
                        )
                    elif attr_type == 'string':
                        cmds.addAttr(
                            node,
                            longName=attr_name,
                            dataType=attr_type,
                        )
                    else:
                        cmds.addAttr(
                            node,
                            longName=attr_name,
                            attributeType=attr_type,
                            **add_option,
                        )
                except RuntimeError:
                    logging.warning('Attributes already exist : %s', attr_name)

        # ======================================================================
        # Set decoration attributes
        # ======================================================================
        for node in selection:
            for index in indexes:
                if index.column() != 0:
                    continue

                (
                    attr_name,
                    attr_type,
                    value,
                    default_value,
                    enum_value,
                    color,
                    parent_attr,
                    keyable,
                    channelbox,
                    minimum,
                    maximum,
                ) = model.row_data(index.row())

                set_arg: dict[str, Any] = {}
                set_arg['keyable'] = keyable
                set_arg['channelBox'] = channelbox

                cmds.setAttr(f'{node}.{attr_name}', edit=True, **set_arg)

                if attr_type == 'string':
                    cmds.setAttr(f'{node}.{attr_name}', value, type='string')
                elif attr_type == 'float3':
                    cmds.setAttr(
                        f'{node}.{attr_name}', value[0], value[1], value[2]
                    )
                elif attr_type == 'double3':
                    cmds.setAttr(
                        f'{node}.{attr_name}', value[0], value[1], value[2]
                    )
                else:
                    cmds.setAttr(f'{node}.{attr_name}', value)


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

        copy_button: QPushButton = QPushButton('Copy', self)
        copy_button.clicked.connect(self.copy_callback)
        main_layout.addWidget(copy_button, 3, 0)

        paste_button: QPushButton = QPushButton('Paste', self)
        paste_button.clicked.connect(self.paste_callback)
        main_layout.addWidget(paste_button, 3, 1)

    @widgets.undo
    def copy_callback(self) -> None:
        '''Copy Callback'''
        self.__viewer.copy()

    @widgets.undo
    def paste_callback(self) -> None:
        '''Paste Callback'''
        self.__viewer.paste()


class StockerTab(widgets.TabWidget):
    '''Tab for Stocker.'''

    default_tab_name = 'Tab'
    title = __product__

    # override
    def add_tab(self, label: str = '') -> None:
        '''Add tab[override]'''
        if not label:
            label = StockerTab.default_tab_name

        stock: Stock = Stock(self)
        self.addTab(stock, label)
        self.setCurrentIndex(self.count() - 1)


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        unique_id: str = '',
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag, unique_id)
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
def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
