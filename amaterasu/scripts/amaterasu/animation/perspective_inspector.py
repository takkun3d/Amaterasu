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
"""Inspects perspective lines to calculate camera focal length and rotation."""

from __future__ import annotations
from typing import Any
import math
import pathlib
import json
from maya import cmds
from maya.api import OpenMaya as om
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc, maths, framework, utils, widgets

__product__: str = "Perspective Inspector"
__version__: str = "1.11"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved geometry of the window.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class PerspectiveSolver:
    """Calculates focal length and camera rotation from perspective lines."""

    def __init__(
        self,
        width: int,
        height: int,
        film_width: float = 36.0,
    ) -> None:
        """Initializes the instance.

        Args:
            width (int): The image width in pixels.
            height (int): The image height in pixels.
            film_width (float, optional): The camera film width in mm.
                Defaults to 36.0.
        """
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
        """Executes the main solver logic based on input axes.

        Args:
            x_lines (list[list[float]]): Guide lines for the X-axis.
            y_lines (list[list[float]]): Guide lines for the Y-axis.
            z_lines (list[list[float]]): Guide lines for the Z-axis.

        Returns:
            dict[str, float]: A dictionary containing 'focal_length' and
                'rotation' data. Returns an empty dict if unsolvable.
        """
        # Calculate vanishing points for each axis
        vp_x: list[float] = maths.average_intersection(x_lines)
        vp_y: list[float] = maths.average_intersection(y_lines)
        vp_z: list[float] = maths.average_intersection(z_lines)

        # Invalidate vanishing points that are too far away.
        vp_x = vp_x if self.is_vp_valid(vp_x) else []
        vp_y = vp_y if self.is_vp_valid(vp_y) else []
        vp_z = vp_z if self.is_vp_valid(vp_z) else []

        # VP2
        vp2_result: dict[str, float] = {}
        if vp_x and vp_z:
            vp2_result = self.solve_vp2(vp_x, vp_z, "XZ")

        elif vp_x and vp_y:
            vp2_result = self.solve_vp2(vp_x, vp_y, "XY")

        elif vp_y and vp_z:
            vp2_result = self.solve_vp2(vp_y, vp_z, "YZ")

        if vp2_result:
            return vp2_result

        # VP1
        if vp_x and len(z_lines) >= 2:
            return self.solve_vp1(vp_x, z_lines, "XZ", is_vp_primary=True)

        elif vp_z and len(x_lines) >= 2:
            return self.solve_vp1(vp_z, x_lines, "XZ", is_vp_primary=False)

        elif vp_y and len(x_lines) >= 2:
            return self.solve_vp1(vp_y, x_lines, "XY", is_vp_primary=False)

        elif vp_x and len(y_lines) >= 2:
            return self.solve_vp1(vp_x, y_lines, "XY", is_vp_primary=True)

        elif vp_y and len(z_lines) >= 2:
            return self.solve_vp1(vp_y, z_lines, "YZ", is_vp_primary=True)

        elif vp_z and len(y_lines) >= 2:
            return self.solve_vp1(vp_z, y_lines, "YZ", is_vp_primary=False)

        return {}

    def is_vp_valid(
        self,
        vp: list[float] | None,
        threshold_ratio: float = 100.0,
    ) -> bool:
        """Validates if the vanishing point is within an acceptable distance.

        Args:
            vp (list[float] | None): The vanishing point coordinates [x, y].
            threshold_ratio (float, optional): Maximum distance ratio relative
                to the image width. Defaults to 100.0.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not vp:
            return False

        dx: float = vp[0] - self.__cx
        dy: float = vp[1] - self.__cy
        dist: float = math.sqrt(dx * dx + dy * dy)
        if dist > self.__width * threshold_ratio:
            return False

        return True

    def solve_vp2(
        self,
        vp1: list[float],
        vp2: list[float],
        pair_mode: str,
    ) -> dict[str, float]:
        """Calculates true focal length using the orthogonality of two axes.

        Args:
            vp1 (list[float]): First vanishing point coordinates [x, y].
            vp2 (list[float]): Second vanishing point coordinates [x, y].
            pair_mode (str): The axis pair being used (e.g., 'XZ', 'XY').

        Returns:
            dict[str, float]: Calculated camera parameters.
        """

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
        vec_1: list[float] = maths.normalize([v1_x, v1_y, -f_pixel])
        vec_2: list[float] = maths.normalize([v2_x, v2_y, -f_pixel])

        rotate: list[float] = self.rotation_matrix(vec_1, vec_2, pair_mode)
        return self.__format_result(focal_length, rotate)

    def solve_vp1(
        self,
        vp: list[float],
        parallel_lines: list[list[float]],
        pair_mode: str,
        is_vp_primary: bool,
    ) -> dict[str, float]:
        """Estimates camera rotation using a single vanishing point.

        Focal length cannot be mathematically determined from 1 VP alone,
        so it defaults to 35.0mm.

        Args:
            vp (list[float]): The single valid vanishing point [x, y].
            parallel_lines (list[list[float]]): Lines that remain parallel.
            pair_mode (str): The axis pair being used.
            is_vp_primary (bool): Indicates if the VP belongs to the primary
                axis in the pair.

        Returns:
            dict[str, float]: Estimated camera parameters.
        """
        focal_length: float = 35.0
        f_pixel: float = (focal_length * self.__width) / self.__film_width

        # Vector towards the vanishing point.
        # (Optical Axis direction usually)
        vec_converge: list[float] = maths.normalize(
            [
                vp[0] - self.__cx,
                -(vp[1] - self.__cy),
                -f_pixel,
            ]
        )

        # Vector for lines that are parallel on screen.
        # (Perpendicular to Optical Axis)
        line_vec: list[float] = maths.average_direction(parallel_lines)
        vec_parallel: list[float] = maths.normalize(
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
        self,
        vec_1: list[float],
        vec_2: list[float],
        mode: str,
    ) -> list[float]:
        """Calculates a valid Maya Euler rotation from orthogonalized vectors.

        Args:
            vec_1 (list[float]): Primary axis vector.
            vec_2 (list[float]): Secondary axis vector.
            mode (str): The axis pair context (e.g., 'XZ', 'XY', 'YZ').

        Returns:
            list[float]: Euler rotation values in degrees [x, y, z].
        """
        cam_x: list[float] = [1, 0, 0]
        cam_y: list[float] = [0, 1, 0]
        cam_z: list[float] = [0, 0, 1]

        if mode == "XZ":
            # X(v1), Z(v2)
            # Fix Z (Depth), generate Y, then recalculate X.
            raw_x: list[float] = vec_1
            raw_z: list[float] = vec_2

            # Z x X = Y (Create temporary Y-axis)
            temp_y: list[float] = maths.normalize(
                maths.cross_product(raw_z, raw_x)
            )

            # Correct Y orientation (Y-up: Flip if pointing down)
            if temp_y[1] < 0:
                temp_y = [-temp_y[0], -temp_y[1], -temp_y[2]]

            # Fix Y and Z
            cam_y = temp_y
            cam_z = raw_z

            # Y x Z = X (X is now perfectly orthogonal)
            cam_x = maths.normalize(maths.cross_product(cam_y, cam_z))

        elif mode == "XY":
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
            cam_z = maths.normalize(maths.cross_product(raw_x, cam_y))

            # Y x Z = X (X is now perfectly orthogonal)
            cam_x = maths.normalize(maths.cross_product(cam_y, cam_z))

        elif mode == "YZ":
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
            cam_x = maths.normalize(maths.cross_product(cam_y, raw_z))

            # X x Y = Z (Z is now perfectly orthogonal)
            cam_z = maths.normalize(maths.cross_product(cam_x, cam_y))

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
        self, focal_length: float, rotation: list[float]
    ) -> dict[str, float]:
        """Formats the calculated parameters into a dictionary.

        Args:
            focal_length (float): The calculated focal length.
            rotation (list[float]): The calculated Euler rotation.

        Returns:
            dict[str, float]: Formatted dictionary.
        """
        return {
            "focal_length": round(focal_length, 1),
            "rotation_x": round(rotation[0], 3),
            "rotation_y": round(rotation[1], 3),
            "rotation_z": round(rotation[2], 3),
        }


class HandleItem(QtWidgets.QGraphicsEllipseItem):
    """Interactive handle item for manipulating guide lines."""

    def __init__(self, x: float, y: float, parent_line: GuideLineItem) -> None:
        """Initializes the instance.

        Args:
            x (float): Initial X position.
            y (float): Initial Y position.
            parent_line (GuideLineItem): The parent guide line instance.
        """
        super().__init__(-3, -3, 6, 6, parent_line)
        self.setPos(x, y)
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
        )
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )
        self.setBrush(QtGui.QBrush(QtGui.QColor(255, 170, 0)))
        self.setZValue(30)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.__parent_line: GuideLineItem = parent_line

    def itemChange(
        self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: str
    ) -> object:
        """Handles item state changes to update the parent line.

        Args:
            change (QtWidgets.QGraphicsItem.GraphicsItemChange): The change type.
            value (str): The new value.

        Returns:
            object: Processed change value.
        """
        if (
            change
            == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
            and self.__parent_line
        ):
            self.__parent_line.update_ui()

        return super().itemChange(change, value)


class GuideLineItem(QtWidgets.QGraphicsItem):
    """Smart line item representing an axis guide."""

    def __init__(
        self,
        line: QtCore.QLineF,
        axis: str = "X",
        view_ref: DrawingView | None = None,
    ) -> None:
        """Initializes the instance.

        Args:
            line (QtCore.QLineF): The initial geometry for the line.
            axis (str, optional): The assigned axis ('X', 'Y', or 'Z').
                Defaults to 'X'.
            view_ref (DrawingView | None, optional): Reference to the view.
                Defaults to None.
        """
        super().__init__()
        self.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True
        )

        self.__axis: str = axis
        self.__view_ref: DrawingView | None = view_ref
        self.__color: QtGui.QColor = self.__get_axis_color(axis)
        self.__guide_item: QtWidgets.QGraphicsLineItem = (
            self.__create_guide_line()
        )
        self.__line_item: QtWidgets.QGraphicsLineItem = (
            self.__create_main_line()
        )
        self.__handle1: HandleItem = self.__create_handle(line.p1())
        self.__handle2: HandleItem = self.__create_handle(line.p2())
        self.setHandlesChildEvents(False)
        self.update_ui()

    def boundingRect(self) -> QtCore.QRectF:
        """Overrides bounding rect to match the main line."""
        return self.__line_item.boundingRect()

    def shape(self) -> QtGui.QPainterPath:
        """Overrides shape to match the main line."""
        return self.__line_item.shape()

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:
        """Paint event override (handled by child items)."""

    def __get_axis_color(self, axis: str) -> QtGui.QColor:
        """Gets the visual color based on the assigned axis."""
        colors: dict[str, QtGui.QColor] = {
            "X": QtGui.QColor(255, 50, 50),
            "Y": QtGui.QColor(50, 255, 50),
            "Z": QtGui.QColor(80, 120, 255),
        }
        return colors.get(axis, QtGui.QColor(255, 255, 255))

    def __create_guide_line(self) -> QtWidgets.QGraphicsLineItem:
        """Creates the infinite background guide line."""
        pen: QtGui.QPen = QtGui.QPen(self.__color)
        pen.setWidth(1)
        pen.setCosmetic(True)

        item: QtWidgets.QGraphicsLineItem = QtWidgets.QGraphicsLineItem(self)
        item.setPen(pen)
        return item

    def __create_main_line(self) -> QtWidgets.QGraphicsLineItem:
        """Creates the interactive main line connecting the handles."""
        pen: QtGui.QPen = QtGui.QPen(self.__color)
        pen.setWidth(2)
        pen.setCosmetic(True)

        item: QtWidgets.QGraphicsLineItem = QtWidgets.QGraphicsLineItem(self)
        item.setPen(pen)
        item.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )
        return item

    def __create_handle(self, pos: QtCore.QPointF) -> HandleItem:
        """Creates a handle at the given position."""
        return HandleItem(pos.x(), pos.y(), self)

    def update_ui(self) -> None:
        """Updates internal positions based on handle movements."""
        self.prepareGeometryChange()
        p1: QtCore.QPointF = self.__handle1.scenePos()
        p2: QtCore.QPointF = self.__handle2.scenePos()
        local_p1: QtCore.QPointF = self.mapFromScene(p1)
        local_p2: QtCore.QPointF = self.mapFromScene(p2)
        self.__line_item.setLine(QtCore.QLineF(local_p1, local_p2))

        line_vec: QtCore.QPointF = local_p2 - local_p1
        length: float = math.hypot(line_vec.x(), line_vec.y())
        if length > 0:
            scale = 100000
            dx: float = (line_vec.x() / length) * scale
            dy: float = (line_vec.y() / length) * scale
            self.__guide_item.setLine(
                QtCore.QLineF(
                    local_p1.x() - dx,
                    local_p1.y() - dy,
                    local_p2.x() + dx,
                    local_p2.y() + dy,
                )
            )

        if self.__view_ref:
            self.__view_ref.update_ui()

    def remove_from_scene(self) -> None:
        """Safely removes this item from the current scene."""
        scene: QtWidgets.QGraphicsScene = self.scene()
        if scene:
            scene.removeItem(self)

    def line(self) -> QtCore.QLineF:
        """Retrieves the line geometry in scene coordinates."""
        return QtCore.QLineF(
            self.__handle1.scenePos(), self.__handle2.scenePos()
        )

    def axis(self) -> str:
        """Returns the assigned axis character."""
        return self.__axis

    def coordinates(self) -> list[float]:
        """Returns the explicit coordinates of both end points."""
        line: QtCore.QLineF = self.line()
        return [line.p1().x(), line.p1().y(), line.p2().x(), line.p2().y()]


class DrawingView(QtWidgets.QGraphicsView):
    """Custom view for handling user interactions and rendering."""

    lines_updated: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        scene: QtWidgets.QGraphicsScene,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the instance.

        Args:
            scene (QtWidgets.QGraphicsScene): The scene to manage.
            parent (QtWidgets.QWidget | None, optional): Parent widget.
        """
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setResizeAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )

        self.__is_zooming: bool = False
        self.__is_panning: bool = False
        self.__last_pos: QtCore.QPoint = QtCore.QPoint()

        self.__temp_line: QtWidgets.QGraphicsLineItem | None = None
        self.__start_pos: QtCore.QPointF = QtCore.QPointF()
        self.__current_axis_mode: str = "X"
        self.__lines: list[GuideLineItem] = []

        self.__vp_marker_x: QtWidgets.QGraphicsEllipseItem = (
            self.__create_vp_marker(QtGui.QColor(255, 50, 50))
        )
        self.__vp_marker_y: QtWidgets.QGraphicsEllipseItem = (
            self.__create_vp_marker(QtGui.QColor(50, 255, 50))
        )
        self.__vp_marker_z: QtWidgets.QGraphicsEllipseItem = (
            self.__create_vp_marker(QtGui.QColor(80, 120, 255))
        )

        h_pen: QtGui.QPen = QtGui.QPen(QtGui.QColor(0, 255, 255))
        h_pen.setWidth(2)
        h_pen.setCosmetic(True)

        self.__horizon_line = QtWidgets.QGraphicsLineItem()
        self.__horizon_line.setPen(h_pen)
        self.__horizon_line.setZValue(15)
        self.scene().addItem(self.__horizon_line)

        self.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing
            | QtGui.QPainter.RenderHint.SmoothPixmapTransform
        )
        self.update_ui()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse press events for zooming, panning, and drawing."""
        if event.modifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            if (
                event.button() == QtCore.Qt.MouseButton.MiddleButton
                or event.button() == QtCore.Qt.MouseButton.LeftButton
            ):
                self.__is_panning = True
                self.__last_pos = event.pos()
                self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return

            if event.button() == QtCore.Qt.MouseButton.RightButton:
                self.__is_zooming = True
                self.__last_pos = event.pos()
                self.setTransformationAnchor(
                    QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter
                )
                self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
                event.accept()
                return

        item: QtWidgets.QGraphicsItem = self.itemAt(event.pos())
        if isinstance(
            item, (HandleItem, QtWidgets.QGraphicsLineItem, GuideLineItem)
        ):
            super().mousePressEvent(event)
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.__start_pos = self.mapToScene(event.pos())

            pen: QtGui.QPen = QtGui.QPen(QtCore.Qt.GlobalColor.black)
            pen.setWidth(2)
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
            pen.setCosmetic(True)

            self.__temp_line = QtWidgets.QGraphicsLineItem(
                QtCore.QLineF(self.__start_pos, self.__start_pos)
            )
            self.__temp_line.setPen(pen)
            self.scene().addItem(self.__temp_line)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse move events for interaction logic."""
        delta: QtCore.QPoint = event.pos() - self.__last_pos
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
            current_pos: QtCore.QPointF = self.mapToScene(event.pos())
            line: QtCore.QLineF = self.__temp_line.line()
            line.setP2(current_pos)
            self.__temp_line.setLine(line)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse release events to finalize drawing."""
        if self.__is_panning or self.__is_zooming:
            self.__is_zooming = False
            self.__is_panning = False
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        if self.__temp_line:
            end_pos: QtCore.QPointF = self.mapToScene(event.pos())
            self.scene().removeItem(self.__temp_line)
            self.__temp_line = None
            if (end_pos - self.__start_pos).manhattanLength() > 10:
                line = GuideLineItem(
                    QtCore.QLineF(self.__start_pos, end_pos),
                    self.__current_axis_mode,
                    self,
                )
                self.add_line(line)

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Handles mouse wheel scrolling for zooming."""
        factor = 1.1
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1.0 / factor, 1.0 / factor)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handles key press events (e.g., deletion of lines)."""
        if (
            event.key() == QtCore.Qt.Key.Key_Delete
            or event.key() == QtCore.Qt.Key.Key_Backspace
        ):
            selected_items: list[QtWidgets.QGraphicsItem] = (
                self.scene().selectedItems()
            )
            changed: bool = False
            for item in selected_items:
                parent_item: QtWidgets.QGraphicsItem = item.parentItem()
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

    def __create_vp_marker(
        self, color: QtGui.QColor
    ) -> QtWidgets.QGraphicsEllipseItem:
        """Creates a hidden marker for a vanishing point."""
        marker = QtWidgets.QGraphicsEllipseItem(-6, -6, 12, 12)
        marker.setBrush(QtGui.QBrush(color))
        marker.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
        )
        marker.setZValue(25)
        marker.setVisible(False)
        self.scene().addItem(marker)
        return marker

    def __update_vp_marker(
        self,
        marker_item: QtWidgets.QGraphicsEllipseItem,
        lines: list[QtCore.QLineF],
    ) -> QtCore.QPointF | None:
        """Updates the visual position of a vanishing point marker."""
        if len(lines) < 2:
            marker_item.setVisible(False)
            return None

        line_list: list[list[float]] = [
            [ln.p1().x(), ln.p1().y(), ln.p2().x(), ln.p2().y()] for ln in lines
        ]
        position: list[float] = maths.average_intersection(line_list)
        if not position:
            marker_item.setVisible(False)
            return None

        point: QtCore.QPointF = QtCore.QPointF(*position)
        marker_item.setPos(point)
        marker_item.setVisible(True)
        return point

    def axis_mode(self) -> str:
        """Returns the current drawing axis mode."""
        return self.__current_axis_mode

    def set_axis_mode(self, axis: str) -> None:
        """Sets the drawing axis mode."""
        self.__current_axis_mode = axis

    def lines(self) -> list[GuideLineItem]:
        """Returns the list of active guide line items."""
        return self.__lines

    def add_line(self, line: GuideLineItem) -> None:
        """Adds a new line to the view and tracks it."""
        self.scene().addItem(line)
        self.__lines.append(line)
        self.update_ui()

    def update_ui(self) -> None:
        """Updates the rendering state, vanishing points, and horizon."""
        lines_x: list[QtCore.QLineF] = [
            line.line() for line in self.__lines if line.axis() == "X"
        ]
        lines_y: list[QtCore.QLineF] = [
            line.line() for line in self.__lines if line.axis() == "Y"
        ]
        lines_z: list[QtCore.QLineF] = [
            line.line() for line in self.__lines if line.axis() == "Z"
        ]
        vp_x: QtCore.QPointF | None = self.__update_vp_marker(
            self.__vp_marker_x, lines_x
        )
        self.__update_vp_marker(self.__vp_marker_y, lines_y)
        vp_z: QtCore.QPointF | None = self.__update_vp_marker(
            self.__vp_marker_z, lines_z
        )

        if vp_x and vp_z:
            self.__horizon_line.setVisible(True)
            diff: QtCore.QPointF = vp_z - vp_x
            scale = 100000
            length: float = math.sqrt(diff.x() ** 2 + diff.y() ** 2)
            if length > 0:
                dx: float = (diff.x() / length) * scale
                dy: float = (diff.y() / length) * scale
                self.__horizon_line.setLine(
                    QtCore.QLineF(
                        vp_x.x() - dx,
                        vp_x.y() - dy,
                        vp_z.x() + dx,
                        vp_z.y() + dy,
                    )
                )
        else:
            self.__horizon_line.setVisible(False)

        self.lines_updated.emit()


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Perspective Inspector tool."""

    SAVE_NODE_NAME: str = "amaterasuPerspectiveInspector"
    SAVE_ATTR_NAME: str = "saveData"

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
            unique_id (str, optional): Unique ID for restoring states.
        """
        self.__current_image_path: str = ""
        self.__bg_item: QtWidgets.QGraphicsPixmapItem | None = None
        self.__width: int = 1280
        self.__height: int = 720

        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(1200, 800)
        self.load_data_from_scene()

        self.__scene: QtWidgets.QGraphicsScene
        self.__view: DrawingView
        self.__opacity: QtWidgets.QSlider
        self.__focal_length: QtWidgets.QLineEdit
        self.__rotation_x: QtWidgets.QLineEdit
        self.__rotation_y: QtWidgets.QLineEdit
        self.__rotation_z: QtWidgets.QLineEdit

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget containing the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tool Layout
        tool_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(tool_layout)

        btn_open = QtWidgets.QPushButton("Open", parent)
        btn_open.clicked.connect(self.open_image_dialog)
        btn_open.setFixedWidth(50)
        tool_layout.addWidget(btn_open)

        btn_save = QtWidgets.QPushButton("Save", parent)
        btn_save.clicked.connect(self.save_data_to_scene)
        btn_save.setFixedWidth(50)
        tool_layout.addWidget(btn_save)

        tool_layout.addWidget(widgets.VerticalLine(parent))

        axis_group = QtWidgets.QButtonGroup(parent)

        btn_x = QtWidgets.QPushButton("X", parent)
        btn_x.setCheckable(True)
        btn_x.setChecked(True)
        btn_x.clicked.connect(lambda: self.set_mode("X"))
        btn_x.setFixedWidth(50)
        axis_group.addButton(btn_x)
        tool_layout.addWidget(btn_x)

        btn_y = QtWidgets.QPushButton("Y", parent)
        btn_y.setCheckable(True)
        btn_y.clicked.connect(lambda: self.set_mode("Y"))
        btn_y.setFixedWidth(50)
        axis_group.addButton(btn_y)
        tool_layout.addWidget(btn_y)

        btn_z = QtWidgets.QPushButton("Z", parent)
        btn_z.setCheckable(True)
        btn_z.clicked.connect(lambda: self.set_mode("Z"))
        btn_z.setFixedWidth(50)
        axis_group.addButton(btn_z)
        tool_layout.addWidget(btn_z)

        tool_layout.addWidget(widgets.VerticalLine(parent))

        btn_fit = QtWidgets.QPushButton("Fit View", parent)
        btn_fit.setFixedWidth(50)
        btn_fit.clicked.connect(self.fit_view)
        tool_layout.addWidget(btn_fit)

        tool_layout.addWidget(QtWidgets.QLabel("Opacity : ", parent))

        self.__opacity = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal, parent
        )
        self.__opacity.setRange(0, 100)
        self.__opacity.setValue(100)
        self.__opacity.setFixedWidth(100)
        self.__opacity.valueChanged.connect(self.change_opacity)
        tool_layout.addWidget(self.__opacity)

        tool_layout.addWidget(widgets.VerticalLine(parent))

        tool_layout.addWidget(QtWidgets.QLabel("Focal Length : ", parent))

        self.__focal_length = QtWidgets.QLineEdit(parent)
        self.__focal_length.setEnabled(False)
        tool_layout.addWidget(self.__focal_length)

        tool_layout.addWidget(QtWidgets.QLabel("Rotation : ", parent))

        self.__rotation_x = QtWidgets.QLineEdit(parent)
        self.__rotation_x.setEnabled(False)
        tool_layout.addWidget(self.__rotation_x)

        self.__rotation_y = QtWidgets.QLineEdit(parent)
        self.__rotation_y.setEnabled(False)
        tool_layout.addWidget(self.__rotation_y)

        self.__rotation_z = QtWidgets.QLineEdit(parent)
        self.__rotation_z.setEnabled(False)
        tool_layout.addWidget(self.__rotation_z)

        tool_layout.addStretch()

        btn_apply = QtWidgets.QPushButton("Apply", parent)
        btn_apply.setFixedWidth(50)
        btn_apply.clicked.connect(self.apply)
        tool_layout.addWidget(btn_apply)

        # Graphics View setup
        self.__scene = QtWidgets.QGraphicsScene(parent)
        self.__view = DrawingView(self.__scene, parent)
        main_layout.addWidget(self.__view)
        self.__view.lines_updated.connect(self.execute_solver_for_preview)

        # Settings Binding
        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    def open_image_dialog(self) -> None:
        """Opens a file dialog to load a background image."""
        result: tuple[str, str] = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if result[0]:
            self.load_image(result[0])

    def load_image(self, file_path: str) -> None:
        """Loads an image file into the viewport.

        Args:
            file_path (str): The absolute path to the image file.
        """
        pixmap = QtGui.QPixmap(file_path)
        if pixmap.isNull():
            return

        self.__current_image_path = file_path
        self.set_background_image(pixmap)
        if self.__bg_item:
            self.__view.fitInView(
                self.__bg_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )

    def set_background_image(self, pixmap: QtGui.QPixmap) -> None:
        """Applies a pixmap to the graphics scene background.

        Args:
            pixmap (QtGui.QPixmap): The pixmap to display.
        """
        if self.__bg_item:
            self.__scene.removeItem(self.__bg_item)

        self.__bg_item = self.__scene.addPixmap(pixmap)
        self.__bg_item.setZValue(-100)
        self.__bg_item.setFlag(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False
        )
        self.__bg_item.setOpacity(self.__opacity.value() / 100.0)
        self.__width = pixmap.width()
        self.__height = pixmap.height()
        margin: int = 100000
        rect: QtCore.QRectF = QtCore.QRectF(
            -margin,
            -margin,
            self.__width + margin * 2,
            self.__height + margin * 2,
        )
        self.__scene.setSceneRect(rect)
        self.execute_solver_for_preview()

    def fit_view(self) -> None:
        """Fits the viewport to frame the current background image."""
        if self.__bg_item:
            self.__view.fitInView(
                self.__bg_item, QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )
        else:
            self.__view.fitInView(
                0, 0, 1280, 720, QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )

    def change_opacity(self, value: int) -> None:
        """Adjusts the opacity of the background image.

        Args:
            value (int): Opacity percentage from 0 to 100.
        """
        if self.__bg_item:
            self.__bg_item.setOpacity(value / 100.0)

    def set_mode(self, mode: str) -> None:
        """Sets the axis context mode for drawing guide lines.

        Args:
            mode (str): Axis identifier ('X', 'Y', or 'Z').
        """
        self.__view.set_axis_mode(mode)

    def execute_solver_for_preview(self) -> None:
        """Runs the solver logic to preview parameters in the UI."""
        result: dict[str, float] = self.execute_solver()
        if not result:
            self.__focal_length.setText("")
            self.__rotation_x.setText("")
            self.__rotation_y.setText("")
            self.__rotation_z.setText("")
        else:
            self.__focal_length.setText(f"{result['focal_length']}")
            self.__rotation_x.setText(f"{result['rotation_x']}")
            self.__rotation_y.setText(f"{result['rotation_y']}")
            self.__rotation_z.setText(f"{result['rotation_z']}")

    def execute_solver(self) -> dict[str, float]:
        """Gathers lines from the view and runs the perspective solver.

        Returns:
            dict[str, float]: Calculated camera parameters.
        """
        x_lines: list[list[float]] = []
        y_lines: list[list[float]] = []
        z_lines: list[list[float]] = []

        for line in self.__view.lines():
            coords: list[float] = line.coordinates()
            if line.axis() == "X":
                x_lines.append(coords)
            elif line.axis() == "Y":
                y_lines.append(coords)
            else:
                z_lines.append(coords)

        if (len(x_lines) >= 2) + (len(y_lines) >= 2) + (len(z_lines) >= 2) < 2:
            return {}

        solver = PerspectiveSolver(self.__width, self.__height)
        return solver.solve(x_lines, y_lines, z_lines)

    @dcc.undo
    def apply(self) -> None:
        """Applies solver results to the active Maya camera."""
        self.save_settings()

        result: dict[str, float] = self.execute_solver()
        if not result:
            _logger.error(
                "Requires at least two axes, each with a minimum of two lines."
            )
            return

        apply_camera_transform(
            result["focal_length"],
            [result["rotation_x"], result["rotation_y"], result["rotation_z"]],
        )
        _logger.info("Done.")

    @dcc.undo
    def save_data_to_scene(self) -> None:
        """Serializes current lines and settings into the Maya scene."""
        lines_data: list[dict[str, object]] = []
        for line in self.__view.lines():
            lines_data.append(
                {"coords": line.coordinates(), "axis": line.axis()}
            )

        save_data: dict[str, object] = {
            "image_path": self.__current_image_path,
            "opacity": self.__opacity.value(),
            "lines": lines_data,
        }
        json_str: str = json.dumps(save_data)

        if not cmds.objExists(self.SAVE_NODE_NAME):
            cmds.createNode("network", name=self.SAVE_NODE_NAME)

        if not cmds.attributeQuery(
            self.SAVE_ATTR_NAME, node=self.SAVE_NODE_NAME, exists=True
        ):
            cmds.addAttr(
                self.SAVE_NODE_NAME,
                longName=self.SAVE_ATTR_NAME,
                dataType="string",
            )

        cmds.setAttr(
            f"{self.SAVE_NODE_NAME}.{self.SAVE_ATTR_NAME}",
            json_str,
            type="string",
        )
        _logger.info("Saved.")

    def load_data_from_scene(self) -> None:
        """Loads serialized settings and lines from the Maya scene."""
        if not cmds.objExists(self.SAVE_NODE_NAME) or not cmds.attributeQuery(
            self.SAVE_ATTR_NAME, node=self.SAVE_NODE_NAME, exists=True
        ):
            return

        try:
            attr_val = cmds.getAttr(
                f"{self.SAVE_NODE_NAME}.{self.SAVE_ATTR_NAME}"
            )
            data: dict[str, Any] = json.loads(attr_val)

        except (json.JSONDecodeError, TypeError):
            _logger.error("Failed to load data.")
            return

        image_path: str = str(data.get("image_path", ""))
        if not pathlib.Path(image_path).exists():
            _logger.error("Image path does not exist : %s", image_path)
            return

        self.load_image(image_path)
        self.__opacity.setValue(int(data.get("opacity", 100)))

        lines_data: list[dict[str, object]] = data.get("lines", [])  # type: ignore
        for l_data in lines_data:
            c: list[float] = l_data["coords"]  # type: ignore
            line = GuideLineItem(
                QtCore.QLineF(
                    QtCore.QPointF(c[0], c[1]), QtCore.QPointF(c[2], c[3])
                ),
                str(l_data["axis"]),
                self.__view,
            )
            self.__view.add_line(line)

        self.__view.update_ui()
        self.fit_view()
        _logger.info("Loaded save data.")


def apply_camera_transform(focal_length: float, rotation: list[float]) -> bool:
    """Applies the calculated focal length and rotation to the Maya scene.

    Args:
        focal_length (float): The calculated camera focal length.
        rotation (list[float]): Euler rotation values in degrees [x, y, z].

    Returns:
        bool: True on success.
    """
    selection: list[str] = cmds.ls(selection=True)
    target_camera: str = ""
    if selection:
        shapes: list[str] = (
            cmds.listRelatives(selection[0], shapes=True, fullPath=True) or []
        )
        if cmds.nodeType(selection[0]) == "camera":
            target_camera = selection[0]
        elif shapes and cmds.nodeType(shapes[0]) == "camera":
            target_camera = selection[0]

    if not target_camera:
        target_camera = cmds.camera(name="render_cam")[0]  # type: ignore
        target_camera = cmds.rename(target_camera, "render_cam")

    # cmds.setAttr(f'{target_camera}.horizontalFilmAperture', 1.417)
    # cmds.setAttr(f'{target_camera}.verticalFilmAperture', 0.945)
    # cmds.setAttr(f'{target_camera}.lensSqueezeRatio', 1.0)
    cmds.setAttr(f"{target_camera}.rotateOrder", 0)
    cmds.setAttr(f"{target_camera}.focalLength", focal_length)
    cmds.setAttr(f"{target_camera}.rotate", *rotation, type="double3")
    return True


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): Unique identifier for window instance.
    """
    window = MainWindow(unique_id=unique_id)
    window.show()
