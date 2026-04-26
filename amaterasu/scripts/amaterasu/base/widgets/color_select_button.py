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
"""Color selection button widget for Amaterasu.

This module provides the `ColorSelectButton` class, an interactive color
button that opens a standard color dialog when clicked, allowing users
to pick and set a new color.
"""
from __future__ import annotations
from amaterasu.base.qt import QtGui, QtWidgets
from amaterasu.base.widgets.color_button import ColorButton


class ColorSelectButton(ColorButton):
    """A color button that opens a QColorDialog when clicked."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the ColorSelectButton widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
            Defaults to None.
        """
        super().__init__(parent)
        self.clicked.connect(self.show_dialog)

    def show_dialog(self) -> None:
        """Open a color dialog and update the button's color
        if a valid color is selected."""
        c: list[float] = self.color()
        color: QtGui.QColor = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)),
            self,
            'Select Color',
            QtWidgets.QColorDialog.ColorDialogOption.DontUseNativeDialog,
        )
        if color.isValid():
            self.set_color(color.redF(), color.greenF(), color.blueF())
