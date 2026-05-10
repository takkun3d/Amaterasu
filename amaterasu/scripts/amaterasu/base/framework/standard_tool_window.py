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
    ('Apply & Close', 'Apply', 'Close'). Subclasses only need to implement
    `create_ui` to build the custom options and `apply` for execution logic.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the StandardToolWindow.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Widget.
            unique_id (str, optional): A unique identifier for the widget.
                Defaults to "".
        """
        super().__init__(parent=parent, flag=flag, unique_id=unique_id)

    def create_framework_ui(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Overrides the framework UI build process to add a scroll area and buttons.

        This method injects a scrollable container for the tool options and
        appends the standard execution buttons ('Apply & Close', 'Apply', 'Close')
        at the bottom of the provided layout. It then delegates the internal UI
        construction to `create_ui`.

        Args:
            layout (QtWidgets.QVBoxLayout): The parent layout where the scroll
                area and buttons should be added.
        """
        layout.setSpacing(8)

        sub_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        sub_layout.setContentsMargins(10, 0, 10, 10)
        layout.addLayout(sub_layout)

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        scroll_area.setMinimumHeight(1)
        sub_layout.addWidget(scroll_area, 1, 0, 1, 3)

        option_widget: QtWidgets.QWidget = QtWidgets.QWidget(scroll_area)
        scroll_area.setWidget(option_widget)

        self.create_ui(option_widget)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply && Close", self
        )
        button.clicked.connect(self.apply_close)
        sub_layout.addWidget(button, 2, 0)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply)
        sub_layout.addWidget(button, 2, 1)

        button = QtWidgets.QPushButton("Close", self)
        button.clicked.connect(self.close)
        sub_layout.addWidget(button, 2, 2)

    @abc.abstractmethod
    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        This abstract method must be implemented by subclasses to build and
        layout their custom UI components within the main option area.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
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
