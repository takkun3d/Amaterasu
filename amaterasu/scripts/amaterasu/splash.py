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
"""Amaterasu splash screen module.

This module handles overriding the default Maya splash screen with custom
Amaterasu startup images.
"""

from __future__ import annotations
import random
from maya import cmds
from amaterasu.base.qt import shiboken, QtCore, QtGui, QtWidgets
from . import env


def override_splash_screen() -> QtWidgets.QApplication | None:
    """Overrides the default Maya splash screen with a custom Amaterasu image.

    Finds the `QSplashScreen` widget from the main Qt application and replaces
    its pixmap with a randomly selected image from the `startup_images` directory.
    It also dynamically draws the installed Maya version text onto the image.
    This function safely aborts if Maya is running in batch mode.

    Returns:
        QtWidgets.QApplication | None: The active Qt application instance if
            successful, or None if in batch mode or the splash screen is not found.
    """
    if cmds.about(batch=True):
        return None

    splash_screen: QtWidgets.QSplashScreen | None = None
    core_app: QtCore.QCoreApplication | None = (
        QtCore.QCoreApplication.instance()
    )
    app: QtWidgets.QApplication | None = None
    if isinstance(core_app, QtCore.QCoreApplication):
        app = shiboken.wrapInstance(
            shiboken.getCppPointer(core_app)[0], QtWidgets.QApplication
        )  # type: ignore

    if app is None:
        return None

    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QSplashScreen):
            splash_screen = widget
            break

    if not splash_screen:
        return None

    images: list[str] = [
        str(x) for x in (env.ICONS_PATH / "startup_images").glob("*.png")
    ]
    if images:
        image: str = random.choice(images)
        geometry: QtCore.QRect = splash_screen.geometry()
        pixmap: QtGui.QPixmap = QtGui.QPixmap(image)
        painter: QtGui.QPainter = QtGui.QPainter()
        painter.begin(pixmap)
        painter.setFont(QtGui.QFont("Arial", 8, 1))
        painter.setPen(QtGui.QPen(QtGui.QColor("#bdbdbd")))
        painter.drawText(
            QtCore.QPoint(15, 480),
            cmds.about(installedVersion=True),
        )
        painter.end()
        splash_screen.setPixmap(pixmap)
        splash_screen.setGeometry(geometry)

    return app
