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
"""Custom form label widget for Amaterasu.

This module provides the `FormLabel` class, a QLabel subclass
styled to resemble Maya's native UI labels, specifically designed
for use within QFormLayouts.
"""
from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets


class FormLabel(QtWidgets.QLabel):
    """A custom QLabel styled to resemble Maya's native form labels.

    Automatically appends a colon and space (": ") to the provided text
    and aligns it to the right with a fixed minimum width.
    """

    def __init__(
        self,
        text: str,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initialize the FormLabel widget.

        Args:
            text (str): The text to display on the label. A colon and space
                are automatically appended if the text is not empty.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        if text:
            text = f"{text} : "

        super().__init__(text, parent, flag)
        self.setMinimumWidth(70)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
