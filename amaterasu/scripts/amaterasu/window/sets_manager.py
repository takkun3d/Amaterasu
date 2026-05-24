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
"""Tool for managing selection sets in Autodesk Maya.

This module provides a UI to create, modify, and manage selection sets,
including a favorite system for quick access to frequently used sets.
"""

from __future__ import annotations
from typing import cast, Any
from dataclasses import dataclass

from maya import cmds
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils

__product__: str = "Sets Manager"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)

IGNORE_SETS: tuple[str, ...] = (
    "defaultLightSet",
    "defaultObjectSet",
    "initialParticleSE",
    "initialShadingGroup",
    "TurtleDefaultBakeLayer",
)


@dataclass(slots=True)
class ActionDef:
    """Data class representing an action button in the delegate.

    Attributes:
        name (str): The internal identifier for the action.
        icon_name (str): The filename of the icon image.
    """

    name: str
    icon_name: str


FAVORITE_ICONS: tuple[str, str] = (
    "view/a_star_off.png",
    "view/a_star_on.png",
)

ACTION_LIST: tuple[ActionDef, ...] = (
    ActionDef("add", "view/a_add.png"),
    ActionDef("remove", "view/a_remove.png"),
    ActionDef("show", "view/a_show.png"),
    ActionDef("hide", "view/a_hide.png"),
    ActionDef("delete", "view/a_trash.png"),
)


class Settings(framework.ToolSettings):
    """Settings for the Sets Manager tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        ignore_reference (framework.Variant[bool]): State of the ignore reference option.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    ignore_reference: framework.Variant[bool] = framework.Variant(False)


class SetsViewDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate for rendering sets and interaction buttons.

    Handles the drawing of the favorite star, text, and action buttons,
    as well as routing mouse clicks to the appropriate signals.
    """

    CELL_SIZE: int = 20
    favorite_toggled = QtCore.Signal(str, bool)
    action_triggered = QtCore.Signal(str, str, QtCore.Qt.KeyboardModifier)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the delegate and caches icons for performance.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__favorite_icons: tuple[QtGui.QPixmap, ...] = tuple(
            QtGui.QPixmap(dcc.get_icon_path(icon)) for icon in FAVORITE_ICONS
        )
        self.__action_icons: list[QtGui.QPixmap] = [
            QtGui.QPixmap(dcc.get_icon_path(action.icon_name))
            for action in ACTION_LIST
        ]

    def createEditor(
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        """Creates the editor widget for renaming sets.

        Args:
            parent (QtWidgets.QWidget): The parent widget.
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.

        Returns:
            QtWidgets.QWidget: The editor widget (QLineEdit) or base editor.
        """
        if index.column() == 1:
            return QtWidgets.QLineEdit(parent)

        return super().createEditor(parent, option, index)

    def setEditorData(
        self,
        editor: QtWidgets.QWidget,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Populates the editor widget with the current sets name.

        Args:
            editor (QtWidgets.QWidget): The editor widget.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.
        """
        if index.column() == 1 and isinstance(editor, QtWidgets.QLineEdit):
            value: str = index.model().data(
                index, QtCore.Qt.ItemDataRole.EditRole
            )
            editor.setText(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(
        self,
        editor: QtWidgets.QWidget,
        model: QtCore.QAbstractItemModel,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Saves the renamed sets back to the model and Maya scene.

        Args:
            editor (QtWidgets.QWidget): The editor widget.
            model (QtCore.QAbstractItemModel): The data model.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.
        """
        if index.column() == 1 and isinstance(editor, QtWidgets.QLineEdit):
            new_value: str = editor.text()
            old_value: str = index.data()
            if old_value == new_value:
                return

            try:
                actual_name: str = cmds.rename(old_value, new_value)
                model.setData(
                    index, actual_name, QtCore.Qt.ItemDataRole.EditRole
                )

            except RuntimeError:
                _logger.error("Failed rename : %s -> %s", old_value, new_value)

        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Updates the geometry of the editor to match the cell.

        Args:
            editor (QtWidgets.QWidget): The editor widget.
            option (QtWidgets.QStyleOptionViewItem): Style options containing the rect.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.
        """
        editor.setGeometry(option.rect)

    def editorEvent(
        self,
        event: QtCore.QEvent,
        model: QtCore.QAbstractItemModel,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> bool:
        """Handles mouse interactions (clicks) on the custom drawn elements.

        Args:
            event (QtCore.QEvent): The UI event.
            model (QtCore.QAbstractItemModel): The data model.
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.

        Returns:
            bool: True if the event was handled, otherwise False.
        """
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            mouse_event: QtGui.QMouseEvent = cast(QtGui.QMouseEvent, event)
            if index.column() == 0:
                is_favorite: bool = not index.model().data(
                    index, QtCore.Qt.ItemDataRole.EditRole
                )
                model.setData(
                    index, is_favorite, QtCore.Qt.ItemDataRole.EditRole
                )

                sets_name: str = model.index(index.row(), 1).data()
                self.favorite_toggled.emit(sets_name, is_favorite)
                return True

            elif index.column() == 1:
                sets_name = model.index(index.row(), 1).data()
                self.action_triggered.emit(
                    "select",
                    sets_name,
                    QtWidgets.QApplication.keyboardModifiers(),
                )
                return True

            elif index.column() == 2:
                for i, action_def in enumerate(ACTION_LIST):
                    action_rect: QtCore.QRect = QtCore.QRect(
                        option.rect.left() + self.CELL_SIZE * i,
                        option.rect.top(),
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    if action_rect.contains(mouse_event.pos()):
                        sets_name = model.index(index.row(), 1).data()
                        self.action_triggered.emit(
                            action_def.name,
                            sets_name,
                            QtWidgets.QApplication.keyboardModifiers(),
                        )
                        return True

        return super().editorEvent(event, model, option, index)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Draws the custom cell contents including icons and backgrounds.

        Args:
            painter (QtGui.QPainter): The painter object.
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.
        """
        data: Any = index.data()
        painter.fillRect(
            option.rect, QtGui.QColor(QtCore.Qt.GlobalColor.transparent)
        )

        if index.column() == 0:
            icon: QtGui.QPixmap = self.__favorite_icons[int(data)]
            pos: QtCore.QPoint = QtCore.QPoint(
                int(
                    option.rect.x()
                    + (option.rect.width() / 2.0)
                    - (icon.width() / 2.0)
                ),
                int(
                    option.rect.y()
                    + (option.rect.height() / 2.0)
                    - (icon.height() / 2.0)
                ),
            )
            painter.drawPixmap(pos, icon)

        elif index.column() == 1:
            if option.state & QtWidgets.QStyle.StateFlag.State_MouseOver:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.drawText(
                option.rect,
                QtCore.Qt.AlignmentFlag.AlignLeft
                | QtCore.Qt.AlignmentFlag.AlignVCenter,
                str(data),
            )

        elif index.column() == 2:
            for i, icon in enumerate(self.__action_icons):
                pos = QtCore.QPoint(
                    int(
                        option.rect.x()
                        + (icon.width() / 2.0)
                        + (self.CELL_SIZE * i)
                    ),
                    int(
                        option.rect.y()
                        + (option.rect.height() / 2.0)
                        - (icon.height() / 2.0)
                    ),
                )
                painter.drawPixmap(pos, icon)

            if not option.state & QtWidgets.QStyle.StateFlag.State_MouseOver:
                background_brush: QtGui.QBrush = option.palette.base()
                over_color: QtGui.QColor = background_brush.color()
                over_color.setAlphaF(0.8)
                background_brush.setColor(over_color)
                painter.fillRect(option.rect, background_brush)

    def sizeHint(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtCore.QSize:
        """Returns the appropriate size for the cell.

        Args:
            option (QtWidgets.QStyleOptionViewItem): Style options.
            index (QtCore.QModelIndex | QtCore.QPersistentModelIndex): The model index.

        Returns:
            QtCore.QSize: The calculated size hint for the cell.
        """
        if index.column() == 0:
            return QtCore.QSize(self.CELL_SIZE, self.CELL_SIZE)

        elif index.column() == 1:
            return QtCore.QSize(option.rect.width(), option.rect.height())

        else:
            return QtCore.QSize(
                self.CELL_SIZE * len(ACTION_LIST) + 10, self.CELL_SIZE
            )


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Sets Manager tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Window.
            unique_id (str, optional): A unique identifier for the window instance.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        self.__model: QtGui.QStandardItemModel
        self.__sets_name: QtWidgets.QLineEdit

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__sets_name = QtWidgets.QLineEdit(self)
        main_layout.addWidget(self.__sets_name, 0, 0)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Create", self)
        button.clicked.connect(self.create_sets)
        main_layout.addWidget(button, 0, 1)

        tab: QtWidgets.QTabWidget = QtWidgets.QTabWidget(self)
        tab.setDocumentMode(True)
        main_layout.addWidget(tab, 1, 0, 1, 2)

        self.__model = QtGui.QStandardItemModel(0, 3, self)
        delegater: SetsViewDelegate = SetsViewDelegate(self)
        delegater.favorite_toggled.connect(self.favorite)
        delegater.action_triggered.connect(self.action)

        view: QtWidgets.QTreeView = QtWidgets.QTreeView(self)
        view.setModel(self.__model)
        view.setItemDelegate(delegater)
        view.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        view.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        view.setRootIsDecorated(False)
        self.__setup_view_header(view)
        view.setMouseTracking(True)
        view.viewportEntered.connect(view.viewport().update)
        tab.addTab(view, "Sets")

        proxy_model = QtCore.QSortFilterProxyModel(self)
        proxy_model.setDynamicSortFilter(True)
        proxy_model.setSourceModel(self.__model)
        proxy_model.setFilterKeyColumn(0)
        proxy_model.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseSensitive
        )
        proxy_model.setFilterWildcard("true")
        proxy_model.setFilterRole(QtCore.Qt.ItemDataRole.EditRole)

        proxy_view: QtWidgets.QTreeView = QtWidgets.QTreeView(self)
        proxy_view.setModel(proxy_model)
        proxy_view.setItemDelegate(delegater)
        proxy_view.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        proxy_view.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        proxy_view.setRootIsDecorated(False)
        self.__setup_view_header(proxy_view)
        proxy_view.setMouseTracking(True)
        proxy_view.viewportEntered.connect(proxy_view.viewport().update)
        tab.addTab(proxy_view, "Favorite")

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        self.update_model()

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates custom menus for view options.

        Args:
            menu_bar (QtWidgets.QMenuBar): The main menu bar widget.
        """
        view_menu: QtWidgets.QMenu = QtWidgets.QMenu("View", self)
        menu_bar.addMenu(view_menu)

        ignore_reference_sets: QtGui.QAction = view_menu.addAction(
            "Ignore Referenced sets"
        )
        ignore_reference_sets.setCheckable(True)
        ignore_reference_sets.triggered.connect(self.update_model)
        ignore_reference_sets.triggered.connect(self.save_settings)

        action: QtGui.QAction = view_menu.addAction("Update")
        action.triggered.connect(self.update_model)

        settings: Settings = self.tool_settings()
        settings.ignore_reference.bind(
            setter=ignore_reference_sets.setChecked,
            getter=ignore_reference_sets.isChecked,
        )

    def __setup_view_header(self, view: QtWidgets.QTreeView) -> None:
        """Configures the header dimensions for the tree view.

        Args:
            view (QtWidgets.QTreeView): The tree view to configure.
        """
        header: QtWidgets.QHeaderView = view.header()
        header.hide()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

    @QtCore.Slot(str, bool)
    @dcc.undo
    def favorite(self, sets_name: str, value: bool) -> None:
        """Saves the favorite state when toggled from the delegate.

        Args:
            sets_name (str): The target sets name.
            value (bool): The new favorite state.
        """
        dcc.sets.set_favorite_state(sets_name, value)

    @QtCore.Slot(str, str, QtCore.Qt.KeyboardModifier)
    @dcc.undo
    def action(
        self,
        action_name: str,
        sets_name: str,
        modifiers: QtCore.Qt.KeyboardModifier,
    ) -> None:
        """Routes the dynamically triggered actions from the delegate to functions.

        Args:
            action_name (str): The name of the action triggered
                (e.g., 'select', 'add').
            sets_name (str): The target sets name.
            modifiers (QtCore.Qt.KeyboardModifier): The keyboard modifiers active during the event.
        """
        result: utils.Result = utils.Result()
        if action_name == "select":
            mode: dcc.sets.SelectionMode = dcc.sets.SelectionMode.REPLACE
            if (modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier) and (
                modifiers & QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                mode = dcc.sets.SelectionMode.ADD

            elif modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
                mode = dcc.sets.SelectionMode.TOGGLE

            elif modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
                mode = dcc.sets.SelectionMode.DESELECT

            dcc.sets.select(sets_name, mode)

        elif action_name == "add":
            result = dcc.sets.add_member(sets_name)

        elif action_name == "remove":
            result = dcc.sets.remove_member(sets_name)

        elif action_name == "show":
            result = dcc.sets.show_member(sets_name)

        elif action_name == "hide":
            result = dcc.sets.hide_member(sets_name)

        elif action_name == "delete":
            result = dcc.sets.delete(sets_name)
            self.update_model()

        if result.status() != utils.ResultStatus.SUCCESS:
            result.log(_logger)

    @QtCore.Slot()
    def create_sets(self) -> None:
        """Handles the creation of a new sets from the UI input."""
        sets_name: str = self.__sets_name.text()
        if not sets_name:
            return

        new_sets: str = dcc.sets.create(sets_name)
        self.add_item(new_sets)
        self.__sets_name.setText("")

    def add_item(self, sets_name: str) -> None:
        """Adds a single sets item to the model.

        Args:
            sets_name (str): The name of the sets to add.
        """
        row: int = self.__model.rowCount()
        self.__model.setRowCount(row + 1)

        index: QtCore.QModelIndex = self.__model.index(row, 0)
        self.__model.setData(index, dcc.sets.get_favorite_state(sets_name))

        index = self.__model.index(row, 1)
        self.__model.setData(index, sets_name)

        index = self.__model.index(row, 2)
        self.__model.setData(index, None)

    @QtCore.Slot()
    def update_model(self) -> None:
        """Refreshes the view model with the current Maya scene data."""
        self.__model.removeRows(0, self.__model.rowCount())

        sets_list: list[str] = cmds.ls(sets=True)
        if self.tool_settings().ignore_reference.value():
            sets_list = cmds.ls("*", sets=True)

        for sets_node in sets_list:
            if sets_node in IGNORE_SETS:
                continue

            if cmds.sets(sets_node, query=True, renderable=True):
                continue

            if cmds.sets(sets_node, query=True, edges=True):
                continue

            if cmds.sets(sets_node, query=True, editPoints=True):
                continue

            if cmds.sets(sets_node, query=True, facets=True):
                continue

            if cmds.sets(sets_node, query=True, vertices=True):
                continue

            self.add_item(sets_node)


def main(unique_id: str = "") -> None:
    """Entry point for launching the Sets Manager tool window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
