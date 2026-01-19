# ==============================================================================
#
# Perspective Inspector
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import math
import itertools
import pathlib
import json

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
        QButtonGroup,
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
            QButtonGroup,
        )
from maya import cmds
from maya.api import OpenMaya as om
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


class PerspectiveSolver:
    '''Perspective Solver'''

    def __init__(
        self, width: int, height: int, film_width: float = 36.0
    ) -> None:
        '''Initialize'''
        self.__width: float = float(width)
        self.__height: float = float(height)
        self.__cx: float = self.__width / 2.0
        self.__cy: float = self.__height / 2.0
        self.__film_width: float = film_width

    def solve(
        self,
        x_lines: list[list[float]],
        y_lines: list[list[float]],
        z_lines: list[list[float]],
    ) -> dict[str, float]:
        '''Main solver method.'''
        # Calculate vanishing points for each axis
        vp_x: list[float] = self.intersection(x_lines)
        vp_y: list[float] = self.intersection(y_lines)
        vp_z: list[float] = self.intersection(z_lines)

        # Invalidate vanishing points that are too far away.
        vp_x = vp_x if self.is_vp_valid(vp_x) else []
        vp_y = vp_y if self.is_vp_valid(vp_y) else []
        vp_z = vp_z if self.is_vp_valid(vp_z) else []

        # VP2
        vp2_result: dict[str, float] = {}
        if vp_x and vp_z:
            vp2_result = self.solve_vp2(vp_x, vp_z, 'XZ')

        elif vp_x and vp_y:
            vp2_result = self.solve_vp2(vp_x, vp_y, 'XY')

        elif vp_y and vp_z:
            vp2_result = self.solve_vp2(vp_y, vp_z, 'YZ')

        if vp2_result:
            return vp2_result

        # VP1
        if vp_x and len(z_lines) >= 2:
            return self.solve_vp1(vp_x, z_lines, 'XZ', is_vp_primary=True)

        elif vp_z and len(x_lines) >= 2:
            return self.solve_vp1(vp_z, x_lines, 'XZ', is_vp_primary=False)

        elif vp_y and len(x_lines) >= 2:
            return self.solve_vp1(vp_y, x_lines, 'XY', is_vp_primary=False)

        elif vp_x and len(y_lines) >= 2:
            return self.solve_vp1(vp_x, y_lines, 'XY', is_vp_primary=True)

        elif vp_y and len(z_lines) >= 2:
            return self.solve_vp1(vp_y, z_lines, 'YZ', is_vp_primary=True)

        elif vp_z and len(y_lines) >= 2:
            return self.solve_vp1(vp_z, y_lines, 'YZ', is_vp_primary=False)

        return {}

    def is_vp_valid(
        self, vp: list[float] | None, threshold_ratio: float = 100.0
    ) -> bool:
        '''Check if the VP is within a valid distance.'''
        if not vp:
            return False

        dx: float = vp[0] - self.__cx
        dy: float = vp[1] - self.__cy
        dist: float = math.sqrt(dx * dx + dy * dy)
        if dist > self.__width * threshold_ratio:
            return False

        return True

    def solve_vp2(
        self, vp1: list[float], vp2: list[float], pair_mode: str
    ) -> dict[str, float]:
        '''Calculates true focal length using the orthogonality of axes.'''

        # Convert VP coordinates to vectors from the image center
        v1_x: float = vp1[0] - self.__cx
        v1_y: float = -(vp1[1] - self.__cy)
        v2_x: float = vp2[0] - self.__cx
        v2_y: float = -(vp2[1] - self.__cy)

        # Calculate the dot product of the image plane vectors.
        # Ideally: V1 . V2 = -f^2 (derived from V1_3d . V2_3d = 0)
        dot_part: float = v1_x * v2_x + v1_y * v2_y
        if dot_part >= 0:
            return {}

        # Calculate Focal Length (in pixels)
        f_pixel: float = math.sqrt(-dot_part)

        # Convert to mm (35mm equivalent)
        focal_length: float = (f_pixel * self.__film_width) / self.__width

        # Reconstruct 3D vectors from camera to VPs
        vec_1: list[float] = self.normalize([v1_x, v1_y, -f_pixel])
        vec_2: list[float] = self.normalize([v2_x, v2_y, -f_pixel])

        rotate: list[float] = self.rotation_matrix(vec_1, vec_2, pair_mode)
        return self.__format_result(focal_length, rotate)

    def solve_vp1(
        self,
        vp: list[float],
        parallel_lines: list[list[float]],
        pair_mode: str,
        is_vp_primary: bool,
    ) -> dict[str, float]:
        '''Focal length cannot be mathematically determined from 1 VP alone.'''
        focal_length: float = 35.0
        f_pixel: float = (focal_length * self.__width) / self.__film_width

        # Vector towards the vanishing point.
        # (Optical Axis direction usually)
        vec_converge: list[float] = self.normalize(
            [
                vp[0] - self.__cx,
                -(vp[1] - self.__cy),
                -f_pixel,
            ]
        )

        # Vector for lines that are parallel on screen.
        # (Perpendicular to Optical Axis)
        line_vec: list[float] = self.angle(parallel_lines)
        vec_parallel: list[float] = self.normalize(
            [line_vec[0], -line_vec[1], 0]
        )

        if is_vp_primary:
            vec_1: list[float] = vec_converge
            vec_2: list[float] = vec_parallel
        else:
            vec_1 = vec_parallel
            vec_2 = vec_converge

        rotate: list[float] = self.rotation_matrix(vec_1, vec_2, pair_mode)
        return self.__format_result(focal_length, rotate)

    def rotation_matrix(
        self, vec_1: list[float], vec_2: list[float], mode: str
    ) -> list[float]:
        '''Calculate rotation matrix from two vectors with orthogonalization.'''
        cam_x: list[float] = [1, 0, 0]
        cam_y: list[float] = [0, 1, 0]
        cam_z: list[float] = [0, 0, 1]

        if mode == 'XZ':
            # X(v1), Z(v2)
            # Fix Z (Depth), generate Y, then recalculate X.
            raw_x: list[float] = vec_1
            raw_z: list[float] = vec_2

            # Z x X = Y (Create temporary Y-axis)
            temp_y: list[float] = self.normalize(
                self.cross_product(raw_z, raw_x)
            )

            # Correct Y orientation (Y-up: Flip if pointing down)
            if temp_y[1] < 0:
                temp_y = [-temp_y[0], -temp_y[1], -temp_y[2]]

            # Fix Y and Z
            cam_y = temp_y
            cam_z = raw_z

            # Y x Z = X (X is now perfectly orthogonal)
            cam_x = self.normalize(self.cross_product(cam_y, cam_z))

        elif mode == 'XY':
            # X(v1), Y(v2)
            # Fix Y (Height), generate Z, then recalculate X.
            raw_x = vec_1
            raw_y: list[float] = vec_2

            # Correct Y orientation
            if raw_y[1] < 0:
                raw_y = [-raw_y[0], -raw_y[1], -raw_y[2]]

            # Fix Y
            cam_y = raw_y

            # X x Y = Z (Create Z-axis)
            cam_z = self.normalize(self.cross_product(raw_x, cam_y))

            # Y x Z = X (X is now perfectly orthogonal)
            cam_x = self.normalize(self.cross_product(cam_y, cam_z))

        elif mode == 'YZ':
            # Y(v1), Z(v2)
            # Fix Y (Height), generate X, then recalculate Z.
            raw_y = vec_1
            raw_z = vec_2

            # Correct Y orientation
            if raw_y[1] < 0:
                raw_y = [-raw_y[0], -raw_y[1], -raw_y[2]]

            # Fix Y
            cam_y = raw_y

            # Y x Z = X (Create X-axis)
            cam_x = self.normalize(self.cross_product(cam_y, raw_z))

            # X x Y = Z (Z is now perfectly orthogonal)
            cam_z = self.normalize(self.cross_product(cam_x, cam_y))

        # Transpose matrix (Inverse rotation)
        matrix_list: list[float] = [
            cam_x[0],
            cam_y[0],
            cam_z[0],
            0.0,
            cam_x[1],
            cam_y[1],
            cam_z[1],
            0.0,
            cam_x[2],
            cam_y[2],
            cam_z[2],
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]

        matrix: om.MMatrix = om.MMatrix(matrix_list)
        transform_matrix: om.MTransformationMatrix = om.MTransformationMatrix(
            matrix
        )
        transform_matrix.reorderRotation(om.MTransformationMatrix.kXYZ)
        rotate: om.MEulerRotation = transform_matrix.rotation(False)
        rotate.setToClosestSolution(om.MEulerRotation(0, 0, 0))
        return [
            math.degrees(rotate.x),
            math.degrees(rotate.y),
            math.degrees(rotate.z),
        ]

    def __format_result(
        self, focal_length: float, rotate: list[float]
    ) -> dict[str, float]:
        '''Format the output dictionary.'''
        return {
            'focal_length': round(focal_length, 1),
            'rotate_x': round(rotate[0], 3),
            'rotate_y': round(rotate[1], 3),
            'rotate_z': round(rotate[2], 3),
        }

    @staticmethod
    def normalize(v: list[float]) -> list[float]:
        '''Returns normalized vector.'''
        norm: float = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
        if norm == 0:
            return [0, 0, 0]
        return [v[0] / norm, v[1] / norm, v[2] / norm]

    @staticmethod
    def cross_product(a: list[float], b: list[float]) -> list[float]:
        '''Returns cross product of two vectors.'''
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ]

    @staticmethod
    def intersection(lines: list[list[float]]) -> list[float]:
        '''Calculate average intersection point of multiple lines.'''
        if len(lines) < 2:
            return []

        intersections: list[list[float]] = []
        for line_a, line_b in itertools.combinations(lines, 2):
            point: list[float] = PerspectiveSolver.cross_point(line_a, line_b)
            if point:
                intersections.append(point)

        if not intersections:
            return []

        avg_x: float = sum(p[0] for p in intersections) / len(intersections)
        avg_y: float = sum(p[1] for p in intersections) / len(intersections)
        return [avg_x, avg_y]

    @staticmethod
    def cross_point(line_a: list[float], line_b: list[float]) -> list[float]:
        '''Calculate intersection point of two lines.'''
        x1: float = line_a[0]
        y1: float = line_a[1]
        x2: float = line_a[2]
        y2: float = line_a[3]

        x3: float = line_b[0]
        y3: float = line_b[1]
        x4: float = line_b[2]
        y4: float = line_b[3]

        denom: float = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return []

        px: float = (
            (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
        ) / denom

        py: float = (
            (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
        ) / denom
        return [px, py]

    @staticmethod
    def angle(lines: list[list[float]]) -> list[float]:
        '''Return angle between two vectors.'''
        dx_sum: float = 0.0
        dy_sum: float = 0.0
        for line in lines:
            dx: float = line[2] - line[0]
            dy: float = line[3] - line[1]
            length: float = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                dx_sum += dx / length
                dy_sum += dy / length

        return [dx_sum, dy_sum]


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
            self.__parent_line.update_ui()

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

        self.__axis: str = axis
        self.__view_ref: DrawingView | None = view_ref
        self.__color: QColor = self.__get_axis_color(axis)
        self.__guide_item: QGraphicsItem = self.__create_guide_line()
        self.__line_item: QGraphicsLineItem = self.__create_main_line()
        self.__handle1: HandleItem = self.__create_handle(line.p1())
        self.__handle2: HandleItem = self.__create_handle(line.p2())
        self.setHandlesChildEvents(False)
        self.update_ui()

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

    def update_ui(self) -> None:
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
            self.__view_ref.update_ui()

    def remove_from_scene(self) -> None:
        '''Remove self from scene.'''
        scene: QGraphicsScene = self.scene()
        if scene:
            scene.removeItem(self)

    def line(self) -> QLineF:
        '''Get QLineF in scene coordinates.'''
        return QLineF(self.__handle1.scenePos(), self.__handle2.scenePos())

    def axis(self) -> str:
        '''Returns axis.'''
        return self.__axis

    def coordinates(self) -> list[float]:
        '''Returns position of point1 and point2.'''
        line: QLineF = self.line()
        return [line.p1().x(), line.p1().y(), line.p2().x(), line.p2().y()]


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
        self.update_ui()

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
                line = GuideLineItem(
                    QLineF(self.__start_pos, end_pos),
                    self.__current_axis_mode,
                    self,
                )
                self.add_line(line)

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
                self.update_ui()

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

    def __update_vp_marker(
        self, marker_item: QGraphicsEllipseItem, lines: list[QLineF]
    ) -> QPointF | None:
        '''Update vanishing point.'''
        if len(lines) < 2:
            marker_item.setVisible(False)
            return None

        line_list: list[list[float]] = [
            [ln.p1().x(), ln.p1().y(), ln.p2().x(), ln.p2().y()] for ln in lines
        ]
        position: list[float] = PerspectiveSolver.intersection(line_list)
        point: QPointF = QPointF(*position)
        if not point:
            marker_item.setVisible(False)
            return None

        marker_item.setPos(point)
        marker_item.setVisible(True)
        return point

    def axis_mode(self) -> str:
        '''Return axis mode'''
        return self.__current_axis_mode

    def set_axis_mode(self, axis: str) -> None:
        '''Set axis mode'''
        self.__current_axis_mode = axis

    def lines(self) -> list[GuideLineItem]:
        '''Returns a list of guide line items.'''
        return self.__lines

    def add_line(self, line: GuideLineItem) -> None:
        '''Add line.'''
        self.scene().addItem(line)
        self.__lines.append(line)
        self.update_ui()

    def update_ui(self) -> None:
        '''Update View.'''
        lines_x: list[QLineF] = [
            line.line() for line in self.__lines if line.axis() == 'X'
        ]
        lines_y: list[QLineF] = [
            line.line() for line in self.__lines if line.axis() == 'Y'
        ]
        lines_z: list[QLineF] = [
            line.line() for line in self.__lines if line.axis() == 'Z'
        ]
        vp_x: QPointF | None = self.__update_vp_marker(
            self.__vp_marker_x, lines_x
        )
        vp_y: QPointF | None = self.__update_vp_marker(
            self.__vp_marker_y, lines_y
        )
        vp_z: QPointF | None = self.__update_vp_marker(
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

    SAVE_NODE_NAME: str = 'amaterasuPerspectiveInspector'
    SAVE_ATTR_NAME: str = 'saveData'

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
        button.clicked.connect(self.save_data_to_scene)
        button.setFixedWidth(50)
        tool_layout.addWidget(button)

        tool_layout.addWidget(widgets.VerticalLine(self))

        axis_group: QButtonGroup = QButtonGroup(self)

        button: QPushButton = QPushButton('X', self)
        button.setCheckable(True)
        button.setChecked(True)
        button.clicked.connect(lambda: self.set_mode('X'))
        button.setFixedWidth(50)
        axis_group.addButton(button)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Y', self)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.set_mode('Y'))
        button.setFixedWidth(50)
        axis_group.addButton(button)
        tool_layout.addWidget(button)

        button: QPushButton = QPushButton('Z', self)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.set_mode('Z'))
        button.setFixedWidth(50)
        axis_group.addButton(button)
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

        self.__view.lines_updated.connect(self.perform_solver_for_preview)
        self.load_data_from_scene()

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
        '''Set background image.'''
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
        self.perform_solver_for_preview()

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

    def perform_solver_for_preview(self) -> None:
        '''Perform solver for preview.'''
        result: dict[str, float] = self.perform_solver()
        if not result:
            self.__focal_length.setText('')
            self.__rotate_x.setText('')
            self.__rotate_y.setText('')
            self.__rotate_z.setText('')

        else:
            self.__focal_length.setText(f"{result['focal_length']}")
            self.__rotate_x.setText(f"{result['rotate_x']}")
            self.__rotate_y.setText(f"{result['rotate_y']}")
            self.__rotate_z.setText(f"{result['rotate_z']}")

    def perform_solver(self) -> dict[str, float]:
        '''Perform solver.'''
        x_lines: list[list[float]] = []
        y_lines: list[list[float]] = []
        z_lines: list[list[float]] = []
        for line in self.__view.lines():
            coords: list[float] = line.coordinates()
            if line.axis() == 'X':
                x_lines.append(coords)

            elif line.axis() == 'Y':
                y_lines.append(coords)

            else:
                z_lines.append(coords)

        if (len(x_lines) >= 2) + (len(y_lines) >= 2) + (len(z_lines) >= 2) < 2:
            return {}

        solver: PerspectiveSolver = PerspectiveSolver(
            self.__width, self.__height
        )
        return solver.solve(x_lines, y_lines, z_lines)

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        result: dict[str, float] = self.perform_solver()
        if not result:
            _logger.error('Need at least 2 axes with 2 lines each.')
            return

        apply_to_maya_scene(
            result['focal_length'],
            [result['rotate_x'], result['rotate_y'], result['rotate_z']],
        )
        _logger.info('Done.')

    @widgets.undo
    def save_data_to_scene(self) -> None:
        '''Save data to scene.'''
        lines_data: list[dict[str, Any]] = []
        for line in self.__view.lines():
            lines_data.append(
                {'coords': line.coordinates(), 'axis': line.axis()}
            )

        save_data: dict[str, Any] = {
            'image_path': self.__current_image_path,
            'opacity': self.__opacity.value(),
            'lines': lines_data,
        }
        json_str: str = json.dumps(save_data)
        if not cmds.objExists(self.SAVE_NODE_NAME):
            cmds.createNode('network', name=self.SAVE_NODE_NAME)

        if not cmds.attributeQuery(
            self.SAVE_ATTR_NAME, node=self.SAVE_NODE_NAME, exists=True
        ):
            cmds.addAttr(
                self.SAVE_NODE_NAME,
                longName=self.SAVE_ATTR_NAME,
                dataType='string',
            )

        cmds.setAttr(
            f'{self.SAVE_NODE_NAME}.{self.SAVE_ATTR_NAME}',
            json_str,
            type='string',
        )
        _logger.info('Saved.')

    def load_data_from_scene(self) -> None:
        '''Load data from scene.'''
        if not cmds.objExists(self.SAVE_NODE_NAME) or not cmds.attributeQuery(
            self.SAVE_ATTR_NAME, node=self.SAVE_NODE_NAME, exists=True
        ):
            return

        try:
            data: dict[str, Any] = json.loads(
                cmds.getAttr(f'{self.SAVE_NODE_NAME}.{self.SAVE_ATTR_NAME}')
            )

        except json.JSONDecodeError:
            _logger.error('Failed to load data.')
            return

        image_path: str = data.get('image_path', '')
        if not pathlib.Path(image_path).exists():
            _logger.error('Image path does not exist : %s', image_path)
            return

        self.load_image(image_path)
        self.__opacity.setValue(data.get('opacity', 100))
        lines_data: list[dict[str, Any]] = data.get('lines', [])
        for l_data in lines_data:
            c: list[float] = l_data['coords']
            line: GuideLineItem = GuideLineItem(
                QLineF(QPointF(c[0], c[1]), QPointF(c[2], c[3])),
                l_data['axis'],
                self.__view,
            )
            self.__view.add_line(line)

        self.__view.update_ui()
        self.fit_view()
        _logger.info('Loaded save data.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply_to_maya_scene(focal_length: float, rotate: list[float]) -> bool:
    '''Apply to maya scene.'''
    selection: list[str] = cmds.ls(selection=True)
    target_camera: str = ''
    if selection:
        shapes: list[str] = (
            cmds.listRelatives(selection[0], shapes=True, fullPath=True) or []
        )
        if cmds.nodeType(selection[0]) == 'camera':
            target_camera = selection[0]

        elif shapes and cmds.nodeType(shapes[0]) == 'camera':
            target_camera = selection[0]

    if not target_camera:
        target_camera = cmds.camera(name='render_cam')[0]  # type:ignore
        target_camera = cmds.rename(target_camera, 'render_cam')

    # cmds.setAttr(f'{target_camera}.horizontalFilmAperture', 1.417)
    # cmds.setAttr(f'{target_camera}.verticalFilmAperture', 0.945)
    # cmds.setAttr(f'{target_camera}.lensSqueezeRatio', 1.0)
    cmds.setAttr(f'{target_camera}.rotateOrder', 0)
    cmds.setAttr(f'{target_camera}.focalLength', focal_length)
    cmds.setAttr(f'{target_camera}.rotate', *rotate, type='double3')
    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
