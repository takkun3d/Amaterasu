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
"""Amaterasu: Open source toolset for Autodesk Maya."""

from __future__ import annotations
import os
import pathlib
import random
import webbrowser
from maya import cmds, utils
from maya.api import OpenMaya
from amaterasu.base.qt import shiboken, QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework
from . import menu

__product__: str = "Amaterasu"
__version__: int = 20260510

DEFAULT_LICENSE: str = """Copyright (c) 2014-2026 takkun (takkun3d).<br />
<br />
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:<br />
<br />
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.<br />
<br />
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent
SCRIPT_PATH: pathlib.Path = ROOT_PATH.parent
MODULE_PATH: pathlib.Path = SCRIPT_PATH.parent
ICONS_PATH: pathlib.Path = MODULE_PATH / "icons"
RESOURCE_PATH: pathlib.Path = MODULE_PATH / "resource"
MAYA_APP_DIR: pathlib.Path = pathlib.Path(os.getenv("MAYA_APP_DIR") or "")
USER_DATA_DIR: pathlib.Path = MAYA_APP_DIR / __product__.lower()

DCN_URL: str = (
    r"https://telling-mink-b5d.notion.site/Digital-Craft-Notes-22788977f41f8049891aef08895de07f"
)
HOME_URL: str = (
    r"https://telling-mink-b5d.notion.site/Amaterasu-15c88977f41f80a7af4adcfca26d304a"
)
PATCH_NOTE_URL: str = (
    r"https://telling-mink-b5d.notion.site/15c88977f41f811bb5a5ff41c9e85754"
)
MANUAL_URL: str = (
    r"https://telling-mink-b5d.notion.site/15c88977f41f811cbcbad4a462dd9c8f"
)

MAYA_VERSION: int = OpenMaya.MGlobal.apiVersion()


class Settings(framework.ToolSettings):
    """Global settings for the Amaterasu package.

    Attributes:
        latest_version (framework.Variant[int]): The latest executed version of Amaterasu.
        override_splash_screen (framework.Variant[bool]): Whether to override the Maya
            splash screen on startup.
    """

    latest_version: framework.Variant[int] = framework.Variant(0)
    override_splash_screen: framework.Variant[bool] = framework.Variant(True)


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
        str(x) for x in (ICONS_PATH / "startup_images").glob("*.png")
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


def show_dcn() -> None:
    """Opens Digital Craft Notes."""
    webbrowser.open(DCN_URL)


def show_home() -> None:
    """Opens the Amaterasu home page."""
    webbrowser.open(HOME_URL)


def show_patch_note() -> None:
    """Opens the patch notes."""
    webbrowser.open(PATCH_NOTE_URL)


def show_manual() -> None:
    """Opens the user manual."""
    webbrowser.open(MANUAL_URL)


def show_about() -> None:
    """Displays the About dialog using the common widget."""
    framework.AboutDialog.info(
        dcc.get_maya_window(),
        __product__,
        str(__version__),
        DEFAULT_LICENSE,
        __doc__,
    )


def execute_deferred() -> None:
    """Initializes components after Maya is fully loaded."""
    settings: Settings = Settings.instance(__name__, True)
    menu.create_main_menu()
    menu.create_channelbox_menu()

    if settings.latest_version.value() < __version__:
        settings.latest_version.set_value(__version__)
        settings.write()
        show_patch_note()


def main() -> None:
    """The main startup sequence."""
    settings: Settings = Settings.instance(__name__, True)
    if settings.override_splash_screen.value():
        override_splash_screen()

    utils.executeDeferred(execute_deferred)
