# ==============================================================================
#
# Perspective Inspector
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import math

try:
    from PySide2.QtCore import Qt, Signal, QRectF, QLineF, QPointF, QPoint
    from PySide2.QtGui import (
        QPainter,
        QPainterPath,
        QColor,
        QBrush,
        QPen,
        QPixmap,
        QMouseEvent,
        QWheelEvent,
        QKeyEvent,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGraphicsScene,
        QGraphicsView,
        QGraphicsItem,
        QGraphicsEllipseItem,
        QGraphicsLineItem,
        QGraphicsPixmapItem,
        QPushButton,
        QLineEdit,
        QLabel,
        QSlider,
        QFileDialog,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QRectF, QLineF, QPointF, QPoint
        from PySide6.QtGui import (
            QPainter,
            QPainterPath,
            QColor,
            QBrush,
            QPen,
            QPixmap,
            QMouseEvent,
            QWheelEvent,
            QKeyEvent,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QGraphicsScene,
            QGraphicsView,
            QGraphicsItem,
            QGraphicsEllipseItem,
            QGraphicsLineItem,
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


class HandleItem(QGraphicsEllipseItem):
    '''Handle Item.'''

    def __init__(self, x: float, y: float, parent_line: GuideLineItem) -> None:
        '''Initialize'''
        super().__init__(-3, -3, 6, 6, parent_line)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setBrush(QBrush(QColor(255, 170, 0)))
        self.setZValue(30)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.__parent_line: GuideLineItem = parent_line

    def itemChange(
        self, change: QGraphicsItem.GraphicsItemChange, value: str
    ) -> object:
        '''Override'''
        if (
            change == QGraphicsItem.ItemPositionHasChanged
            and self.__parent_line
        ):
            self.__parent_line.update_position_from_handles()

        return super().itemChange(change, value)


class GuideLineItem(QGraphicsItem):
    '''Smart Line Item.'''

    def __init__(
        self,
        line: QLineF,
        axis: str = 'X',
        view_ref: DrawingView | None = None,
    ) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        self.color_type: str = axis
        self.__view_ref: DrawingView | None = view_ref
        self.__color: QColor = self.__get_axis_color(axis)
        self.__guide_item: QGraphicsItem = self.__create_guide_line()
        self.__line_item: QGraphicsLineItem = self.__create_main_line()
        self.__handle1: HandleItem = self.__create_handle(line.p1())
        self.__handle2: HandleItem = self.__create_handle(line.p2())
        self.setHandlesChildEvents(False)
        self.update_position_from_handles()

    def boundingRect(self) -> QRectF:
        '''Override bounding rect.'''
        return self.__line_item.boundingRect()

    def shape(self) -> QPainterPath:
        '''Override shape to match the main line.'''
        return self.__line_item.shape()

    def paint(
        self,
        painter: QPainter,
        option: object,
        widget: QWidget | None = None,
    ) -> None:
        '''Paint event.'''

    def __get_axis_color(self, axis: str) -> QColor:
        '''Get color based on axis.'''
        colors: dict[str, QColor] = {
            'X': QColor(255, 50, 50),
            'Y': QColor(50, 255, 50),
            'Z': QColor(80, 120, 255),
        }
        return colors.get(axis, QColor(255, 255, 255))

    def __create_guide_line(self) -> QGraphicsLineItem:
        '''Create infinite guide line item.'''
        pen = QPen(self.__color)
        pen.setWidth(1)
        pen.setCosmetic(True)

        item = QGraphicsLineItem(self)
        item.setPen(pen)
        return item

    def __create_main_line(self) -> QGraphicsLineItem:
        '''Create main line item.'''
        pen = QPen(self.__color)
        pen.setWidth(2)
        pen.setCosmetic(True)

        item = QGraphicsLineItem(self)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        return item

    def __create_handle(self, pos: QPointF) -> HandleItem:
        '''Create handle item.'''
        handle = HandleItem(pos.x(), pos.y(), self)
        return handle

    def update_position_from_handles(self) -> None:
        '''Update position from handles.'''
        self.prepareGeometryChange()
        p1: QPointF = self.__handle1.scenePos()
        p2: QPointF = self.__handle2.scenePos()
        local_p1: QPointF = self.mapFromScene(p1)
        local_p2: QPointF = self.mapFromScene(p2)
        self.__line_item.setLine(QLineF(local_p1, local_p2))

        line_vec: QPointF = local_p2 - local_p1
        length: float = math.hypot(line_vec.x(), line_vec.y())
        if length > 0:
            scale = 100000
            dx: float = (line_vec.x() / length) * scale
            dy: float = (line_vec.y() / length) * scale
            self.__guide_item.setLine(
                QLineF(
                    local_p1.x() - dx,
                    local_p1.y() - dy,
                    local_p2.x() + dx,
                    local_p2.y() + dy,
                )
            )

        if self.__view_ref:
            self.__view_ref.update_global_visuals()

    def remove_from_scene(self) -> None:
        '''Remove self from scene.'''
        scene: QGraphicsScene = self.scene()
        if scene:
            scene.removeItem(self)

    def get_line_f(self) -> QLineF:
        '''Get QLineF in scene coordinates.'''
        return QLineF(self.__handle1.scenePos(), self.__handle2.scenePos())


class DrawingView(QGraphicsView):
    '''Drawing View'''

    lines_updated = Signal()

    def __init__(
        self,
        scene: QGraphicsScene,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.__is_zooming: bool = False
        self.__is_panning: bool = False
        self.__last_pos: QPoint = QPoint()

        self.__temp_line: QGraphicsLineItem | None = None
        self.__start_pos: QPointF = QPointF()
        self.__current_axis_mode: str = 'X'
        self.__lines: list[GuideLineItem] = []

        self.__vp_marker_x: QGraphicsEllipseItem = self.__create_vp_marker(
            QColor(255, 50, 50)
        )
        self.__vp_marker_y: QGraphicsEllipseItem = self.__create_vp_marker(
            QColor(50, 255, 50)
        )
        self.__vp_marker_z: QGraphicsEllipseItem = self.__create_vp_marker(
            QColor(80, 120, 255)
        )

        h_pen = QPen(QColor(0, 255, 255))
        h_pen.setWidth(2)
        h_pen.setCosmetic(True)

        self.__horizon_line = QGraphicsLineItem()
        self.__horizon_line.setPen(h_pen)
        self.__horizon_line.setZValue(15)
        self.scene().addItem(self.__horizon_line)

        self.setRenderHints(
            QPainter.Antialiasing | QPainter.SmoothPixmapTransform
        )
        self.update_global_visuals()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if event.modifiers() == Qt.AltModifier:
            if (
                event.button() == Qt.MiddleButton
                or event.button() == Qt.LeftButton
            ):
                self.__is_panning = True
                self.__last_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return

            if event.button() == Qt.RightButton:
                self.__is_zooming = True
                self.__last_pos = event.pos()
                self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
                self.setCursor(Qt.SizeVerCursor)
                event.accept()
                return

        item: QGraphicsItem = self.itemAt(event.pos())
        if isinstance(item, HandleItem):
            super().mousePressEvent(event)
            return

        if isinstance(item, QGraphicsLineItem):
            super().mousePressEvent(event)
            return

        if isinstance(item, GuideLineItem):
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self.__start_pos = self.mapToScene(event.pos())

            pen: QPen = QPen(Qt.black)
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            pen.setCosmetic(True)

            self.__temp_line = QGraphicsLineItem(
                QLineF(self.__start_pos, self.__start_pos)
            )
            self.__temp_line.setPen(pen)
            self.scene().addItem(self.__temp_line)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        delta: QPoint = event.pos() - self.__last_pos
        if self.__is_zooming:
            zoom_input: int = delta.x() - delta.y()
            zoom_factor: float = 1.0 + (zoom_input * 0.003)
            if zoom_factor > 0:
                self.scale(zoom_factor, zoom_factor)
                self.__last_pos = event.pos()
            return

        if self.__is_panning:
            self.__last_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return

        if self.__temp_line:
            current_pos: QPointF = self.mapToScene(event.pos())
            line: QLineF = self.__temp_line.line()
            line.setP2(current_pos)
            self.__temp_line.setLine(line)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if self.__is_panning or self.__is_zooming:
            self.__is_zooming = False
            self.__is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if self.__temp_line:
            end_pos: QPointF = self.mapToScene(event.pos())
            self.scene().removeItem(self.__temp_line)
            self.__temp_line = None
            if (end_pos - self.__start_pos).manhattanLength() > 10:
                new_smart_line = GuideLineItem(
                    QLineF(self.__start_pos, end_pos),
                    self.__current_axis_mode,
                    self,
                )
                self.scene().addItem(new_smart_line)
                self.__lines.append(new_smart_line)
                self.update_global_visuals()

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        '''Override'''
        factor = 1.1
        if event.delta() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1.0 / factor, 1.0 / factor)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        '''Handle key press events.'''
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            selected_items: list[QGraphicsItem] = self.scene().selectedItems()
            changed: bool = False
            for item in selected_items:
                parent_item: QGraphicsItem = item.parentItem()
                if isinstance(item, GuideLineItem):
                    if item in self.__lines:
                        self.__lines.remove(item)

                    item.remove_from_scene()
                    changed = True

                elif isinstance(parent_item, GuideLineItem):
                    if parent_item in self.__lines:
                        self.__lines.remove(parent_item)

                    parent_item.remove_from_scene()
                    changed = True

            if changed:
                self.update_global_visuals()

        else:
            super().keyPressEvent(event)

    def __create_vp_marker(self, color: QColor) -> QGraphicsEllipseItem:
        '''Create vanishing point maker.'''
        marker = QGraphicsEllipseItem(-6, -6, 12, 12)
        marker.setBrush(QBrush(color))
        marker.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        marker.setZValue(25)
        marker.setVisible(False)
        self.scene().addItem(marker)
        return marker

    def __update_single_vp(
        self, marker_item: QGraphicsEllipseItem, lines: list[QLineF]
    ) -> QPointF | None:
        '''Update vanishing point.'''
        if len(lines) < 2:
            marker_item.setVisible(False)
            return None

        pt: QPointF | None = calculate_intersection(lines[0], lines[1])
        if not pt:
            marker_item.setVisible(False)
            return None

        marker_item.setPos(pt)
        marker_item.setVisible(True)
        return pt

    def axis_mode(self) -> str:
        '''Return axis mode'''
        return self.__current_axis_mode

    def set_axis_mode(self, axis: str) -> None:
        '''Set axis mode'''
        self.__current_axis_mode = axis

    def update_global_visuals(self) -> None:
        '''Update View.'''
        lines_x: list[QLineF] = [
            line.get_line_f() for line in self.__lines if line.color_type == 'X'
        ]
        lines_y: list[QLineF] = [
            line.get_line_f() for line in self.__lines if line.color_type == 'Y'
        ]
        lines_z: list[QLineF] = [
            line.get_line_f() for line in self.__lines if line.color_type == 'Z'
        ]
        vp_x: QPointF | None = self.__update_single_vp(
            self.__vp_marker_x, lines_x
        )
        vp_y: QPointF | None = self.__update_single_vp(
            self.__vp_marker_y, lines_y
        )
        vp_z: QPointF | None = self.__update_single_vp(
            self.__vp_marker_z, lines_z
        )
        if vp_x and vp_z:
            self.__horizon_line.setVisible(True)
            diff: QPointF = vp_z - vp_x
            scale = 100000
            length: float = math.sqrt(diff.x() ** 2 + diff.y() ** 2)
            if length > 0:
                dx: float = (diff.x() / length) * scale
                dy: float = (diff.y() / length) * scale
                self.__horizon_line.setLine(
                    QLineF(
                        vp_x.x() - dx,
                        vp_x.y() - dy,
                        vp_z.x() + dx,
                        vp_z.y() + dy,
                    )
                )
        else:
            self.__horizon_line.setVisible(False)

        self.lines_updated.emit()


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
        button.clicked.connect(lambda: self.set_mode('X'))
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Y', self)
        button.clicked.connect(lambda: self.set_mode('Y'))
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Z', self)
        button.clicked.connect(lambda: self.set_mode('Z'))
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
        button.clicked.connect(self.apply)
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

    def set_mode(self, mode: str) -> None:
        '''Set line mode.'''
        self.__view.set_axis_mode(mode)

    def calc_preview(self) -> None:
        '''Calc focal length and rotate as preview.'''

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def calculate_intersection(line1: QPointF, line2: QPointF) -> QPointF | None:
    '''Calculate intersection.'''
    x1: float = line1.p1().x()
    y1: float = line1.p1().y()
    x2: float = line1.p2().x()
    y2: float = line1.p2().y()

    x3: float = line2.p1().x()
    y3: float = line2.p1().y()
    x4: float = line2.p2().x()
    y4: float = line2.p2().y()

    denom: float = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None

    px: float = (
        (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    ) / denom
    py: float = (
        (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
    ) / denom
    return QPointF(px, py)


def apply() -> bool:
    '''Docstring'''
    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
