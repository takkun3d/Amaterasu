# ==============================================================================
#
# Outliner Color
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QHBoxLayout, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QPushButton,
        )
from maya import cmds
from ..lib import parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Outliner Color'
__version__: str = '1.00'
__doc__ = 'Set outliner color to selected nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

TRASH: str = 'a_trash.png'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    rgb: parser.Variant[list[float]] = parser.Variant([1.0, 0.0, 0.0])


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(200, 50)

        option_widget: QWidget = self.option_widget()
        self.__main_layout: widgets.FormLayout = widgets.FormLayout(
            option_widget
        )
        self.__main_layout.setContentsMargins(0, 0, 0, 0)

        rgb_layout: QHBoxLayout = QHBoxLayout()
        self.__main_layout.addRow('RGB Color', rgb_layout)

        self.__rgb_color: widgets.ColorSelectButton = widgets.ColorSelectButton(
            self
        )
        self.__rgb_color.setFixedSize(70, 20)
        rgb_layout.addWidget(self.__rgb_color)
        rgb_layout.addStretch(True)

        button: QPushButton = QPushButton('Remove', self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.remove_rgb_color_callback)
        rgb_layout.addWidget(button)

        button = QPushButton('Apply', self)
        button.setFixedSize(60, 20)
        button.clicked.connect(self.apply_rgb_color_callback)
        rgb_layout.addWidget(button)

        palette = widgets.ColorPalette(None, 8, self)
        palette.clicked.connect(self.__set_color_from_palette)
        self.__main_layout.addRow('', palette)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__rgb_color.set_color(*settings.rgb.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.rgb.set_value(self.__rgb_color.color())
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

    def __set_color_from_palette(self, color: list[float]) -> None:
        '''Set color to button from palette'''
        self.__rgb_color.set_color(*color)

    @widgets.undo
    def remove_rgb_color_callback(self) -> None:
        '''Remove RGB color callback'''
        self.save_settings()
        apply(None, None)

    @widgets.undo
    def apply_rgb_color_callback(self) -> None:
        '''Apply RGB color callback'''
        self.save_settings()
        apply(self.__rgb_color.color(), None)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    rgb: list[float] | None = None,
    selection: list[str] | None = None,
) -> None:
    '''Apply outliner color to selected nodes.'''
    if not selection:
        selection = cmds.ls(selection=True)

    if not selection:
        _logger.error('Select object to set outliner color.')
        return

    for node in selection:
        if rgb is None:
            cmds.setAttr(f'{node}.useOutlinerColor', 0)
        else:
            cmds.setAttr(f'{node}.useOutlinerColor', 1)
            cmds.setAttr(f'{node}.outlinerColor', *rgb, type='double3')

    _logger.info('Done.')


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
