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
Unlike the basic `ToolWidget`, this class includes a built-in scroll
area for options and standard execution buttons ('Apply & Close',
'Apply', 'Close') at the bottom of the window. It is ideal for tools
that require user input followed by a specific execution action.
"""
from __future__ import annotations
import abc
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base.framework import workspace_control


class StandardToolWindow(
    workspace_control.WorkspaceControlWindow,
    abc.ABC,
    metaclass=workspace_control.QWidgetABCMeta,
):
    """Template for standard tools requiring execution buttons.

    This class extends `BaseToolWidget` to provide a standardized layout
    featuring a menu bar, a scrollable option area, and three standard
    action buttons ('Apply & Close', 'Apply', 'Close'). Subclasses must
    implement the core UI construction and execution logic.
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
                Defaults to ''.
        """
        super().__init__(parent=parent, flag=flag, unique_id=unique_id)

        self.__main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)

        self.create_menu()

        sub_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        sub_layout.setContentsMargins(10, 0, 10, 10)
        self.__main_layout.addLayout(sub_layout)

        self.__scroll: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        self.__scroll.setWidgetResizable(True)
        self.__scroll.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.__scroll.setMinimumHeight(1)
        sub_layout.addWidget(self.__scroll, 1, 0, 1, 3)

        self.__option_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        self.__scroll.setWidget(self.__option_widget)

        self.create_ui(self.__option_widget)

        self.__apply_close: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply && Close", self
        )
        self.__apply_close.clicked.connect(self.apply_close)
        sub_layout.addWidget(self.__apply_close, 2, 0)

        self.__apply: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply", self
        )
        self.__apply.clicked.connect(self.apply)
        sub_layout.addWidget(self.__apply, 2, 1)

        self.__close: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Close", self
        )
        self.__close.clicked.connect(self.close)
        sub_layout.addWidget(self.__close, 2, 2)

    def create_menu(self) -> None:
        """Creates the standard menu bar including 'File' and 'Help' menus.

        This method builds the base menus and triggers `create_custom_menu`
        to allow subclasses to inject their own specific menus.
        """
        self.__menu_bar: QtWidgets.QMenuBar = QtWidgets.QMenuBar(self)
        self.__main_layout.addWidget(self.__menu_bar)

        self.__file_menu: QtWidgets.QMenu = QtWidgets.QMenu("File", self)
        self.__menu_bar.addMenu(self.__file_menu)

        action: QtGui.QAction = self.__file_menu.addAction("Save Settings")
        action.triggered.connect(self.save_settings)

        action = self.__file_menu.addAction("Reset Settings")
        action.triggered.connect(self.reset_settings)

        self.__file_menu.addSeparator()

        action = self.__file_menu.addAction("Exit")
        action.triggered.connect(self.close)

        self.create_custom_menu(self.__menu_bar)

        self.__help_menu: QtWidgets.QMenu = QtWidgets.QMenu("Help", self)
        self.__menu_bar.addMenu(self.__help_menu)

        action: QtGui.QAction = self.__help_menu.addAction("About")
        action.triggered.connect(self.about)

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates custom menus to be added between 'File' and 'Help'.

        This method is intended to be overridden by subclasses that require
        additional, tool-specific menus in the menu bar. By default, it does
        nothing.

        Args:
            menu_bar (QtWidgets.QMenuBar): The main menu bar widget where
                the custom menus should be added.
        """

    @abc.abstractmethod
    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        This abstract method must be implemented by subclasses to build and
        layout their custom UI components within the main option area.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
                custom UI elements should be added.
        """

    def close(self) -> bool:
        """Closes the widget and saves current settings.

        Returns:
            bool: True if the widget was successfully closed, False otherwise.
        """
        self.save_settings()
        return super().close()

    def show(self) -> None:
        """Shows the widget and loads saved settings."""
        self.load_settings()
        super().show()

    @abc.abstractmethod
    def load_settings(self) -> None:
        """Loads tool-specific settings from a configuration file."""

    @abc.abstractmethod
    @QtCore.Slot()
    def save_settings(self) -> None:
        """Saves the current tool settings to a configuration file."""

    @abc.abstractmethod
    @QtCore.Slot()
    def reset_settings(self) -> None:
        """Resets the tool settings to their default values."""

    @abc.abstractmethod
    @QtCore.Slot()
    def about(self) -> None:
        """Shows the 'About' dialog for the tool."""

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

    def scroll_widget(self) -> QtWidgets.QScrollArea:
        """Gets the main scroll area widget.

        Returns:
            QtWidgets.QScrollArea: The scroll area instance.
        """
        return self.__scroll

    def option_widget(self) -> QtWidgets.QWidget:
        """Gets the central widget container inside the scroll area.

        Returns:
            QtWidgets.QWidget: The container widget for tool-specific options.
        """
        return self.__option_widget

    def apply_close_button(self) -> QtWidgets.QPushButton:
        """Gets the 'Apply & Close' button widget.

        Returns:
            QtWidgets.QPushButton: The 'Apply & Close' button instance.
        """
        return self.__apply_close

    def apply_button(self) -> QtWidgets.QPushButton:
        """Gets the 'Apply' button widget.

        Returns:
            QtWidgets.QPushButton: The 'Apply' button instance.
        """
        return self.__apply

    def close_button(self) -> QtWidgets.QPushButton:
        """Gets the 'Close' button widget.

        Returns:
            QtWidgets.QPushButton: The 'Close' button instance.
        """
        return self.__close

    def menu_bar(self) -> QtWidgets.QMenuBar:
        """Gets the main menu bar widget.

        Returns:
            QtWidgets.QMenuBar: The menu bar instance.
        """
        return self.__menu_bar

    def file_menu(self) -> QtWidgets.QMenu:
        """Gets the 'File' menu.

        Returns:
            QtWidgets.QMenu: The file menu instance.
        """
        return self.__file_menu

    def help_menu(self) -> QtWidgets.QMenu:
        """Gets the 'Help' menu.

        Returns:
            QtWidgets.QMenu: The help menu instance.
        """
        return self.__help_menu
