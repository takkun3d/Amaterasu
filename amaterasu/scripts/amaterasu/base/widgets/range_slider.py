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
"""Custom range slider widget for Amaterasu.

This module provides a specialized slider widget (RangeSlider) that allows users
to select an integer range with two handles. It is designed to be a reusable
base component for various Amaterasu tools.
"""
from __future__ import annotations
import enum
from amaterasu.base.qt import QtCore, QtGui, QtWidgets


class RangeSlider(QtWidgets.QWidget):
    """Integer Range Slider.

    Behaves like QSlider/QSpinBox but for selecting a range (low, high).

    Attributes:
        valueChanged (QtCore.Signal): Signal emitted when the low or
            high value changes.
            Emits (low_value, high_value).
    """

    class Handle(enum.IntEnum):
        """Enum representing the active handle of the slider."""

        NONE = 0
        LOW = 1
        HIGH = 2

    valueChanged: QtCore.Signal = QtCore.Signal(int, int)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the RangeSlider widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)
        self.setMinimumSize(100, 20)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

        self._minimum: int = 0
        self._maximum: int = 100
        self._low: int = 0
        self._high: int = 100

        self._handle_w: int = 10
        self._handle_h: int = 16
        self._active_handle: RangeSlider.Handle = RangeSlider.Handle.NONE

        self._bg_color: QtGui.QColor = QtGui.QColor(35, 35, 35)
        self._bar_color: QtGui.QColor = QtGui.QColor(96, 125, 139)
        self._handle_color: QtGui.QColor = QtGui.QColor(180, 180, 180)

    def minimum(self) -> int:
        """Get the minimum limit of the slider.

        Returns:
            int: The minimum limit value.
        """
        return self._minimum

    def maximum(self) -> int:
        """Get the maximum limit of the slider.

        Returns:
            int: The maximum limit value.
        """
        return self._maximum

    def low_value(self) -> int:
        """Get the current low value of the selected range.

        Returns:
            int: The current low value.
        """
        return self._low

    def high_value(self) -> int:
        """Get the current high value of the selected range.

        Returns:
            int: The current high value.
        """
        return self._high

    def set_minimum(self, val: int) -> None:
        """Set the minimum limit of the slider.

        Args:
            val (int): The new minimum limit value.
        """
        self._minimum = int(val)
        self.set_values(self._low, self._high)

    def set_maximum(self, val: int) -> None:
        """Set the maximum limit of the slider.

        Args:
            val (int): The new maximum limit value.
        """
        self._maximum = int(val)
        self.set_values(self._low, self._high)

    def set_range(self, min_val: int, max_val: int) -> None:
        """Set both the minimum and maximum limits of the slider.

        Args:
            min_val (int): The new minimum limit value.
            max_val (int): The new maximum limit value.
        """
        self._minimum = int(min_val)
        self._maximum = int(max_val)
        self.set_values(self._low, self._high)

    def set_values(self, low: int, high: int) -> None:
        """Set the current low and high values of the selected range.

        Args:
            low (int): The new low value.
            high (int): The new high value.
        """
        low = max(self._minimum, min(self._maximum, int(low)))
        high = max(self._minimum, min(self._maximum, int(high)))

        new_low: int = min(low, high)
        new_high: int = max(low, high)

        if self._low != new_low or self._high != new_high:
            self._low = new_low
            self._high = new_high
            self.update()
            self.valueChanged.emit(self._low, self._high)

    def set_bar_color(self, color: QtGui.QColor | tuple[int, int, int]) -> None:
        """Set the color of the selected range bar.

        Args:
            color (QtGui.QColor | tuple[int, int, int]): The color to set.
                Can be a QColor object or an RGB tuple.
        """
        self._bar_color = (
            QtGui.QColor(*color) if isinstance(color, tuple) else color
        )
        self.update()

    def _val_to_x(self, val: int) -> float:
        """Convert a slider value to an X-coordinate on the widget.

        Args:
            val (int): The slider value to convert.

        Returns:
            float: The corresponding X-coordinate.
        """
        margin: float = self._handle_w / 2.0
        w: float = self.width() - margin * 2.0
        if self._maximum <= self._minimum:
            return margin

        return (
            margin
            + float(val - self._minimum) / (self._maximum - self._minimum) * w
        )

    def _x_to_val(self, x: float) -> int:
        """Convert an X-coordinate on the widget to a slider value.

        Args:
            x (float): The X-coordinate to convert.

        Returns:
            int: The corresponding slider value.
        """
        margin: float = self._handle_w / 2.0
        w: float = self.width() - margin * 2.0
        if w <= 0:
            return self._minimum

        val: float = self._minimum + (x - margin) / w * (
            self._maximum - self._minimum
        )
        return max(self._minimum, min(self._maximum, int(round(val))))

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Paint the custom slider interface.

        Args:
            event (QtGui.QPaintEvent): The paint event parameters.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        y: float = self.height() / 2.0
        x_low: float = self._val_to_x(self._low)
        x_high: float = self._val_to_x(self._high)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(
            QtCore.QRectF(
                self._handle_w / 2, y - 2, self.width() - self._handle_w, 4
            ),
            2,
            2,
        )

        painter.setBrush(self._bar_color)
        painter.drawRoundedRect(
            QtCore.QRectF(x_low, y - 2, x_high - x_low, 4), 2, 2
        )

        painter.setBrush(self._handle_color)
        for x in [x_low, x_high]:
            rect = QtCore.QRectF(
                x - self._handle_w / 2,
                y - self._handle_h / 2,
                self._handle_w,
                self._handle_h,
            )
            painter.drawRoundedRect(rect, 2, 2)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse press events to activate a slider handle.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        x: float = event.x()
        dist_low: float = abs(x - self._val_to_x(self._low))
        dist_high: float = abs(x - self._val_to_x(self._high))

        self._active_handle = (
            RangeSlider.Handle.LOW
            if dist_low < dist_high
            else RangeSlider.Handle.HIGH
        )
        self._update_value_from_pos(x)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse move events to drag the active slider handle.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        if self._active_handle != RangeSlider.Handle.NONE:
            self._update_value_from_pos(event.x())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse release events to deactivate the slider handle.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        self._active_handle = RangeSlider.Handle.NONE

    def _update_value_from_pos(self, x: float) -> None:
        """Update the active handle's value based on the mouse X-coordinate.

        Args:
            x (float): The current X-coordinate of the mouse.
        """
        val: int = self._x_to_val(x)

        if self._active_handle == RangeSlider.Handle.LOW:
            self.set_values(val, self._high)

        elif self._active_handle == RangeSlider.Handle.HIGH:
            self.set_values(self._low, val)
