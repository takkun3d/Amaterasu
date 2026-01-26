# ==============================================================================
#
# Overscan
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from functools import partial

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QSpinBox, QPushButton, QMessageBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QSpinBox,
            QPushButton,
            QMessageBox,
        )

from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Overscan'
__version__: str = '1.00'
__doc__ = 'Applies overscan to resolution and post scale.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    margin: parser.Variant[int] = parser.Variant(100)
    margin_percent: parser.Variant[int] = parser.Variant(10)


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
        self.resize(300, 100)

        option_widget: QWidget = self.option_widget()
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)
        main_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__margin: QSpinBox = QSpinBox(self)
        self.__margin.setRange(1, 10000)
        main_layout.addRow(widgets.FormLabel('Margin (px)'), self.__margin)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(partial(self.apply, False))
        main_layout.addRow('', button)

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__margin_percent: QSpinBox = QSpinBox(self)
        self.__margin.setRange(1, 10000)
        main_layout.addRow(
            widgets.FormLabel('Margin (%)'), self.__margin_percent
        )

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(partial(self.apply, True))
        main_layout.addRow('', button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__margin.setValue(settings.margin.value())
        self.__margin_percent.setValue(settings.margin_percent.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.margin.set_value(self.__margin.value())
        settings.margin_percent.set_value(self.__margin_percent.value())
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

    @widgets.undo
    def apply(self, is_percent: bool = False) -> None:
        '''Apply'''
        result: int = QMessageBox.warning(
            self,
            'Warning',
            'This operation modifies the render resolution settings.\n'
            'Undo functionality may not work correctly after execution.\n\n'
            'Do you want to proceed?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.No:
            _logger.info('Cancelled.')

            return

        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select camera to calculate overscan.')
            return

        if len(selection) != 1:
            _logger.error('Select a single camera to calculate overscan.')
            return

        if is_percent:
            apply(selection[0], None, settings.margin_percent.value())
        else:
            apply(selection[0], settings.margin.value(), None)

        _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(camera: str, margin: int | None, margin_percent: int | None) -> None:
    '''Apply'''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return

    width: int = cmds.getAttr('defaultResolution.width')
    height: int = cmds.getAttr('defaultResolution.height')
    post_scale: float = cmds.getAttr(f'{camera_shapes[0]}.postScale')
    device_aspect: float = float(width) / float(height)
    pixel_aspect: float = cmds.getAttr('defaultResolution.pixelAspect')

    new_width: int = width
    new_height: int = height
    if margin is not None:
        new_width = width + (margin * 2)
        new_height = height + (margin * 2)

    elif margin_percent is not None:
        factor: float = 1.0 + (margin_percent / 100.0)
        new_width = int(width * factor)
        new_height = int(height * factor)

    else:
        return

    scale_x: float = width / float(new_width)
    scale_y: float = height / float(new_height)
    scale: float = min(scale_x, scale_y)
    new_post_scale: float = post_scale * scale

    cmds.setAttr('defaultResolution.lockDeviceAspectRatio', 0)
    cmds.setAttr('defaultResolution.width', new_width)
    cmds.setAttr('defaultResolution.height', new_height)
    cmds.setAttr('defaultResolution.deviceAspectRatio', device_aspect)
    cmds.setAttr('defaultResolution.pixelAspect', pixel_aspect)
    cmds.setAttr(f'{camera_shapes[0]}.postScale', new_post_scale)


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
