# ==============================================================================
#
# Xray Geometry
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
from functools import partial

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QHBoxLayout, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from maya import cmds
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Xray Geometry'
__version__: str = '1.10'
__doc__ = 'Set Xray for per geometry.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        unique_id: str = '',
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(50, 50)

        option_widget: QWidget = self.option_widget()
        main_layout: QHBoxLayout = QHBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        button: QPushButton = QPushButton('ON', self)
        button.setMinimumWidth(100)
        button.clicked.connect(partial(apply, True))
        main_layout.addWidget(button)

        button = QPushButton('OFF', self)
        button.setMinimumWidth(100)
        button.clicked.connect(partial(apply, False))
        main_layout.addWidget(button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )


# ==============================================================================
#
# Functions
#
# ==============================================================================
@widgets.undo
def apply(xray: bool) -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select one or more nodes to set xray.')
        return

    for node in selection:
        cmds.displaySurface(node, xRay=xray)


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
