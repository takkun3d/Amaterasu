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
"""A custom PySide widget that mimics Maya's collapsible frame layout."""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtGui, QtWidgets


class FrameWidget(QtWidgets.QGroupBox):
    """A custom PySide group box acting as a Maya-style collapsible frame.

    This widget provides a custom paint event to draw a header with a
    collapsible triangle icon, mimicking the default Maya UI behavior.
    """

    def __init__(
        self,
        title: str = "",
        collapsed: bool = False,
        collapsible: bool = True,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the FrameWidget.

        Args:
            title (str): The title text displayed on the frame header.
            collapsed (bool): Whether the frame is initially collapsed.
            collapsible (bool): Whether the frame can be collapsed by the user.
            parent (QtWidgets.QWidget | None): The parent widget.
        """
        super().__init__(parent)
        self.setFlat(True)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 7, 0, 0)
        layout.setSpacing(0)
        # super().setLayout(layout)

        self.__widget: QtWidgets.QFrame = QtWidgets.QFrame(parent)
        self.__widget.setFrameShape(QtWidgets.QFrame.Shape.Panel)
        self.__widget.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.__widget.setLineWidth(0)
        layout.addWidget(self.__widget)

        self.__collapsed: bool = collapsed
        self.__collapsible: bool = collapsible
        self.__clicked = False

        self.setTitle(title)

    def layout(self) -> QtWidgets.QLayout:
        """Gets the layout of the internal frame widget.

        Returns:
            QtWidgets.QLayout: The layout assigned to the internal widget.
        """
        return self.__widget.layout()

    def setLayout(self, layout: QtWidgets.QLayout) -> None:
        """Sets the layout for the internal frame widget.

        Args:
            layout (QtWidgets.QLayout): The layout to set.
        """
        self.__widget.setLayout(layout)

    def setFrameShape(self, shape: QtWidgets.QFrame.Shape) -> None:
        """Sets the frame shape of the internal widget.

        Args:
            shape (QtWidgets.QFrame.Shape): The frame shape to apply.
        """
        self.__widget.setFrameShape(shape)

    def setFrameShadow(self, shadow: QtWidgets.QFrame.Shadow) -> None:
        """Sets the frame shadow of the internal widget.

        Args:
            shadow (QtWidgets.QFrame.Shadow): The frame shadow to apply.
        """
        self.__widget.setFrameShadow(shadow)

    def setLineWidth(self, width: int) -> None:
        """Sets the line width of the internal widget.

        Args:
            width (int): The line width to apply.
        """
        self.__widget.setLineWidth(width)

    def expand_collapse_rect(self) -> QtCore.QRect:
        """Calculates the rectangle area used for the expand/collapse toggle.

        Returns:
            QtCore.QRect: The clickable area for toggling the frame.
        """
        return QtCore.QRect(0, 0, self.width(), 20)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse release events to toggle the collapsed state.

        Args:
            event (QtGui.QMouseEvent): The mouse event object.
        """
        if self.__clicked and self.expand_collapse_rect().contains(event.pos()):
            self.toggle_collapsed()
            event.accept()
        else:
            event.ignore()

        self.__clicked = False

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse press events for the collapsible header.

        Args:
            event (QtGui.QMouseEvent): The mouse event object.
        """
        if (
            event.button() == QtCore.Qt.MouseButton.LeftButton
            and self.expand_collapse_rect().contains(event.pos())
        ):
            self.__clicked = True
            event.accept()

        else:
            self.__clicked = False
            event.ignore()

    def is_collapsed(self) -> bool:
        """Checks if the frame is currently collapsed.

        Returns:
            bool: True if the frame is collapsed, False otherwise.
        """
        return self.__collapsed

    def is_collapsible(self) -> bool:
        """Checks if the frame is allowed to be collapsed.

        Returns:
            bool: True if the frame is collapsible, False otherwise.
        """
        return self.__collapsible

    def __draw_triangle(self, painter: QtGui.QPainter, x: int, y: int) -> None:
        """Draws the expand/collapse triangle icon on the header.

        Args:
            painter (QtGui.QPainter): The painter object used for drawing.
            x (int): The x-coordinate for the triangle.
            y (int): The y-coordinate for the triangle.
        """
        color: QtGui.QColor = QtGui.QColor(255, 255, 255, 160)
        if not self.is_collapsed():
            points: list[QtCore.QPoint] = [
                QtCore.QPoint(x + 10, y + 6),
                QtCore.QPoint(x + 20, y + 6),
                QtCore.QPoint(x + 15, y + 11),
            ]

        else:
            points = [
                QtCore.QPoint(x + 10, y + 4),
                QtCore.QPoint(x + 15, y + 9),
                QtCore.QPoint(x + 10, y + 14),
            ]

        current_brush: QtGui.QBrush = painter.brush()
        current_pen: QtGui.QPen = painter.pen()

        painter.setBrush(QtGui.QBrush(color, QtCore.Qt.BrushStyle.SolidPattern))
        painter.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        painter.drawPolygon(QtGui.QPolygon(points))
        painter.setBrush(current_brush)
        painter.setPen(current_pen)

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        """Paints the custom frame header and background.

        Args:
            event (QtGui.QPaintEvent): The paint event object.
        """
        painter: QtGui.QPainter = QtGui.QPainter()
        painter.begin(self)

        font: QtGui.QFont = painter.font()
        font.setBold(True)
        painter.setFont(font)

        x: int = self.rect().x()
        y: int = self.rect().y()
        w: int = self.rect().width() - 1
        offset = 10
        if self.__collapsible:
            offset = 25

        header_height: int = 20
        header_rect: QtCore.QRect = QtCore.QRect(x, y, w, header_height)

        # Base
        painter.fillRect(header_rect, QtGui.QColor(93, 93, 93))
        painter.drawText(
            x + offset,
            y + 3,
            w,
            16,
            (
                QtCore.Qt.AlignmentFlag.AlignLeft
                | QtCore.Qt.AlignmentFlag.AlignTop
            ),
            self.title(),
        )
        if self.__collapsible:
            self.__draw_triangle(painter, x, y)

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)
        painter.end()

    def set_collapsed(self, state: bool = True) -> None:
        """Sets the collapsed state of the frame.

        Args:
            state (bool): True to collapse the frame, False to expand it.
        """
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
        """Sets whether the frame can be collapsed by the user.

        Args:
            state (bool): True to allow collapsing, False to prevent it.
        """
        self.__collapsible = state

    def toggle_collapsed(self) -> None:
        """Toggles the current collapsed state of the frame."""
        self.set_collapsed(not self.is_collapsed())

    def widget(self) -> QtWidgets.QWidget:
        """Gets the internal widget that holds the layout and contents.

        Returns:
            QtWidgets.QWidget: The internal frame widget.
        """
        return self.__widget
