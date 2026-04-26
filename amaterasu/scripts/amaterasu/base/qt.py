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
"""Amaterasu custom Qt binding and compatibility module.

This module provides a unified interface for PySide2 and PySide6, allowing
tools to be written using modern PySide6 syntax while maintaining backward
compatibility with PySide2 (Maya 2024 and older).

It automatically detects the available PySide version and applies patches
to PySide2 to mimic PySide6 behavior, such as aliasing `exec_` to `exec`,
mapping moved classes (e.g., `QAction`, `QShortcut`), and resolving flag
differences.

Attributes:
    PYSIDE_VERSION (int): The loaded version of PySide (either 2 or 6).
    QtCore (module): The loaded PySide.QtCore module.
    QtGui (module): The loaded PySide.QtGui module.
    QtWidgets (module): The loaded PySide.QtWidgets module.
    Signal (type): The Qt Signal class.
    Slot (type): The Qt Slot decorator.
    Property (type): The Qt Property function.
    shiboken (module): The loaded shiboken module (shiboken2 or shiboken6).

Functions:
    wrap_instance(ptr, base): Wraps a C++ pointer into a PySide object.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, cast

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Signal, Slot, Property
    import shiboken6 as shiboken

    PYSIDE_VERSION = 6

except ImportError:
    if not TYPE_CHECKING:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import Signal, Slot, Property
        import shiboken2 as shiboken

    PYSIDE_VERSION = 2

__all__: list[str] = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "Signal",
    "Slot",
    "Property",
    "shiboken",
    "PYSIDE_VERSION",
    "wrap_instance",
]

T = TypeVar("T", bound=QtCore.QObject)

if not TYPE_CHECKING and PYSIDE_VERSION == 2:
    # Modules
    QtGui.QAction = QtWidgets.QAction
    QtGui.QActionGroup = QtWidgets.QActionGroup
    QtGui.QShortcut = QtWidgets.QShortcut
    QtGui.QFileSystemModel = QtWidgets.QFileSystemModel
    QtCore.QRegularExpression = QtCore.QRegExp
    QtGui.QRegularExpressionValidator = QtGui.QRegExpValidator

    # Methods
    for cls in (
        QtCore.QEventLoop,
        QtCore.QCoreApplication,
        QtWidgets.QApplication,
        QtWidgets.QDialog,
        QtWidgets.QMenu,
    ):
        cls.exec = cls.exec_

    # Flags
    QtCore.Qt.AlignmentFlag = QtCore.Qt
    QtCore.Qt.WindowType = QtCore.Qt
    QtCore.Qt.WindowModality = QtCore.Qt
    QtCore.Qt.CheckState = QtCore.Qt
    QtCore.Qt.KeyboardModifier = QtCore.Qt
    QtCore.Qt.MouseButton = QtCore.Qt
    QtCore.Qt.Orientation = QtCore.Qt
    QtCore.Qt.MouseButton.MiddleButton = QtCore.Qt.MidButton


def wrap_instance(ptr: int, base: type[T]) -> T | None:
    """Wraps a C++ pointer into a PySide object.

    Args:
        ptr (int): The memory address (pointer) of the C++ object.
        base (type[T]): The PySide class to wrap the pointer into.

    Returns:
        T | None: The wrapped PySide object of type T, or None
            if the conversion fails or the pointer is invalid.
    """
    if not ptr:
        return None

    obj: T = cast(T, shiboken.wrapInstance(ptr, base))
    return obj
