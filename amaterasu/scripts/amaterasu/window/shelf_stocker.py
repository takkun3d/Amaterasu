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
"""Tool for stocking and organizing Maya shelf icons.

This module allows users to drag and drop shelf buttons from the Maya UI
into a custom window, saving them for quick access across different workspaces.
"""

from __future__ import annotations
from typing import Any
from functools import partial
import json
import dataclasses
from maya import cmds, mel
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Shelf Stocker"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)

SHELF_MIME_TYPE: str = "text/plain"
MAYA_MIME_TYPE: str = "application/x-qabstractitemmodeldatalist"
MIME_TYPE: str = "application/x-amaterasu-shelf-stocker-data"
SHELF_ARROW: str = "a_shelf_arrow.png"

SHELF_WIDGET_CSS: str = """
ShelfWidget {
    show-decoration-selected: 0;
    outline: 0;
}
ShelfWidget::item:selected {
    background: transparent;
    border: none;
}
ShelfWidget::item:hover {
    background: transparent;
}
"""


class Settings(framework.ToolSettings):
    """Settings for the Shelf Stocker tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        shelf_data (framework.Variant[list[dict[str, Any]]]):
            Saved shelf button configurations.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    shelf_data: framework.Variant[list[dict[str, Any]]] = framework.Variant([])


@dataclasses.dataclass(slots=True)
class SubMenuItemData:
    """Data class representing a right-click submenu item for a shelf button.

    Attributes:
        label (str): The display text of the submenu item.
        command (str): The script command to execute.
        language (str): The script language (e.g., 'python' or 'mel').
        separator (bool): Whether this item is a visual separator.
    """

    label: str = ""
    command: str = ""
    language: str = "python"
    separator: bool = False

    @classmethod
    def from_maya_ui(cls, menu_item: str) -> SubMenuItemData | None:
        """Creates a SubMenuItemData instance by querying a Maya menu item UI.

        Args:
            menu_item (str): The UI name of the Maya menu item.

        Returns:
            SubMenuItemData | None: The populated data class,
                or None if it is an internal Maya item.
        """
        cmd: str = cmds.menuItem(menu_item, query=True, command=True)  # type: ignore
        if cmd and "/*dSBRMBMI*/" in cmd:
            return None

        return cls(
            cmds.menuItem(menu_item, query=True, label=True),  # type: ignore
            cmd,
            cmds.menuItem(menu_item, query=True, sourceType=True),  # type: ignore
            cmds.menuItem(menu_item, query=True, divider=True),  # type: ignore
        )


@dataclasses.dataclass(slots=True)
class ShelfButtonData:
    """Data class representing a Maya shelf button configuration.

    Attributes:
        label (str): The text label of the button.
        overlay_label (str): The short overlay text drawn on the icon.
        annotation (str): The tooltip description.
        command (str): The primary script command to execute on single click.
        dc_command (str): The script command to execute on double click.
        image (str): The path or name of the icon image.
        language (str): The script language (e.g., 'python' or 'mel').
        sub_menu (list[SubMenuItemData]):
            A list of right-click submenu configurations.
    """

    label: str = ""
    overlay_label: str = ""
    annotation: str = ""
    command: str = ""
    dc_command: str = ""
    image: str = ""
    language: str = "python"
    sub_menu: list[SubMenuItemData] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShelfButtonData:
        """Creates a ShelfButtonData instance from a dictionary.

        Args:
            data (dict[str, Any]): The dictionary containing raw JSON data.

        Returns:
            ShelfButtonData: The populated data class instance.
        """
        sub_menu: list[SubMenuItemData] = [
            SubMenuItemData(**item) for item in data.get("sub_menu", [])
        ]
        return cls(
            data.get("label", ""),
            data.get("overlay_label", ""),
            data.get("annotation", ""),
            data.get("command", ""),
            data.get("dc_command", ""),
            data.get("image", ""),
            data.get("language", "mel"),
            sub_menu,
        )

    @classmethod
    def from_maya_ui(cls, button: str) -> ShelfButtonData:
        """Creates a ShelfButtonData instance by querying a Maya shelf button UI.

        Args:
            button (str): The UI name of the Maya shelf button.

        Returns:
            ShelfButtonData: The populated data class.
        """
        menu_list: list[str] = cmds.shelfButton(
            button, query=True, popupMenuArray=True
        )  # type: ignore
        menu_items: list[str] = (
            cmds.popupMenu(menu_list, query=True, itemArray=True) or []  # type: ignore
        )

        sub_menu: list[SubMenuItemData] = []
        for menu_item in menu_items:
            item_data: SubMenuItemData | None = SubMenuItemData.from_maya_ui(
                menu_item
            )
            if item_data:
                sub_menu.append(item_data)

        return cls(
            cmds.shelfButton(button, query=True, label=True),  # type: ignore
            cmds.shelfButton(button, query=True, imageOverlayLabel=True),  # type: ignore
            cmds.shelfButton(button, query=True, annotation=True),  # type: ignore
            cmds.shelfButton(button, query=True, command=True),  # type: ignore
            cmds.shelfButton(button, query=True, doubleClickCommand=True),  # type: ignore
            cmds.shelfButton(button, query=True, image1=True),  # type: ignore
            cmds.shelfButton(button, query=True, sourceType=True),  # type: ignore
            sub_menu,
        )


class ShelfButton(QtWidgets.QLabel):
    """A custom widget representing a stocked shelf button."""

    clicked = QtCore.Signal()
    double_clicked = QtCore.Signal()
    delete = QtCore.Signal()

    def __init__(
        self,
        icon: QtGui.QIcon,
        label: str = "",
        context_menu_data: list[SubMenuItemData] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the ShelfButton.

        Args:
            icon (QtGui.QIcon): The icon to display.
            label (str, optional): The overlay label. Defaults to "".
            context_menu_data (list[SubMenuItemData] | None, optional):
                Data for the right-click menu. Defaults to None.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)

        if not context_menu_data:
            context_menu_data = []

        self.setFixedSize(34, 34)
        self.setContentsMargins(0, 0, 0, 0)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.__timer: QtCore.QTimer = QtCore.QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__time_out)
        self.__count: int = 0
        self.__icon: QtGui.QIcon = icon
        self.__label: str = label
        self.__context_menu_data: list[SubMenuItemData] = context_menu_data
        self.set_icon(icon, label)

    def set_icon(self, icon: QtGui.QIcon, label: str = "") -> None:
        """Sets the icon and overlay label for the widget.

        Args:
            icon (QtGui.QIcon): The icon to apply.
            label (str, optional): The text overlay to draw. Defaults to "".
        """
        self.__icon = icon
        self.__label = label

        pixmap: QtGui.QPixmap = icon.pixmap(QtCore.QSize(32, 32))
        painter: QtGui.QPainter = QtGui.QPainter()
        painter.begin(pixmap)

        if self.__context_menu_data:
            painter.drawPixmap(
                0,
                0,
                QtGui.QPixmap(dcc.get_icon_path(SHELF_ARROW)),
            )

        if label:
            brush: QtGui.QBrush = QtGui.QBrush(
                QtGui.QColor(0, 0, 0, 150), QtCore.Qt.BrushStyle.SolidPattern
            )
            painter.setBrush(brush)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QtCore.QRect(0, 17, 32, 15), 2, 2)

            painter.setFont(QtGui.QFont("Arial", 7, QtGui.QFont.Weight.Bold))
            painter.setPen(QtGui.QColor(204, 204, 204))
            painter.drawText(
                QtCore.QRect(0, 0, 32, 30),
                QtCore.Qt.AlignmentFlag.AlignHCenter
                | QtCore.Qt.AlignmentFlag.AlignBottom,
                label,
            )

        painter.end()
        self.setPixmap(pixmap)

    def set_context_menu_data(
        self, context_menu_data: list[SubMenuItemData]
    ) -> None:
        """Updates the context menu data for this button.

        Args:
            context_menu_data (list[SubMenuItemData]):
                The new menu configuration data.
        """
        self.__context_menu_data = context_menu_data
        self.set_icon(self.__icon, self.__label)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse press events for click detection.

        Args:
            event (QtGui.QMouseEvent): The Qt mouse event.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.__count == 0:
                self.__timer.start(QtWidgets.QApplication.doubleClickInterval())

            else:
                self.__count += 1

        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse release events to distinguish clicks from double-clicks.

        Args:
            event (QtGui.QMouseEvent): The Qt mouse event.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.__count += 1
            if self.__count == 1 and not self.__timer.isActive():
                self.clicked.emit()
                self.__count = 0

            elif self.__count >= 2:
                self.double_clicked.emit()
                self.__count = 0
                self.__timer.stop()

        else:
            super().mouseReleaseEvent(event)

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, position: QtCore.QPoint) -> None:
        """Displays the right-click context menu.

        Args:
            position (QtCore.QPoint): The local position to show the menu.
        """
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self)

        action: QtGui.QAction = menu.addAction("Delete")
        action.triggered.connect(self.__delete_item)

        menu.addSeparator()

        for menu_item in self.__context_menu_data:
            if menu_item.separator:
                menu.addSeparator()
                continue

            action = menu.addAction(menu_item.label)
            if menu_item.language == "python":
                action.triggered.connect(partial(exec_py, menu_item.command))

            else:
                action.triggered.connect(partial(exec_mel, menu_item.command))

        menu.exec_(self.mapToGlobal(position))

    @QtCore.Slot()
    def __delete_item(self) -> None:
        """Emits the signal to delete this button."""
        self.delete.emit()

    @QtCore.Slot()
    def __time_out(self) -> None:
        """Handles click logic if the double-click timer expires."""
        if self.__count == 1:
            self.clicked.emit()
            self.__count = 0


class ShelfWidget(widgets.ListWidget):
    """A list widget modified to act as a custom Maya shelf."""

    data_changed = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the ShelfWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setFlow(QtWidgets.QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QtWidgets.QListWidget.ResizeMode.Adjust)
        self.setSpacing(2)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.setDragEnabled(True)
        self.setDragDropMode(
            QtWidgets.QAbstractItemView.DragDropMode.InternalMove
        )
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setMinimumSize(QtCore.QSize(40, 40))
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setStyleSheet(SHELF_WIDGET_CSS)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.set_placeholder_text(
            "Drag and drop Maya shelf buttons here to stock them."
        )

    def startDrag(self, supported_actions: QtCore.Qt.DropAction) -> None:
        """Custom drag initialization for dragging items internally.

        Args:
            supported_actions (QtCore.Qt.DropAction): The allowed drop actions.
        """
        items: list[QtWidgets.QListWidgetItem] = self.selectedItems()
        mime_data: QtCore.QMimeData = self.mimeData(items)
        mime_data.setProperty(MIME_TYPE, items)

        drag: QtGui.QDrag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)

        pixmap: QtGui.QPixmap = QtGui.QPixmap(
            self.viewport().visibleRegion().boundingRect().size()
        )
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter: QtGui.QPainter = QtGui.QPainter()
        painter.begin(pixmap)
        for item in items:
            rect: QtCore.QRect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))

        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QtGui.QCursor.pos()))
        drag.exec_(supported_actions)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Filters mouse presses to ignore middle clicks unless on an item.

        Args:
            event (QtGui.QMouseEvent): The Qt mouse event.
        """
        super().mousePressEvent(event)
        if event.buttons() != QtCore.Qt.MouseButton.MiddleButton or self.itemAt(
            event.pos()
        ):
            return

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accepts drag events from Maya shelves or internal items.

        Args:
            event (QtGui.QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasFormat(
            SHELF_MIME_TYPE
        ) or event.mimeData().hasFormat(MAYA_MIME_TYPE):
            event.accept()

        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handles drops, generating new buttons from Maya shelf data.

        Args:
            event (QtGui.QDropEvent): The drop event.
        """
        if event.mimeData().hasFormat(SHELF_MIME_TYPE):
            command: str = event.mimeData().text()
            self._import_from_maya_shelf(command)

        elif event.mimeData().hasFormat(MAYA_MIME_TYPE):
            super().dropEvent(event)
            self.data_changed.emit()

    def _import_from_maya_shelf(self, target_command: str) -> None:
        """Parses the active Maya shelf to find and import a dropped button.

        Args:
            target_command (str): The command of the dropped shelf button.
        """
        current_tab: str = cmds.shelfTabLayout(
            "ShelfLayout", query=True, selectTab=True
        )  # type: ignore
        buttons: list[str] = cmds.layout(
            current_tab, query=True, childArray=True
        )  # type: ignore
        for button in buttons:
            if "separator" in button.lower():
                continue

            btn_cmd: str = cmds.shelfButton(button, query=True, command=True)  # type: ignore
            if btn_cmd != target_command:
                continue

            data: ShelfButtonData = ShelfButtonData.from_maya_ui(button)
            self.add_button(data)
            self.data_changed.emit()
            break

    def add_button(self, data: ShelfButtonData) -> None:
        """Creates and adds a new ShelfButton to the widget.

        Args:
            data (ShelfButtonData): The shelf button configuration data class.
        """
        shelf_button: ShelfButton = ShelfButton(
            QtGui.QIcon(dcc.get_icon_path(data.image)),
            data.overlay_label,
            data.sub_menu,
            self,
        )
        shelf_button.setToolTip(
            f"<strong>{data.label}</strong><hr />{data.annotation}"
        )

        if data.language == "python":
            shelf_button.clicked.connect(partial(exec_py, data.command))
            shelf_button.double_clicked.connect(
                partial(exec_py, data.dc_command)
            )
        else:
            shelf_button.clicked.connect(partial(exec_mel, data.command))
            shelf_button.double_clicked.connect(
                partial(exec_mel, data.dc_command)
            )

        shelf_button.delete.connect(self.delete_button)

        item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(self)
        item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, data)
        item.setSizeHint(shelf_button.size())
        self.setItemWidget(item, shelf_button)

    @QtCore.Slot()
    def delete_button(self) -> None:
        """Removes the button that triggered the delete signal."""
        for i in range(self.count()):
            if self.sender() == self.itemWidget(self.item(i)):
                self.takeItem(i)
                break
        self.data_changed.emit()

    def get_data(self) -> list[dict[str, Any]]:
        """Retrieves all shelf button configurations for saving.

        Returns:
            list[dict[str, Any]]:
                A list of configuration dictionaries converted from DataClasses.
        """
        items: list[Any] = []
        for i in range(self.count()):
            data: ShelfButtonData = self.item(i).data(
                QtCore.Qt.ItemDataRole.UserRole + 1
            )
            items.append(dataclasses.asdict(data))
        return items

    def load_data(self, datas: list[dict[str, Any]]) -> None:
        """Populates the shelf from a list of configuration dictionaries.

        Args:
            datas (list[dict[str, Any]]): The configurations to load.
        """
        self.clear()
        for data in datas:
            self.add_button(ShelfButtonData.from_dict(data))

    @QtCore.Slot(QtCore.QPoint)
    def show_context_menu(self, position: QtCore.QPoint) -> None:
        """Displays a right-click menu to clear the shelf.

        Args:
            position (QtCore.QPoint): The local position to show the menu.
        """
        menu: QtWidgets.QMenu = QtWidgets.QMenu(self)
        action: QtGui.QAction = menu.addAction("Clear All")

        def _clear_all() -> None:
            self.clear()
            self.data_changed.emit()

        action.triggered.connect(_clear_all)
        menu.exec_(self.mapToGlobal(position))


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Shelf Stocker tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Window.
            unique_id (str, optional): A unique identifier for the window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 10)
        self.__shelf: ShelfWidget

    def create_framework_ui(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Overrides the base framework UI creation to inject custom layouts.

        Args:
            layout (QtWidgets.QVBoxLayout): The main layout of the tool window.
        """
        sub_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(sub_layout)

        option_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        sub_layout.addWidget(option_widget, True)

        self.create_ui(option_widget)

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates custom menus for data import/export.

        Args:
            menu_bar (QtWidgets.QMenuBar): The main menu bar widget.
        """
        data_menu: QtWidgets.QMenu = QtWidgets.QMenu("Data", self)
        menu_bar.addMenu(data_menu)

        action: QtGui.QAction = QtGui.QAction("Import JSON...", self)
        action.triggered.connect(self.import_json)
        data_menu.addAction(action)

        action = QtGui.QAction("Export JSON...", self)
        action.triggered.connect(self.export_json)
        data_menu.addAction(action)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget):
                The parent widget to attach the UI elements to.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__shelf = ShelfWidget(self)
        main_layout.addWidget(self.__shelf)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.shelf_data.bind(
            setter=self.__shelf.load_data,
            getter=self.__shelf.get_data,
        )

        self.__shelf.data_changed.connect(self.save_settings)

    @QtCore.Slot()
    def import_json(self) -> None:
        """Imports shelf configuration from a JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_list: Any = json.load(f)

            self.__shelf.load_data(raw_list)
            self.__shelf.data_changed.emit()

        except json.JSONDecodeError as e:
            _logger.error("Invalid JSON format in file %s: %s", file_path, e)

        except OSError as e:
            _logger.error("File access error %s: %s", file_path, e)

    @QtCore.Slot()
    def export_json(self) -> None:
        """Exports the current shelf configuration to a JSON file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            json_data: list[dict[str, Any]] = self.__shelf.get_data()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

        except OSError as e:
            _logger.error("File write error for %s: %s", file_path, e)

        except TypeError as e:
            _logger.error("JSON serialization error : %s", e)


@dcc.undo
def exec_py(command: str) -> None:
    """Executes a Python command as an undoable chunk.

    Args:
        command (str): The Python script to execute.
    """
    exec(command, globals(), {})


@dcc.undo
def exec_mel(command: str) -> None:
    """Executes a MEL command as an undoable chunk.

    Args:
        command (str): The MEL script to execute.
    """
    mel.eval(command)


def main(unique_id: str = "") -> None:
    """Entry point for launching the Shelf Stocker tool.

    Args:
        unique_id (str, optional): A unique identifier for the window.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
