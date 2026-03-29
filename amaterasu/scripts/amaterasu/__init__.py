# ==============================================================================
#
# Amaterasu
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import os
import pathlib
import random
import webbrowser

try:
    from shiboken2 import wrapInstance, getCppPointer
    from PySide2.QtCore import QCoreApplication, QPoint
    from PySide2.QtGui import QPixmap, QPainter, QFont, QPen, QColor
    from PySide2.QtWidgets import QApplication, QWidget, QSplashScreen

except ImportError:
    if not TYPE_CHECKING:
        from shiboken6 import wrapInstance, getCppPointer
        from PySide6.QtCore import QCoreApplication, QPoint
        from PySide6.QtGui import QPixmap, QPainter, QFont, QPen, QColor
        from PySide6.QtWidgets import QApplication, QWidget, QSplashScreen
from maya import cmds, utils
from maya.api import OpenMaya
from .lib import parser, widgets
from . import menu


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Amaterasu'
__version__: int = 20260329
__doc__ = '''
Amaterasu is a toolset for Autodesk Maya.
Amaterasu provides a set of convenient tools to your contents creation process.
'''
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent
SCRIPT_PATH: pathlib.Path = ROOT_PATH.parent
MODULE_PATH: pathlib.Path = SCRIPT_PATH.parent
ICONS_PATH: pathlib.Path = MODULE_PATH / 'icons'
RESOURCE_PATH: pathlib.Path = MODULE_PATH / 'resource'
MAYA_APP_DIR: pathlib.Path = pathlib.Path(os.getenv('MAYA_APP_DIR') or '')
USER_DATA_DIR: pathlib.Path = MAYA_APP_DIR / __product__.lower()

DCN_URL: str = (
    r'https://telling-mink-b5d.notion.site/Digital-Craft-Notes-22788977f41f8049891aef08895de07f'
)
HOME_URL: str = (
    r'https://telling-mink-b5d.notion.site/Amaterasu-15c88977f41f80a7af4adcfca26d304a'
)
PATCH_NOTE_URL: str = (
    r'https://telling-mink-b5d.notion.site/15c88977f41f811bb5a5ff41c9e85754'
)
MANUAL_URL: str = (
    r'https://telling-mink-b5d.notion.site/15c88977f41f811cbcbad4a462dd9c8f'
)
MAYA_VERSION: int = OpenMaya.MGlobal.apiVersion()


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    latest_version: parser.Variant[int] = parser.Variant(0)
    override_splash_screen: parser.Variant[bool] = parser.Variant(True)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def override_splash_screen() -> QCoreApplication | None:
    '''Override image of splash screen.'''
    if cmds.about(batch=True):
        return None

    splash_screen: QSplashScreen | None = None
    app: QCoreApplication = QCoreApplication.instance()
    if isinstance(app, QCoreApplication):
        app = wrapInstance(getCppPointer(app)[0], QApplication)

    widgets: list[QWidget] = app.topLevelWidgets()
    for widget in widgets:
        if isinstance(widget, QSplashScreen):
            splash_screen = widget
            break

    if not splash_screen:
        return None

    images: list[str] = [
        str(x) for x in (ICONS_PATH / 'startup_images').glob('*.png')
    ]
    if images:
        image: str = random.choice(images)
        geometry = splash_screen.geometry()
        pixmap: QPixmap = QPixmap(image)
        painter: QPainter = QPainter()
        painter.begin(pixmap)
        painter.setFont(QFont('Arial', 8, QFont.Bold))
        painter.setPen(QPen(QColor('#bdbdbd')))
        painter.drawText(QPoint(15, 480), cmds.about(installedVersion=True))
        painter.end()
        splash_screen.setPixmap(pixmap)
        splash_screen.setGeometry(geometry)

    return app


def show_dcn() -> None:
    '''Show Digital Craft Nodes of notion'''
    webbrowser.open(DCN_URL)


def show_home() -> None:
    '''Show home page of notion'''
    webbrowser.open(HOME_URL)


def show_patch_note() -> None:
    '''Show patch note window'''
    webbrowser.open(PATCH_NOTE_URL)


def show_manual() -> None:
    '''Show home page of notion'''
    webbrowser.open(MANUAL_URL)


def show_about() -> None:
    '''Show about dialog.'''
    widgets.AboutDialog.info(
        None, __product__, str(__version__), __copyright__, __doc__
    )


def execute_deferred() -> None:
    '''Event executed after the Maya loaded GUI.'''
    settings: Settings = Settings.instance(__name__, True)
    menu.create_main_menu()
    menu.create_channelbox_menu()

    if settings.latest_version.value() < __version__:
        settings.latest_version.set_value(__version__)
        settings.write()
        show_patch_note()


def main() -> None:
    '''Amaterasu startup process.'''
    settings: Settings = Settings.instance(__name__, True)
    if settings.override_splash_screen.value():
        override_splash_screen()

    utils.executeDeferred(execute_deferred)
