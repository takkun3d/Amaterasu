# ==============================================================================
#
# Perspective Inspector
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, QRectF, QPoint
    from PySide2.QtGui import QPainter, QPixmap, QMouseEvent, QWheelEvent
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGraphicsScene,
        QGraphicsView,
        QGraphicsItem,
        QGraphicsPixmapItem,
        QPushButton,
        QLineEdit,
        QLabel,
        QSlider,
        QFileDialog,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QRectF, QPoint
        from PySide6.QtGui import QPainter, QPixmap, QMouseEvent, QWheelEvent
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QGraphicsScene,
            QGraphicsView,
            QGraphicsItem,
            QGraphicsPixmapItem,
            QPushButton,
            QLineEdit,
            QLabel,
            QSlider,
            QFileDialog,
        )
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Perspective Inspector'
__version__: str = '1.00'
__doc__ = 'Inspect perspective lines to solve camera focal length and rotation.'
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


class DrawingView(QGraphicsView):
    '''Drawing View'''

    def __init__(
        self,
        scene: QGraphicsScene,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(scene, parent)
        self._is_zooming: bool = False
        self._is_panning: bool = False
        self._last_pan_pos: QPoint = QPoint()

        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if event.modifiers() == Qt.AltModifier:
            if (
                event.button() == Qt.MiddleButton
                or event.button() == Qt.LeftButton
            ):
                self._is_panning = True
                self._last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return

            if event.button() == Qt.RightButton:
                self._is_zooming = True
                self._last_pan_pos = event.pos()
                self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
                self.setCursor(Qt.SizeVerCursor)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        delta: QPoint = event.pos() - self._last_pan_pos
        if self._is_zooming:
            zoom_input: int = delta.x() - delta.y()
            zoom_factor: float = 1.0 + (zoom_input * 0.001)
            if zoom_factor > 0:
                self.scale(zoom_factor, zoom_factor)
            return

        if self._is_panning:
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if self._is_panning or self._is_zooming:
            self._is_zooming = False
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        '''Override'''
        factor = 1.1
        if event.delta() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1.0 / factor, 1.0 / factor)


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
        self.resize(1200, 800)
        self.__current_image_path: str = ''
        self.__bg_item: QGraphicsPixmapItem | None = None
        self.__width: int = 1280
        self.__height: int = 720

        option_widget: QWidget = self.option_widget()

        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tool
        tool_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(tool_layout)

        button: QPushButton = QPushButton('Open', self)
        button.clicked.connect(self.open_image_dialog)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Save', self)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        tool_layout.addWidget(widgets.VerticalLine(self))

        button: QPushButton = QPushButton('X', self)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Y', self)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Z', self)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        tool_layout.addWidget(widgets.VerticalLine(self))

        button: QPushButton = QPushButton('Fit View', self)
        button.setFixedWidth(50)
        button.clicked.connect(self.fit_view)
        tool_layout.addWidget(button)

        label: QLabel = QLabel('Opacity : ', self)
        tool_layout.addWidget(label)

        self.__opacity: QSlider = QSlider(Qt.Horizontal, self)
        self.__opacity.setRange(0, 100)
        self.__opacity.setValue(100)
        self.__opacity.setFixedWidth(100)
        self.__opacity.valueChanged[int].connect(self.change_opacity)
        tool_layout.addWidget(self.__opacity)

        tool_layout.addWidget(widgets.VerticalLine(self))

        label = QLabel('Focal Length : ', self)
        tool_layout.addWidget(label)

        self.__focal_length: QLineEdit = QLineEdit(self)
        self.__focal_length.setEnabled(False)
        tool_layout.addWidget(self.__focal_length)

        label = QLabel('Rotate : ', self)
        tool_layout.addWidget(label)

        self.__rotate_x: QLineEdit = QLineEdit(self)
        self.__rotate_x.setEnabled(False)
        tool_layout.addWidget(self.__rotate_x)

        self.__rotate_y: QLineEdit = QLineEdit(self)
        self.__rotate_y.setEnabled(False)
        tool_layout.addWidget(self.__rotate_y)

        self.__rotate_z: QLineEdit = QLineEdit(self)
        self.__rotate_z.setEnabled(False)
        tool_layout.addWidget(self.__rotate_z)

        tool_layout.addStretch()

        button: QPushButton = QPushButton('Apply', self)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        # View
        self.__scene: QGraphicsScene = QGraphicsScene(self)
        self.__view: DrawingView = DrawingView(self.__scene)
        main_layout.addWidget(self.__view)

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

    def open_image_dialog(self) -> None:
        '''Open image dialog.'''
        result: tuple[str, str] = QFileDialog.getOpenFileName(
            self,
            'Open Image',
            '',
            'Images (*.png *.jpg *.jpeg *.bmp)',
        )
        if result[0]:
            self.load_image(result[0])

    def load_image(self, file_path: str) -> None:
        '''Load image to view.'''
        pixmap: QPixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        self.__current_image_path = file_path
        self.set_background_image(pixmap)
        if self.__bg_item:
            self.__view.fitInView(self.__bg_item, Qt.KeepAspectRatio)

    def set_background_image(self, pixmap: QPixmap) -> None:
        '''Set ground image'''
        if self.__bg_item:
            self.__scene.removeItem(self.__bg_item)

        self.__bg_item = self.__scene.addPixmap(pixmap)
        self.__bg_item.setZValue(-100)
        self.__bg_item.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.__bg_item.setOpacity(self.__opacity.value() / 100.0)
        self.__width = pixmap.width()
        self.__height = pixmap.height()
        margin: int = 100000
        rect: QRectF = QRectF(
            -margin,
            -margin,
            self.__width + margin * 2,
            self.__height + margin * 2,
        )
        self.__scene.setSceneRect(rect)
        self.calc_preview()

    def fit_view(self) -> None:
        '''Fit view.'''
        if self.__bg_item:
            self.__view.fitInView(self.__bg_item, Qt.KeepAspectRatio)
        else:
            self.__view.fitInView(0, 0, 1280, 720, Qt.KeepAspectRatio)

    def change_opacity(self, value: int) -> None:
        '''Change opacity for back ground image.'''
        if self.__bg_item:
            self.__bg_item.setOpacity(value / 100.0)

    def calc_preview(self) -> None:
        '''Calc focal length and rotate as preview.'''

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply() -> bool:
    '''Docstring'''
    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
