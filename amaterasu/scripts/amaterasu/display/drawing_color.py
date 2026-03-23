# ==============================================================================
#
# Drawing Color
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
from functools import partial

try:
    from PySide2.QtCore import Qt, Signal, Slot, QSize
    from PySide2.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, Slot, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QHBoxLayout,
            QPushButton,
        )
from maya import cmds
from ..lib import logger, parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Drawing Color'
__version__: str = '1.20'
__doc__ = 'Set drawing color to selected nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

TRASH: str = 'a_trash.png'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    color_mode: parser.Variant[int] = parser.Variant(0)
    rgb: parser.Variant[list[float]] = parser.Variant([0.0, 0.275, 0.098])


class IndexColorPalette(QWidget):
    '''Index color palette widget.'''

    clicked: Signal = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        row: int = -1
        col: int = -1
        for i in range(32):
            col += 1
            if not i % 8:
                row += 1
                col = 0

            if i == 0:
                trash_button: widgets.IconButton = widgets.IconButton(self)
                trash_button.set_icon(widgets.icon_from_file_name(TRASH))
                trash_button.setFixedSize(QSize(24, 24))
                trash_button.clicked.connect(partial(self.apply, i))
                main_layout.addWidget(trash_button, row, col)
            else:
                color: list[float] = cmds.colorIndex(i, query=True)
                button: widgets.ColorButton = widgets.ColorButton(self)
                button.set_color(color[0], color[1], color[2])
                button.setFixedSize(QSize(24, 24))
                button.clicked.connect(partial(self.apply, i))
                main_layout.addWidget(button, row, col)

    @widgets.undo
    def apply(self, index: int) -> None:
        '''Apply'''
        result: bool = apply(0, index)
        if result:
            _logger.info('Done.')

        self.clicked.emit()


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
        self.resize(200, 200)

        option_widget: QWidget = self.option_widget()
        self.__main_layout: widgets.FormLayout = widgets.FormLayout(
            option_widget
        )
        self.__main_layout.setContentsMargins(0, 0, 0, 0)

        self.__mode = widgets.RadioButtons(self)
        self.__mode.set_labels(('Index', 'RGB'))
        self.__mode.button_group().buttonClicked.connect(self.set_valid_options)
        self.__main_layout.addRow(widgets.FormLabel('Color'), self.__mode)

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        # Index Color
        index_color: IndexColorPalette = IndexColorPalette(self)
        index_color.clicked.connect(self.save_settings)
        self.__main_layout.addRow(widgets.FormLabel('Index Color'), index_color)
        self.__index_color_index: int = self.__main_layout.row_id()

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        # RGB Color
        rgb_layout: QHBoxLayout = QHBoxLayout()
        self.__main_layout.addRow('RGB Color', rgb_layout)
        self.__rgb_color_index: int = self.__main_layout.row_id()

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
        self.__palette_index: int = self.__main_layout.row_id()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__mode.set_check_id(settings.color_mode.value())
        self.__rgb_color.set_color(*settings.rgb.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.color_mode.set_value(self.__mode.check_id())
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

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        if self.__mode.check_id() == 0:
            self.__main_layout.set_row_enabled(self.__index_color_index, True)
            self.__main_layout.set_row_enabled(self.__rgb_color_index, False)
            self.__main_layout.set_row_enabled(self.__palette_index, False)
        else:
            self.__main_layout.set_row_enabled(self.__index_color_index, False)
            self.__main_layout.set_row_enabled(self.__rgb_color_index, True)
            self.__main_layout.set_row_enabled(self.__palette_index, True)

    def __set_color_from_palette(self, color: list[float]) -> None:
        '''Set color to button from palette'''
        self.__rgb_color.set_color(*color)

    @widgets.undo
    def remove_rgb_color_callback(self) -> None:
        '''Remove RGB color callback'''
        self.save_settings()
        result: bool = apply(1, 0)
        if result:
            _logger.info('Done.')

    @widgets.undo
    def apply_rgb_color_callback(self) -> None:
        '''Apply RGB color callback'''
        self.save_settings()
        result: bool = apply(1, 0, self.__rgb_color.color())
        if result:
            _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    mode: int,
    index: int = 0,
    rgb: list[float] | None = None,
    force_layer: bool = True,
    selection: list[str] | None = None,
) -> bool:
    '''Apply display color to selected nodes.'''
    if not selection:
        selection = cmds.ls(selection=True)

    if not selection:
        _logger.error('Select object to set wireframe color.')
        return False

    if index >= 32:
        _logger.error('Color index is maximum value of 31.')
        return False

    if index <= -1:
        _logger.error('Color index is minimum value of 0.')
        return False

    for node in selection:
        if force_layer:
            plugs: list[str] = cmds.listConnections(
                f'{node}.drawOverride',
                type='displayLayer',
                source=True,
                destination=False,
                plugs=True,
            )
            if plugs:
                cmds.disconnectAttr(plugs[0], f'{node}.drawOverride')

        # Index Color
        if mode == 0:
            if index == 0:
                cmds.setAttr(f'{node}.overrideEnabled', 0)
            else:
                cmds.setAttr(f'{node}.overrideEnabled', 1)
                cmds.setAttr(f'{node}.overrideRGBColors', 0)
                cmds.setAttr(f'{node}.overrideColor', index)

        # RGB Color
        else:
            if rgb is None:
                cmds.setAttr(f'{node}.overrideEnabled', 0)
            else:
                cmds.setAttr(f'{node}.overrideEnabled', 1)
                cmds.setAttr(f'{node}.overrideRGBColors', 1)
                cmds.setAttr(f'{node}.overrideColorRGB', *rgb, type='double3')

    return True


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
