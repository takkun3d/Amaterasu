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
"""Standard tool widget with execution buttons for Amaterasu.

This module provides the `StandardToolWindow` abstract base class.
Unlike the basic `ToolWindow`, this class includes a built-in scroll
area for options and standard execution buttons ('Apply & Close',
'Apply', 'Close') at the bottom of the window. It is ideal for tools
that require user input followed by a specific execution action.
"""
from __future__ import annotations
from typing import TypeVar, Generic
import abc
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base.framework import tool_window, settings

T = TypeVar("T", bound=settings.ToolSettings)


class StandardToolWindow(
    tool_window.ToolWindow[T],
    Generic[T],
):
    """Template for standard tools requiring execution buttons.

    This class extends `ToolWindow` to provide a standardized layout
    featuring a scrollable option area and three standard action buttons
    ('Apply & Close', 'Apply', 'Close'). Subclasses must implement
    `create_tool_ui` and `apply` execution logic.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the StandardToolWindow with layout and standard buttons.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Widget.
            unique_id (str, optional): A unique identifier for the widget.
                Defaults to "".
        """
        super().__init__(parent=parent, flag=flag, unique_id=unique_id)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the standard layout with scroll area and buttons.

        Note: Subclasses should NOT override this method. Instead,
        implement `create_tool_ui` to build custom UI elements.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        self.__scroll: QtWidgets.QScrollArea = QtWidgets.QScrollArea(parent)
        self.__scroll.setWidgetResizable(True)
        self.__scroll.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.__scroll.setMinimumHeight(1)
        main_layout.addWidget(self.__scroll, 1)

        self.__tool_option_widget: QtWidgets.QWidget = QtWidgets.QWidget(
            self.__scroll
        )
        self.__scroll.setWidget(self.__tool_option_widget)

        self.create_tool_ui(self.__tool_option_widget)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(button_layout)

        self.__apply_close: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply && Close", parent
        )
        self.__apply_close.clicked.connect(self.apply_close)
        button_layout.addWidget(self.__apply_close)

        self.__apply: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply", parent
        )
        self.__apply.clicked.connect(self.apply)
        button_layout.addWidget(self.__apply)

        self.__close: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Close", parent
        )
        self.__close.clicked.connect(self.close)
        button_layout.addWidget(self.__close)

    @abc.abstractmethod
    def create_tool_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        This abstract method must be implemented by subclasses to build and
        layout their custom UI components within the scroll area.

        Args:
            parent (QtWidgets.QWidget): The container widget where the
                custom UI elements should be added.
        """

    @abc.abstractmethod
    @QtCore.Slot()
    def apply(self) -> None:
        """Executes the main functionality of the tool.

        This abstract method must be implemented by subclasses to define
        what happens when the user clicks the 'Apply' button.
        """

    @QtCore.Slot()
    def apply_close(self) -> None:
        """Executes the tool's main functionality and then closes the widget."""
        self.apply()
        self.close()

    # def scroll_widget(self) -> QtWidgets.QScrollArea:
    #     """Gets the main scroll area widget.

    #     Returns:
    #         QtWidgets.QScrollArea: The scroll area instance.
    #     """
    #     return self.__scroll

    # def tool_option_widget(self) -> QtWidgets.QWidget:
    #     """Gets the central widget container inside the scroll area.

    #     Returns:
    #         QtWidgets.QWidget: The container widget for tool-specific options.
    #     """
    #     return self.__tool_option_widget

    # def apply_close_button(self) -> QtWidgets.QPushButton:
    #     """Gets the 'Apply & Close' button widget.

    #     Returns:
    #         QtWidgets.QPushButton: The 'Apply & Close' button instance.
    #     """
    #     return self.__apply_close

    # def apply_button(self) -> QtWidgets.QPushButton:
    #     """Gets the 'Apply' button widget.

    #     Returns:
    #         QtWidgets.QPushButton: The 'Apply' button instance.
    #     """
    #     return self.__apply

    # def close_button(self) -> QtWidgets.QPushButton:
    #     """Gets the 'Close' button widget.

    #     Returns:
    #         QtWidgets.QPushButton: The 'Close' button instance.
    #     """
    #     return self.__close
