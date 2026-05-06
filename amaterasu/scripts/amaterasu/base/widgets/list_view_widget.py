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
"""Custom ListWidget with placeholder text support."""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets, QtGui


class ListWidget(QtWidgets.QListWidget):
    """A QListWidget that displays a placeholder text when empty."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the ListWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__placeholder_text: str = ""

    def set_placeholder_text(self, text: str) -> None:
        """Sets the placeholder text to display when the list is empty.

        Args:
            text (str): The text to display.
        """
        self.__placeholder_text = text
        self.viewport().update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Overrides paintEvent to draw the placeholder text.

        Args:
            event (QtGui.QPaintEvent): The paint event.
        """
        super().paintEvent(event)

        if self.count() == 0 and self.__placeholder_text:
            painter = QtGui.QPainter(self.viewport())
            color: QtGui.QColor = self.palette().color(
                QtGui.QPalette.ColorRole.PlaceholderText
            )
            painter.setPen(color)
            painter.drawText(
                self.viewport().rect(),
                (
                    QtCore.Qt.AlignmentFlag.AlignCenter
                    | QtCore.Qt.TextFlag.TextWordWrap
                ),
                self.__placeholder_text,
            )
            painter.end()
