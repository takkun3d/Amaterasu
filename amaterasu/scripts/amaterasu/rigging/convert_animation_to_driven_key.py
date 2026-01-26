# ==============================================================================
#
# Convert Animation To Driven Key
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QLineEdit,
        QDoubleSpinBox,
        QPushButton,
        QMessageBox,
        QHBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QLineEdit,
            QDoubleSpinBox,
            QPushButton,
            QMessageBox,
            QHBoxLayout,
        )
from maya import cmds, mel
from ..lib import parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Convert Animation To Driven Key'
__version__: str = '1.01'
__doc__ = 'Convert animation to driven key.'
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
    driver: parser.Variant[str] = parser.Variant('')
    min: parser.Variant[float] = parser.Variant(0.0)
    max: parser.Variant[float] = parser.Variant(1.0)


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

        option_widget: QWidget = self.option_widget()
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        driver_layout = QHBoxLayout(self)
        self.__driver = QLineEdit(self)
        driver_layout.addWidget(self.__driver)

        button = QPushButton('Get', self)
        button.setMinimumWidth(80)
        button.clicked.connect(self.set_driver)
        driver_layout.addWidget(button)
        main_layout.addRow(widgets.FormLabel('Driver', self), driver_layout)

        self.__min = QDoubleSpinBox(self)
        self.__min.setDecimals(2)
        self.__min.setRange(-9999, 9999)
        self.__min.setButtonSymbols(QDoubleSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Min'), self.__min)

        self.__max = QDoubleSpinBox(self)
        self.__max.setDecimals(2)
        self.__max.setRange(-9999, 9999)
        self.__max.setButtonSymbols(QDoubleSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Max'), self.__max)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__driver.setText(settings.driver.value())
        self.__min.setValue(settings.min.value())
        self.__max.setValue(settings.max.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.driver.set_value(self.__driver.text())
        settings.min.set_value(self.__min.value())
        settings.max.set_value(self.__max.value())
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

    def set_driver(self) -> None:
        '''Set driver from selection'''
        channel_box: str = mel.eval('$gChannelBoxName=$gChannelBoxName;')
        object: list[str] = cmds.channelBox(
            channel_box, query=True, mainObjectList=True
        )
        attr: list[str] = cmds.channelBox(
            channel_box, query=True, selectedMainAttributes=True
        )
        if not object or not attr:
            QMessageBox.critical(
                self,
                __product__,
                'Select attribute  to set driver in channel box.',
            )
            return

        self.__driver.setText(f'{object[0]}.{attr[0]}')

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        drivens: list[str] = cmds.ls(selection=True)
        if not drivens:
            QMessageBox.critical(
                self,
                __product__,
                'Select node to covert animation to driven key.',
            )
            return

        result: int = apply(
            self.__driver.text(),
            drivens,
            self.__min.value(),
            self.__max.value(),
        )
        if result == 1:
            _logger.info('Done.')

        elif result == -1:
            QMessageBox.critical(
                self, __product__, f'Invalid driver {self.__driver.text()}'
            )
            return

        elif result == -2:
            QMessageBox.critical(self, __product__, 'Driven has not animation.')
            return


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    driver: str,
    drivens: list[str],
    min_value: float = 0.0,
    max_value: float = 1.0,
) -> int:
    '''Apply'''

    if not cmds.objExists(driver):
        return -1

    all_keys: list[float] = cmds.keyframe(drivens, query=True, shape=True) or []
    if not all_keys:
        return -2

    fps: int = utility.get_fps()
    min_frame: float = min(all_keys)
    max_frame: float = max(all_keys)

    cmds.keyframe(
        drivens, shape=True, relative=True, timeChange=min_value - min_frame
    )
    try:
        cmds.scaleKey(
            drivens,
            shape=True,
            timePivot=min_value,
            timeScale=((max_value - min_value) / (max_frame - min_frame)),
        )
    except RuntimeError:
        cmds.scaleKey(drivens, shape=True, timePivot=min_value, timeScale=0)

    driven_args: list[list[str]] = []
    driven_kwargs: list[dict[str, Any]] = []
    tangent_args: list[list[str]] = []
    tangent_kwargs: list[dict[str, Any]] = []
    anim_curves: list[str] = cmds.keyframe(
        drivens, query=True, shape=True, name=True
    )
    delete_curves: list[str] = []
    for anim_curve in anim_curves:
        key_times: list[float] = cmds.keyframe(anim_curve, query=True)
        if not key_times:
            continue

        driven_attr: list[str] = cmds.listConnections(anim_curve, plugs=True)
        for key_time in key_times:
            time: tuple[float, float] = (key_time, key_time)
            key_values: list[Any] = cmds.keyframe(
                anim_curve, time=time, query=True, eval=True
            )
            in_tangent_type: list[str] = cmds.keyTangent(
                anim_curve, time=time, query=True, inTangentType=True
            )
            out_tangent_type: list[str] = cmds.keyTangent(
                anim_curve, time=time, query=True, outTangentType=True
            )
            ix: list[float] = cmds.keyTangent(
                anim_curve, time=time, query=True, ix=True
            )
            iy: list[float] = cmds.keyTangent(
                anim_curve, time=time, query=True, iy=True
            )
            ox: list[float] = cmds.keyTangent(
                anim_curve, time=time, query=True, ox=True
            )
            oy: list[float] = cmds.keyTangent(
                anim_curve, time=time, query=True, oy=True
            )

            driven_args.append([driven_attr[0]])
            driven_kwargs.append(
                {
                    'currentDriver': driver,
                    'value': key_values[0],
                    'driverValue': key_time,
                }
            )

            tangent_args.append([driven_attr[0]])
            tangent_kwargs.append(
                {
                    'edit': True,
                    'float': time,
                    'inTangentType': in_tangent_type[0],
                    'outTangentType': out_tangent_type[0],
                    'ix': ix[0] * fps,
                    'iy': iy[0],
                    'ox': ox[0] * fps,
                    'oy': oy[0],
                }
            )
        delete_curves.append(anim_curve)

    cmds.delete(*delete_curves)
    for args, kwargs in zip(driven_args, driven_kwargs):
        cmds.setDrivenKeyframe(*args, **kwargs)

    for args, kwargs in zip(tangent_args, tangent_kwargs):
        cmds.keyTangent(*args, **kwargs)

    cmds.dgdirty(allPlugs=True)
    return 1


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
