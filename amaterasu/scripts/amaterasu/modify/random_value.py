# ==============================================================================
#
# Random Value
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from itertools import product
import random

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QLabel,
        QDoubleSpinBox,
        QCheckBox,
        QSpinBox,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QLabel,
            QDoubleSpinBox,
            QCheckBox,
            QSpinBox,
            QMessageBox,
        )
from maya import cmds, mel
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Random Value'
__version__: str = '1.00'
__doc__ = 'Set random value for attribute selected in Channel Box.'
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
    seed: parser.Variant[int] = parser.Variant(0)
    method: parser.Variant[int] = parser.Variant(1)
    range: parser.Variant[int] = parser.Variant(1)
    random_min: parser.Variant[float] = parser.Variant(-10.0)
    random_max: parser.Variant[float] = parser.Variant(10.0)
    uniform_scale: parser.Variant[bool] = parser.Variant(True)


class MainWindow(widgets.StandardToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        self.__main_layout = widgets.FormLayout(self.option_widget())

        seed_layout = QHBoxLayout(self)
        self.__main_layout.addRow(widgets.FormLabel('Seed'), seed_layout)

        self.__seed = QSpinBox(self)
        self.__seed.setRange(-999999, 999999)
        self.__seed.setMaximumWidth(80)
        self.__seed.setButtonSymbols(QSpinBox.NoButtons)
        self.__seed.setToolTip('If set to 0, result changes every time.')
        seed_layout.addWidget(self.__seed)

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('Absolute', 'Relatives'))
        self.__main_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__range: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__range.set_labels(('Custom', 'Attribute Min/Max'))
        self.__range.button_group().buttonClicked.connect(
            self.set_valid_options
        )
        self.__main_layout.addRow(widgets.FormLabel('Range'), self.__range)

        custom_range_layout = QHBoxLayout(self)
        self.__main_layout.addRow('', custom_range_layout)
        self.__custom_range_id = self.__main_layout.row_id()

        custom_range_layout.addWidget(QLabel('Min : '))

        self.__min = QDoubleSpinBox(self)
        self.__min.setRange(-999999, 999999)
        self.__min.setDecimals(5)
        self.__min.setMaximumWidth(80)
        self.__min.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__min.setToolTip(
            'If attribute has no maximum value, Random range is setting to this.'
        )
        custom_range_layout.addWidget(self.__min)

        custom_range_layout.addWidget(QLabel('Max : '))

        self.__max = QDoubleSpinBox(self)
        self.__max.setRange(-999999, 999999)
        self.__max.setDecimals(5)
        self.__max.setMaximumWidth(80)
        self.__max.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__max.setToolTip(
            'If attribute has no maximum value, Random range is setting to this.'
        )
        custom_range_layout.addWidget(self.__max)

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__uniform_scale = QCheckBox('Uniform Scale', self)
        self.__main_layout.addWidget(self.__uniform_scale)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__seed.setValue(settings.seed.value())
        self.__method.set_check_id(settings.method.value())
        self.__range.set_check_id(settings.range.value())
        self.__min.setValue(settings.random_min.value())
        self.__max.setValue(settings.random_max.value())
        self.__uniform_scale.setChecked(settings.uniform_scale.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.seed.set_value(self.__seed.value())
        settings.method.set_value(self.__method.check_id())
        settings.range.set_value(self.__range.check_id())
        settings.random_min.set_value(self.__min.value())
        settings.random_max.set_value(self.__max.value())
        settings.uniform_scale.set_value(self.__uniform_scale.isChecked())
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
        # self.__main_layout.set_row_enabled(
        #     self.__custom_range_id, (self.__range.check_id() == 0)
        # )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QMessageBox.critical(
                self, 'Error', 'Select node to set random value.'
            )
            return

        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    plugs: list[str],
    seed: int = 0,
    method: int = 0,
    range: int = 1,
    min_value: float = -10,
    max_value: float = 10,
    uniform_scale: bool = False,
) -> bool:
    '''
    Random value to plugs.
    method = 0:Absolute / 1:Relatives
    range = 0:Custom / 1:Attribute[min-max]
    '''
    if seed != 0:
        random.seed(seed)

    scale_cache: dict[str, float] = {}
    scale_attrs: list[str] = ['sx', 'sy', 'sz']

    for plug in plugs:
        temp: list[str] = plug.split('.')
        node: str = temp[0]
        attr: str = '.'.join(temp[1:])

        min_exists: bool = cmds.attributeQuery(attr, node=node, minExists=True)
        max_exists: bool = cmds.attributeQuery(attr, node=node, maxExists=True)
        attr_min: float = (
            cmds.attributeQuery(attr, node=node, minimum=True)[0]
            if min_exists
            else 0.0
        )
        attr_max: float = (
            cmds.attributeQuery(attr, node=node, maximum=True)[0]
            if max_exists
            else 0.0
        )

        if range == 1:
            min_value = attr_min if min_exists else min_value
            max_value = attr_max if max_exists else max_value

        value: float = random.uniform(min_value, max_value)

        if method == 1:
            value += float(cmds.getAttr(plug))

            # Clamp
            value = min(max_value, value) if min_exists else value
            value = max(min_value, value) if max_exists else value

        if uniform_scale and attr in scale_attrs and node not in scale_cache:
            # Uniform scale settings are done using cache.
            scale_cache[node] = value

        else:
            try:
                cmds.setAttr(plug, value)

            except RuntimeError:
                _logger.error('Failed to set %s.', plug)

    # Uniform scale
    if uniform_scale:
        for node, attr in product(scale_cache.keys(), scale_attrs):
            try:
                cmds.setAttr(f'{node}.{attr}', scale_cache[node])
            except RuntimeError:
                _logger.error('Failed to set %s.', f'{node}.{attr}')

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''

    def create_plug_list(nodes: list[str], attrs: list[str]) -> list[str]:
        '''Create plug list'''
        result: list[str] = []
        for node, attr in product(nodes, attrs):
            result.append(f'{node}.{attr}')

        return result

    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node to set random value.')
        return

    plugs: list[str] = []
    cb_name: str = mel.eval('$gChannelBoxName=$gChannelBoxName;')
    plugs.extend(
        create_plug_list(
            cmds.channelBox(cb_name, query=True, mainObjectList=True) or [],
            cmds.channelBox(cb_name, query=True, selectedMainAttributes=True)
            or [],
        )
    )
    plugs.extend(
        create_plug_list(
            cmds.channelBox(cb_name, query=True, shapeObjectList=True) or [],
            cmds.channelBox(cb_name, query=True, selectedShapeAttributes=True)
            or [],
        )
    )
    plugs.extend(
        create_plug_list(
            cmds.channelBox(cb_name, query=True, historyObjectList=True) or [],
            cmds.channelBox(cb_name, query=True, selectedHistoryAttributes=True)
            or [],
        )
    )
    if not plugs:
        _logger.error('In Channel Box, Select attribute to set random value.')
        return

    settings: Settings = Settings.instance(__name__, True)
    settings.seed.value()
    settings.method.value()
    settings.range.value()
    settings.random_min.value()
    settings.random_max.value()
    settings.uniform_scale.value()
    result: bool = apply(
        plugs,
        settings.seed.value(),
        settings.method.value(),
        settings.range.value(),
        settings.random_min.value(),
        settings.random_max.value(),
        settings.uniform_scale.value(),
    )
    if result:
        _logger.info('Done.')
