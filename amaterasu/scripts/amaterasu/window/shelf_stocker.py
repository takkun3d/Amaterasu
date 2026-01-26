# ==============================================================================
#
# Shelf Stocker
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
from functools import partial

try:
    from PySide2.QtCore import (
        Qt,
        Signal,
        QTimer,
        QSize,
        QRect,
        QPoint,
        QMimeData,
    )
    from PySide2.QtGui import (
        QPainter,
        QIcon,
        QPixmap,
        QColor,
        QBrush,
        QFont,
        QMouseEvent,
        QDragEnterEvent,
        QDropEvent,
        QDrag,
        QCursor,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QLabel,
        QApplication,
        QMenu,
        QAction,
        QListWidget,
        QFrame,
        QListWidgetItem,
        QVBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            Qt,
            Signal,
            QTimer,
            QSize,
            QRect,
            QPoint,
            QMimeData,
        )
        from PySide6.QtGui import (
            QPainter,
            QIcon,
            QPixmap,
            QColor,
            QBrush,
            QFont,
            QMouseEvent,
            QDragEnterEvent,
            QDropEvent,
            QAction,
            QDrag,
            QCursor,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QLabel,
            QApplication,
            QMenu,
            QListWidget,
            QFrame,
            QListWidgetItem,
            QVBoxLayout,
        )
from maya import cmds, mel
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Shelf Stocker'
__version__: str = '1.00'
__doc__ = 'Stock shelf icon.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

SHELF_MIME_TYPE: str = 'text/plain'
MAYA_MIME_TYPE: str = 'application/x-qabstractitemmodeldatalist'
MIME_TYPE: str = 'application/x-amaterasu-shelf-stocker-data'
SHELF_ARROW: str = 'a_shelf_arrow.png'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    shelf_data: parser.Variant[list[dict[str, Any]]] = parser.Variant([])


class ShelfButton(QLabel):
    '''Shelf button'''

    clicked = Signal()
    double_clicked = Signal()
    delete = Signal()

    def __init__(
        self,
        icon: QIcon,
        label: str = '',
        context_menu_data: list[Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget'''
        super().__init__(parent)

        if not context_menu_data:
            context_menu_data = []

        self.setFixedSize(34, 34)
        self.setContentsMargins(0, 0, 0, 0)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.__timer: QTimer = QTimer()
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__time_out)
        self.__count: int = 0
        self.__icon: QIcon = icon
        self.__label: str = label
        self.__context_menu_data: list[Any] = context_menu_data
        self.set_icon(icon, label)

    def set_icon(self, icon: QIcon, label: str = '') -> None:
        '''Set icon to my widget.'''
        self.__icon = icon
        self.__label = label

        pixmap: QPixmap = icon.pixmap(QSize(32, 32))
        painter: QPainter = QPainter()
        painter.begin(pixmap)

        # Arrow
        if self.__context_menu_data:
            painter.drawPixmap(
                0,
                0,
                widgets.pixmap_from_file_name(SHELF_ARROW),
            )

        if label:
            # Box
            brush: QBrush = QBrush(QColor(0, 0, 0, 150), Qt.SolidPattern)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(0, 17, 32, 15), 2, 2)

            # Text
            painter.setFont(QFont('Arial', 7, QFont.Bold))
            painter.setPen(QColor(204, 204, 204))
            painter.drawText(
                QRect(0, 0, 32, 30), Qt.AlignHCenter | Qt.AlignBottom, label
            )

        painter.end()
        self.setPixmap(pixmap)

    def set_context_menu_data(self, context_menu_data: list[Any]) -> None:
        '''Set context menu data.'''
        self.__context_menu_data = context_menu_data
        self.set_icon(self.__icon, self.__label)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''mousePressEvent[override]'''
        if event.button() == Qt.LeftButton:
            # Start timer when counter is 0.
            if self.__count == 0:
                self.__timer.start(QApplication.doubleClickInterval())

            # Count up when a timer is available.
            else:
                self.__count += 1
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''mouseReleaseEvent[override]'''
        if event.button() == Qt.LeftButton:
            self.__count += 1
            # Decided slow click
            if self.__count == 1 and not self.__timer.isActive():
                self.clicked.emit()
                self.__count = 0

            # Decided double click
            elif self.__count >= 2:
                self.double_clicked.emit()
                self.__count = 0
                self.__timer.stop()
        else:
            super().mouseReleaseEvent(event)

    def show_context_menu(self, position: QPoint) -> None:
        '''Show context menu at specific position.'''
        menu: QMenu = QMenu(self)

        action: QAction = menu.addAction('Delete')
        action.triggered.connect(self.__delete_item)

        menu.addSeparator()

        for menu_item in self.__context_menu_data:
            if menu_item['separator']:
                menu.addSeparator()
                continue

            action = menu.addAction(menu_item['label'])
            if menu_item['language'] == 'python':
                action.triggered.connect(partial(exec_py, menu_item['command']))
            else:
                action.triggered.connect(
                    partial(exec_mel, menu_item['command'])
                )

        menu.exec_(self.mapToGlobal(position))

    def __delete_item(self) -> None:
        '''Emit delete signal.'''
        self.delete.emit()

    def __time_out(self) -> None:
        '''Time out double click interval.'''
        if self.__count == 1:
            self.clicked.emit()
            self.__count = 0


class ShelfWidget(QListWidget):
    '''Shelf list widgets.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget'''
        super().__init__(parent)

        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.Adjust)
        self.setSpacing(2)
        self.setEditTriggers(QListWidget.NoEditTriggers)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumSize(QSize(40, 40))
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet('ShelfWidget{show-decoration-selected: 0;}')
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    # override
    def startDrag(self, supported_actions: Qt.DropActions) -> None:
        '''startDrag[override]'''
        items: list[QListWidgetItem] = self.selectedItems()
        mimeData: QMimeData = self.mimeData(items)
        mimeData.setProperty(MIME_TYPE, items)

        drag: QDrag = QDrag(self)
        drag.setMimeData(mimeData)

        pixmap: QPixmap = QPixmap(
            self.viewport().visibleRegion().boundingRect().size()
        )
        pixmap.fill(Qt.transparent)

        painter: QPainter = QPainter()
        painter.begin(pixmap)
        for item in items:
            rect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supported_actions)

    # override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''mousePressEvent[override]'''
        super().mousePressEvent(event)
        if event.buttons() != Qt.MiddleButton or self.itemAt(event.pos()):
            return

    # override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        '''dragEnterEvent[override]'''
        # Form Shelf
        if event.mimeData().hasFormat(SHELF_MIME_TYPE):
            event.accept()

        # From Internal
        elif event.mimeData().hasFormat(MAYA_MIME_TYPE):
            event.accept()

        else:
            event.ignore()

    # override
    def dropEvent(self, event: QDropEvent) -> None:
        '''dropEvent[override]'''
        # Form Shelf
        if event.mimeData().hasFormat(SHELF_MIME_TYPE):
            command: str = event.mimeData().text()
            current_tab: str = cmds.shelfTabLayout(
                'ShelfLayout', query=True, selectTab=True
            )
            buttons: list[str] = cmds.layout(
                current_tab, query=True, childArray=True
            )
            for button in buttons:
                if 'separator' in button or 'Separator' in button:
                    continue

                command_: str = cmds.shelfButton(
                    button, query=True, command=True
                )
                if command_ != command:
                    continue

                data: dict[str, Any] = {}
                data['label'] = cmds.shelfButton(button, query=True, label=True)
                data['overlayLabel'] = cmds.shelfButton(
                    button, query=True, imageOverlayLabel=True
                )
                data['annotation'] = cmds.shelfButton(
                    button, query=True, annotation=True
                )
                data['command'] = cmds.shelfButton(
                    button, query=True, command=True
                )
                data['dcCommand'] = cmds.shelfButton(
                    button, query=True, doubleClickCommand=True
                )
                data['image'] = cmds.shelfButton(
                    button, query=True, image1=True
                )
                data['language'] = cmds.shelfButton(
                    button, query=True, sourceType=True
                )
                data['subMenu'] = []
                menu_list: list[str] = cmds.shelfButton(
                    button, query=True, popupMenuArray=True
                )
                menu_items: list[str] = cmds.popupMenu(
                    menu_list, query=True, itemArray=True
                )
                if not menu_items:
                    menu_items = []

                for menu_item in menu_items:
                    label: str = cmds.menuItem(
                        menu_item, query=True, label=True
                    )
                    command: str = cmds.menuItem(
                        menu_item, query=True, command=True
                    )
                    language: str = cmds.menuItem(
                        menu_item, query=True, sourceType=True
                    )
                    separator: bool = cmds.menuItem(
                        menu_item, query=True, divider=True
                    )
                    if command and '/*dSBRMBMI*/' in command:
                        continue

                    sub_menu_data = {
                        'label': label,
                        'command': command,
                        'language': language,
                        'separator': separator,
                    }
                    data['subMenu'].append(sub_menu_data)
            self.add_button(data)

        # From Internal
        elif event.mimeData().hasFormat(MAYA_MIME_TYPE):
            super().dropEvent(event)

    def add_button(self, data: dict[str, Any]) -> None:
        '''Add button'''
        shelf_button: ShelfButton = ShelfButton(
            widgets.icon_from_file_name(data['image']),
            data['overlayLabel'],
            data['subMenu'],
            self,
        )
        shelf_button.setToolTip(
            f"<strong>{data['label']}</strong><hr />{data['annotation']}"
        )
        if data['language'] == 'python':
            shelf_button.clicked.connect(partial(exec_py, data['command']))
            shelf_button.double_clicked.connect(
                partial(exec_py, data['dcCommand'])
            )
        else:
            shelf_button.clicked.connect(partial(exec_mel, data['command']))
            shelf_button.double_clicked.connect(
                partial(exec_mel, data['dcCommand'])
            )
        shelf_button.delete.connect(self.delete_button)

        item: QListWidgetItem = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, data)
        item.setSizeHint(shelf_button.size())
        self.setItemWidget(item, shelf_button)

    def delete_button(self) -> None:
        '''Delete button in list.'''
        for i in range(self.count()):
            if self.sender() == self.itemWidget(self.item(i)):
                self.takeItem(i)

        self.save_settings()

    def load_settings(self) -> None:
        '''Load settings'''
        self.clear()
        settings: Settings = Settings.instance(__name__, True)
        for data in settings.shelf_data.value():
            self.add_button(data)

    def save_settings(self) -> None:
        '''Save settings'''
        data: list[Any] = []
        for i in range(self.count()):
            data.append(self.item(i).data(Qt.UserRole + 1))

        settings: Settings = Settings.instance(__name__, True)
        settings.shelf_data.set_value(data)
        settings.write()

    def reset_settings(self) -> None:
        '''Reset settings'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    def show_context_menu(self, position: QPoint) -> None:
        '''Show context menu to specific position.'''
        menu: QMenu = QMenu(self)
        action = menu.addAction('Clear')
        action.triggered.connect(self.reset_settings)
        menu.exec_(self.mapToGlobal(position))


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
        self.resize(400, 60)

        self.option_layout().setContentsMargins(0, 0, 0, 0)

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__shelf: ShelfWidget = ShelfWidget()
        main_layout.addWidget(self.__shelf)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__shelf.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        self.__shelf.save_settings()
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.__shelf.reset_settings()
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
@widgets.undo
def exec_py(command: str) -> None:
    '''Execute python.'''
    exec(command, globals(), {})


@widgets.undo
def exec_mel(command: str) -> None:
    '''Execute mel.'''
    mel.eval(command)


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
