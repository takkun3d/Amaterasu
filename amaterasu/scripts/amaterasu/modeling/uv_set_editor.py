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
"""A matrix-based UI tool for managing UV sets across multiple nodes."""

from __future__ import annotations
from typing import cast, Any
import re
from functools import partial
from dataclasses import dataclass, replace
from enum import IntEnum
from maya import cmds, mel
from maya.api import OpenMaya
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "UV Set Editor"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class UvStatus(IntEnum):
    """UV status indicator.

    Attributes:
        NONE: UV set does not exist.
        EMPTY: UV set exists but contains no UVs.
        HAS_UV: UV set exists and contains UVs.
    """

    NONE = -1
    EMPTY = 0
    HAS_UV = 1


@dataclass
class UvCellData:
    """Dataclass holding information for each UV cell in the table.

    Attributes:
        is_current (bool): Whether this is the active UV set.
        status (UvStatus): The status of the UV set.
        is_copied (bool): Whether the cell is currently copied.
    """

    is_current: bool = False
    status: UvStatus = UvStatus.NONE
    is_copied: bool = False


class UvSetDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for drawing UV set cell contents and animations."""

    def __init__(self, parent: QtWidgets.QTableWidget) -> None:
        """Initializes the delegate.

        Args:
            parent (QtWidgets.QTableWidget): The parent table widget.
        """
        super().__init__(parent)
        self.icon = QtGui.QIcon(dcc.get_icon_path("a_uv_set.png"))
        self.empty_icon = QtGui.QIcon(dcc.get_icon_path("a_empty_uv_set.png"))
        self.__is_animating: bool = False
        self.__dash_offset: int = 0
        self.__timer = QtCore.QTimer(self)
        self.__timer.timeout.connect(self.__update_animation)
        self.__timer.start(50)

    def __update_animation(self) -> None:
        """Updates the dash offset for the copy animation."""
        if self.__is_animating:
            self.__dash_offset += 1
            if self.__dash_offset > 8:
                self.__dash_offset = 0

            self.parent().viewport().update()  # type: ignore

    def start_animation(self) -> None:
        """Starts the copy outline animation."""
        self.__is_animating = True

    def stop_animation(self) -> None:
        """Stops the copy outline animation."""
        self.__is_animating = False

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,  # type: ignore
    ) -> None:
        """Paints the delegate item.

        Args:
            painter (QtGui.QPainter): The painter object.
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex): The model index of the item.
        """
        data: UvCellData | Any = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(data, UvCellData):
            super().paint(painter, option, index)
            return

        painter.save()
        if data.is_current:
            painter.fillRect(option.rect, QtGui.QColor(100, 166, 82))

        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        if data.status == UvStatus.HAS_UV:
            self.icon.paint(
                painter, option.rect, QtCore.Qt.AlignmentFlag.AlignCenter
            )
        elif data.status == UvStatus.EMPTY:
            self.empty_icon.paint(
                painter, option.rect, QtCore.Qt.AlignmentFlag.AlignCenter
            )

        if data.is_copied:
            pen = QtGui.QPen(QtGui.QColor(0, 255, 150))
            pen.setWidth(2)
            pen.setStyle(QtCore.Qt.PenStyle.CustomDashLine)
            pen.setDashPattern([4, 4])
            pen.setDashOffset(self.__dash_offset)
            painter.setPen(pen)
            painter.drawRect(option.rect.adjusted(1, 1, -2, -2))

        painter.restore()


class UvSetObjectHeader(QtWidgets.QHeaderView):
    """Custom vertical header to display error states for geometries."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the header view.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
        """
        super().__init__(QtCore.Qt.Orientation.Vertical, parent)
        self.setSectionsClickable(True)

    def paintSection(
        self, painter: QtGui.QPainter, rect: QtCore.QRect, logicalIndex: int
    ) -> None:
        """Paints the header section.

        Args:
            painter (QtGui.QPainter): The painter object.
            rect (QtCore.QRect): The rectangle area to paint.
            logicalIndex (int): The index of the section.
        """
        model: QtCore.QAbstractItemModel | None = self.model()
        if not model:
            super().paintSection(painter, rect, logicalIndex)
            return

        if self.orientation() == QtCore.Qt.Orientation.Horizontal:
            super().paintSection(painter, rect, logicalIndex)
            return

        has_error: bool = model.headerData(
            logicalIndex,
            QtCore.Qt.Orientation.Vertical,
            QtCore.Qt.ItemDataRole.UserRole,
        )
        if not has_error:
            super().paintSection(painter, rect, logicalIndex)
            return

        painter.save()
        painter.fillRect(rect, QtGui.QColor(255, 100, 100))
        painter.setPen(QtGui.QColor(45, 45, 45))
        display_data = model.headerData(
            logicalIndex, self.orientation(), QtCore.Qt.ItemDataRole.DisplayRole
        )
        painter.drawText(
            rect.adjusted(4, 0, -4, 0),
            QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter,
            str(display_data),
        )
        painter.restore()


class UvSetTableWidget(QtWidgets.QTableWidget):
    """Main table widget for editing UV sets."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the table widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
        """
        super().__init__(parent)
        self.__current_geometries: list[str] = []
        self.__copied_cells_data: list[tuple[int, int, str, str]] = []

        self.setSelectionBehavior(
            QtWidgets.QTableWidget.SelectionBehavior.SelectItems
        )
        self.setSelectionMode(
            QtWidgets.QTableWidget.SelectionMode.ExtendedSelection
        )
        self.setIconSize(QtCore.QSize(24, 24))
        self.itemSelectionChanged.connect(  # pylint: disable=no-member
            self.selection_changed
        )
        self.itemDoubleClicked.connect(  # pylint: disable=no-member
            self.show_uv_editor
        )
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(  # pylint: disable=no-member
            self.show_context_menu
        )

        header_h: QtWidgets.QHeaderView = self.horizontalHeader()
        header_h.setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        header_h.setDefaultSectionSize(80)
        header_h.sectionClicked.connect(self.create_uv_set)
        header_h.sectionDoubleClicked.connect(self.rename_uv_set)
        header_h.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        header_h.customContextMenuRequested.connect(
            self.show_uv_set_context_menu
        )

        header_v: UvSetObjectHeader = UvSetObjectHeader(self)
        header_v.sectionClicked.connect(  # pylint: disable=no-member
            self.add_geometry
        )
        header_v.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        header_v.customContextMenuRequested.connect(  # pylint: disable=no-member
            self.geometry_context_menu
        )
        self.setVerticalHeader(header_v)

        self.__delegate: UvSetDelegate = UvSetDelegate(self)
        self.setItemDelegate(self.__delegate)

        self.__copy_act = QtGui.QAction("Copy UV Set", self)
        self.__copy_act.setShortcut(QtGui.QKeySequence("Ctrl+C"))
        self.__copy_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__copy_act.triggered.connect(self.copy)
        self.addAction(self.__copy_act)

        self.__paste_act = QtGui.QAction("Paste UV Set", self)
        self.__paste_act.setShortcut(QtGui.QKeySequence("Ctrl+V"))
        self.__paste_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__paste_act.triggered.connect(self.paste)
        self.addAction(self.__paste_act)

        self.__duplicate_act = QtGui.QAction("Duplicate UV Set ...", self)
        self.__duplicate_act.setShortcut(QtGui.QKeySequence("Ctrl+D"))
        self.__duplicate_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__duplicate_act.triggered.connect(self.duplicate_uv_set)
        self.addAction(self.__duplicate_act)

        self.__delete_act = QtGui.QAction("Delete UV Set", self)
        self.__delete_act.setShortcut(QtGui.QKeySequence("Delete"))
        self.__delete_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__delete_act.triggered.connect(self.delete_uv_set_from_selection)
        self.addAction(self.__delete_act)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handles key press events.

        Args:
            event (QtGui.QKeyEvent): The key event.
        """
        key: int = event.key()
        if key == QtCore.Qt.Key.Key_Escape:
            if self.__copied_cells_data:
                self.clear_copy_data()
                self.viewport().update()
                _logger.info("Copy canceled.")
            event.accept()
            return

        super().keyPressEvent(event)

    def set_filter(self, text: str) -> None:
        """Sets a search filter on the table rows.

        Args:
            text (str): The text to filter by.
        """
        text = text.lower()
        for row in range(self.rowCount()):
            if row == self.rowCount() - 1:
                self.setRowHidden(row, False)
                continue

            header_item: QtWidgets.QTableWidgetItem = self.verticalHeaderItem(
                row
            )
            geometry: str = header_item.text().lower()
            self.setRowHidden(row, text not in geometry)

    def show_uv_set_context_menu(self, pos: QtCore.QPoint) -> None:
        """Shows the context menu for the horizontal UV header.

        Args:
            pos (QtCore.QPoint): The global position for the menu.
        """
        col: int = self.horizontalHeader().logicalIndexAt(pos)
        if col < 0 or col == self.columnCount() - 1:
            return

        uv_name: str = self.horizontalHeaderItem(col).text()
        menu = QtWidgets.QMenu(self)

        action: QtGui.QAction = menu.addAction(f'Set "{uv_name}" as Current')
        action.triggered.connect(partial(self.set_current_uv_set, col))
        if uv_name != "map1":
            menu.addSeparator()
            action = menu.addAction(f'Rename "{uv_name}" ...')
            action.triggered.connect(partial(self.rename_uv_set, col))

            action = menu.addAction(f'Delete "{uv_name}"')
            action.triggered.connect(partial(self.delete_uv_set, col))

        menu.exec_(self.horizontalHeader().mapToGlobal(pos))

    def geometry_context_menu(self, pos: QtCore.QPoint) -> None:
        """Shows the context menu for the vertical geometry header.

        Args:
            pos (QtCore.QPoint): The global position for the menu.
        """
        row: int = self.verticalHeader().logicalIndexAt(pos)
        if row < 0 or row == self.rowCount() - 1:
            return

        geometry: str = self.verticalHeaderItem(row).text()
        selected_rows: list[int] = list(
            set(item.row() for item in self.selectedItems())
        )

        menu = QtWidgets.QMenu(self)

        action: QtGui.QAction = menu.addAction(f'Remove "{geometry}"')
        action.triggered.connect(partial(self.remove_geometry, [row]))

        if selected_rows:
            action = menu.addAction(
                f"Remove {len(selected_rows)} selected items"
            )
            action.triggered.connect(
                partial(self.remove_geometry, selected_rows)
            )

        menu.addSeparator()

        action = menu.addAction("Cleanup Empty UV Sets")
        if selected_rows:
            action.triggered.connect(
                partial(self.cleanup_empty_uv_sets, selected_rows)
            )
        else:
            action.triggered.connect(partial(self.cleanup_empty_uv_sets, [row]))

        action = menu.addAction("Fix Errors")
        if selected_rows:
            action.triggered.connect(partial(self.fix_errors, selected_rows))
        else:
            action.triggered.connect(partial(self.fix_errors, [row]))

        menu.exec_(self.verticalHeader().mapToGlobal(pos))

    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Shows the context menu for the table cells.

        Args:
            pos (QtCore.QPoint): The global position for the menu.
        """
        item: QtWidgets.QTableWidgetItem | None = self.itemAt(pos)
        if not item:
            return

        if item.row() == self.rowCount() - 1:
            return

        if item.column() == self.columnCount() - 1:
            return

        menu = QtWidgets.QMenu(self)

        action: QtGui.QAction = menu.addAction("Set Current UVSet")
        action.triggered.connect(self.set_current_uv_set_from_cells)

        menu.addSeparator()

        menu.addAction(self.__copy_act)
        menu.addAction(self.__paste_act)
        menu.addAction(self.__duplicate_act)
        menu.addAction(self.__delete_act)

        menu.addSeparator()

        action = menu.addAction("Cleanup Empty UV Sets")
        action.triggered.connect(self.cleanup_empty_uv_sets)

        action = menu.addAction("Fix Errors")
        action.triggered.connect(self.fix_errors)

        menu.exec_(self.viewport().mapToGlobal(pos))

    @dcc.undo
    def selection_changed(self) -> None:
        """Handles item selection changes by selecting the geometry in Maya."""
        selected_items: list[QtWidgets.QTableWidgetItem] = self.selectedItems()
        if not selected_items:
            return

        geometries: list[str] = []
        processed_rows: set[int] = set()
        for item in selected_items:
            row: int = item.row()
            if row in processed_rows:
                continue

            processed_rows.add(row)
            geometries.append(self.verticalHeaderItem(row).text())

        if geometries:
            cmds.select(*geometries)

    @dcc.undo
    def show_uv_editor(self, item: QtWidgets.QTableWidgetItem) -> None:
        """Opens the Maya UV Editor and sets the active UV set.

        Args:
            item (QtWidgets.QTableWidgetItem): The double-clicked item.
        """
        row: int = item.row()
        geometry: str = self.verticalHeaderItem(row).text()
        uv_name: str = self.horizontalHeaderItem(item.column()).text()
        data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)

        if not cmds.objExists(geometry):
            _logger.error("Does not exist: %s", geometry)
            return

        if data.status == UvStatus.NONE:
            _logger.error(
                "Cannot open: %s does not exist on %s", uv_name, geometry
            )
            return

        elif data.status == UvStatus.EMPTY:
            _logger.warning("%s is an empty uv on %s.", uv_name, geometry)

        cmds.select(geometry)
        cmds.polyUVSet(geometry, currentUVSet=True, uvSet=uv_name)
        uv_editor: str = "polyTexturePlacementPanel1Window"
        if cmds.window(uv_editor, query=True, exists=True):
            if not cmds.window(uv_editor, query=True, visible=True):
                mel.eval("TextureViewWindow;")
        else:
            mel.eval("TextureViewWindow;")

        for col in range(self.columnCount() - 1):
            _item: QtWidgets.QTableWidgetItem = self.item(row, col)
            _uv_name: str = self.horizontalHeaderItem(_item.column()).text()
            is_current: bool = uv_name == _uv_name
            cell_data: UvCellData = cast(
                UvCellData, _item.data(QtCore.Qt.ItemDataRole.UserRole)
            )
            if isinstance(cell_data, UvCellData):
                cell_data = replace(cell_data, is_current=is_current)
                _item.setData(QtCore.Qt.ItemDataRole.UserRole, cell_data)

    @dcc.undo
    def create_uv_set(self, col: int) -> None:
        """Creates a new UV set on all managed geometries.

        Args:
            col (int): The column index clicked.
        """
        if col != self.columnCount() - 1:
            return

        new_name: str
        ok: bool
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create UV Set",
            "New UV set name:",
            QtWidgets.QLineEdit.EchoMode.Normal,
        )
        if not new_name or not ok:
            return

        changed: bool = False
        for geometry in self.__current_geometries:
            if create_uv_set(geometry, new_name):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def duplicate_uv_set(self) -> None:
        """Duplicates the selected UV set."""
        selected_items: list[QtWidgets.QTableWidgetItem] = self.selectedItems()
        if not selected_items:
            return

        new_name: str
        ok: bool
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Create UV Set from UV Set",
            "New UV set name:",
            QtWidgets.QLineEdit.EchoMode.Normal,
        )
        if not new_name or not ok:
            return

        changed: bool = False
        for item in selected_items:
            data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data.status == UvStatus.NONE:
                continue

            geometry: str = self.verticalHeaderItem(item.row()).text()
            src_uv: str = self.horizontalHeaderItem(item.column()).text()
            if duplicate_uv_set(geometry, src_uv, new_name):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def rename_uv_set(self, col: int) -> None:
        """Renames a UV set across all managed geometries.

        Args:
            col (int): The column index to rename.
        """
        if col == self.columnCount() - 1:
            return

        old_name: str = self.horizontalHeaderItem(col).text()
        if old_name == "map1":
            _logger.error("Cannot rename map1")
            return

        new_name: str
        ok: bool
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Rename UVSet",
            "New UV set name:",
            QtWidgets.QLineEdit.EchoMode.Normal,
            old_name,
        )

        if not new_name or not ok:
            return

        changed: bool = False
        for geometry in self.__current_geometries:
            if rename_uv_set(geometry, old_name, new_name):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def delete_uv_set(self, col: int) -> None:
        """Deletes a UV set across all managed geometries.

        Args:
            col (int): The column index representing the UV set.
        """
        if col == self.columnCount() - 1:
            return

        uv_set: str = self.horizontalHeaderItem(col).text()
        changed: bool = False
        for geometry in self.__current_geometries:
            if delete_uv_set(geometry, uv_set):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def delete_uv_set_from_selection(self) -> None:
        """Deletes the UV set corresponding to the currently selected cells."""
        selected_items: list[QtWidgets.QTableWidgetItem] = self.selectedItems()
        if not selected_items:
            return

        changed: bool = False
        for item in selected_items:
            data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data.status == UvStatus.NONE:
                continue

            geometry: str = self.verticalHeaderItem(item.row()).text()
            uv_set: str = self.horizontalHeaderItem(item.column()).text()
            if delete_uv_set(geometry, uv_set):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def set_current_uv_set(self, col: int) -> None:
        """Sets the active UV set based on the header clicked.

        Args:
            col (int): The column index clicked.
        """
        if col == self.columnCount() - 1:
            return

        uv_name: str = self.horizontalHeaderItem(col).text()
        changed: bool = False
        for geometry in self.__current_geometries:
            if set_current_uv_set(geometry, uv_name):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def set_current_uv_set_from_cells(self) -> None:
        """Sets the active UV set based on the selected cells."""
        selected_items: list[QtWidgets.QTableWidgetItem] = [
            i for i in self.selectedItems()
        ]
        if not selected_items:
            return

        changed: bool = False
        for item in selected_items:
            geo: str = self.verticalHeaderItem(item.row()).text()
            uv_name: str = self.horizontalHeaderItem(item.column()).text()
            data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data.status == UvStatus.NONE:
                _logger.warning("%s does not exist on %s", uv_name, geo)
                continue

            if set_current_uv_set(geo, uv_name):
                changed = True

        if changed:
            self.update_ui()

    @dcc.undo
    def cleanup_empty_uv_sets(self, rows: list[int] | None = None) -> None:
        """Removes all empty UV sets from the specified or selected rows.

        Args:
            rows (list[int] | None, optional): The rows to process.
        """
        selected_items: list[QtWidgets.QTableWidgetItem] = []
        if rows:
            for row in rows:
                for col in range(self.columnCount() - 1):
                    selected_items.append(self.item(row, col))
        else:
            selected_items = self.selectedItems()

        if not selected_items:
            return

        changed: bool = False
        for item in selected_items:
            data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data.status != UvStatus.EMPTY:
                continue

            geometry: str = self.verticalHeaderItem(item.row()).text()
            uv_set: str = self.horizontalHeaderItem(item.column()).text()
            if delete_uv_set(geometry, uv_set):
                changed = True

        if changed:
            self.update_ui()

        _logger.info("Done.")

    @dcc.undo
    def fix_errors(self, rows: list[int] | None = None) -> None:
        """Fixes invalid UV set states (missing map1, invalid names).

        Args:
            rows (list[int] | None, optional): The rows to process.
        """
        selected_items: list[QtWidgets.QTableWidgetItem] = []
        if rows:
            for row in rows:
                for col in range(self.columnCount() - 1):
                    selected_items.append(self.item(row, col))
        else:
            selected_items = self.selectedItems()

        if not selected_items:
            return

        geometries: list[str] = list(
            set(
                self.verticalHeaderItem(item.row()).text()
                for item in selected_items
            )
        )
        fixed_count = 0
        for geometry in geometries:
            if not cmds.objExists(geometry):
                _logger.error("Does not exist: %s", geometry)
                continue

            shapes: list[str] = (
                cmds.listRelatives(
                    geometry, shapes=True, type="mesh", noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            shape: str = shapes[0]
            uv_sets: list[str] = get_all_uv_sets(shape)
            if not uv_sets:
                cmds.polyUVSet(geometry, create=True, uvSet="map1")
                uv_sets = ["map1"]
                fixed_count += 1
                _logger.info("%s created map1.", geometry)

            if "map1" not in uv_sets:
                rename_uv_set(geometry, uv_sets[0], "map1")
                uv_sets[0] = "map1"
                fixed_count += 1
                _logger.info("%s restored first uv set to map1.", geometry)

            else:
                if uv_sets[0] != "map1":
                    cmds.polyUVSet(
                        geometry,
                        reorder=True,
                        uvSet="map1",
                        newUVSet=uv_sets[0],
                    )
                    idx: int = uv_sets.index("map1")
                    uv_sets[0] = uv_sets[idx]
                    uv_sets[idx] = uv_sets[0]
                    fixed_count += 1
                    _logger.info("%s forced map1 to index 0.", geometry)

            for i, uv in enumerate(uv_sets):
                if uv == "map1":
                    continue

                if not uv or not re.match(r"^[a-zA-Z0-9_]+$", uv):
                    safe_name: str = f"uvSet{i}"
                    rename_uv_set(geometry, uv, safe_name)
                    uv_sets[i] = safe_name
                    fixed_count += 1
                    _logger.info(
                        '%s recovered invalid UV name "%s" as "%s".',
                        geometry,
                        uv,
                        safe_name,
                    )

        if fixed_count > 0:
            _logger.info("Fixed %s errors.", fixed_count)
            self.update_ui()
        else:
            _logger.info("Done.")

    def add_geometry(self, row: int) -> None:
        """Adds selected geometries from Maya to the table.

        Args:
            row (int): The row index clicked.
        """
        if row != self.rowCount() - 1:
            return

        selection: list[str] = cmds.ls(selection=True, type="transform")
        added = False
        for geometry in selection:
            shapes: list[str] = (
                cmds.listRelatives(
                    geometry, shapes=True, type="mesh", noIntermediate=True
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
        """Copies the selected UV sets to an internal buffer."""
        self.clear_copy_data()

        selected_items: list[QtWidgets.QTableWidgetItem] = self.selectedItems()
        if not selected_items:
            return

        min_row: int = min(item.row() for item in selected_items)
        min_col: int = min(item.column() for item in selected_items)
        for item in selected_items:
            data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if data.status == UvStatus.NONE:
                continue

            row: int = item.row()
            col: int = item.column()
            geometry: str = self.verticalHeaderItem(row).text()
            uv_set: str = self.horizontalHeaderItem(col).text()

            data = replace(data, is_copied=True)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, data)

            self.__copied_cells_data.append(
                (row - min_row, col - min_col, geometry, uv_set)
            )

        self.__delegate.start_animation()

    @dcc.undo
    def paste(self) -> None:
        """Pastes the copied UV sets onto the current selection."""
        if not self.__copied_cells_data:
            return

        selected_items: list[QtWidgets.QTableWidgetItem] = self.selectedItems()
        if not selected_items:
            return

        paste_row: int = min(item.row() for item in selected_items)
        paste_col: int = min(item.column() for item in selected_items)
        pasted = False
        for rel_row, rel_col, src_geo, src_uv in self.__copied_cells_data:
            dst_row: int = paste_row + rel_row
            dst_col: int = paste_col + rel_col

            dst_geo_item: QtWidgets.QTableWidgetItem = self.verticalHeaderItem(
                dst_row
            )
            dst_uv_item: QtWidgets.QTableWidgetItem = self.horizontalHeaderItem(
                dst_col
            )
            if not dst_geo_item or not dst_uv_item:
                continue

            dst_geo: str = dst_geo_item.text()
            dst_uv: str = dst_uv_item.text()
            if copy_uv_set(src_geo, src_uv, dst_geo, dst_uv):
                pasted = True

        if pasted:
            self.clear_copy_data()
            self.update_ui()

    def clear_copy_data(self) -> None:
        """Clears the internal UV copy buffer and stops animations."""
        self.__copied_cells_data = []
        self.__delegate.stop_animation()
        for row in range(self.rowCount() - 1):
            for col in range(self.columnCount() - 1):
                item: QtWidgets.QTableWidgetItem | None = self.item(row, col)
                if not item:
                    continue

                data: UvCellData = item.data(QtCore.Qt.ItemDataRole.UserRole)
                if not data:
                    continue

                data = replace(data, is_copied=False)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, data)

    def remove_geometry(self, rows: list[int]) -> None:
        """Removes the specified rows from the table view.

        Args:
            rows (list[int]): A list of row indices to remove.
        """
        removed = False
        for row in rows:
            geometry: str = self.verticalHeaderItem(row).text()
            self.__current_geometries.remove(geometry)
            removed = True

        if removed:
            self.update_ui()

    def load_from_selection(self) -> None:
        """Loads the current Maya selection into the table."""
        selection: list[str] = cmds.ls(selection=True, type="transform")
        if selection:
            self.__current_geometries = selection

        self.update_ui()

    def update_ui(self) -> None:
        """Updates the table user interface based on current geometries."""
        self.blockSignals(True)
        self.clear()
        self.clear_copy_data()

        all_uvsets: set[str] = set()
        mesh_data: dict[str, Any] = {}
        for node in self.__current_geometries:
            if not cmds.objExists(node):
                continue

            shapes: list[str] = (
                cmds.listRelatives(
                    node, shapes=True, type="mesh", noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            shape: str = shapes[0]
            uv_sets: list[str] = get_all_uv_sets(shape)
            current_uv_set: str = get_current_uv_set(shape)
            has_error: bool = False
            if not uv_sets:  # Does not exists uv sets
                has_error = True

            elif 'map1' not in uv_sets:  # Does not exists map1
                has_error = True

            elif uv_sets[0] != 'map1':  # Map1 is not at index 0
                has_error = True

            uv_info: dict[str, UvStatus] = {}
            for uv_name in uv_sets:
                num_uvs: int = get_uv_count(shape, uv_name)
                uv_info[uv_name] = (
                    UvStatus.HAS_UV if num_uvs > 0 else UvStatus.EMPTY
                )
                if not uv_name or not re.match(r"^[a-zA-Z0-9_]+$", uv_name):
                    has_error = True
                    break

            all_uvsets.update(uv_sets)
            mesh_data[node] = {
                "current": current_uv_set,
                "uv_info": uv_info,
                "has_error": has_error,
            }

        geometries: list[str] = [geo for geo in mesh_data]
        self.setRowCount(len(geometries) + 1)

        unique_uvsets: list[str] = sorted(list(all_uvsets))
        if "map1" in unique_uvsets:
            unique_uvsets.remove("map1")
            unique_uvsets.insert(0, "map1")

        self.setColumnCount(len(unique_uvsets) + 1)

        for row, geometry in enumerate(geometries):
            current_uv_set = mesh_data[geometry]["current"]
            uv_info = mesh_data[geometry]["uv_info"]
            has_error = mesh_data[geometry]["has_error"]

            item: QtWidgets.QTableWidgetItem = QtWidgets.QTableWidgetItem(
                geometry
            )
            item.setData(QtCore.Qt.ItemDataRole.UserRole, has_error)
            self.setVerticalHeaderItem(row, item)

            for col, uvset in enumerate(unique_uvsets):
                is_current: bool = uvset == current_uv_set
                item = QtWidgets.QTableWidgetItem(uvset)
                self.setHorizontalHeaderItem(col, item)

                item = QtWidgets.QTableWidgetItem()
                item.setFlags(
                    QtCore.Qt.ItemFlag.ItemIsSelectable
                    | QtCore.Qt.ItemFlag.ItemIsEnabled
                )
                if uvset in uv_info:
                    cell_data: UvCellData = UvCellData(
                        is_current, uv_info[uvset], False
                    )
                else:
                    cell_data = UvCellData(False, UvStatus.NONE, False)

                item.setData(QtCore.Qt.ItemDataRole.UserRole, cell_data)
                self.setItem(row, col, item)

        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                if row == len(geometries) or col == len(unique_uvsets):
                    item = QtWidgets.QTableWidgetItem("")
                    item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                    self.setItem(row, col, item)

        item = QtWidgets.QTableWidgetItem("+")
        self.setVerticalHeaderItem(len(geometries), item)

        item = QtWidgets.QTableWidgetItem("+")
        self.setHorizontalHeaderItem(len(unique_uvsets), item)

        self.blockSignals(False)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the UV Set Editor tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
            unique_id (str, optional): A unique ID for saving window states.
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)
        self.__filter: QtWidgets.QLineEdit
        self.__table: UvSetTableWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget containing the UI.
        """
        main_layout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(header_layout)

        self.__filter = QtWidgets.QLineEdit(parent)
        self.__filter.setPlaceholderText("Search ...")
        header_layout.addWidget(self.__filter)

        update_btn: widgets.IconButton = widgets.IconButton(self)
        update_btn.set_icon(dcc.get_icon_path("a_update.png"))
        header_layout.addWidget(update_btn)

        self.__table = UvSetTableWidget(parent)
        self.__table.load_from_selection()
        self.__table.set_filter(self.__filter.text())
        main_layout.addWidget(self.__table)

        # Event
        self.__filter.textChanged.connect(self.__table.set_filter)
        update_btn.clicked.connect(  # pylint: disable=no-member
            self.__table.load_from_selection
        )

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )


def get_all_uv_sets(geometry: str) -> list[str]:
    """Retrieves all UV sets associated with the specified geometry.

    Args:
        geometry (str): The name of the geometry node.

    Returns:
        list[str]: A list of UV set names.
    """
    if not cmds.objExists(geometry):
        return []

    uv_sets: list[str] = cmds.polyUVSet(
        geometry,
        query=True,
        allUVSets=True,
    )  # type: ignore

    return uv_sets or []


def get_current_uv_set(geometry: str) -> str:
    """Retrieves the name of the currently active UV set.

    Args:
        geometry (str): The name of the geometry node.

    Returns:
        str: The name of the current UV set, or an empty string.
    """
    current_uv_sets: list[str] = cmds.polyUVSet(
        geometry,
        query=True,
        currentUVSet=True,
    )  # type: ignore
    return current_uv_sets[0] if current_uv_sets else ""


def get_uv_count(shape: str, uv_name: str) -> int:
    """Returns the total number of UV coordinates for a specific UV set.

    Args:
        shape (str): The shape node name.
        uv_name (str): The name of the UV set.

    Returns:
        int: The highest count of either U or V coordinates.
    """
    sel = OpenMaya.MSelectionList()
    sel.add(shape)
    dag_path: OpenMaya.MDagPath = sel.getDagPath(0)
    fn_mesh = OpenMaya.MFnMesh(dag_path)

    u_array: OpenMaya.MFloatArray
    v_array: OpenMaya.MFloatArray
    u_array, v_array = fn_mesh.getUVs(uv_name)
    return max(len(u_array), len(v_array))


def create_uv_set(geometry: str, uv_name: str) -> bool:
    """Creates a new UV set on the specified geometry.

    Args:
        geometry (str): The name of the geometry node.
        uv_name (str): The name of the new UV set.

    Returns:
        bool: True if created successfully, False otherwise.
    """
    exist_uvs: list[str] = get_all_uv_sets(geometry)
    if uv_name in exist_uvs:
        return False

    cmds.polyUVSet(geometry, create=True, uvSet=uv_name)
    return True


def duplicate_uv_set(geometry: str, src_uv: str, dst_uv: str) -> bool:
    """Duplicates an existing UV set.

    Args:
        geometry (str): The name of the geometry node.
        src_uv (str): The source UV set name.
        dst_uv (str): The target UV set name.

    Returns:
        bool: True if duplicated successfully, False otherwise.
    """
    exist_uvs: list[str] = get_all_uv_sets(geometry)
    if dst_uv in exist_uvs or src_uv not in exist_uvs:
        return False

    cmds.polyUVSet(geometry, copy=True, uvSet=src_uv, newUVSet=dst_uv)
    return True


def delete_uv_set(geometry: str, uv_name: str) -> bool:
    """Deletes a specific UV set from the geometry.

    Args:
        geometry (str): The name of the geometry node.
        uv_name (str): The name of the UV set to delete.

    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    if uv_name == "map1":
        _logger.error("Cannot delete map1")
        return False

    exist_uvs: list[str] = get_all_uv_sets(geometry)
    if uv_name not in exist_uvs:
        return False

    cmds.polyUVSet(geometry, delete=True, uvSet=uv_name)
    return True


def rename_uv_set(geometry: str, old_name: str, new_name: str) -> bool:
    """Renames an existing UV set.

    Args:
        geometry (str): The name of the geometry node.
        old_name (str): The current name of the UV set.
        new_name (str): The new name for the UV set.

    Returns:
        bool: True if renamed successfully, False otherwise.
    """
    if old_name == "map1":
        _logger.error("Cannot rename map1")
        return False

    exist_uvs: list[str] = get_all_uv_sets(geometry)
    if old_name in exist_uvs and new_name not in exist_uvs:
        cmds.polyUVSet(geometry, rename=True, uvSet=old_name, newUVSet=new_name)
        return True

    return False


def set_current_uv_set(geometry: str, uv_name: str) -> bool:
    """Sets the active UV set for the geometry.

    Args:
        geometry (str): The name of the geometry node.
        uv_name (str): The name of the UV set to make active.

    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    exist_uvs: list[str] = get_all_uv_sets(geometry)
    if uv_name in exist_uvs:
        cmds.polyUVSet(geometry, currentUVSet=True, uvSet=uv_name)
        return True

    return False


def copy_uv_set(src_geo: str, src_uv: str, dst_geo: str, dst_uv: str) -> bool:
    """Copies UV set data from one geometry to another.

    Args:
        src_geo (str): The source geometry name.
        src_uv (str): The source UV set name.
        dst_geo (str): The destination geometry name.
        dst_uv (str): The destination UV set name.

    Returns:
        bool: True if copied successfully, False otherwise.
    """
    if not cmds.objExists(dst_geo):
        return False

    if src_geo != dst_geo:
        _logger.warning(
            "Cannot paste UV set to a different geometry : %s -> %s",
            src_geo,
            dst_geo,
        )
        return False

    if src_uv == dst_uv:
        return False

    exist_uvs: list[str] = get_all_uv_sets(dst_geo)
    if dst_uv not in exist_uvs:
        cmds.polyUVSet(dst_geo, create=True, uvSet=dst_uv)

    cmds.polyCopyUV(dst_geo, uvSetNameInput=src_uv, uvSetName=dst_uv)
    return True


def main(unique_id: str = "") -> None:
    """Shows the tool main window.

    Args:
        unique_id (str, optional): A unique ID for the window. Defaults to "".
    """
    window = MainWindow(unique_id=unique_id)
    window.show()
