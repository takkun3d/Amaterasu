# ==============================================================================
#
# Offset Keyframe
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from functools import partial

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QSpinBox,
        QCheckBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QSpinBox,
            QCheckBox,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Offset Keyframe'
__version__: str = '1.10'
__doc__ = 'Offset keyframe time with selected node.'
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
    offset_value: parser.Variant[int] = parser.Variant(2)
    delay: parser.Variant[bool] = parser.Variant(False)


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
        self.resize(400, 20)

        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        offset_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(offset_layout)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous3.png'))
        button.clicked.connect(partial(self.offset_callback, -3))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous2.png'))
        button.clicked.connect(partial(self.offset_callback, -2))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous.png'))
        button.clicked.connect(partial(self.offset_callback, -1))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        self.__offset_value: QSpinBox = QSpinBox(self)
        self.__offset_value.setRange(-99999, 99999)
        self.__offset_value.setButtonSymbols(QSpinBox.NoButtons)
        offset_layout.addWidget(self.__offset_value)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next.png'))
        button.clicked.connect(partial(self.offset_callback, 1))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next2.png'))
        button.clicked.connect(partial(self.offset_callback, 2))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next3.png'))
        button.clicked.connect(partial(self.offset_callback, 3))
        button.setMaximumSize(24, 24)
        offset_layout.addWidget(button)

        self.__delay: QCheckBox = QCheckBox('Delay time each selection.', self)
        main_layout.addWidget(self.__delay)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__offset_value.setValue(settings.offset_value.value())
        self.__delay.setChecked(settings.delay.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.offset_value.set_value(self.__offset_value.value())
        settings.delay.set_value(self.__delay.isChecked())
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
    def offset_callback(self, rate: int = 1) -> None:
        '''Apply'''
        self.save_settings()
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select node to offset keyframes time.')
            return

        offset_value: int = self.__offset_value.value() * rate
        apply(selection, offset_value, self.__delay.isChecked())


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(nodes: list[str], offset_value: int, delay: bool = False) -> bool:
    '''Offset keyframe time with selected node.'''
    if delay:
        delay_rate: int = 0
        for node in nodes:
            cmds.keyframe(
                node, relative=True, timeChange=(offset_value * delay_rate)
            )
            delay_rate += 1

    else:
        cmds.keyframe(*nodes, relative=True, timeChange=offset_value)
    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
