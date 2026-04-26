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
"""Icon button widget for Amaterasu.

This module provides the `IconButton` class, an image-based button
that supports different icons for default, hover, and pressed states,
as well as a custom signal for right-click detection.
"""
from __future__ import annotations
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base.dcc import paths


class IconButton(QtWidgets.QPushButton):
    """A button that displays an icon and supports state-based icon switching.

    Attributes:
        right_clicked (QtCore.Signal): Signal emitted when the button is right-clicked.
    """

    right_clicked: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the IconButton widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.__default_icon: QtGui.QIcon | None = None
        self.__hover_icon: QtGui.QIcon | None = None
        self.__pressed_icon: QtGui.QIcon | None = None

        self.setFlat(True)
        self.setStyleSheet('QPushButton:pressed{padding:0;}')

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle the mouse press event to display the pressed icon.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        super().mousePressEvent(event)
        if self.__pressed_icon:
            self.setIcon(self.__pressed_icon)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle the mouse release event to restore the default icon and detect right-clicks.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        super().mouseReleaseEvent(event)
        if self.__default_icon:
            self.setIcon(self.__default_icon)

        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.right_clicked.emit()

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        """Handle the mouse enter event to display the hover icon.

        Args:
            event (QtGui.QEnterEvent): The enter event parameters.
        """
        super().enterEvent(event)
        if self.__hover_icon:
            self.setIcon(self.__hover_icon)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Handle the mouse leave event to restore the default icon.

        Args:
            event (QtCore.QEvent): The leave event parameters.
        """
        super().leaveEvent(event)
        if self.__default_icon:
            self.setIcon(self.__default_icon)

    def setIconSize(self, size: QtCore.QSize) -> None:
        """Set the icon size and lock the button's fixed size to match.

        Args:
            size (QtCore.QSize): The target size for the icon and the button.
        """
        super().setIconSize(size)
        super().setFixedSize(size)

    def set_icon(self, icon: str) -> None:
        """Set the default icon for the button from a file name.

        Args:
            icon (str): The file name of the default icon (e.g., "icon.png").
        """
        self.__default_icon = QtGui.QIcon(paths.get_icon_path(icon))
        super().setIcon(self.__default_icon)

    def set_hover_icon(self, icon: str) -> None:
        """Set the icon to display when the mouse hovers over the button.

        Args:
            icon (str): The file name of the hover icon.
        """
        self.__hover_icon = QtGui.QIcon(paths.get_icon_path(icon))

    def set_pressed_icon(self, icon: str) -> None:
        """Set the icon to display when the button is pressed.

        Args:
            icon (str): The file name of the pressed icon.
        """
        self.__pressed_icon = QtGui.QIcon(paths.get_icon_path(icon))
        self.setStyleSheet('QPushButton:pressed{border:none; padding:0;}')
