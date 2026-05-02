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
"""Generic graphical user interface widgets for Amaterasu.

This module provides reusable UI components designed to be used across
various Amaterasu tools. Widgets defined here, such as `IndexColorGrid`,
are intended to be pure UI elements. They rely on Qt signals to communicate
user interactions and strictly avoid containing Maya-specific business logic,
ensuring maximum reusability and clean MVC architecture.
"""

from __future__ import annotations
import functools
from maya import cmds
from amaterasu.base import dcc
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base.widgets.color_button import ColorButton
from amaterasu.base.widgets.icon_button import IconButton


class IndexColorPalette(QtWidgets.QWidget):
    """A generic widget displaying a grid of Maya index colors (0-31).

    This widget provides a 32-color grid including a trash icon at index 0.
    It emits the selected color index as an integer when any button is clicked,
    acting as a pure UI component devoid of direct Maya modification logic.
    """

    index_selected: QtCore.Signal = QtCore.Signal(int)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the IndexColorGrid.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        for i in range(32):
            row: int
            col: int
            row, col = divmod(i, 8)

            button: QtWidgets.QPushButton
            if i == 0:
                button = IconButton(self)
                button.set_icon(dcc.get_icon_path("a_trash.png"))
                button.setFixedSize(QtCore.QSize(24, 24))

            else:
                color: list[float] = cmds.colorIndex(i, query=True)  # type: ignore
                button = ColorButton(self)
                button.set_color(color)
                button.setFixedSize(QtCore.QSize(24, 24))

            button.clicked.connect(
                functools.partial(self.index_selected.emit, i)
            )
            main_layout.addWidget(button, row, col)

        main_layout.setRowStretch(4, 1)
        main_layout.setColumnStretch(8, 1)
