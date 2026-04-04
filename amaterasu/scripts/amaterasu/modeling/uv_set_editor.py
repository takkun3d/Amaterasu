# ==============================================================================
#
# UV Set Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import re

try:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QTableWidget,
        QHeaderView,
        QTableWidgetItem,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLineEdit,
            QTableWidget,
            QHeaderView,
            QTableWidgetItem,
        )
from maya import cmds, mel
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'UV Set Editor'
__version__: str = '1.00'
__doc__ = 'A matrix-based UI tool for managing UV sets across multiple nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


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
        self.__current_geometries: list[str] = []

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(header_layout)

        self.__filter: QLineEdit = QLineEdit(self)
        self.__filter.setPlaceholderText('Search ...')
        self.__filter.textChanged.connect(self.set_filter)
        header_layout.addWidget(self.__filter)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_update.png'))
        button.clicked.connect(self.load_from_selection)
        header_layout.addWidget(button)

        self.__table: QTableWidget = QTableWidget(self)
        self.__table.setSelectionBehavior(QTableWidget.SelectItems)
        self.__table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.__table.setIconSize(QSize(24, 24))
        self.__table.itemSelectionChanged.connect(self.selection_changed)
        self.__table.itemDoubleClicked.connect(self.double_clicked)
        main_layout.addWidget(self.__table)

        header_h: QHeaderView = self.__table.horizontalHeader()
        header_h.setSectionResizeMode(QHeaderView.Interactive)
        header_h.setDefaultSectionSize(80)

        header_v: QHeaderView = self.__table.verticalHeader()

        self.load_from_selection()

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

    def set_filter(self, text: str) -> None:
        '''Set filter to table'''
        text = text.lower()
        for row in range(self.__table.rowCount()):
            if row == self.__table.rowCount() - 1:
                self.__table.setRowHidden(row, False)
                continue

            header_item: QTableWidgetItem = self.__table.verticalHeaderItem(row)
            geometry: str = header_item.text().lower()
            self.__table.setRowHidden(row, text not in geometry)

    @widgets.undo
    def selection_changed(self) -> None:
        '''Selection changed at table'''
        selected_items: list[QTableWidgetItem] = self.__table.selectedItems()
        if not selected_items:
            return

        geometries: list[str] = []
        processed_rows: set[int] = set()
        for item in selected_items:
            row: int = item.row()
            if row in processed_rows:
                continue

            processed_rows.add(row)
            geometries.append(self.__table.verticalHeaderItem(row).text())

        if geometries:
            cmds.select(*geometries)

    @widgets.undo
    def double_clicked(self, item: QTableWidgetItem) -> None:
        '''Double clicked item at table'''
        row: int = item.row()
        geometry: str = self.__table.verticalHeaderItem(row).text()
        uv_name: str = self.__table.horizontalHeaderItem(item.column()).text()
        data: list[bool, int] = item.data(Qt.UserRole)
        is_current: bool = data[0]
        status: int = data[1]

        if not cmds.objExists(geometry):
            _logger.error('Does not exists %s,', geometry)
            return

        if status == -1:
            _logger.error(
                'Cannot open: %s does not exist on %s', uv_name, geometry
            )
            return

        elif status == 0:
            _logger.warning('%s is empty uv on %s.', uv_name, geometry)

        cmds.select(geometry)
        cmds.polyUVSet(geometry, currentUVSet=True, uvSet=uv_name)
        mel.eval('TextureViewWindow;')

        for col in range(self.__table.columnCount() - 1):
            _item: QTableWidgetItem = self.__table.item(row, col)
            _uv_name: str = self.__table.horizontalHeaderItem(
                _item.column()
            ).text()
            data = _item.data(Qt.UserRole)
            data[0] = uv_name == _uv_name
            _item.setData(Qt.UserRole, data)
            _item.setText(f'{data[0]}, {data[1]}')

    def load_from_selection(self) -> None:
        '''Load from selection'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if selection:
            self.__current_geometries = selection

        self.update_ui()

    def update_ui(self) -> None:
        '''Update UI'''
        self.__table.blockSignals(True)
        self.__table.clear()

        all_uvsets: set[str] = set()
        mesh_data: dict[str, Any] = {}
        for node in self.__current_geometries:
            shapes: list[str] = (
                cmds.listRelatives(
                    node, shapes=True, type='mesh', noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            shape: str = shapes[0]
            uv_sets: list[str] = (
                cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            )  # type: ignore
            uv_indices: list[int] = (
                cmds.polyUVSet(shape, query=True, allUVSetsIndices=True) or []
            )  # type: ignore
            current_uv_sets: list[str] = cmds.polyUVSet(
                shape, query=True, currentUVSet=True
            )  # type: ignore
            current: str = current_uv_sets[0] if current_uv_sets else ''

            has_error: bool = False
            if not uv_sets:  # Does not exists uv sets
                has_error = True

            elif 'map1' not in uv_sets:  # Does not exists map1
                has_error = True

            elif uv_sets[0] != 'map1':  # Map1 is not at index 0
                has_error = True

            uv_info: dict[str, int] = {}
            for uv_name, index in zip(uv_sets, uv_indices):
                try:
                    num_uvs: int = cmds.getAttr(
                        f'{shape}.uvSet[{index}].uvSetPoints', size=True
                    )
                    uv_info[uv_name] = 1 if num_uvs else 0

                except ValueError:
                    uv_info[uv_name] = 0

                # Invalid uvset name.
                if not uv_name or not re.match(r'^[a-zA-Z0-9_]+$', uv_name):
                    has_error = True
                    break

            all_uvsets.update(uv_sets)
            mesh_data[node] = {
                'uv_info': uv_info,
                'current': current,
                'has_error': has_error,
            }

        geometries: list[str] = [geo for geo in mesh_data]
        self.__table.setRowCount(len(geometries) + 1)

        unique_uvsets: list[str] = sorted(list(all_uvsets))
        if 'map1' in unique_uvsets:
            unique_uvsets.remove('map1')
            unique_uvsets.insert(0, 'map1')

        self.__table.setColumnCount(len(unique_uvsets) + 1)

        for row, geometry in enumerate(geometries):
            current = mesh_data[geometry]['current']
            uv_info = mesh_data[geometry]['uv_info']
            has_error = mesh_data[geometry]['has_error']

            item: QTableWidgetItem = QTableWidgetItem(geometry)
            item.setData(Qt.UserRole, has_error)
            if has_error:
                item.setText(f'[!] {geometry}')
            self.__table.setVerticalHeaderItem(row, item)

            for col, uvset in enumerate(unique_uvsets):
                is_current: bool = uvset == current
                item = QTableWidgetItem(uvset)
                self.__table.setHorizontalHeaderItem(col, item)

                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if uvset in uv_info:
                    item.setData(Qt.UserRole, [is_current, uv_info[uvset]])
                    item.setText(f'{is_current}, {uv_info[uvset]}')
                else:
                    item.setData(Qt.UserRole, [False, -1])
                    item.setText('False, -1')

                self.__table.setItem(row, col, item)

        for row in range(self.__table.rowCount()):
            for col in range(self.__table.columnCount()):
                if row == len(geometries) or col == len(unique_uvsets):
                    item = QTableWidgetItem('')
                    item.setFlags(Qt.NoItemFlags)
                    self.__table.setItem(row, col, item)

        item = QTableWidgetItem('+')
        self.__table.setVerticalHeaderItem(len(geometries), item)

        item = QTableWidgetItem('+')
        self.__table.setHorizontalHeaderItem(len(unique_uvsets), item)

        self.set_filter(self.__filter.text())
        self.__table.blockSignals(False)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
