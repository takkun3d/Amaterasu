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
"""Provides custom PySide widgets for building standardized tool interfaces.

This module contains reusable UI components, such as actionable checkboxes,
to ensure a consistent user experience across the Amaterasu framework.
"""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets


class ActionableCheckBox(QtWidgets.QWidget):
    """A custom widget combining a checkbox and an execution button."""

    clicked = QtCore.Signal()

    def __init__(
        self,
        label: str = "",
        button_label: str = "",
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the ActionableCheckBox widget.

        Args:
            label (str, optional): The text for the checkbox label. Defaults
                to "".
            button_label (str, optional): The text for the execution button.
                Defaults to "".
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flags (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__check: QtWidgets.QCheckBox = QtWidgets.QCheckBox(label, self)
        layout.addWidget(self.__check, True)

        self.__apply: QtWidgets.QPushButton = QtWidgets.QPushButton(
            button_label, self
        )
        self.__apply.setMinimumWidth(80)
        self.__apply.clicked.connect(self.clicked)
        layout.addWidget(self.__apply, False)

    def set_label_text(self, text: str) -> None:
        """Sets the text for the checkbox label.

        Args:
            text (str): The label text to set.
        """
        self.__check.setText(text)

    def set_button_text(self, text: str) -> None:
        """Sets the text for the execution button.

        Args:
            text (str): The button text to set.
        """
        self.__apply.setText(text)

    def set_checked(self, value: bool) -> None:
        """Sets the checked state of the checkbox.

        Args:
            value (bool): True to check, False to uncheck.
        """
        self.__check.setChecked(value)

    def is_checked(self) -> bool:
        """Returns the current checked state.

        Returns:
            bool: True if checked, False otherwise.
        """
        return self.__check.isChecked()
