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
"""Utilities for integrating Qt widgets with Autodesk Maya's UI elements.

This module provides helper functions to retrieve and wrap internal Maya UI
components (like windows, controls, layouts, and menus) into accessible Qt
widget instances using OpenMayaUI.MQtUtil.
"""

from typing import TypeVar
from maya import OpenMayaUI, cmds, mel
from amaterasu.base.qt import QtCore, QtWidgets, wrap_instance

T = TypeVar("T", bound=QtCore.QObject)


def get_maya_window() -> QtWidgets.QMainWindow | None:
    """Retrieves the main Maya application window as a Qt widget.

    Returns:
        QtWidgets.QMainWindow | None: The main window instance,
            or None if it cannot be found.
    """
    return wrap_instance(
        int(OpenMayaUI.MQtUtil.mainWindow()), QtWidgets.QMainWindow
    )


def find_control(item: str, widget_type: type[T]) -> T | None:
    """Finds a Maya control by its UI string name and wraps it into a Qt widget.

    Args:
        item (str): The string name of the Maya control.
        widget_type (type[T]): The expected Qt class type
            (e.g., QtWidgets.QPushButton).

    Returns:
        T | None: The wrapped Qt widget instance,
            or None if the control is not found.
    """
    ptr: int = int(OpenMayaUI.MQtUtil.findControl(item))
    return wrap_instance(int(ptr), widget_type)


def find_layout(item: str, widget_type: type[T]) -> T | None:
    """Finds a Maya layout by its UI string name and wraps it into a Qt widget.

    Args:
        item (str): The string name of the Maya layout.
        widget_type (type[T]): The expected Qt class type
            (e.g., QtWidgets.QVBoxLayout).

    Returns:
        T | None: The wrapped Qt layout instance,
            or None if the layout is not found.
    """
    ptr: int = int(OpenMayaUI.MQtUtil.findLayout(item))
    return wrap_instance(int(ptr), widget_type)


def find_menu_item(item: str, widget_type: type[T]) -> T | None:
    """Finds a Maya menu item by its UI string name and wraps it into a Qt object.

    Args:
        item (str): The string name of the Maya menu item.
        widget_type (type[T]): The expected Qt class type
            (e.g., QtGui.QAction).

    Returns:
        T | None: The wrapped Qt object instance,
            or None if the menu item is not found.
    """
    ptr: int = int(OpenMayaUI.MQtUtil.findMenuItem(item))
    return wrap_instance(int(ptr), widget_type)


def show_attribute_editor(node_name: str) -> None:
    """Selects the node and opens the Attribute Editor.

    Args:
        node_name (str): The name of the node to select.
    """
    cmds.select(node_name)
    mel.eval("ShowAttributeEditorOrChannelBox")
