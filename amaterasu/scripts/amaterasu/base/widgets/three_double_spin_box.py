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
"""Three double spin box widget for Amaterasu.

This module provides the `ThreeDoubleSpinBox` class, a reusable UI component
that groups three `QDoubleSpinBox` widgets horizontally for editing 3D values
such as position, rotation, or scale.
"""

from __future__ import annotations

from amaterasu.base.qt import QtCore, QtWidgets


class ThreeDoubleSpinBox(QtWidgets.QWidget):
    """A widget containing three double spin boxes for X, Y, and Z values.

    Attributes:
        value_changed (QtCore.Signal): Signal emitted when any of the three
            values change, carrying the updated values as `list[float]`.
    """

    value_changed = QtCore.Signal(list)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the ThreeDoubleSpinBox widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowFlags | None, optional): Window flags for
                the widget. Defaults to None.
        """
        super().__init__(parent, flag)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__x: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.__x.setDecimals(5)
        self.__x.setRange(-99999.0, 99999.0)
        self.__x.setMinimumWidth(80)
        self.__x.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.__x.valueChanged.connect(self.__on_value_changed)
        layout.addWidget(self.__x)

        self.__y: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.__y.setDecimals(5)
        self.__y.setRange(-99999.0, 99999.0)
        self.__y.setMinimumWidth(80)
        self.__y.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.__y.valueChanged.connect(self.__on_value_changed)
        layout.addWidget(self.__y)

        self.__z: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.__z.setDecimals(5)
        self.__z.setRange(-99999.0, 99999.0)
        self.__z.setMinimumWidth(80)
        self.__z.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.__z.valueChanged.connect(self.__on_value_changed)
        layout.addWidget(self.__z)

    def __on_value_changed(self, _value: float) -> None:
        """Emit the value_changed signal when any spin box value changes.

        Args:
            _value (float): The updated value from the triggered spin box.
        """
        self.value_changed.emit(self.value())

    def value(self) -> list[float]:
        """Get the current values of the three spin boxes.

        Returns:
            list[float]: The current values as a list of floats [x, y, z].
        """
        return [self.__x.value(), self.__y.value(), self.__z.value()]

    def set_value(self, values: list[float]) -> None:
        """Set the X, Y, and Z values of the widget.

        Args:
            values (list[float]): A list of three floats representing [x, y, z].
        """
        old_values: list[float] = self.value()

        prev_x: bool = self.__x.blockSignals(True)
        prev_y: bool = self.__y.blockSignals(True)
        prev_z: bool = self.__z.blockSignals(True)

        self.__x.setValue(values[0])
        self.__y.setValue(values[1])
        self.__z.setValue(values[2])

        self.__x.blockSignals(prev_x)
        self.__y.blockSignals(prev_y)
        self.__z.blockSignals(prev_z)

        new_values: list[float] = self.value()
        if new_values != old_values:
            self.value_changed.emit(new_values)

    def set_decimals(self, decimals: int) -> None:
        """Set the number of decimal places for all spin boxes.

        Args:
            decimals (int): The number of decimal places to display.
        """
        self.__x.setDecimals(decimals)
        self.__y.setDecimals(decimals)
        self.__z.setDecimals(decimals)

    def set_range(self, min_value: float, max_value: float) -> None:
        """Set the minimum and maximum values for all spin boxes.

        Args:
            min_value (float): The minimum allowed value.
            max_value (float): The maximum allowed value.
        """
        self.__x.setRange(min_value, max_value)
        self.__y.setRange(min_value, max_value)
        self.__z.setRange(min_value, max_value)
