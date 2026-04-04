# ==============================================================================
#
# UV Set Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import re
from functools import partial
from dataclasses import dataclass, replace
from enum import IntEnum

try:
    from PySide2.QtCore import (
        Qt,
        QSize,
        QRect,
        QPoint,
        QTimer,
        QModelIndex,
        QAbstractItemModel,
    )
    from PySide2.QtGui import QIcon, QPainter, QColor, QPen
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QTableWidget,
        QHeaderView,
        QTableWidgetItem,
        QStyledItemDelegate,
        QStyleOptionViewItem,
        QStyle,
        QInputDialog,
        QMenu,
        QAction,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            Qt,
            QSize,
            QRect,
            QPoint,
            QTimer,
            QModelIndex,
            QAbstractItemModel,
        )
        from PySide6.QtGui import QIcon, QPainter, QColor, QPen, QAction
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLineEdit,
            QTableWidget,
            QHeaderView,
            QTableWidgetItem,
            QStyledItemDelegate,
            QStyleOptionViewItem,
            QStyle,
            QInputDialog,
            QMenu,
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


class UvStatus(IntEnum):
    '''UV status'''

    NONE = -1
    EMPTY = 0
    HAS_UV = 1


@dataclass
class UvCellData:
    '''UV cell data'''

    is_current: bool = False
    status: UvStatus = UvStatus.NONE
    is_copied: bool = False


class UvSetDelegate(QStyledItemDelegate):
    '''UV Set Delegate'''

    icon: QIcon = widgets.icon_from_file_name('a_uv_set.png')
    empty_icon: QIcon = widgets.icon_from_file_name('a_empty_uv_set.png')

    def __init__(self, parent: QTableWidget) -> None:
        '''Initialize'''
        super().__init__(parent)
        self.__is_animating: bool = False
        self.__dash_offset: int = 0
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__update_animation)
        self.__timer.start(50)

    def __update_animation(self) -> None:
        '''Update animation'''
        if self.__is_animating:
            self.__dash_offset += 1
            if self.__dash_offset > 8:
                self.__dash_offset = 0

            self.parent().viewport().update()

    def start_animation(self) -> None:
        '''Start animation'''
        self.__is_animating = True

    def stop_animation(self) -> None:
        '''Stop animation'''
        self.__is_animating = False

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        '''paint (override)'''
        data: UvCellData | Any = index.data(Qt.UserRole)
        if not isinstance(data, UvCellData):
            super().paint(painter, option, index)
            return

        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if data.is_current:
            painter.fillRect(option.rect, QColor(100, 166, 82))

        if data.status == UvStatus.HAS_UV:
            self.icon.paint(painter, option.rect, Qt.AlignCenter)

        elif data.status == UvStatus.EMPTY:
            self.empty_icon.paint(painter, option.rect, Qt.AlignCenter)

        if data.is_copied:
            pen = QPen(QColor(0, 255, 150))
            pen.setWidth(2)
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern([4, 4])
            pen.setDashOffset(self.__dash_offset)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -2, -2))

        painter.restore()


class UvSetObjectHeader(QHeaderView):
    '''Uv Set Object Header'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize'''
        super().__init__(Qt.Vertical, parent)
        self.setSectionsClickable(True)

    def paintSection(
        self, painter: QPainter, rect: QRect, logicalIndex: int
    ) -> None:
        '''paintSection (override)'''
        model: QAbstractItemModel = self.model()
        if not model:
            super().paintSection(painter, rect, logicalIndex)
            return

        if self.orientation() == Qt.Horizontal:
            super().paintSection(painter, rect, logicalIndex)
            return

        has_error: bool = model.headerData(
            logicalIndex, Qt.Vertical, Qt.UserRole
        )
        if not has_error:
            super().paintSection(painter, rect, logicalIndex)
            return

        painter.save()
        painter.fillRect(rect, QColor(255, 100, 100))
        painter.setPen(QColor(45, 45, 45))
        painter.drawText(
            rect.adjusted(4, 0, -4, 0),
            Qt.AlignLeft | Qt.AlignVCenter,
            model.headerData(logicalIndex, self.orientation(), Qt.DisplayRole),
        )
        painter.restore()


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
        self.__copied_cells_data: list[tuple[int, int, str, str]] = []

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
        self.__table.itemDoubleClicked.connect(self.show_uv_editor)
        self.__table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.__table)

        header_h: QHeaderView = self.__table.horizontalHeader()
        header_h.setSectionResizeMode(QHeaderView.Interactive)
        header_h.setDefaultSectionSize(80)
        header_h.sectionClicked.connect(self.create_uv_set)
        header_h.sectionDoubleClicked.connect(self.rename_uv_set)
        header_h.setContextMenuPolicy(Qt.CustomContextMenu)
        header_h.customContextMenuRequested.connect(self.uv_set_context_menu)

        header_v: UvSetObjectHeader = UvSetObjectHeader(self)
        header_v.sectionClicked.connect(self.add_geometry)
        header_v.setContextMenuPolicy(Qt.CustomContextMenu)
        header_v.customContextMenuRequested.connect(self.geometry_context_menu)
        self.__table.setVerticalHeader(header_v)

        self.__delegate: UvSetDelegate = UvSetDelegate(self.__table)
        self.__table.setItemDelegate(self.__delegate)

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

    def uv_set_context_menu(self, pos: QPoint) -> None:
        '''Show uv set context menu'''
        col: int = self.__table.horizontalHeader().logicalIndexAt(pos)
        if col < 0 or col == self.__table.columnCount() - 1:
            return

        uv_name: str = self.__table.horizontalHeaderItem(col).text()
        menu = QMenu(self.__table)

        action: QAction = menu.addAction(f'Set "{uv_name}" as Current')
        action.triggered.connect(partial(self.set_current_uv_set, col))
        if uv_name != 'map1':
            menu.addSeparator()
            action = menu.addAction(f'Rename "{uv_name}" ...')
            action.triggered.connect(partial(self.rename_uv_set, col))

            action = menu.addAction(f'Delete "{uv_name}"')
            action.triggered.connect(partial(self.delete_uv_set, col))

        if hasattr(menu, 'exec'):
            menu.exec(self.__table.horizontalHeader().mapToGlobal(pos))
        else:
            menu.exec_(self.__table.horizontalHeader().mapToGlobal(pos))

    def geometry_context_menu(self, pos: QPoint) -> None:
        '''Show geometry context menu'''
        row: int = self.__table.verticalHeader().logicalIndexAt(pos)
        if row < 0 or row == self.__table.rowCount() - 1:
            return

        geometry: str = self.__table.verticalHeaderItem(row).text()
        selected_rows: list[int] = list(
            set(item.row() for item in self.__table.selectedItems())
        )

        menu = QMenu(self.__table)

        action: QAction = menu.addAction(f'Remove "{geometry}"')
        action.triggered.connect(partial(self.remove_geometry, [row]))

        if selected_rows:
            action = menu.addAction(
                f'Remove {len(selected_rows)} selected items'
            )
            action.triggered.connect(
                partial(self.remove_geometry, selected_rows)
            )

        menu.addSeparator()

        action = menu.addAction('Clean Up Empty UV Sets')
        if selected_rows:
            action.triggered.connect(
                partial(self.clean_up_empty_uv_sets, selected_rows)
            )
        else:
            action.triggered.connect(
                partial(self.clean_up_empty_uv_sets, [row])
            )

        action = menu.addAction('Fix Errors')
        if selected_rows:
            action.triggered.connect(partial(self.fix_errors, selected_rows))
        else:
            action.triggered.connect(partial(self.fix_errors, [row]))

        if hasattr(menu, 'exec'):
            menu.exec(self.__table.verticalHeader().mapToGlobal(pos))
        else:
            menu.exec_(self.__table.verticalHeader().mapToGlobal(pos))

    def show_context_menu(self, pos: QPoint) -> None:
        '''Show context menu'''
        item: QTableWidgetItem = self.__table.itemAt(pos)
        if not item:
            return

        if item.row() == self.__table.rowCount() - 1:
            return

        if item.column() == self.__table.columnCount() - 1:
            return

        menu = QMenu(self.__table)

        action: QAction = menu.addAction('Set Current UVSet')
        action.triggered.connect(self.set_current_uv_set_from_cells)

        menu.addSeparator()

        action = menu.addAction('Copy UV Set')
        action.triggered.connect(self.copy)

        action = menu.addAction('Paste UV Set')
        action.triggered.connect(self.paste)

        action = menu.addAction('Duplicate UV Set ...')
        action.triggered.connect(self.duplicate_uv_set)

        action = menu.addAction('Delete UV Set')
        action.triggered.connect(self.delete_uv_set_from_selection)

        menu.addSeparator()

        action = menu.addAction('Clean Up Empty UV Sets')
        action.triggered.connect(self.clean_up_empty_uv_sets)

        action = menu.addAction('Fix Errors')
        action.triggered.connect(self.fix_errors)

        if hasattr(menu, 'exec'):
            menu.exec(self.__table.viewport().mapToGlobal(pos))
        else:
            menu.exec_(self.__table.viewport().mapToGlobal(pos))

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
    def show_uv_editor(self, item: QTableWidgetItem) -> None:
        '''Double clicked item at table'''
        row: int = item.row()
        geometry: str = self.__table.verticalHeaderItem(row).text()
        uv_name: str = self.__table.horizontalHeaderItem(item.column()).text()
        data: UvCellData = item.data(Qt.UserRole)

        if not cmds.objExists(geometry):
            _logger.error('Does not exists %s,', geometry)
            return

        if data.status == UvStatus.NONE:
            _logger.error(
                'Cannot open: %s does not exist on %s', uv_name, geometry
            )
            return

        elif data.status == UvStatus.EMPTY:
            _logger.warning('%s is empty uv on %s.', uv_name, geometry)

        cmds.select(geometry)
        cmds.polyUVSet(geometry, currentUVSet=True, uvSet=uv_name)
        uv_editor: str = 'polyTexturePlacementPanel1Window'
        if cmds.window(uv_editor, query=True, exists=True):
            if not cmds.window(uv_editor, query=True, visible=True):
                mel.eval('TextureViewWindow;')
        else:
            mel.eval('TextureViewWindow;')

        for col in range(self.__table.columnCount() - 1):
            _item: QTableWidgetItem = self.__table.item(row, col)
            _uv_name: str = self.__table.horizontalHeaderItem(
                _item.column()
            ).text()
            data = _item.data(Qt.UserRole)
            data = replace(data, is_current=(uv_name == _uv_name))
            _item.setData(Qt.UserRole, data)

    @widgets.undo
    def create_uv_set(self, col: int) -> None:
        '''Create uv set'''
        if col != self.__table.columnCount() - 1:
            return

        new_name: str
        ok: bool
        new_name, ok = QInputDialog.getText(
            self,
            'Create UV Set',
            'New UV set name:',
            QLineEdit.Normal,
        )
        if not new_name or not ok:
            return

        for geometry in self.__current_geometries:
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            exist_uv: list[str] = (
                cmds.polyUVSet(geometry, query=True, allUVSets=True) or []
            )
            if new_name not in exist_uv:
                cmds.polyUVSet(geometry, create=True, uvSet=new_name)

        self.update_ui()

    @widgets.undo
    def duplicate_uv_set(self) -> None:
        '''Create uv set (Copy into new UV Set)'''
        selected_items: list[QTableWidgetItem] = self.__table.selectedItems()
        if not selected_items:
            return

        new_name: str
        ok: bool
        new_name, ok = QInputDialog.getText(
            self,
            'Create UV Set from UV Set',
            'New UV set name:',
            QLineEdit.Normal,
        )
        if not new_name or not ok:
            return

        for item in selected_items:
            if item.data(Qt.UserRole) == "-":
                continue

            geometry: str = self.__table.verticalHeaderItem(item.row()).text()
            src_uv: str = self.__table.horizontalHeaderItem(
                item.column()
            ).text()

            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            exist_uv: list[str] = (
                cmds.polyUVSet(geometry, query=True, allUVSets=True) or []
            )
            if new_name not in exist_uv:
                cmds.polyUVSet(
                    geometry, copy=True, uvSet=src_uv, newUVSet=new_name
                )

        self.update_ui()

    @widgets.undo
    def rename_uv_set(self, col: int) -> None:
        '''Rename uv set'''
        if col == self.__table.columnCount() - 1:
            return

        old_name: str = self.__table.horizontalHeaderItem(col).text()
        if old_name == 'map1':
            _logger.error('Cannot rename map1')
            return

        new_name: str
        ok: bool
        new_name, ok = QInputDialog.getText(
            self, 'Rename UVSet', 'New UV set name:', QLineEdit.Normal, old_name
        )

        if not new_name or not ok:
            return

        for geometry in self.__current_geometries:
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            exist_uv: list[str] = (
                cmds.polyUVSet(geometry, query=True, allUVSets=True) or []
            )
            if old_name in exist_uv and new_name not in exist_uv:
                cmds.polyUVSet(
                    geometry, rename=True, uvSet=old_name, newUVSet=new_name
                )

        self.update_ui()

    @widgets.undo
    def delete_uv_set(self, col: int) -> None:
        '''Delete uv set'''
        if col == self.__table.columnCount() - 1:
            return

        uv_set: str = self.__table.horizontalHeaderItem(col).text()
        if uv_set == 'map1':
            _logger.error('Cannot delete map1')
            return

        for geometry in self.__current_geometries:
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            exist_uv: list[str] = (
                cmds.polyUVSet(geometry, query=True, allUVSets=True) or []
            )
            if uv_set in exist_uv:
                cmds.polyUVSet(geometry, delete=True, uvSet=uv_set)

        self.update_ui()

    @widgets.undo
    def delete_uv_set_from_selection(self) -> None:
        '''Delete uv set from selection'''
        selected_items: list[QTableWidgetItem] = self.__table.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            data: UvCellData = item.data(Qt.UserRole)
            if data.status == UvStatus.NONE:
                continue

            geometry: str = self.__table.verticalHeaderItem(item.row()).text()
            uv_set: str = self.__table.horizontalHeaderItem(
                item.column()
            ).text()
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            cmds.polyUVSet(geometry, delete=True, uvSet=uv_set)

        self.update_ui()

    @widgets.undo
    def set_current_uv_set(self, col: int) -> None:
        '''Set current uv set from header'''
        if col == self.__table.columnCount() - 1:
            return

        uv_name: str = self.__table.horizontalHeaderItem(col).text()
        changed: bool = False
        for geometry in self.__current_geometries:
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            exist_uv: list[str] = (
                cmds.polyUVSet(geometry, query=True, allUVSets=True) or []
            )
            if uv_name in exist_uv:
                cmds.polyUVSet(geometry, currentUVSet=True, uvSet=uv_name)
                changed = True

        if changed:
            self.update_ui()

    @widgets.undo
    def set_current_uv_set_from_cells(self) -> None:
        '''Set current uv set from cells'''
        selected_items: list[QTableWidgetItem] = [
            i for i in self.__table.selectedItems()
        ]
        if not selected_items:
            return

        changed = False
        for item in selected_items:
            geo: str = self.__table.verticalHeaderItem(item.row()).text()
            uv_name: str = self.__table.horizontalHeaderItem(
                item.column()
            ).text()
            data: UvCellData = item.data(Qt.UserRole)
            if data.status == UvStatus.NONE:
                _logger.warning('%s does not exist on %s', uv_name, geo)
                continue

            if not cmds.objExists(geo):
                _logger.error('Does not exists %s', geo)
                continue

            cmds.polyUVSet(geo, currentUVSet=True, uvSet=uv_name)
            changed = True

        if changed:
            self.update_ui()

    @widgets.undo
    def clean_up_empty_uv_sets(self, rows: list[int] | None = None) -> None:
        '''Cleanup empty uv sets'''
        selected_items: list[QTableWidgetItem] = []
        if rows:
            for row in rows:
                for col in range(self.__table.columnCount() - 1):
                    selected_items.append(self.__table.item(row, col))
        else:
            selected_items = self.__table.selectedItems()

        if not selected_items:
            return

        deleted: bool = False
        for item in selected_items:
            data: UvCellData = item.data(Qt.UserRole)
            if data.status != UvStatus.EMPTY:
                continue

            geometry: str = self.__table.verticalHeaderItem(item.row()).text()
            uv_set: str = self.__table.horizontalHeaderItem(
                item.column()
            ).text()

            cmds.polyUVSet(geometry, delete=True, uvSet=uv_set)
            deleted = True

        if deleted:
            self.update_ui()

        _logger.info('Done.')

    @widgets.undo
    def fix_errors(self, rows: list[int] | None = None) -> None:
        '''Fix errors'''
        selected_items: list[QTableWidgetItem] = []
        if rows:
            for row in rows:
                for col in range(self.__table.columnCount() - 1):
                    selected_items.append(self.__table.item(row, col))
        else:
            selected_items = self.__table.selectedItems()

        if not selected_items:
            return

        geometries: list[str] = list(
            set(
                self.__table.verticalHeaderItem(item.row()).text()
                for item in selected_items
            )
        )
        fixed_count = 0
        for geometry in geometries:
            if not cmds.objExists(geometry):
                _logger.error('Does not exists %s', geometry)
                continue

            shapes: list[str] = (
                cmds.listRelatives(
                    geometry, shapes=True, type='mesh', noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            shape: str = shapes[0]
            uv_sets: list[str] = (
                cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            )
            if not uv_sets:
                cmds.polyUVSet(geometry, create=True, uvSet='map1')
                uv_sets = ['map1']
                fixed_count += 1
                _logger.info('%s created map1.', geometry)

            if 'map1' not in uv_sets:
                cmds.polyUVSet(
                    geometry, rename=True, uvSet=uv_sets[0], newUVSet='map1'
                )
                uv_sets[0] = 'map1'
                fixed_count += 1
                _logger.info('%s restored first uv set to map1.', geometry)

            else:
                if uv_sets[0] != 'map1':
                    cmds.polyUVSet(
                        geometry,
                        reorder=True,
                        uvSet='map1',
                        newUVSet=uv_sets[0],
                    )
                    idx: int = uv_sets.index('map1')
                    uv_sets[0] = uv_sets[idx]
                    uv_sets[idx] = uv_sets[0]
                    fixed_count += 1
                    _logger.info('%s forced map1 to index 0.', geometry)

            for i, uv in enumerate(uv_sets):
                if uv == 'map1':
                    continue

                if not uv or not re.match(r'^[a-zA-Z0-9_]+$', uv):
                    safe_name: str = f'uvSet{i}'
                    cmds.polyUVSet(
                        geometry, rename=True, uvSet=uv, newUVSet=safe_name
                    )
                    uv_sets[i] = safe_name
                    fixed_count += 1
                    _logger.info(
                        '%s recovered invalid UV name "%s" as "%s".',
                        geometry,
                        uv,
                        safe_name,
                    )

        if fixed_count > 0:
            _logger.info('Fixed %s errors.', fixed_count)
            self.update_ui()

        else:
            _logger.info('Done.')

    def add_geometry(self, row: int) -> None:
        '''Add geometry to table'''
        if row != self.__table.rowCount() - 1:
            return

        selection: list[str] = cmds.ls(selection=True, type='transform')
        added = False
        for geometry in selection:
            shapes: list[str] = (
                cmds.listRelatives(
                    geometry, shapes=True, type='mesh', noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            if geometry not in self.__current_geometries:
                self.__current_geometries.append(geometry)
                added = True

        if added:
            self.update_ui()

    def copy(self) -> None:
        '''Copy'''
        self.clear_copy_data()

        selected_items: list[QTableWidgetItem] = self.__table.selectedItems()
        if not selected_items:
            self.__delegate.set_copied_cells([])
            return

        min_row: int = min(item.row() for item in selected_items)
        min_col: int = min(item.column() for item in selected_items)
        for item in selected_items:
            data: UvCellData = item.data(Qt.UserRole)
            if data.status == UvStatus.NONE:
                continue

            row: int = item.row()
            col: int = item.column()
            geometry: str = self.__table.verticalHeaderItem(row).text()
            uv_set: str = self.__table.horizontalHeaderItem(col).text()

            data = replace(data, is_copied=True)
            item.setData(Qt.UserRole, data)

            # Row and column are relative positions.
            self.__copied_cells_data.append(
                (row - min_row, col - min_col, geometry, uv_set)
            )

        self.__delegate.start_animation()

    def paste(self) -> None:
        '''Paste'''
        if not self.__copied_cells_data:
            return

        selected_items: list[QTableWidgetItem] = self.__table.selectedItems()
        if not selected_items:
            return

        paste_row: int = min(item.row() for item in selected_items)
        paste_col: int = min(item.column() for item in selected_items)
        pasted = False
        for rel_row, rel_col, src_geo, src_uv in self.__copied_cells_data:
            dst_row: int = paste_row + rel_row
            dst_col: int = paste_col + rel_col

            if (
                dst_row >= self.__table.rowCount() - 1
                or dst_col >= self.__table.columnCount() - 1
            ):
                continue

            dst_geo_item: QTableWidgetItem = self.__table.verticalHeaderItem(
                dst_row
            )
            dst_uv_item: QTableWidgetItem = self.__table.horizontalHeaderItem(
                dst_col
            )
            if not dst_geo_item or not dst_uv_item:
                continue

            dst_geo: str = dst_geo_item.text()
            dst_uv: str = dst_uv_item.text()

            if src_geo != dst_geo:
                _logger.warning(
                    'Skipped: Cannot paste UV set to a different geometry : %s -> %s',
                    src_geo,
                    dst_geo,
                )
                continue

            if src_uv == dst_uv:
                continue

            if not cmds.objExists(dst_geo):
                continue

            target_cell_item: QTableWidgetItem = self.__table.item(
                dst_row, dst_col
            )
            data: UvCellData = target_cell_item.data(Qt.UserRole)
            if target_cell_item and data.status == UvStatus.NONE:
                exist_uv: list[str] = (
                    cmds.polyUVSet(dst_geo, query=True, allUVSets=True) or []
                )
                if dst_uv not in exist_uv:
                    cmds.polyUVSet(dst_geo, create=True, uvSet=dst_uv)

            cmds.polyCopyUV(dst_geo, uvSetNameInput=src_uv, uvSetName=dst_uv)
            pasted = True

        if pasted:
            self.clear_copy_data()
            self.update_ui()

    def clear_copy_data(self) -> None:
        '''Clear copy data'''
        self.__copied_cells_data = []
        self.__delegate.stop_animation()
        for row in range(self.__table.rowCount() - 1):
            for col in range(self.__table.columnCount() - 1):
                item: QTableWidgetItem = self.__table.item(row, col)
                if not item:
                    continue

                data: UvCellData = item.data(Qt.UserRole)
                if not data:
                    continue

                data = replace(data, is_copied=False)
                item.setData(Qt.UserRole, data)

    def remove_geometry(self, rows: list[int]) -> None:
        '''Remove geometry from table'''
        removed = False
        for row in rows:
            geometry: str = self.__table.verticalHeaderItem(row).text()
            self.__current_geometries.remove(geometry)
            removed = True

        if removed:
            self.update_ui()

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
        self.clear_copy_data()

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

            uv_info: dict[str, UvStatus] = {}
            for uv_name, index in zip(uv_sets, uv_indices):
                try:
                    num_uvs: int = cmds.getAttr(
                        f'{shape}.uvSet[{index}].uvSetPoints', size=True
                    )
                    uv_info[uv_name] = (
                        UvStatus.HAS_UV if num_uvs else UvStatus.EMPTY
                    )

                except ValueError:
                    uv_info[uv_name] = UvStatus.EMPTY

                # Invalid uvset name.
                if not uv_name or not re.match(r'^[a-zA-Z0-9_]+$', uv_name):
                    has_error = True
                    break

            all_uvsets.update(uv_sets)
            mesh_data[node] = {
                'current': current,
                'uv_info': uv_info,
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
            self.__table.setVerticalHeaderItem(row, item)

            for col, uvset in enumerate(unique_uvsets):
                is_current: bool = uvset == current
                item = QTableWidgetItem(uvset)
                self.__table.setHorizontalHeaderItem(col, item)

                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if uvset in uv_info:
                    cell_data: UvCellData = UvCellData(
                        is_current, uv_info[uvset], False
                    )
                else:
                    cell_data = UvCellData(False, UvStatus.NONE, False)

                item.setData(Qt.UserRole, cell_data)
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
