# ==============================================================================
#
# Between Keyframe
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import random

try:
    from PySide2.QtCore import Qt, Slot, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QSlider,
        QButtonGroup,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QSlider,
            QButtonGroup,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Between Keyframe'
__version__: str = '1.10'
__doc__ = 'Modify keyframe between selected keyframes.'
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


class Ease:
    '''Ease Base Class.'''

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        '''Return ease in.'''
        return 0.0

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        '''Return ease out.'''
        return 0.0

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        '''Return ease in out.'''
        return 0.0


class EaseQuadratic(Ease):
    '''
    Ease Quadratic.
    Reference:
    http://nakamura001.hatenablog.com/entry/20111117/1321539246

    t = time
    b = start value
    c = difference value start to end.
    d = tween total time.
    '''

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        t /= d
        return c * t * t + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        t /= d
        return -c * t * (t - 2.0) + b

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        t /= d / 2.0
        if t < 1:
            return c / 2.0 * t * t + b
        t = t - 1
        return -c / 2.0 * (t * (t - 2) - 1) + b


class EaseCubic(Ease):
    '''
    Ease EaseCubic.
    Reference:
    http://nakamura001.hatenablog.com/entry/20111117/1321539246

    t = time
    b = start value
    c = difference value start to end.
    d = tween total time.
    '''

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        t /= d
        return c * t * t * t + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        t /= d
        t = t - 1
        return c * (t * t * t + 1) + b

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        t /= d / 2.0
        if t < 1:
            return c / 2.0 * t * t * t + b
        t = t - 2
        return c / 2.0 * (t * t * t + 2) + b


class EaseExponential(Ease):
    '''
    Ease Exponential.
    Reference:
    http://nakamura001.hatenablog.com/entry/20111117/1321539246

    t = time
    b = start value
    c = difference value start to end.
    d = tween total time.
    '''

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        return c * 2 ** (10 * (t / d - 1)) + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        return float(c * (-(2.0 ** (-10.0 * t / d)) + 1.0) + b)

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        t /= d / 2.0
        if t < 1:
            return float(c / 2.0 * 2.0 ** (10.0 * (t - 1.0)) + b)

        t = t - 1
        return float(c / 2.0 * (-(2.0 ** (-10.0 * t)) + 2.0) + b)


class AnimationCurveData:
    '''Selected keyframe datas'''

    def __init__(self, curve: str) -> None:
        '''Initialize'''
        self.curve_name: str = curve
        self.indexes: list[int] = cmds.keyframe(
            curve, query=True, selected=True, indexValue=True
        )
        self.times: list[float] = cmds.keyframe(
            curve, query=True, selected=True, timeChange=True
        )
        self.values: list[Any] = cmds.keyframe(
            curve, query=True, selected=True, valueChange=True
        )

        self.all_indexes: list[int] = cmds.keyframe(
            curve, query=True, indexValue=True
        )
        self.all_times: list[float] = cmds.keyframe(
            curve, query=True, timeChange=True
        )
        self.all_values: list[Any] = cmds.keyframe(
            curve, query=True, valueChange=True
        )

        self.start_index: int = self.indexes[0] - 1
        if self.start_index < self.all_indexes[0]:
            self.start_index = self.all_indexes[0]

        self.end_index: int = self.indexes[-1] + 1
        if self.end_index > self.all_indexes[-1]:
            self.end_index = self.all_indexes[-1]

        self.start_time: float = self.all_times[self.start_index]
        self.end_time: float = self.all_times[self.end_index]
        self.start_value: Any = self.all_values[self.start_index]
        self.end_value: Any = self.all_values[self.end_index]


class Between:
    '''Between Base Class'''

    def __init__(self) -> None:
        '''Initialize'''
        self.__current_show_buffer_curves: str = 'off'
        self.__data: list[AnimationCurveData] = []
        self.__interpolation: Ease = Ease()

    def drag_start(self) -> None:
        '''Drag Start Event'''
        anim_curves: list[str] = cmds.keyframe(
            query=True, selected=True, name=True
        )
        if not anim_curves:
            return

        cmds.undoInfo(openChunk=True)
        cmds.bufferCurve(animation='keys', overwrite=True)
        self.__current_show_buffer_curves = cmds.animCurveEditor(
            'graphEditor1GraphEd', query=True, showBufferCurves=True
        )
        cmds.animCurveEditor(
            'graphEditor1GraphEd', edit=True, showBufferCurves='on'
        )

        for anim_curve in anim_curves:
            data = AnimationCurveData(anim_curve)
            self.__data.append(data)

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.'''

    def drag_end(self) -> None:
        '''Drag end event.'''
        if not self.__data:
            return

        self.__data = []
        cmds.bufferCurve(animation='keys', overwrite=True)
        cmds.animCurveEditor(
            'graphEditor1GraphEd',
            edit=True,
            showBufferCurves=self.__current_show_buffer_curves,
        )
        cmds.undoInfo(closeChunk=True)

    def data(self) -> list[AnimationCurveData]:
        '''Return AnimationCurveData list.'''
        return self.__data

    def set_data(self, data: list[AnimationCurveData]) -> None:
        '''Set AnimationCurveData list.'''
        self.__data = data

    def interpolation(self) -> Ease:
        '''Return interpolation'''
        return self.__interpolation

    def set_interpolation(self, interpolation: Ease) -> None:
        '''Set interpolation.'''
        self.__interpolation = interpolation


class BetweenToDefault(Between):
    '''Between to default value.'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        for data in self.data():
            for index, value in zip(data.indexes, data.values):
                value = value + ((0.0 - value) * (slider_value / 100.0))
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=value,
                )


class BetweenToLinear(Between):
    '''Between to linear.'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        for data in self.data():
            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                factor = slider_value / 100.0 * 2.0
                lerpValue = lerp(
                    data.start_time,
                    data.start_value,
                    data.end_time,
                    data.end_value,
                    time,
                )

                v: float = between(value, lerpValue, factor)
                if value >= lerpValue:
                    v = max(v, lerpValue)
                else:
                    v = min(v, lerpValue)

                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=v,
                )


class GaussNoise(Between):
    '''Gauss Noise'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        factor: float = slider_value / 100.0
        for data in self.data():
            mu = 0.0
            sigma = abs(data.start_value - data.end_value)
            if sigma == 0:
                sigma = 1.0
            sigma = sigma * factor

            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                random.seed(f'{data.curve_name}{index}{time}')
                value = value + random.gauss(mu, sigma)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=value,
                )


class Smooth(Between):
    '''Smooth'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        factor: float = slider_value / 100.0
        for data in self.data():
            for index, value in zip(data.indexes, data.values):
                pre_index: int = index - 1
                if pre_index < data.all_indexes[0]:
                    continue
                pre_value: Any = data.all_values[pre_index]

                pos_index: int = index + 1
                if pos_index > data.all_indexes[-1]:
                    continue
                pos_value = data.all_values[pos_index]

                smoothValue: float = (pre_value + value + pos_value) / 3.0
                value = between(value, smoothValue, factor)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=value,
                )


class BetweenEase(Between):
    '''Between ease.'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        interpolation = self.interpolation()
        factor: float = abs(slider_value) / 100.0 * 2.0
        for data in self.data():
            step: float = data.end_value - data.start_value
            time_range: float = data.end_time - data.start_time
            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                time_factor: float = (time - data.start_time) / time_range

                if slider_value >= 0:
                    time_factor = interpolation.ease_in(time_factor, 0, 1, 1)
                    value = value + (step * factor * time_factor)
                    if data.start_value < data.end_value:
                        value = min(value, data.end_value)
                    else:
                        value = max(value, data.end_value)

                else:
                    time_factor = interpolation.ease_out(time_factor, 1, -1, 1)
                    value = value + (step * factor * -1 * time_factor)
                    if data.start_value < data.end_value:
                        value = max(value, data.start_value)
                    else:
                        value = min(value, data.start_value)

                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=value,
                )


class CycleEase(BetweenEase):
    '''Cycle Ease'''

    def drag_start(self) -> None:
        '''Drag start event.[override]'''
        super().drag_start()
        new_data: list[AnimationCurveData] = []
        for data in self.data():
            data.start_value = data.all_values[-1]
            data.end_value = data.all_values[0]
            new_data.append(data)

        self.set_data(new_data)


class ReplaceEase(Between):
    '''Replace Ease'''

    def drag_move(self, slider_value: float) -> None:
        '''Drag move event.[override]'''
        interpolation = self.interpolation()
        factor: float = abs(slider_value) / 100.0 * 5.0
        for data in self.data():
            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                time_factor: float = (time - data.start_time) / (
                    data.end_time - data.start_time
                )
                lerp_value: float = lerp(
                    data.start_time,
                    data.start_value,
                    data.end_time,
                    data.end_value,
                    time,
                )

                if slider_value >= 0:
                    time_factor = interpolation.ease_in(
                        time_factor,
                        data.start_value,
                        (data.end_value - data.start_value),
                        1,
                    )

                else:
                    time_factor = interpolation.ease_out(
                        time_factor,
                        data.start_value,
                        (data.end_value - data.start_value),
                        1,
                    )

                value = lerp_value + factor * (lerp_value - time_factor)
                value = clamp(value, data.start_value, data.end_value)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),
                    valueChange=value,
                )


class BetweenSlider(QSlider):
    '''Brween Slider widget.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setOrientation(Qt.Horizontal)
        self.setRange(-100, 100)
        self.setValue(0)
        self.sliderPressed.connect(self.drag_start)
        self.sliderMoved.connect(self.drag_move)
        self.sliderReleased.connect(self.drag_end)
        self.__between: Between = Between()

    def between(self) -> Between:
        '''Return between object.'''
        return self.__between

    def set_between(self, between_value: Between) -> None:
        '''Set between object.'''
        self.__between = between_value

    def set_interpolation(self, interpolation: Ease) -> None:
        '''Set interpolation object.'''
        self.__between.set_interpolation(interpolation)

    @Slot()
    def drag_start(self) -> None:
        '''Drag start event.'''
        self.__between.drag_start()

    @Slot()
    def drag_move(self) -> None:
        '''Drag move event.'''
        self.__between.drag_move(self.value())

    @Slot()
    def drag_end(self) -> None:
        '''Drag end event.'''
        self.__between.drag_end()
        self.setValue(0)


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    method_icons: list[str] = [
        'a_between_ease.png',
        'a_between_replace.png',
        'a_between_linear.png',
        'a_between_flat.png',
        'a_between_noise.png',
        'a_between_smooth.png',
        'a_between_cycle.png',
    ]
    method_tooltips: list[str] = [
        'Between Offset to Easing Curve.',
        'Between to Easing Curvce',
        'Between to Linear',
        'Between to Default',
        'Add Gauss Noise',
        'Smooth Curve',
        'Between to Cycle Curve',
    ]
    interpolation_icons: list[str] = [
        'a_quadratic.png',
        'a_cubic.png',
        'a_exponential.png',
    ]
    interpolation_tooltips: list[str] = [
        'Quadratic',
        'Cubic',
        'Exponential',
    ]
    betweens: list[Between] = [
        BetweenEase(),
        ReplaceEase(),
        BetweenToLinear(),
        BetweenToDefault(),
        GaussNoise(),
        Smooth(),
        CycleEase(),
    ]
    interpolations: list[Ease] = [
        EaseQuadratic(),
        EaseCubic(),
        EaseExponential(),
    ]

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
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        button_layout: QHBoxLayout = QHBoxLayout(self)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        main_layout.addLayout(button_layout)

        self.__method_grp: QButtonGroup = QButtonGroup(self)
        self.__method_grp.idClicked[int].connect(self.change_method_callback)

        i: int = 0
        for icon, tooltip in zip(self.method_icons, self.method_tooltips):
            button: widgets.IconButton = widgets.IconButton(self)
            button.set_icon(icon)
            button.setToolTip(tooltip)
            button.setIconSize(QSize(24, 24))
            button.setCheckable(True)
            button.setChecked(i == 0)
            button_layout.addWidget(button)
            self.__method_grp.addButton(button, i)
            i += 1

        button_layout.addWidget(widgets.VerticalLine(self))

        self.__interpolation_grp: QButtonGroup = QButtonGroup(self)
        self.__interpolation_grp.idClicked[int].connect(
            self.change_interpolation_callback
        )

        i = 0
        for icon, tooltip in zip(
            self.interpolation_icons, self.interpolation_tooltips
        ):
            button = widgets.IconButton(self)
            button.set_icon(icon)
            button.setToolTip(tooltip)
            button.setIconSize(QSize(24, 24))
            button.setCheckable(True)
            button.setChecked(i == 0)
            button_layout.addWidget(button)
            self.__interpolation_grp.addButton(button, i)
            i += 1

        button_layout.addStretch(True)

        self.__slider: BetweenSlider = BetweenSlider(self)
        main_layout.addWidget(self.__slider)

        self.change_method_callback(0)
        self.change_interpolation_callback(0)

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

    @Slot(int)
    def change_method_callback(self, index: int) -> None:
        '''Change method callback.'''
        self.__slider.set_between(self.betweens[index])
        for button in self.__interpolation_grp.buttons():
            button.setEnabled(index in [0, 1, 6])

        self.change_interpolation_callback(self.__interpolation_grp.checkedId())

    @Slot(int)
    def change_interpolation_callback(self, index: int) -> None:
        '''Change Interpolation_callback'''
        self.__slider.set_interpolation(self.interpolations[index])

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def lerp(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    '''Return leap value of x-pointfrom two point.'''
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def between(x: float, y: float, f: float) -> float:
    '''
    Return between value of f-point from x to y.
    f = 0 to 1
    '''
    return (x * (1.0 - f)) + (y * f)


def clamp(value: float, start_value: float, end_value: float) -> float:
    '''Return clamp value from start to end.'''
    min_value: float = min(start_value, end_value)
    max_value: float = max(start_value, end_value)
    return max(min(value, max_value), min_value)


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
