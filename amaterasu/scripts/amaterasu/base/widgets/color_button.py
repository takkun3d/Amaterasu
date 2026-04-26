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
"""Color button widget for Amaterasu.

This module provides the `ColorButton` class, a reusable UI component
that displays a specific solid color as its background.
"""
from __future__ import annotations
from amaterasu.base.qt import QtWidgets

COLOR_BUTTON_QSS: str = """
QPushButton#%s{
	border:none;
	background-color:rgb(%s, %s, %s);
}
QPushButton#%s:disabled{
	background-color:rgba(%s, %s, %s, 0.4);
}
"""


class ColorButton(QtWidgets.QPushButton):
    """A button that displays a specific solid color."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the ColorButton widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__color: list[float] = [0.0, 0.275, 0.098]

        self.setObjectName(f"ColorButton{str(id(self))}")
        self.set_color(*self.__color)

    def set_color(self, r: float, g: float, b: float) -> None:
        """Set the background color of the button.

        Args:
            r (float): Red value (0.0 - 1.0).
            g (float): Green value (0.0 - 1.0).
            b (float): Blue value (0.0 - 1.0).
        """
        self.__color = [r, g, b]
        self.setStyleSheet(
            COLOR_BUTTON_QSS
            % (
                self.objectName(),
                r * 255,
                g * 255,
                b * 255,
                self.objectName(),
                r * 255,
                g * 255,
                b * 255,
            )
        )

    def color(self) -> list[float]:
        """Get the current color of the button.

        Returns:
            list[float]: The current RGB color as a list of floats [r, g, b].
        """
        return self.__color
