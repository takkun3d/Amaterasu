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
"""Color palette widget for Amaterasu.

This module provides the `ColorPalette` class, a reusable UI component
that displays a grid of color buttons, allowing users to select from a
predefined or custom list of colors.
"""

from __future__ import annotations
from typing import cast
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import widgets


class ColorPalette(QtWidgets.QWidget):
    """A grid widget displaying a palette of color buttons.

    Attributes:
        clicked (QtCore.Signal): Signal emitted when a color button is clicked.
            Passes the selected RGB color as a list of floats.
        default_colors (list[list[float]]): The default list of RGB colors used
            if no custom colors are provided.
    """

    clicked: QtCore.Signal = QtCore.Signal(list)
    default_colors: list[list[float]] = [
        [0.99, 0.36, 0.38],  # 01. Red
        [1.00, 0.29, 0.57],  # 02. Rose
        [0.90, 0.30, 0.90],  # 03. Magenta
        [0.56, 0.33, 0.97],  # 04. Purple
        [0.34, 0.42, 0.98],  # 05. Blue-Purple
        [0.27, 0.57, 0.99],  # 06. Blue
        [0.26, 0.76, 0.99],  # 07. Sky Blue
        [0.20, 0.94, 0.98],  # 08. Cyan
        [0.25, 0.98, 0.78],  # 09. Aquamarine
        [0.36, 0.98, 0.58],  # 10. Mint
        [0.52, 0.98, 0.38],  # 11. Light Green
        [0.75, 0.99, 0.27],  # 12. Lime
        [0.96, 1.00, 0.25],  # 13. Yellow
        [1.00, 0.83, 0.27],  # 14. Golden Yellow
        [1.00, 0.63, 0.34],  # 15. Orange
        [1.00, 0.43, 0.36],  # 16. Red-Orange
    ]

    def __init__(
        self,
        colors: list[list[float]] | None = None,
        max_columns: int = 8,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize the ColorPalette widget.

        Args:
            colors (list[list[float]] | None, optional): A list of RGB colors to display.
                Defaults to None (uses default_colors).
            max_columns (int, optional): The maximum number of columns in the grid layout.
                Defaults to 8.
            parent (QtWidgets.QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        if colors is None:
            colors = self.default_colors

        self.__layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        self.__layout.setSpacing(2)
        self.__layout.setContentsMargins(0, 0, 0, 0)

        self.__buttons: list[widgets.ColorButton] = []
        self.__max_columns: int = max_columns
        self.__create_color_buttons(colors)

    def __create_color_buttons(self, colors: list[list[float]]) -> None:
        """Create and arrange color buttons in the grid layout.

        Args:
            colors (list[list[float]]): A list of RGB colors to populate the palette.
        """
        for i, rgb in enumerate(colors):
            button: widgets.ColorButton = widgets.ColorButton(self)
            button.set_color(rgb)
            button.clicked.connect(self.__on_color_selected)

            row: int = i // self.__max_columns
            colmum: int = i % self.__max_columns
            self.__layout.addWidget(button, row, colmum)
            self.__buttons.append(button)

    def __on_color_selected(self) -> None:
        """Handle color button clicks and emit the selected color."""
        button: widgets.ColorButton = cast(widgets.ColorButton, self.sender())
        self.clicked.emit(button.color())

    def set_color(self, index: int, color: list[float]) -> None:
        """Set the color of a specific button in the palette by its index.

        Args:
            index (int): The index of the button to update.
            color (list[float]): The new RGB color to set as [r, g, b].
        """
        self.__buttons[index].set_color(color)

    def set_colors(self, colors: list[list[float]]) -> None:
        """Rebuild the entire palette with a new set of colors.

        Args:
            colors (list[list[float]]): The new list of RGB colors to display.
        """
        for button in self.__buttons:
            button.deleteLater()
        self.__buttons = []
        self.__create_color_buttons(colors)

    def colors(self) -> list[list[float]]:
        """Get all colors currently available in the palette.

        Returns:
            list[list[float]]: A list containing the RGB colors of all buttons in the palette.
        """
        return [x.color() for x in self.__buttons]
