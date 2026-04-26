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
"""Standard tool widget template for Amaterasu.

This module provides the `ToolWindow` abstract base class, which extends
the foundational `BaseToolWindow` to include a standardized UI layout.
It automatically sets up a menu bar with 'File' and 'Help' menus, and
defines abstract methods for saving, loading, and resetting tool settings,
ensuring a consistent user experience across all Amaterasu tools.
"""
from __future__ import annotations
import abc
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base.framework import workspace_control


class ToolWindow(
    workspace_control.WorkspaceControlWindow,
    abc.ABC,
    metaclass=workspace_control.QWidgetABCMeta,
):
    """Abstract base class for standard Amaterasu tool windows.

    This class provides a pre-configured UI template including a main layout,
    a menu bar (with File/Help menus), and a central area for tool-specific
    options. It enforces the implementation of settings management methods
    (load, save, reset) to maintain consistency.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the ToolWindow with a standard menu and layout.

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

        self.__sub_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.__sub_layout.setContentsMargins(10, 0, 10, 10)
        self.__main_layout.addLayout(self.__sub_layout)

        self.__option_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        self.__sub_layout.addWidget(self.__option_widget, True)

        self.create_ui(self.__option_widget)

    def create_menu(self) -> None:
        """Creates the standard menu bar and menus for the tool widget.

        This sets up the basic 'File' (Save, Reset, Exit) and 'Help' (About)
        menus. It also invokes `create_custom_menu` to allow subclasses to
        inject their own specific menus.
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

        action: QtGui.QAction = self.__file_menu.addAction("Exit")
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

    def option_widget(self) -> QtWidgets.QWidget:
        """Gets the central widget container for tool-specific UI elements.

        Returns:
            QtWidgets.QWidget: The container widget.
        """
        return self.__option_widget

    def option_layout(self) -> QtWidgets.QLayout:
        """Gets the layout applied to the tool-specific option area.

        Returns:
            QtWidgets.QLayout: The vertical layout instance.
        """
        return self.__sub_layout
