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
""""""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets


class DoubleRangeWidget(QtWidgets.QWidget):
    """"""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """"""
        super().__init__(parent, flag)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # layout.addWidget(QtWidgets.QLabel("Min :"))
        self.__min: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.__min.setRange(-999999, 999999)
        self.__min.setDecimals(5)
        self.__min.setMaximumWidth(80)
        layout.addWidget(self.__min)

        layout.addWidget(QtWidgets.QLabel(" - "))

        # layout.addWidget(QtWidgets.QLabel("Max :"))
        self.__max: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.__max.setRange(-999999, 999999)
        self.__max.setDecimals(5)
        self.__max.setMaximumWidth(80)
        layout.addWidget(self.__max)
        layout.addStretch(True)

    def min_value(self) -> float:
        """"""
        return self.__min.value()

    def set_min_value(self, value: float) -> None:
        """"""
        self.__min.setValue(value)

    def max_value(self) -> float:
        """"""
        return self.__max.value()

    def set_max_value(self, value: float) -> None:
        """"""
        self.__max.setValue(value)

    def range(self) -> list[float]:
        """"""
        return [self.__min.value(), self.__max.value()]

    def set_range(self, range_value: list[float]) -> None:
        """"""
        self.__min.setValue(range_value[0])
        self.__max.setValue(range_value[1])
