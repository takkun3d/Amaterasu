# ==============================================================================
#
# widgets
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
from abc import ABC, ABCMeta, abstractmethod
import os
import random
import shutil
import functools

try:
    from shiboken2 import wrapInstance
    from PySide2.QtCore import (
        Qt,
        Signal,
        Slot,
        QByteArray,
        QSize,
        QEvent,
        QRect,
        QPoint,
        QDir,
        QFileInfo,
        QModelIndex,
        QSortFilterProxyModel,
        QUrl,
    )
    from PySide2.QtGui import (
        QIcon,
        QCloseEvent,
        QPixmap,
        QMouseEvent,
        QEnterEvent,
        QResizeEvent,
        QPaintEvent,
        QDragEnterEvent,
        QDropEvent,
        QColor,
        QBrush,
        QPen,
        QPolygon,
        QPainter,
        QStandardItemModel,
        QStandardItem,
    )
    from PySide2.QtWidgets import (
        QMainWindow,
        QWidget,
        QScrollArea,
        QPushButton,
        QFrame,
        QDialog,
        QLabel,
        QTextEdit,
        QDoubleSpinBox,
        QRadioButton,
        QButtonGroup,
        QTabBar,
        QTabWidget,
        QStackedWidget,
        QTreeView,
        QListView,
        QSlider,
        QSplitter,
        QFileIconProvider,
        QHBoxLayout,
        QVBoxLayout,
        QGridLayout,
        QFormLayout,
        QLayout,
        QLayoutItem,
        QInputDialog,
        QLineEdit,
        QGroupBox,
        QMenuBar,
        QMenu,
        QAction,
        QColorDialog,
        QFileSystemModel,
        QMessageBox,
        QSizePolicy,
    )
    from PySide2.QtWebEngineWidgets import QWebEngineView

except ImportError:
    if not TYPE_CHECKING:
        from shiboken6 import wrapInstance
        from PySide6.QtCore import (
            Qt,
            Signal,
            Slot,
            QByteArray,
            QSize,
            QEvent,
            QRect,
            QPoint,
            QDir,
            QFileInfo,
            QModelIndex,
            QSortFilterProxyModel,
            QUrl,
        )
        from PySide6.QtGui import (
            QIcon,
            QCloseEvent,
            QPixmap,
            QMouseEvent,
            QEnterEvent,
            QResizeEvent,
            QPaintEvent,
            QDragEnterEvent,
            QDropEvent,
            QColor,
            QBrush,
            QPen,
            QPolygon,
            QPainter,
            QAction,
            QStandardItemModel,
            QStandardItem,
        )
        from PySide6.QtWidgets import (
            QMainWindow,
            QWidget,
            QScrollArea,
            QPushButton,
            QFrame,
            QDialog,
            QLabel,
            QTextEdit,
            QDoubleSpinBox,
            QRadioButton,
            QButtonGroup,
            QTabBar,
            QTabWidget,
            QStackedWidget,
            QTreeView,
            QListView,
            QSlider,
            QSplitter,
            QFileIconProvider,
            QHBoxLayout,
            QVBoxLayout,
            QGridLayout,
            QFormLayout,
            QLayout,
            QLayoutItem,
            QInputDialog,
            QLineEdit,
            QGroupBox,
            QMenuBar,
            QMenu,
            QColorDialog,
            QFileSystemModel,
            QMessageBox,
            QSizePolicy,
        )
        from PySide6.QtWebEngineWidgets import QWebEngineView

from maya import OpenMaya, OpenMayaUI, cmds, mel
from . import utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__doc__ = 'Custom widget library with PySide.'
BAD_FILE_NAME: str = r'[\\|/|:|?|.|"|<|>|\||\r|\n|\t|\v|\s]'
LOGO: str = 'a_logo.png'
HEADER: str = 'a_about_header.png'
TAB_ADD: str = 'a_add.png'
TAB_ADD_HOVER: str = 'a_add_hover.png'
TAB_ADD_PRESSED: str = 'a_add_pressed.png'
TAB_CLOSE: str = 'a_close.png'
TAB_CLOSE_HOVER: str = 'a_close_hover.png'
TAB_CLOSE_PRESSED: str = 'a_close_pressed.png'
TAB_ICON_SIZE: list[int] = [24, 24]

COLOR_BUTTON_QSS: str = '''
QPushButton#%s{
	border:none;
	background-color:rgb(%s, %s, %s);
}
QPushButton#%s:disabled{
	background-color:rgba(%s, %s, %s, 0.4);
}
'''


# ==============================================================================
#
# Meta Classes
#
# ==============================================================================
class QWidgetMeta(type(QWidget)):  # type: ignore
    '''
    QWidget metaclass.
    Reference:
    https://stackoverflow.com/questions/66591752/metaclass-conflict-when-trying-to-create-a-python-abstract-class-that-also-subcl
    '''


class QWidgetABCMeta(QWidgetMeta, ABCMeta):
    '''
    QWidget metaclass.
    Reference:
    https://stackoverflow.com/questions/66591752/metaclass-conflict-when-trying-to-create-a-python-abstract-class-that-also-subcl
    '''


# ==============================================================================
#
# Classes
#
# ==============================================================================
class HorizontalLine(QFrame):
    '''Horizontal list widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VerticalLine(QFrame):
    '''Vertical line widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class ThreeDoubleSpinBox(QWidget):
    '''3 set double spin box widget.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__x = QDoubleSpinBox(self)
        self.__x.setDecimals(5)
        self.__x.setRange(-99999, 99999)
        self.__x.setMinimumWidth(80)
        self.__x.setButtonSymbols(QDoubleSpinBox.NoButtons)
        layout.addWidget(self.__x)

        self.__y = QDoubleSpinBox(self)
        self.__y.setDecimals(5)
        self.__y.setRange(-99999, 99999)
        self.__y.setMinimumWidth(80)
        self.__y.setButtonSymbols(QDoubleSpinBox.NoButtons)
        layout.addWidget(self.__y)

        self.__z = QDoubleSpinBox(self)
        self.__z.setDecimals(5)
        self.__z.setRange(-99999, 99999)
        self.__z.setMinimumWidth(80)
        self.__z.setButtonSymbols(QDoubleSpinBox.NoButtons)
        layout.addWidget(self.__z)

    def value(self) -> list[float]:
        '''Return Value'''
        return [self.__x.value(), self.__y.value(), self.__z.value()]

    def set_value(self, x: float, y: float, z: float) -> None:
        '''Set 3 float values to widget.'''
        self.__x.setValue(x)
        self.__y.setValue(y)
        self.__z.setValue(z)

    def set_decimals(self, decimals: int) -> None:
        '''Set decimals'''
        self.__x.setDecimals(decimals)
        self.__y.setDecimals(decimals)
        self.__z.setDecimals(decimals)

    def set_range(self, min_value: float, max_value: float) -> None:
        '''Set range.'''
        self.__x.setRange(min_value, max_value)
        self.__y.setRange(min_value, max_value)
        self.__z.setRange(min_value, max_value)


class NodePicker(QWidget):
    '''Node Name Getter'''

    def __init__(
        self, limit_count: int = -1, parent: QWidget | None = None
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)

        self.__selection: list[str] = []
        self.__limit_count: int = limit_count

        main_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__line_edit: QLineEdit = QLineEdit(self)
        main_layout.addWidget(self.__line_edit)

        button: IconButton = IconButton(self)
        button.set_icon('a_import.png')
        button.clicked.connect(self.pick)
        main_layout.addWidget(button)

    def pick(self) -> None:
        '''Get selection.'''
        self.set_text_from_list(cmds.ls(selection=True))

    def text(self) -> str:
        '''Return selection data as a string.'''
        return self.__line_edit.text()

    def set_text(self, text: str) -> None:
        '''Set text to QLineEdit'''
        self.set_text_from_list(text.split(','))

    def placeholder_text(self) -> str:
        '''Return placeholder text from QLineEdit.'''
        return self.__line_edit.placeholderText()

    def set_placeholder_text(self, text: str) -> None:
        '''Set placeholder text to QLineEdit.'''
        self.__line_edit.setPlaceholderText(text)

    def set_text_from_list(self, selection: list[str]) -> None:
        '''Set text to QLineEdit from list of strings.'''
        if not selection:
            self.__selection = selection
            self.__line_edit.setText('')
            return

        if self.__limit_count == -1:
            self.__selection = selection
            self.__line_edit.setText(','.join(self.__selection))

        else:
            self.__selection = selection[: self.__limit_count]
            self.__line_edit.setText(','.join(self.__selection))

    def text_as_list(self) -> list[str]:
        '''Return the selection as a list of strings.'''
        return self.__selection


class RadioButtons(QWidget):
    '''Radio button group.'''

    def __init__(
        self, parent: QWidget | None = None, labels: list[str] | None = None
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        if labels is None:
            labels = []

        self.__main_layout: QHBoxLayout = QHBoxLayout(self)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)

        self.__button_group: QButtonGroup = QButtonGroup(self)
        for i, label in enumerate(labels):
            button: QRadioButton = QRadioButton(label, self)
            self.__button_group.addButton(button, i)
            self.__main_layout.addWidget(button, True)

    def clear(self) -> None:
        '''Delete all radio buttons.'''
        buttons = self.__button_group.buttons()
        for button in buttons:
            self.__button_group.removeButton(button)
            button.deleteLater()

    def set_labels(self, labels: tuple[str, ...]) -> None:
        '''Create radio buttons from a list of label.'''
        self.clear()
        for i, label in enumerate(labels):
            button: QRadioButton = QRadioButton(label, self)
            self.__button_group.addButton(button, i)
            self.__main_layout.addWidget(button, True)

    def button_group(self) -> QButtonGroup:
        '''Return QButtonGroup,'''
        return self.__button_group

    def check_id(self) -> int:
        '''Return id from checked button.'''
        return self.__button_group.checkedId()

    def set_check_id(self, button_id: int) -> None:
        '''Set checked from button id.'''
        self.__button_group.button(button_id).setChecked(True)


class FrameWidget(QGroupBox):
    '''Maya like frame widget.'''

    def __init__(
        self,
        title: str = '',
        collapsed: bool = False,
        collapsible: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setFlat(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 7, 0, 0)
        layout.setSpacing(0)
        super().setLayout(layout)

        self.__widget = QFrame(parent)
        self.__widget.setFrameShape(QFrame.Panel)
        self.__widget.setFrameShadow(QFrame.Plain)
        self.__widget.setLineWidth(0)
        layout.addWidget(self.__widget)

        self.__collapsed = collapsed
        self.__collapsible = collapsible
        self.__clicked = False

        self.setTitle(title)

    def layout(self) -> QLayout:
        '''Return Layout'''
        return self.__widget.layout()

    def setLayout(self, layout: QLayout) -> None:
        '''Set layout.[override]'''
        self.__widget.setLayout(layout)

    def setFrameShape(self, shape: QFrame.Shape) -> None:
        '''Set frame shape.[override]'''
        self.__widget.setFrameShape(shape)

    def setFrameShadow(self, shadow: QFrame.Shadow) -> None:
        '''Set frame shadow.[override]'''
        self.__widget.setFrameShadow(shadow)

    def setLineWidth(self, width: int) -> None:
        '''Set line width.[override]'''
        self.__widget.setLineWidth(width)

    def expandCollapseRect(self) -> QRect:
        '''Expand collapse rect.[override]'''
        return QRect(0, 0, self.width(), 20)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''Mouse Relase Event.[override]'''
        if self.__clicked and self.expandCollapseRect().contains(event.pos()):
            self.toggle_collapsed()
            event.accept()
        else:
            event.ignore()

        self.__clicked = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''Mouse press Event.[override]'''
        if (
            event.button() == Qt.LeftButton
            and self.expandCollapseRect().contains(event.pos())
        ):
            self.__clicked = True
            event.accept()

        else:
            self.__clicked = False
            event.ignore()

    def is_collapsed(self) -> bool:
        '''Return is collapsed.'''
        return self.__collapsed

    def is_collapsible(self) -> bool:
        '''Return is collapsible.'''
        return self.__collapsible

    def __drawTriangle(self, painter: QPainter, x: int, y: int) -> None:
        '''Draw triangle.'''
        color = QColor(255, 255, 255, 160)

        if not self.is_collapsed():
            points = [
                QPoint(x + 10, y + 6),
                QPoint(x + 20, y + 6),
                QPoint(x + 15, y + 11),
            ]

        else:
            points = [
                QPoint(x + 10, y + 4),
                QPoint(x + 15, y + 9),
                QPoint(x + 10, y + 14),
            ]

        current_brush = painter.brush()
        current_pen = painter.pen()

        painter.setBrush(QBrush(color, Qt.SolidPattern))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawPolygon(QPolygon(points))
        painter.setBrush(current_brush)
        painter.setPen(current_pen)

    def paintEvent(self, event: QPaintEvent) -> None:
        '''Paint Event.[override]'''
        painter = QPainter()
        painter.begin(self)

        font = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x = self.rect().x()
        y = self.rect().y()
        w = self.rect().width() - 1

        offset = 10
        if self.__collapsible:
            offset = 25

        header_height: int = 20
        header_rect: QRect = QRect(x, y, w, header_height)

        # Base
        painter.fillRect(header_rect, QColor(93, 93, 93))

        painter.drawText(
            x + offset,
            y + 3,
            w,
            16,
            (Qt.AlignLeft | Qt.AlignTop),
            self.title(),
        )

        if self.__collapsible:
            self.__drawTriangle(painter, x, y)

        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.end()

    def set_collapsed(self, state: bool = True) -> None:
        '''Set collapsed.'''
        if self.is_collapsible():
            self.setUpdatesEnabled(False)

            self.__collapsed = state

            if state:
                self.setMinimumHeight(20)
                self.setMaximumHeight(20)
                self.widget().setVisible(False)
            else:
                self.setMinimumHeight(0)
                self.setMaximumHeight(1000000)
                self.widget().setVisible(True)

            self.setUpdatesEnabled(True)

    def set_collapsible(self, state: bool = True) -> None:
        '''Set collapsible.'''
        self.__collapsible = state

    def toggle_collapsed(self) -> None:
        '''Toggle collapsed.'''
        self.set_collapsed(not self.is_collapsed())

    def widget(self) -> QWidget:
        '''Return widget.'''
        return self.__widget


class FormLabel(QLabel):
    '''Label like maya for QFormLaout.'''

    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initilize widget.'''
        if text:
            text = f'{text} : '

        super().__init__(text, parent, flag)
        self.setMinimumWidth(70)
        self.setAlignment(Qt.AlignRight)


class FormLayout(QFormLayout):
    '''Custom form layout.'''

    def set_row_enabled(self, row: int, enabled: bool) -> None:
        '''Set widget enabled from specificed row.'''
        for role in (QFormLayout.LabelRole, QFormLayout.FieldRole):
            layout_item: QLayoutItem | None = self.itemAt(row, role)
            if not layout_item:
                continue

            layout = layout_item.layout()
            if layout:
                layout.setEnabled(enabled)
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if not widget:
                        continue
                    widget.setEnabled(enabled)

            widget = layout_item.widget()
            if widget:
                widget.setEnabled(enabled)

    def set_row_visible(self, row: int, visible: bool) -> None:
        '''Set widget visible from specificed row.'''
        for role in (QFormLayout.LabelRole, QFormLayout.FieldRole):
            layout_item: QLayoutItem | None = self.itemAt(row, role)
            if not layout_item:
                continue

            layout = layout_item.layout()
            if layout:
                # layout.setEnabled(enabled)
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if not widget:
                        continue
                    widget.setVisible(visible)

            widget = layout_item.widget()
            if widget:
                widget.setVisible(visible)

    def row_id(self) -> int:
        '''Return row id.'''
        return self.rowCount() - 1


class IconButton(QPushButton):
    '''Image based button.'''

    right_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize'''
        super().__init__(parent)
        self.setFlat(True)
        self.setStyleSheet('QPushButton:pressed{padding:0;}')
        self.__default_icon: QIcon | None = None
        self.__hover_icon: QIcon | None = None
        self.__pressed_icon: QIcon | None = None

    # override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''mousePressEvent[override]'''
        super().mousePressEvent(event)
        if self.__pressed_icon:
            self.setIcon(self.__pressed_icon)

    # override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''mouseReleaseEvent[override]'''
        super().mouseReleaseEvent(event)
        if self.__default_icon:
            self.setIcon(self.__default_icon)

        if event.button() == Qt.RightButton:
            self.right_clicked.emit()

    # override
    def enterEvent(self, event: QEvent | QEnterEvent) -> None:
        '''enverEvent[override]'''
        super().enterEvent(event)
        if self.__hover_icon:
            self.setIcon(self.__hover_icon)

    # override
    def leaveEvent(self, event: QEvent) -> None:
        '''leaveEvent[override]'''
        super().leaveEvent(event)
        if self.__default_icon:
            self.setIcon(self.__default_icon)

    # override
    def setIconSize(self, size: QSize) -> None:
        '''setIconSize[override]'''
        super().setIconSize(size)
        super().setFixedSize(size)

    def set_icon(self, icon: str) -> None:
        '''Set default icon.'''
        self.__default_icon = icon_from_file_name(icon)
        super().setIcon(self.__default_icon)

    def set_hover_icon(self, icon: str) -> None:
        '''Set hover icon.'''
        self.__hover_icon = icon_from_file_name(icon)

    def set_pressed_icon(self, icon: str) -> None:
        '''Set pressed icon.'''
        self.__pressed_icon = icon_from_file_name(icon)
        self.setStyleSheet('QPushButton:pressed{border:none; padding:0;}')


class ColorButton(QPushButton):
    '''Color based button.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initilize Widget'''
        super().__init__(parent)
        self.__color: list[float] = [0.0, 0.275, 0.098]

        index = random.randrange(0, 999999)
        self.setObjectName(f"ColorButton{index}")
        self.set_color(*self.__color)

    def set_color(self, r: float, g: float, b: float) -> None:
        '''Set background color.'''
        self.__color = [r, g, b]
        self.setStyleSheet(
            COLOR_BUTTON_QSS
            % (
                self.objectName(),
                r * 255,
                g * 255,
                b * 255,
                self.objectName(),
                r * 255,
                g * 255,
                b * 255,
            )
        )

    def color(self) -> list[float]:
        '''Return color.'''
        return self.__color


class ColorSelectButton(ColorButton):
    '''Choose select button'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initilize Widget'''
        super().__init__(parent)
        self.clicked.connect(self.show_dialog)

    def show_dialog(self) -> None:
        '''Show color dialog'''
        c: list[float] = self.color()
        color: QColor = QColorDialog.getColor(
            QColor(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)),
            self,
            'Select Color',
            QColorDialog.DontUseNativeDialog,
        )
        if color.isValid():
            self.set_color(color.redF(), color.greenF(), color.blueF())


class ColorPalette(QWidget):
    '''Color palette widget.'''

    clicked = Signal(list)
    default_colors: list[list[float]] = [
        [0.99, 0.36, 0.38],  # 01. Red
        [1.00, 0.29, 0.57],  # 02. Rose
        [0.90, 0.30, 0.90],  # 03. Magenta
        [0.56, 0.33, 0.97],  # 04. Purple
        [0.34, 0.42, 0.98],  # 05. Blue-Purple
        [0.27, 0.57, 0.99],  # 06. Blue
        [0.26, 0.76, 0.99],  # 07. Sky Blue
        [0.20, 0.94, 0.98],  # 08. Cyan
        [0.25, 0.98, 0.78],  # 09. Aquamarine
        [0.36, 0.98, 0.58],  # 10. Mint
        [0.52, 0.98, 0.38],  # 11. Light Green
        [0.75, 0.99, 0.27],  # 12. Lime
        [0.96, 1.00, 0.25],  # 13. Yellow
        [1.00, 0.83, 0.27],  # 14. Golden Yellow
        [1.00, 0.63, 0.34],  # 15. Orange
        [1.00, 0.43, 0.36],  # 16. Red-Orange
    ]

    def __init__(
        self,
        colors: list[list[float]] | None = None,
        max_columns: int = 8,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget'''
        super().__init__(parent)
        if colors is None:
            colors = self.default_colors

        self.__layout: QGridLayout = QGridLayout(self)
        self.__layout.setSpacing(2)
        self.__layout.setContentsMargins(0, 0, 0, 0)

        self.__buttons: list[ColorButton] = []
        self.__max_columns: int = max_columns
        self.__create_color_buttons(colors)

    def __create_color_buttons(self, colors: list[list[float]]) -> None:
        '''Create color buttons.'''
        for i, rgb in enumerate(colors):
            button: ColorButton = ColorButton(self)
            button.set_color(*rgb)
            button.clicked.connect(self.__on_color_selected)

            row: int = i // self.__max_columns
            colmum: int = i % self.__max_columns
            self.__layout.addWidget(button, row, colmum)
            self.__buttons.append(button)

    def __on_color_selected(self) -> None:
        '''Callback color button.'''
        button: ColorButton = self.sender()
        self.clicked.emit(button.color())

    def set_color(self, index: int, color: list[float]) -> None:
        '''Set color'''
        self.__buttons[index].set_color(*color)

    def set_colors(self, colors: list[list[float]]) -> None:
        '''Set colors'''
        for button in self.__buttons:
            button.deleteLater()
        self.__buttons = []
        self.__create_color_buttons(colors)

    def colors(self) -> list[list[float]]:
        '''Return colors of palette.'''
        return [x.color() for x in self.__buttons]


class DropImage(QLabel):
    '''Display the dropped image.'''

    def __init__(
        self, parent: QWidget | None = None, width: int = 128, height: int = 128
    ) -> None:
        '''Initialize widget'''
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)
        self.setAcceptDrops(True)
        self.__file_path: str = ''

        pixmap: QPixmap = QPixmap(pixmap_from_file_name('a_download.png'))
        pixmap = pixmap.scaled(self.width(), self.height())
        self.setPixmap(pixmap)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        '''drag enter event[override]'''
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        '''drop event[override]'''
        urls = event.mimeData().urls()
        for url in urls:
            file_path: str = url.toLocalFile()
            pixmap: QPixmap = QPixmap(file_path)
            if pixmap.isNull():
                continue

            pixmap = pixmap.scaled(self.width(), self.height())
            self.setPixmap(pixmap)
            self.__file_path = file_path

    def file_path(self) -> str:
        '''Return file path.'''
        return self.__file_path


class TabBarPlus(QTabBar):
    '''Tab add button'''

    plus_clicked = Signal()
    double_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize'''
        super().__init__(parent)

        self.__plus: IconButton = IconButton(self)
        self.__plus.set_icon(TAB_ADD)
        self.__plus.set_hover_icon(TAB_ADD_HOVER)
        self.__plus.set_pressed_icon(TAB_ADD_PRESSED)
        self.__plus.setIconSize(QSize(*TAB_ICON_SIZE))
        self.__plus.clicked.connect(self.plus_callback)

        self.setStyleSheet(
            '''
            QTabBar::close-button{image: url(%s);}
            QTabBar::close-button:hover{image: url(%s);}
            QTabBar::close-button:pressed{image: url(%s);}
            '''
            % (
                image_file_path(TAB_CLOSE),
                image_file_path(TAB_CLOSE_HOVER),
                image_file_path(TAB_CLOSE_PRESSED),
            )
        )
        self.move_plus_button()

    # override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''mousePressEvent[override]'''
        if event.type() == QEvent.MouseButtonDblClick:
            if self.tabRect(self.currentIndex()).contains(event.pos()):
                self.double_clicked.emit()
        else:
            super().mousePressEvent(event)

    # override
    def sizeHint(self) -> QSize:
        '''sizeHint[override]'''
        size_hint: QSize = super().sizeHint()
        width: int = size_hint.width() + 25
        height: int = TAB_ICON_SIZE[1]
        return QSize(width, height)

    # override
    def resizeEvent(self, event: QResizeEvent) -> None:
        '''resizeEvent[override]'''
        super().resizeEvent(event)
        self.move_plus_button()

    # override
    def tabLayoutChange(self) -> None:
        '''tabLayoutChange[override]'''
        super().tabLayoutChange()
        self.move_plus_button()

    @Slot()
    def plus_callback(self) -> None:
        '''Plus button clicked callback.'''
        self.plus_clicked.emit()

    def move_plus_button(self) -> None:
        '''Move plus button to right.'''
        size: int = 0
        for i in range(self.count()):
            size += self.tabRect(i).width()

        w: int = self.width()
        h: int = self.geometry().top()
        if size > w:
            self.__plus.move(w - 54, h)
        else:
            self.__plus.move(size, h)


class TabWidget(QTabWidget):
    '''Tab with add/remove button.'''

    default_tab_name: str = 'No Name'
    title: str = 'Information'

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize'''
        super().__init__(parent)
        tab_bar: TabBarPlus = TabBarPlus(self)
        tab_bar.plus_clicked.connect(self.add_tab_callback)
        tab_bar.double_clicked.connect(self.rename_tab_callback)
        self.setTabBar(tab_bar)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.remove_tab)

    @Slot()
    def add_tab_callback(self) -> None:
        '''Add tab callback.'''
        text, ok = QInputDialog.getText(
            self,
            self.title,
            'New Tab Name',
            QLineEdit.Normal,
            self.default_tab_name,
        )
        if ok:
            self.add_tab(text)

    @Slot()
    def rename_tab_callback(self) -> None:
        '''Rename tab callback.'''
        text, ok = QInputDialog.getText(
            self,
            self.title,
            'Rename Tab Name',
            QLineEdit.Normal,
            self.tabText(self.currentIndex()),
        )
        if ok:
            self.setTabText(self.currentIndex(), text)

    @Slot(int)
    def remove_tab(self, index: int) -> None:
        '''Remove tab callback.'''
        if self.count() >= 2:
            self.removeTab(index)

    def add_tab(self, label: str) -> None:
        '''Add tab.'''
        self.addTab(QWidget(self), label)
        self.setCurrentIndex(self.count() - 1)


class IconProvider(QFileIconProvider):
    '''Icon Provider'''

    def icon(self, file_info: QFileInfo) -> QIcon:  # type:ignore
        '''Return QIcon.'''
        file_path: str = file_info.filePath()
        if file_path.endswith(('.jpg', '.png')):
            pixmap: QPixmap = QPixmap()
            pixmap.load(file_path)
            return QIcon(pixmap)  # QIcon(pixmap.scaled(QSize(*ICON_SIZE)))

        else:
            return super().icon(file_info)


class FileBrowserItem(QStandardItem):
    '''Item of File Browser.'''

    thumbnail_filename: str = 'thumbnail.jpg'
    no_image: str = 'a_no_image.png'

    def __init__(self, data_path: str):
        super().__init__()
        self.__data_path: str = ''
        self.__name: str = ''
        self.__icon_path: str = ''
        self.__extension: str = ''
        if data_path != '':
            self.set_data_path(data_path)

    def data_path(self) -> str:
        '''return data path'''
        return self.__data_path

    def set_data_path(self, path: str) -> None:
        '''set data path'''
        base_name: str = os.path.basename(path)
        base_name, extension = os.path.splitext(base_name)
        extension = extension[1:]

        self.__data_path = path
        self.__name = base_name
        self.__extension = extension
        self.__icon_path = os.path.join(
            self.__data_path, self.thumbnail_filename
        )
        self.setText(f'[{self.__extension}] {self.__name}')
        if os.path.exists(self.__icon_path):
            self.setIcon(QIcon(self.__icon_path))
        else:
            self.setIcon(icon_from_file_name(self.no_image))

    def icon_path(self) -> str:
        '''return icon path'''
        return self.__icon_path

    def name(self) -> str:
        '''return name'''
        return self.__name

    def extension(self) -> str:
        '''return extension'''
        return self.__extension


class FileBrowser(QWidget):
    '''Outline style file browser.'''

    item_selected = Signal(FileBrowserItem)
    folder_tree_filter: str = r'^([^.]+)$'

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.__filter_text: str = ''
        self.__current_path: str = ''
        self.__current_item: FileBrowserItem | None = None
        self.__action_list: list[Any] = []

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__root_dir: QLineEdit = QLineEdit(self)
        self.__root_dir.textChanged.connect(self.change_home_directory)
        main_layout.addWidget(self.__root_dir)

        # Outline View
        outline_widget: QWidget = QWidget(self)
        outline_layout: QVBoxLayout = QVBoxLayout(outline_widget)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        outline_layout.setSpacing(2)

        outline_header_layout: QHBoxLayout = QHBoxLayout(outline_widget)
        outline_header_layout.setContentsMargins(0, 0, 0, 0)
        outline_header_layout.setSpacing(2)
        outline_header_layout.addStretch(True)
        outline_layout.addLayout(outline_header_layout)

        button = IconButton(self)
        button.set_icon(icon_from_file_name('a_create_folder.png'))
        button.clicked.connect(self.new_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(icon_from_file_name('a_rename.png'))
        button.clicked.connect(self.rename_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(icon_from_file_name('a_trash.png'))
        button.clicked.connect(self.remove_folder)
        button.setMaximumSize(24, 24)
        outline_header_layout.addWidget(button)

        self.__outline_model: QFileSystemModel = QFileSystemModel(self)
        self.__outline_model.setFilter(QDir.NoDotAndDotDot | QDir.Dirs)

        self.__outline_proxy_model = QSortFilterProxyModel()
        self.__outline_proxy_model.setSourceModel(self.__outline_model)
        try:  # PySide2
            self.__outline_proxy_model.setFilterRegExp(self.folder_tree_filter)
        except AttributeError:  # PySide6
            self.__outline_proxy_model.setFilterRegularExpression(
                self.folder_tree_filter
            )

        self.__outline_viewer: QTreeView = QTreeView(self)
        self.__outline_viewer.setHeaderHidden(True)
        self.__outline_viewer.setModel(self.__outline_proxy_model)
        self.__outline_viewer.setFocusPolicy(Qt.NoFocus)
        self.__outline_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__outline_viewer.customContextMenuRequested.connect(
            self.outline_context_menu
        )

        for i in range(1, self.__outline_viewer.header().count()):
            self.__outline_viewer.header().hideSection(i)

        self.__outline_viewer.selectionModel().currentChanged.connect(
            self.change_directory_callback
        )
        self.__outline_viewer.clicked.connect(self.click_outline_callback)
        outline_layout.addWidget(self.__outline_viewer)

        outline_footer_layout: QHBoxLayout = QHBoxLayout(outline_widget)
        outline_footer_layout.setContentsMargins(0, 0, 0, 0)
        outline_footer_layout.setSpacing(2)
        outline_layout.addLayout(outline_footer_layout)

        # File View
        file_viwer_widget: QWidget = QWidget(self)
        file_viewer_layout: QVBoxLayout = QVBoxLayout(file_viwer_widget)
        file_viewer_layout.setContentsMargins(0, 0, 0, 0)
        file_viewer_layout.setSpacing(2)

        self.__file_viewer_header_layout: QHBoxLayout = QHBoxLayout(
            file_viwer_widget
        )
        self.__file_viewer_header_layout.setContentsMargins(0, 0, 0, 0)
        self.__file_viewer_header_layout.setSpacing(2)
        self.__file_viewer_header_layout.addStretch(True)
        file_viewer_layout.addLayout(self.__file_viewer_header_layout)

        button = IconButton(self)
        button.set_icon(icon_from_file_name('a_rename.png'))
        button.clicked.connect(self.rename_item)
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.addWidget(button)

        button = IconButton(self)
        button.set_icon(icon_from_file_name('a_trash.png'))
        button.clicked.connect(self.remove_item)
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.addWidget(button)

        self.__file_model: QStandardItemModel = QStandardItemModel()
        self.__file_proxy_model = QSortFilterProxyModel()
        self.__file_proxy_model.setSourceModel(self.__file_model)

        self.__file_viewer: QListView = QListView(self)
        self.__file_viewer.setViewMode(QListView.IconMode)
        self.__file_viewer.setResizeMode(QListView.Adjust)
        self.__file_viewer.setModel(self.__file_proxy_model)
        self.__file_viewer.setDragEnabled(False)
        self.__file_viewer.setFocusPolicy(Qt.NoFocus)
        self.__file_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__file_viewer.customContextMenuRequested.connect(
            self.file_viewer_context_menu
        )
        self.__file_viewer.selectionModel().currentChanged.connect(
            self.change_item_callback
        )
        self.__file_viewer.clicked.connect(self.click_view_callback)
        file_viewer_layout.addWidget(self.__file_viewer, True)

        file_viewer_footer_layout: QHBoxLayout = QHBoxLayout(file_viwer_widget)
        file_viewer_footer_layout.setContentsMargins(0, 0, 0, 0)
        file_viewer_footer_layout.setSpacing(2)
        file_viewer_layout.addLayout(file_viewer_footer_layout)

        self.__file_viewer_filter: QLineEdit = QLineEdit(self)
        self.__file_viewer_filter.textChanged.connect(self.set_filter)
        file_viewer_footer_layout.addWidget(self.__file_viewer_filter)

        self.__file_viewer_icon_size: QSlider = QSlider(Qt.Horizontal, self)
        self.__file_viewer_icon_size.setRange(0, 100)
        self.__file_viewer_icon_size.setValue(50)
        self.__file_viewer_icon_size.setMaximumWidth(100)
        self.__file_viewer_icon_size.sliderMoved.connect(self.set_icon_size)
        file_viewer_footer_layout.addWidget(self.__file_viewer_icon_size)

        # Option
        # self.__option_widget: QWidget = QWidget(self)

        # Splitter
        self.__splitter: QSplitter = QSplitter(self)
        self.__splitter.setOrientation(Qt.Horizontal)
        self.__splitter.addWidget(outline_widget)
        self.__splitter.addWidget(file_viwer_widget)
        # self.__splitter.addWidget(self.__option_widget)
        self.__splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.__splitter)

    def outline_context_menu(self, position: QPoint) -> None:
        '''Show context menu on outline.'''
        menu: QMenu = QMenu(self)

        action: QAction = menu.addAction(
            icon_from_file_name('a_create_folder.png'),
            'New Folder',
        )
        action.triggered.connect(self.new_folder)

        action = menu.addAction(
            icon_from_file_name('a_rename.png'),
            'Rename Folder',
        )
        action.triggered.connect(self.rename_folder)

        action = menu.addAction(
            icon_from_file_name('a_trash.png'),
            'Delete Folder',
        )
        action.triggered.connect(self.remove_folder)

        menu.exec_(self.mapToGlobal(position))

    def file_viewer_context_menu(self, position: QPoint) -> None:
        '''Show context menu on file view.'''

        menu: QMenu = QMenu(self)

        for action_data in self.__action_list:
            action: QAction = menu.addAction(
                icon_from_file_name(action_data[1]),
                action_data[0],
            )
            action.triggered.connect(action_data[2])

        action = menu.addAction(
            icon_from_file_name('a_rename.png'),
            'Rename Item',
        )
        action.triggered.connect(self.rename_item)

        action = menu.addAction(
            icon_from_file_name('a_trash.png'),
            'Delete Item',
        )
        action.triggered.connect(self.remove_item)

        menu.exec_(self.mapToGlobal(position))

    def root_path(self) -> str:
        '''Return root path.'''
        return self.__root_dir.text()

    def set_root_path(self, path: str) -> None:
        '''Set root path'''
        self.__root_dir.setText(path)

    def outline_viewer(self) -> QTreeView:
        '''Return outline viewer'''
        return self.__outline_viewer

    def file_viewer(self) -> QListView:
        '''Return file viewer'''
        return self.__file_viewer

    def option_widget(self) -> QWidget:
        '''Return option widget.'''
        return self.__option_widget

    def splitter_widget(self) -> QSplitter:
        '''Return splitter widget.'''
        return self.__splitter

    def add_option_widget(self, widget: QWidget) -> None:
        '''Repalce option_widget on splitter.'''
        self.__splitter.addWidget(widget)
        self.__option_widget = widget

    def add_file_view_button(
        self, index: int, label: str, icon_name: str, func: Callable[..., Any]
    ) -> IconButton:
        '''
        Add button to header of file view.

        The current path is set to the argument when the function is executed.
        func(current_path)
        '''
        button = IconButton(self)
        button.set_icon(icon_from_file_name(icon_name))
        button.clicked.connect(
            functools.partial(self.custom_botton_callback, func)
        )
        button.setMaximumSize(24, 24)
        self.__file_viewer_header_layout.insertWidget(index, button)

        self.__action_list.insert(index, [label, icon_name, func])
        return button

    def custom_botton_callback(self, func: Callable[..., Any]) -> None:
        '''Custom button callback'''
        func(self.__current_path)

    def change_home_directory(self, file_path: str) -> None:
        '''Change home directory.'''
        self.__current_path = file_path
        self.__outline_viewer.setRootIndex(
            self.__outline_proxy_model.mapFromSource(
                self.__outline_model.setRootPath(file_path)
            )
        )

    def click_outline_callback(self, selected: QModelIndex) -> None:
        '''Click callback of tree view.'''

        # Move root directory when has not selection item in tree view.
        if not self.__outline_viewer.selectionModel().hasSelection():
            self.__outline_viewer.selectionModel().clear()

    def click_view_callback(self, selected: QModelIndex) -> None:
        '''Click callback of list view.'''

        # Move root directory when has not selection item in tree view.
        if not self.__file_viewer.selectionModel().hasSelection():
            self.__file_viewer.selectionModel().clear()

    def change_directory_callback(
        self, selected: QModelIndex, deselected: QModelIndex
    ) -> None:
        '''Change directory callback.'''
        selected = self.__outline_proxy_model.mapToSource(selected)
        file_path: str = self.__outline_model.filePath(selected)
        if file_path == '':
            file_path = self.__outline_model.rootPath()

        self.change_directory(file_path)

    def change_directory(self, current_path: str) -> None:
        '''Change directory'''
        self.__file_model.clear()
        for path in os.listdir(current_path):
            full_path: str = os.path.join(current_path, path)
            if not os.path.isdir(full_path):
                continue

            name, ext = os.path.splitext(path)
            if ext == '':
                continue

            self.add_item(full_path)

        self.__current_path = current_path

    def change_item_callback(
        self, selected: QModelIndex, deselected: QModelIndex
    ) -> None:
        '''Change item.'''
        if not selected.isValid():
            self.item_selected.emit(FileBrowserItem(''))
            self.__current_item = None
            return

        selected: QModelIndex = self.__file_proxy_model.mapToSource(selected)
        item: FileBrowserItem = self.__file_model.itemFromIndex(selected)
        self.item_selected.emit(item)
        self.__current_item = item

    def add_item(self, path: str) -> None:
        '''Add item to list view.'''
        # Check if it already exists
        for row in range(self.__file_model.rowCount()):
            index: QModelIndex = self.__file_model.index(row, 0)
            item: FileBrowserItem = self.__file_model.itemFromIndex(index)
            if path == item.data_path():
                # Update
                item.set_data_path(path)
                return

        item = FileBrowserItem(path)
        self.__file_model.appendRow(item)

    def filter(self) -> str:
        '''Return filter from file viewer.'''
        return self.__filter_text

    def set_filter_text(self, filter: str) -> None:
        '''Set filter to widget'''
        self.__file_viewer_filter.setText(filter)
        self.set_filter(filter)

    def set_filter(self, filter: str) -> None:
        '''Set filter.'''
        self.__filter_text = filter
        try:  # PySide2
            self.__file_proxy_model.setFilterRegExp(filter)
        except AttributeError:  # PySide6
            self.__file_proxy_model.setFilterRegularExpression(filter)

    def icon_size(self) -> int:
        '''Return icon size.'''
        return self.__file_viewer.iconSize().width()

    def set_icon_size(self, icon_size: int) -> None:
        '''Set icon size to file viewer.'''
        self.__file_viewer.setIconSize(QSize(icon_size, icon_size))
        self.__file_viewer.setGridSize(QSize(icon_size + 12, icon_size + 12))

    def set_icon_range(self, value: int, min_size: int, max_size: int) -> None:
        '''Set icon size to slider'''
        self.__file_viewer_icon_size.setRange(min_size, max_size)
        self.__file_viewer_icon_size.setValue(value)
        self.set_icon_size(value)

    def new_folder(self) -> None:
        '''Create new folder.'''
        source_path: str = self.__current_path
        folder_name, result = QInputDialog.getText(
            self,
            'Create folder',
            f'Location :\n{source_path}\n\n New folder name :',
            QLineEdit.Normal,
        )
        if not result or folder_name == '':
            return

        try:
            full_path: str = os.path.join(source_path, folder_name)
            os.mkdir(full_path)

        except IOError as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to create folder.\n{e}',
                QMessageBox.Ok,
            )
            return

        if self.__outline_model.rootPath() == source_path:
            self.__outline_viewer.selectionModel().clear()
        return

    def rename_folder(self) -> bool:
        '''Rename folder'''
        source_path = self.__current_path
        if self.__outline_model.rootPath() == self.__current_path:
            return False

        split_path: tuple[str, str] = os.path.split(source_path)
        folder_name, result = QInputDialog.getText(
            self,
            'Rename folder',
            'New folder name :',
            QLineEdit.Normal,
            split_path[-1],
        )
        if not result or folder_name == '' or folder_name == split_path[-1]:
            return False

        # Rename
        try:
            dirname: str = os.path.dirname(source_path)
            new_path: str = os.path.join(dirname, folder_name)
            os.rename(source_path, new_path)

        except IOError as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to rename folder.\n\n{e}',
                QMessageBox.Ok,
            )
            return False

        # Clear selection item of view.
        self.__file_viewer.selectionModel().clear()
        self.__outline_viewer.selectionModel().clear()
        return True

    def remove_folder(self) -> bool:
        '''Remove folder'''
        if self.root_path() == self.__current_path:
            return False

        result = QMessageBox.question(
            self,
            'Remove folder',
            f'Are you sure you want to delete?\n{self.__current_path}',
        )
        if result == QMessageBox.No:
            return False

        try:
            shutil.rmtree(self.__current_path)

        except IOError as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to remove folder.\n\n{e}',
                QMessageBox.Ok,
            )
            return False

        # Clear selection item of view.
        self.__file_viewer.selectionModel().clear()
        self.__outline_viewer.selectionModel().clear()
        return True

    def rename_item(self) -> bool:
        '''Rename item.'''
        if not self.__current_item:
            return False

        source_path = self.__current_item.data_path()
        base_name: str = os.path.basename(source_path)
        base_name, extension = os.path.splitext(base_name)
        extension = extension[1:]

        folder_name, result = QInputDialog.getText(
            self,
            'Rename item',
            f'New {extension} item name :',
            QLineEdit.Normal,
            base_name,
        )
        if not result or folder_name == '' or folder_name == base_name:
            return False

        # Rename
        source_item = self.__current_item
        try:
            dirname: str = os.path.dirname(source_path)
            new_path: str = os.path.join(dirname, f'{folder_name}.{extension}')
            os.rename(source_path, new_path)

        except IOError as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to rename folder.\n\n{e}',
                QMessageBox.Ok,
            )
            return False

        # Update item
        source_item.set_data_path(new_path)
        self.__file_viewer.selectionModel().clear()
        return True

    def remove_item(self) -> bool:
        '''remove item.'''
        if not self.__current_item:
            return False

        source_path = self.__current_item.data_path()

        result = QMessageBox.question(
            self,
            'Remove item',
            f'Are you sure you want to delete?\n{source_path}',
        )
        if result == QMessageBox.No:
            return False

        try:
            shutil.rmtree(source_path)

        except IOError as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to remove folder.\n\n{e}',
                QMessageBox.Ok,
            )
            return False

        # Update item
        self.__file_model.removeRow(self.__current_item.row())
        self.__file_viewer.selectionModel().clear()
        return True


class ViewportCapture(QWidget):
    '''Viewport Capture Dialog'''

    viewport_offset_width: int = 0
    viewport_offset_height: int = 0

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        width: int = 512,
        height: int = 512,
        is_shader_ball: bool = False,
    ):
        '''Initialize widget.'''
        self.__width: int = width
        self.__height: int = height
        self.__is_shader_ball: bool = is_shader_ball
        self.__ibl_path: str = os.path.join(
            os.getenv('MAYA_LOCATION'),
            'presets',
            'Assets',
            'IBL',
            'Interior1_Color.exr',
        )
        self.__scriptjob: int = -1
        self.__renderer: str = ''

        super().__init__(parent, flag)
        self.setObjectName('Widget' + str(id(self)))
        self.set_image_size(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setObjectName('Layout' + str(id(main_layout)))

        cmds.setParent(main_layout.objectName())
        self.__model_editor: str = cmds.modelEditor()
        if not self.__is_shader_ball:
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                camera='persp',
                polymeshes=True,
                nurbsSurfaces=True,
                subdivSurfaces=True,
                displayTextures=True,
                displayAppearance='smoothShaded',
                allObjects=False,
                grid=False,
                dynamics=False,
                activeOnly=False,
                manipulators=False,
                headsUpDisplay=False,
                selectionHiliteDisplay=False,
            )
        else:
            # If does not exists Hyper Shade, Maya will crash!
            mel.eval('HypershadeWindow;')
            # mel.eval('HypershadeOpenMaterialViewerWindow;')
            self.__scriptjob = cmds.scriptJob(
                event=('SelectionChanged', self.update_shading_graph)
            )
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                sceneRenderFilter='shaderBallSceneFilter',
            )
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                activeCustomGeometry='meshShaderball',
            )
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                activeCustomEnvironment=self.__ibl_path,
            )
            self.update_shading_graph()

        # It is use trying cmds.parent instead of QT.
        # self.__model_panel_qt = maya_control_to_qt(self.__model_panel)
        # main_layout.addWidget(self.__model_panel_qt)

    def cleanup(self) -> None:
        '''Cleanup widget from maya.cmds'''
        if self.__is_shader_ball:
            cmds.scriptJob(kill=self.__scriptjob)
            cmds.modelEditor(
                self.__model_editor, edit=True, sceneRenderFilter=''
            )
        cmds.deleteUI(self.__model_editor)

    def set_image_size(self, width: int, height: int) -> None:
        '''Set Image.'''
        self.__width = width
        self.__height = height
        self.setMinimumSize(self.__width, self.__height)
        self.setMaximumSize(self.__width, self.__height)
        self.resize(self.__width, self.__height)

    def update_shading_graph(self) -> None:
        '''Update shading graph'''
        selection = cmds.ls(selection=True)
        a: str = ''
        b: str = ''
        c: str = ''
        self.__renderer = ''
        for node in selection:
            c = node
            node_type: str = cmds.nodeType(node)
            if utility.is_surface_shader(node):
                b = node
                connections: list[str] = cmds.listConnections(
                    node,
                    source=False,
                    destination=True,
                    skipConversionNodes=True,
                )
                for connection in connections:
                    if cmds.nodeType(connection) == 'shadingEngine':
                        a = connection
                        break

            elif node_type == 'shadingEngine':
                a = node
                connections = cmds.listConnections(
                    f'{node}.surfaceShader',
                    source=True,
                    destination=False,
                    skipConversionNodes=True,
                )
                if connections:
                    a = connections[0]

                connections = cmds.listConnections(
                    f'{node}.aiSurfaceShader',
                    source=True,
                    destination=False,
                    skipConversionNodes=True,
                )
                if connections:
                    a = connections[0]

            else:
                b = node

            if cmds.nodeType(node, api=True) == 'kPluginDependNode':
                self.__renderer = 'Arnold'

        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            activeShadingGraph=f'{a},{b},{c}',
        )
        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            activeCustomRenderer=self.__renderer,
        )

    def capture(self, output: str) -> bool:
        '''capture viewport.'''
        window: str = cmds.window(width=self.__width, height=self.__height)
        layout: str = cmds.formLayout()
        editor: str = cmds.modelEditor(parent=layout)
        if not self.__is_shader_ball:
            cmds.modelEditor(
                editor,
                edit=True,
                camera='persp',
                polymeshes=True,
                nurbsSurfaces=True,
                subdivSurfaces=True,
                displayTextures=True,
                displayAppearance='smoothShaded',
                allObjects=False,
                grid=False,
                dynamics=False,
                activeOnly=False,
                manipulators=False,
                headsUpDisplay=False,
                selectionHiliteDisplay=False,
            )
        else:
            # If does not exists Hyper Shade, Maya will crash!
            mel.eval('HypershadeWindow;')
            # mel.eval('HypershadeOpenMaterialViewerWindow;')
            cmds.modelEditor(
                editor,
                edit=True,
                sceneRenderFilter='shaderBallSceneFilter',
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomGeometry='meshShaderball',
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomEnvironment=self.__ibl_path,
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeShadingGraph=cmds.modelEditor(
                    self.__model_editor, query=True, activeShadingGraph=True
                ),
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomRenderer=self.__renderer,
            )
        cmds.formLayout(
            layout,
            edit=True,
            attachForm=[
                (editor, 'top', 0),
                (editor, 'left', 0),
                (editor, 'right', 0),
                (editor, 'bottom', 0),
            ],
        )
        cmds.showWindow(window)

        image = OpenMaya.MImage()
        view = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.getM3dViewFromModelEditor(editor, view)
        view.beginGL()
        view.readColorBuffer(image, 1)
        view.endGL()
        image.writeToFile(output)

        cmds.deleteUI(window)
        return True


class Browser(QWidget):
    '''Web browser for Maya.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        if parent is None:
            parent = maya_window_to_qt()
            flag = Qt.Window

        super().__init__(parent, flag)
        self.setWindowIcon(icon_from_file_name(LOGO))
        self.resize(1280, 720)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__web_view: QWebEngineView = QWebEngineView(self)
        main_layout.addWidget(self.__web_view)

    def set_url(self, url: str) -> None:
        '''Change url to widget.'''
        q_url: QUrl = QUrl(url)
        self.__web_view.setUrl(q_url)

    @staticmethod
    def show_url(
        parent: QWidget | None = None, title: str = '', url: str = ''
    ) -> Browser:
        '''Show url in browser.'''
        browser = Browser()
        browser.setWindowTitle(title)
        browser.set_url(url)
        browser.show()
        return browser


class AdaptiveStackedWidget(QStackedWidget):
    '''A custom QStackedWidget that adapts its size to the currently active page.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        size_policy: QSizePolicy = self.sizePolicy()
        size_policy.setVerticalPolicy(QSizePolicy.Fixed)
        self.setSizePolicy(size_policy)
        self.currentChanged.connect(self.updateGeometry)

    def sizeHint(self) -> QSize:
        '''[Override]'''
        current = self.currentWidget()
        if current:
            return current.sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        '''[override]'''
        current = self.currentWidget()
        if current:
            return current.minimumSizeHint()

        return super().minimumSizeHint()


class AboutDialog(QDialog):
    '''Display tool infomation as a dialog.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        if parent is None:
            ptr: Any = OpenMayaUI.MQtUtil.mainWindow()
            parent = wrapInstance(int(ptr), QWidget)

        super().__init__(parent, flag)
        self.setWindowIcon(icon_from_file_name(LOGO))
        self.resize(320, 340)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        header_image: QLabel = QLabel(self)
        header_image.setPixmap(pixmap_from_file_name(HEADER))
        header_image.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_image)

        self.__text_area: QTextEdit = QTextEdit(self)
        self.__text_area.setReadOnly(True)
        main_layout.addWidget(self.__text_area)

        ok_button: QPushButton = QPushButton('OK', self)
        ok_button.clicked.connect(self.accept)
        main_layout.addWidget(ok_button)

    def set_text(self, text: str) -> None:
        '''Set text to QTextEdit.'''
        self.__text_area.setText(text)

    @staticmethod
    def info(
        parent: QWidget | None = None,
        product: str = '',
        version: str = '',
        copyright_: str = '',
        document: str = '',
    ) -> None:
        '''Show a about dialog for information.'''
        text = f'''
<h1>{product}</h1>
<p>Version: {version}<br />{document}</p>
<hr />
<p>{copyright_}</p>
<p>All use of this Software is subject to the terms and conditions of the license agreement accepted upon installation of this Software and/or packaged with the Software.</p>
'''
        dialog = AboutDialog(parent)
        dialog.setWindowTitle(f'About {product}')
        dialog.set_text(text)
        dialog.show()


class ToolWidget(QWidget, ABC, metaclass=QWidgetABCMeta):
    '''Template for tools.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        if parent is None:
            # ptr: Any = OpenMayaUI.MQtUtil.mainWindow()
            # parent = wrapInstance(int(ptr), QWidget)
            parent = maya_window_to_qt()
            flag = Qt.Window

        super().__init__(parent, flag)
        self.setWindowIcon(icon_from_file_name(LOGO))

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ======================================================================
        # Menu Bar
        # ======================================================================
        self.__menu_bar: QMenuBar = QMenuBar(self)
        main_layout.addWidget(self.__menu_bar)

        self.__file_menu: QMenu = QMenu('File', self)
        self.__menu_bar.addMenu(self.__file_menu)

        save_action: QAction = self.__file_menu.addAction('Save Settings')
        save_action.triggered.connect(self.save_settings)

        reset_action: QAction = self.__file_menu.addAction('Reset Settings')
        reset_action.triggered.connect(self.reset_settings)

        self.__file_menu.addSeparator()

        exit_action: QAction = self.__file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        self.__help_menu: QMenu = QMenu('Help', self)
        self.__menu_bar.addMenu(self.__help_menu)

        about_action: QAction = self.__help_menu.addAction('About')
        about_action.triggered.connect(self.about)

        # ======================================================================
        # Frame
        # ======================================================================
        self.__sub_layout: QVBoxLayout = QVBoxLayout(self)
        self.__sub_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.addLayout(self.__sub_layout)

        self.__option_widget: QWidget = QWidget(self)
        self.__sub_layout.addWidget(self.__option_widget, True)

    # override
    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.save_settings()
        super().closeEvent(event)

    # override
    def show(self) -> None:
        '''show[override]'''
        self.load_settings()
        super().show()

    @abstractmethod
    def load_settings(self) -> None:
        '''Load ui settings.'''

    @abstractmethod
    @Slot()
    def save_settings(self) -> None:
        '''Save ui settings.'''

    @abstractmethod
    @Slot()
    def reset_settings(self) -> None:
        '''Reset ui settings.'''

    @abstractmethod
    @Slot()
    def about(self) -> None:
        '''Show a about dialog.'''

    def menu_bar(self) -> QMenuBar:
        '''Return menu bar widget.'''
        return self.__menu_bar

    def file_menu(self) -> QMenu:
        '''Return file menu.'''
        return self.__file_menu

    def help_menu(self) -> QMenu:
        '''Return help menu.'''
        return self.__help_menu

    def option_widget(self) -> QWidget:
        '''Return option widget.'''
        return self.__option_widget

    def option_layout(self) -> QLayout:
        '''Return option layout.'''
        return self.__sub_layout


class StandardToolWidget(QWidget, ABC, metaclass=QWidgetABCMeta):
    '''Template for standard tools.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        if parent is None:
            # ptr: Any = OpenMayaUI.MQtUtil.mainWindow()
            # parent = wrapInstance(int(ptr), QWidget)
            parent = maya_window_to_qt()
            flag = Qt.Window

        super().__init__(parent, flag)
        self.setWindowIcon(icon_from_file_name(LOGO))

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ======================================================================
        # Menu Bar
        # ======================================================================
        self.__menu_bar: QMenuBar = QMenuBar(self)
        main_layout.addWidget(self.__menu_bar)

        self.__file_menu: QMenu = QMenu('File', self)
        self.__menu_bar.addMenu(self.__file_menu)

        save_action: QAction = self.__file_menu.addAction('Save Settings')
        save_action.triggered.connect(self.save_settings)

        reset_action: QAction = self.__file_menu.addAction('Reset Settings')
        reset_action.triggered.connect(self.reset_settings)

        self.__file_menu.addSeparator()

        exit_action: QAction = self.__file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        self.__help_menu: QMenu = QMenu('Help', self)
        self.__menu_bar.addMenu(self.__help_menu)

        about_action: QAction = self.__help_menu.addAction('About')
        about_action.triggered.connect(self.about)

        # ======================================================================
        # Frame
        # ======================================================================
        sub_layout: QGridLayout = QGridLayout(self)
        sub_layout.setContentsMargins(10, 0, 10, 10)
        main_layout.addLayout(sub_layout)

        self.__scroll: QScrollArea = QScrollArea(self)
        self.__scroll.setWidgetResizable(True)
        self.__scroll.setFocusPolicy(Qt.NoFocus)
        self.__scroll.setMinimumHeight(1)
        sub_layout.addWidget(self.__scroll, 1, 0, 1, 3)

        self.__option_widget: QWidget = QWidget(self)
        self.__scroll.setWidget(self.__option_widget)

        self.__apply_close = QPushButton('Apply && Close', self)
        self.__apply_close.clicked.connect(self.apply_close)
        sub_layout.addWidget(self.__apply_close, 2, 0)

        self.__apply = QPushButton('Apply', self)
        self.__apply.clicked.connect(self.apply)
        sub_layout.addWidget(self.__apply, 2, 1)

        self.__close = QPushButton('Close', self)
        self.__close.clicked.connect(self.close)
        sub_layout.addWidget(self.__close, 2, 2)

    # override
    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.save_settings()
        super().closeEvent(event)

    # override
    def show(self) -> None:
        '''show[override]'''
        self.load_settings()
        super().show()

    @abstractmethod
    def load_settings(self) -> None:
        '''Load ui settings.'''

    @abstractmethod
    @Slot()
    def save_settings(self) -> None:
        '''Save ui settings.'''

    @abstractmethod
    @Slot()
    def reset_settings(self) -> None:
        '''Reset ui settings.'''

    @abstractmethod
    @Slot()
    def about(self) -> None:
        '''Show a about dialog.'''

    @abstractmethod
    @Slot()
    def apply(self) -> None:
        '''Apply'''

    @Slot()
    def apply_close(self) -> None:
        '''Apply and close.'''
        self.apply()
        self.close()

    def scroll_widget(self) -> QScrollArea:
        '''Return scroll widget.'''
        return self.__scroll

    def option_widget(self) -> QWidget:
        '''Return option widget.'''
        return self.__option_widget

    def apply_close_button(self) -> QPushButton:
        '''Return button of apply and close.'''
        return self.__apply_close

    def apply_button(self) -> QPushButton:
        '''Return apply button.'''
        return self.__apply

    def close_button(self) -> QPushButton:
        '''Return close button.'''
        return self.__close

    def menu_bar(self) -> QMenuBar:
        '''Return menu bar widget.'''
        return self.__menu_bar

    def file_menu(self) -> QMenu:
        '''Return file menu.'''
        return self.__file_menu

    def help_menu(self) -> QMenu:
        '''Return help menu.'''
        return self.__help_menu


# ==============================================================================
#
# Functions
#
# ==============================================================================
def maya_window_to_qt() -> QMainWindow:
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    widget: QWidget = wrapInstance(int(ptr), QMainWindow)
    return widget


def maya_control_to_qt(maya_widget: str) -> QWidget:
    '''Maya widget to QWidget.'''
    ptr = OpenMayaUI.MQtUtil.findControl(maya_widget)
    widget: QWidget = wrapInstance(int(ptr), QWidget)
    return widget


def maya_layout_to_qt(maya_layout: str) -> QLayout:
    ptr = OpenMayaUI.MQtUtil.findLayout(maya_layout)
    layout: QLayout = wrapInstance(int(ptr), QLayout)
    return layout


def maya_menu_item_to_qt(maya_menu_item: str) -> QAction:
    ptr = OpenMayaUI.MQtUtil.findMenuItem(maya_menu_item)
    action: QAction = wrapInstance(int(ptr), QAction)
    return action


def undo(func: Callable[..., Any]) -> Callable[..., Any]:
    '''This function is decorator for undo.'''

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            cmds.undoInfo(openChunk=True)
            # cmds.refresh(suspend=True)
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
            # cmds.refresh(suspend=False)

    return wrapper


def to_ascii(byte: QByteArray) -> str:
    '''Convert to QByteArray from str.'''
    return bytes(byte.toHex()).decode('ascii')


def to_qt(data: str) -> QByteArray:
    '''Convert to str from QByteArray.'''
    return QByteArray.fromHex(bytes(data, 'ascii'))


def to_check_state(value: bool) -> Qt.CheckState:
    '''Convert to Qt.CheckState from bool.'''
    return Qt.Checked if value else Qt.Unchecked


def icon_from_file_name(file_name: str) -> QIcon:
    '''Return QIcon instance from file name.'''
    icon = QIcon(file_name)
    if len(icon.availableSizes()) > 0:
        return icon

    icon = QIcon(':/' + file_name)
    if len(icon.availableSizes()) > 0:
        return icon

    icon_path: str | None = os.getenv('XBMLANGPATH')
    if not icon_path:
        raise ValueError(f'Not found file: {file_name}')

    for path in icon_path.split(';'):
        fullpath = os.path.join(path, file_name)
        if os.path.isfile(fullpath):
            icon = QIcon(fullpath)
            break

    if len(icon.availableSizes()) == 0:
        raise ValueError(f'Not found file: {file_name}')

    return icon


def pixmap_from_file_name(file_name: str) -> QPixmap:
    '''Return QPixmap instance from file name.'''
    pixmap = QPixmap(file_name)
    if not pixmap.isNull():
        return pixmap

    pixmap = QPixmap(':/' + file_name)
    if not pixmap.isNull():
        return pixmap

    pixmap_path: str | None = os.getenv('XBMLANGPATH')
    if not pixmap_path:
        raise ValueError(f'Not found file: {file_name}')

    for path in pixmap_path.split(';'):
        fullpath = os.path.join(path, file_name)
        if os.path.isfile(fullpath):
            pixmap = QPixmap(fullpath)
            break

    if pixmap.isNull():
        raise ValueError(f'Not found file: {file_name}')

    return pixmap


def image_file_path(file_name: str) -> str:
    '''Return image file path.'''
    pixmap = QPixmap(file_name)
    if not pixmap.isNull():
        return file_name

    pixmap = QPixmap(':/' + file_name)
    if not pixmap.isNull():
        return ':/' + file_name

    pixmap_path: str | None = os.getenv('XBMLANGPATH')
    if not pixmap_path:
        raise ValueError(f'Not found file: {file_name}')

    result: str = ''
    for path in pixmap_path.split(';'):
        fullpath = os.path.join(path, file_name)
        if os.path.isfile(fullpath):
            result = fullpath.replace('\\', '/')
            break

    if result == '':
        raise ValueError(f'Not found file: {file_name}')

    return result
