# ==============================================================================
#
# UV Linker
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, Signal, QItemSelectionModel, QModelIndex
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import (
        QWidget,
        QGridLayout,
        QVBoxLayout,
        QHBoxLayout,
        QTreeView,
        QMessageBox,
        QPushButton,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QItemSelectionModel, QModelIndex
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QVBoxLayout,
            QHBoxLayout,
            QTreeView,
            QMessageBox,
            QPushButton,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'UV Linker'
__version__: str = '1.00'
__doc__ = 'Connect uv links from multiple specified nodes.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class ItemList(QWidget):
    '''Item list widget.'''

    currentChanged: Signal = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self.__model = QStandardItemModel(0, 1, self)
        self.__selection_model = QItemSelectionModel(self.__model)
        self.__selection_model.currentChanged.connect(self.currentChange)

        self.__view = QTreeView(self)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__selection_model)
        self.__view.setAlternatingRowColors(True)
        self.__view.setRootIsDecorated(False)
        self.__view.setFocusPolicy(Qt.NoFocus)
        main_layout.addWidget(self.__view)

    def currentChange(
        self, current: QModelIndex, previous: QModelIndex
    ) -> None:
        '''Current change.'''
        item: QStandardItem | None = self.__model.itemFromIndex(current)
        if item is None:
            return

        self.currentChanged.emit(item.text())

    def set_header_text(self, text: str) -> None:
        '''Set header text.'''
        self.__model.setHeaderData(0, Qt.Horizontal, text)

    def items(self) -> list[str]:
        '''Return text of items.'''
        result: list[str] = []
        for row in range(self.__model.rowCount()):
            result.append(self.__model.item(row, 0).text())
        return result

    def set_items(self, texts: list[str]) -> None:
        '''Set item from selected nodes.'''
        self.clear_item()
        for text in texts:
            item: QStandardItem = QStandardItem(text)
            item.setEditable(False)
            item.setIcon(widgets.pixmap_from_file_name('view/a_null.png'))
            self.__model.appendRow(item)

    def set_icon(self, target_label: str, icon_name: str) -> None:
        '''Set icon of item for specificed label.'''
        items: list[QStandardItem] = self.__model.findItems(target_label)
        for item in items:
            item.setIcon(widgets.pixmap_from_file_name(icon_name))

    def clear_item(self) -> None:
        '''Clear item.'''
        self.__model.removeRows(0, self.__model.rowCount())

    def selected_item(self) -> str:
        '''Return label from selected item.'''
        index: QModelIndex = self.__selection_model.currentIndex()
        item: QStandardItem | None = self.__model.itemFromIndex(index)
        if item is None:
            return ''

        return item.text()


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

        self.__geometrys: list[str] = []

        option_widget: QWidget = self.option_widget()
        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__uv_set_view: ItemList = ItemList(self)
        self.__uv_set_view.set_header_text('UV Sets')
        self.__uv_set_view.currentChanged.connect(self.__update_link_icon)
        main_layout.addWidget(self.__uv_set_view, 0, 0)

        self.__texture_view: ItemList = ItemList(self)
        self.__texture_view.set_header_text('Textures')
        main_layout.addWidget(self.__texture_view, 0, 1)

        button_layout = QHBoxLayout(self)
        main_layout.addLayout(button_layout, 1, 0, 1, 2)

        button: QPushButton = QPushButton('Analyze', self)
        button.clicked.connect(self.analyze)
        button_layout.addWidget(button)

        button = QPushButton('Connect', self)
        button.clicked.connect(self.connect_uv_link)
        button_layout.addWidget(button)

        button = QPushButton('Disconnect', self)
        button.clicked.connect(self.disconnect_uv_link)
        button_layout.addWidget(button)

        button = QPushButton('Clear', self)
        button.clicked.connect(self.clear)
        button_layout.addWidget(button)

        button = QPushButton('Close', self)
        button.clicked.connect(self.close)
        button_layout.addWidget(button)

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

    def __update_link_icon(self, uv_set_name: str) -> None:
        '''Update link icon.'''

        # Set null icon for all item.
        textures: list[str] = self.__texture_view.items()
        for texture in textures:
            self.__texture_view.set_icon(texture, 'view/a_null.png')

        # Set link icon for linked uv set.
        all_linked_textures: list[list[str]] = []
        for node in self.__geometrys:
            index: int = find_uv_set_id_from_name(node, uv_set_name)
            linked_textures: list[str] = cmds.uvLink(
                query=True,
                uvSet=f'{node}.uvSet[{index}].uvSetName',
            )  # type:ignore
            all_linked_textures.append(linked_textures)

            for texture in linked_textures:
                self.__texture_view.set_icon(texture, 'view/a_link.png')

        # Find different uv links for each geometry.
        incomplete_link: list[str] = []
        for i in range(0, len(all_linked_textures) - 1, 1):
            incomplete_link.extend(
                set(all_linked_textures[i]) ^ set(all_linked_textures[i + 1])
            )

        for texture in incomplete_link:
            self.__texture_view.set_icon(texture, 'view/a_incomplete_link.png')

    @widgets.undo
    def analyze(self) -> None:
        '''Analyze selected node and display uv set and texture in list.'''
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QMessageBox.warning(
                self, __product__, 'Select geometrys to be uv linked.'
            )
            return

        uv_sets: list[str] = get_same_uv_set_names(selection)
        uv_sets.sort()

        materials: list[str] = find_material_from_geometry(selection)
        textures: list[str] = []
        for material in materials:
            textures.extend(find_texture_from_material(material))

        textures.sort()
        self.__geometrys = selection
        self.__uv_set_view.set_items(uv_sets)
        self.__texture_view.set_items(textures)

    @widgets.undo
    def clear(self) -> None:
        '''Clear item in list.'''
        self.__geometrys.clear()
        self.__uv_set_view.clear_item()
        self.__texture_view.clear_item()

    @widgets.undo
    def connect_uv_link(self) -> None:
        '''Connect uv link from selected item in view.'''
        self.save_settings()
        connect_uv_links(
            self.__geometrys,
            self.__uv_set_view.selected_item(),
            self.__texture_view.selected_item(),
        )
        self.__update_link_icon(self.__uv_set_view.selected_item())

    @widgets.undo
    def disconnect_uv_link(self) -> None:
        '''Disconnect uv link from selected item in view.'''
        self.save_settings()
        disconnect_uv_links(
            self.__geometrys,
            self.__uv_set_view.selected_item(),
            self.__texture_view.selected_item(),
        )
        self.__update_link_icon(self.__uv_set_view.selected_item())


# ==============================================================================
#
# Functions
#
# ==============================================================================
def connect_uv_link(node: str, uv_set_name: str, texture: str) -> bool:
    '''Connect uv link from specified node and uv set name.'''
    index: int = find_uv_set_id_from_name(node, uv_set_name)
    if index == -1:
        return False

    cmds.uvLink(uvSet=f'{node}.uvSet[{index}].uvSetName', texture=texture)
    return True


def connect_uv_links(nodes: list[str], uv_set_name: str, texture: str) -> bool:
    '''Connect uv links from multiple specified nodes and uv set name.'''
    result: list[bool] = []
    for node in nodes:
        r: bool = connect_uv_link(node, uv_set_name, texture)
        if not r:
            _logger.error('Does not found uv name : %s / %s', node, uv_set_name)
            continue

        result.append(r)

    if all(result):
        _logger.info('Done.')
        return True

    return False


def disconnect_uv_link(node: str, uv_set_name: str, texture: str) -> bool:
    '''Disconnect uv link from specified node and uv set name.'''
    index: int = find_uv_set_id_from_name(node, uv_set_name)
    if index == -1:
        return False

    cmds.uvLink(
        b=True, uvSet=f'{node}.uvSet[{index}].uvSetName', texture=texture
    )
    return True


def disconnect_uv_links(
    nodes: list[str], uv_set_name: str, texture: str
) -> bool:
    '''Disconnect uv links from multiple specified nodes and uv set name.'''
    result: list[bool] = []
    for node in nodes:
        r: bool = disconnect_uv_link(node, uv_set_name, texture)
        if not r:
            _logger.error('Does not found uv name : %s / %s', node, uv_set_name)
            continue

        result.append(r)

    if all(result):
        _logger.info('Done.')
        return True

    return False


def get_uv_set_names(node: str) -> list[str]:
    '''Return uv set names.'''
    uv_indexes: list[int] = cmds.getAttr(f'{node}.uvSet', multiIndices=True)
    if not uv_indexes:
        return []

    result: list[str] = []
    for index in uv_indexes:
        uv_set_name: str = get_uv_set_name(node, index)
        if uv_set_name == '':
            continue

        result.append(uv_set_name)

    return result


def get_uv_set_name(node: str, index: int) -> str:
    '''Return uv set name from id.'''
    return cmds.getAttr(f'{node}.uvSet[{index}].uvSetName') or ''


def get_same_uv_set_names(nodes: list[str]) -> list[str]:
    '''Return same uv set name from specific nodes.'''
    result: list[str] = []
    for node in nodes:
        uv_set_names: list[str] = get_uv_set_names(node)
        if not uv_set_names:
            continue

        if not result:
            result = uv_set_names

        else:
            result = list(set(result) & set(uv_set_names))

    return result


def find_uv_set_id_from_name(node: str, uv_set_name: str) -> int:
    '''Return uv set id from uv set name.'''
    result = -1
    uv_indexes: list[int] = cmds.getAttr(f'{node}.uvSet', multiIndices=True)
    if not uv_indexes:
        return result

    for index in uv_indexes:
        if uv_set_name == get_uv_set_name(node, index):
            return index

    return result


def find_texture_from_material(node: str) -> list[str]:
    '''Return textures from material.'''
    result: list[str] = []
    connected_nodes: list[str] = cmds.listHistory(node)  # type:ignore
    for connected_node in connected_nodes:
        node_type: str = cmds.nodeType(connected_node, derived=True)[0]
        classification: list[str] = cmds.getClassification(node_type) or []
        if not classification:
            continue

        if classification[0].find('texture/2d') != -1:
            result.append(connected_node)

    return result


def find_material_from_geometry(node: list[str]) -> list[str]:
    '''Return materials from geometry.'''
    cmds.hyperShade(shaderNetworksSelectMaterialNodes=True)
    result: list[str] = cmds.ls(selection=True)
    cmds.select(*node)
    return result


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
