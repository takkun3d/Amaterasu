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
"""Modifies keyframe values between selected keyframes."""

from __future__ import annotations
import random
from typing import Any
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, maths, framework, utils, widgets

__product__: str = "Between Keyframe"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Between Keyframe tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class AnimationCurveData:
    """Stores data for a selected animation curve."""

    def __init__(self, curve: str) -> None:
        """Initializes the curve data based on the provided curve name.

        Args:
            curve (str): The name of the animation curve.
        """
        self.curve_name: str = curve
        self.indexes: list[int] = cmds.keyframe(
            curve, query=True, selected=True, indexValue=True
        )  # type: ignore
        self.times: list[float] = cmds.keyframe(
            curve, query=True, selected=True, timeChange=True
        )  # type: ignore
        self.values: list[float] = cmds.keyframe(
            curve, query=True, selected=True, valueChange=True
        )  # type: ignore

        self.all_indexes: list[int] = cmds.keyframe(
            curve, query=True, indexValue=True
        )  # type: ignore
        self.all_times: list[float] = cmds.keyframe(
            curve, query=True, timeChange=True
        )  # type: ignore
        self.all_values: list[float] = cmds.keyframe(
            curve, query=True, valueChange=True
        )  # type: ignore

        self.start_index: int = self.indexes[0] - 1
        if self.start_index < self.all_indexes[0]:
            self.start_index = self.all_indexes[0]

        self.end_index: int = self.indexes[-1] + 1
        if self.end_index > self.all_indexes[-1]:
            self.end_index = self.all_indexes[-1]

        self.start_time: float = self.all_times[self.start_index]
        self.end_time: float = self.all_times[self.end_index]
        self.start_value: float = self.all_values[self.start_index]
        self.end_value: float = self.all_values[self.end_index]


class Between:
    """Base class for evaluating and modifying keyframes between extremes."""

    def __init__(self) -> None:
        """Initializes the base between logic."""
        self.__current_show_buffer_curves: str = "off"
        self.__data: list[AnimationCurveData] = []
        self.__interpolation: maths.Ease = maths.Ease()

    def drag_start(self) -> None:
        """Executes operations when the drag event starts."""
        anim_curves: list[str] = cmds.keyframe(
            query=True, selected=True, name=True
        )  # type: ignore
        if not anim_curves:
            return

        cmds.undoInfo(openChunk=True)
        cmds.bufferCurve(animation="keys", overwrite=True)
        self.__current_show_buffer_curves = cmds.animCurveEditor(
            "graphEditor1GraphEd", query=True, showBufferCurves=True
        )  # type: ignore
        cmds.animCurveEditor(
            "graphEditor1GraphEd", edit=True, showBufferCurves="on"
        )

        for anim_curve in anim_curves:
            data = AnimationCurveData(anim_curve)
            self.__data.append(data)

    def drag_move(self, slider_value: float) -> None:
        """Executes operations during the drag move event.

        Args:
            slider_value (float): The current value from the UI slider.
        """

    def drag_end(self) -> None:
        """Executes operations when the drag event ends."""
        if not self.__data:
            return

        self.__data = []
        cmds.bufferCurve(animation="keys", overwrite=True)
        cmds.animCurveEditor(
            "graphEditor1GraphEd",
            edit=True,
            showBufferCurves=self.__current_show_buffer_curves,
        )
        cmds.undoInfo(closeChunk=True)

    def data(self) -> list[AnimationCurveData]:
        """Retrieves the list of animation curve data.

        Returns:
            list[AnimationCurveData]: A list containing curve data.
        """
        return self.__data

    def set_data(self, data: list[AnimationCurveData]) -> None:
        """Sets the animation curve data list.

        Args:
            data (list[AnimationCurveData]): A list of animation curve data.
        """
        self.__data = data

    def interpolation(self) -> maths.Ease:
        """Retrieves the active ease interpolation instance.

        Returns:
            maths.Ease: The interpolation logic instance.
        """
        return self.__interpolation

    def set_interpolation(self, interpolation: maths.Ease) -> None:
        """Sets the ease interpolation instance.

        Args:
            interpolation (maths.Ease): An instance of an ease interpolation class.
        """
        self.__interpolation = interpolation


class BetweenToDefault(Between):
    """Evaluates keyframes towards their default value."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations for default evaluation.

        Args:
            slider_value (float): The current value from the UI slider.
        """
        for data in self.data():
            for index, value in zip(data.indexes, data.values):
                value = value + ((0.0 - value) * (slider_value / 100.0))
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),  # type: ignore
                    valueChange=value,
                )


class BetweenToLinear(Between):
    """Evaluates keyframes towards a linear transition."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations for linear evaluation.

        Args:
            slider_value (float): The current value from the UI slider.
        """
        for data in self.data():
            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                factor: float = slider_value / 100.0 * 2.0
                remap_value: float = maths.remap(
                    data.start_time,
                    data.start_value,
                    data.end_time,
                    data.end_value,
                    time,
                )

                v: float = maths.lerp(value, remap_value, factor)
                if value >= remap_value:
                    v = max(v, remap_value)
                else:
                    v = min(v, remap_value)

                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),  # type: ignore
                    valueChange=v,
                )


class GaussNoise(Between):
    """Applies Gaussian noise to the selected keyframes."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations for noise evaluation.

        Args:
            slider_value (float): The current value from the UI slider.
        """
        factor: float = slider_value / 100.0
        for data in self.data():
            mu: float = 0.0
            sigma: float = abs(data.start_value - data.end_value)
            if sigma == 0:
                sigma = 1.0

            sigma = sigma * factor

            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                random.seed(f"{data.curve_name}{index}{time}")
                value = value + random.gauss(mu, sigma)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),  # type: ignore
                    valueChange=value,
                )


class Smooth(Between):
    """Smooths the curve values over time."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations for curve smoothing.

        Args:
            slider_value (float): The current value from the UI slider.
        """
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
                pos_value: Any = data.all_values[pos_index]

                smooth_value: float = (pre_value + value + pos_value) / 3.0
                value = maths.lerp(value, smooth_value, factor)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),  # type: ignore
                    valueChange=value,
                )


class BetweenEase(Between):
    """Applies an easing interpolation to the selected keyframes."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations with easing interpolation.

        Args:
            slider_value (float): The current value from the UI slider.
        """
        interpolation: maths.Ease = self.interpolation()
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
                    index=(index, index),  # type: ignore
                    valueChange=value,
                )


class CycleEase(BetweenEase):
    """Applies a cycling easing interpolation."""

    def drag_start(self) -> None:
        """Overrides drag start event to loop start and end values."""
        super().drag_start()
        new_data: list[AnimationCurveData] = []
        for data in self.data():
            data.start_value = data.all_values[-1]
            data.end_value = data.all_values[0]
            new_data.append(data)

        self.set_data(new_data)


class ReplaceEase(Between):
    """Replaces current values smoothly using ease interpolations."""

    def drag_move(self, slider_value: float) -> None:
        """Executes drag move operations for value replacement.

        Args:
            slider_value (float): The current value from the UI slider.
        """
        interpolation: maths.Ease = self.interpolation()
        factor: float = abs(slider_value) / 100.0 * 5.0
        for data in self.data():
            for index, time, value in zip(
                data.indexes, data.times, data.values
            ):
                time_factor: float = (time - data.start_time) / (
                    data.end_time - data.start_time
                )
                remap_value: float = maths.remap(
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

                value = remap_value + factor * (remap_value - time_factor)
                value = maths.clamp(value, data.start_value, data.end_value)
                cmds.keyframe(
                    data.curve_name,
                    edit=True,
                    index=(index, index),  # type: ignore
                    valueChange=value,
                )


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Between Keyframe tool."""

    method_icons: list[str] = [
        "a_between_ease.png",
        "a_between_replace.png",
        "a_between_linear.png",
        "a_between_flat.png",
        "a_between_noise.png",
        "a_between_smooth.png",
        "a_between_cycle.png",
    ]
    method_tooltips: list[str] = [
        "Between Offset to Easing Curve.",
        "Between to Easing Curve.",
        "Between to Linear.",
        "Between to Default.",
        "Add Gauss Noise.",
        "Smooth Curve.",
        "Between to Cycle Curve.",
    ]
    interpolation_icons: list[str] = [
        "a_quadratic.png",
        "a_cubic.png",
        "a_exponential.png",
    ]
    interpolation_tooltips: list[str] = [
        "Quadratic",
        "Cubic",
        "Exponential",
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
    interpolations: list[maths.Ease] = [
        maths.EaseQuadratic(),
        maths.EaseCubic(),
        maths.EaseExponential(),
    ]

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): A unique identifier for restoring
                window states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(100, 10)
        self.__method: QtWidgets.QButtonGroup
        self.__interpolation: QtWidgets.QButtonGroup
        self.__slider: widgets.DragSlider
        self.__active_between: Between = self.betweens[0]

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        main_layout.addLayout(button_layout)

        self.__method = QtWidgets.QButtonGroup(self)
        self.__method.idClicked.connect(self.change_method)

        for i, (icon, tooltip) in enumerate(
            zip(self.method_icons, self.method_tooltips)
        ):
            button: widgets.IconButton = widgets.IconButton(self)
            button.set_icon(dcc.get_icon_path(icon))
            button.setToolTip(tooltip)
            button.setIconSize(QtCore.QSize(24, 24))
            button.setCheckable(True)
            button.setChecked(i == 0)
            button_layout.addWidget(button)
            self.__method.addButton(button, i)

        button_layout.addWidget(widgets.VerticalLine(self))

        self.__interpolation = QtWidgets.QButtonGroup(self)
        self.__interpolation.idClicked.connect(self.change_interpolation)

        for i, (icon, tooltip) in enumerate(
            zip(self.interpolation_icons, self.interpolation_tooltips)
        ):
            button = widgets.IconButton(self)
            button.set_icon(dcc.get_icon_path(icon))
            button.setToolTip(tooltip)
            button.setIconSize(QtCore.QSize(24, 24))
            button.setCheckable(True)
            button.setChecked(i == 0)
            button_layout.addWidget(button)
            self.__interpolation.addButton(button, i)

        button_layout.addStretch(True)

        self.__slider = widgets.DragSlider(self)
        self.__slider.drag_start.connect(self.drag_start)
        self.__slider.drag_move.connect(self.drag_move)
        self.__slider.drag_end.connect(self.drag_end)
        main_layout.addWidget(self.__slider)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        self.change_method(0)
        self.change_interpolation(0)

    @QtCore.Slot(int)
    def change_method(self, index: int) -> None:
        """Slot to handle changing the active method.

        Args:
            index (int): The index of the selected method.
        """
        self.__active_between = self.betweens[index]
        for button in self.__interpolation.buttons():
            button.setEnabled(index in [0, 1, 6])

        self.change_interpolation(self.__interpolation.checkedId())

    @QtCore.Slot(int)
    def change_interpolation(self, index: int) -> None:
        """Slot to handle changing the interpolation logic.

        Args:
            index (int): The index of the selected interpolation method.
        """
        self.__active_between.set_interpolation(self.interpolations[index])

    @QtCore.Slot()
    def drag_start(self) -> None:
        """Slot triggered when the slider drag starts."""
        self.__active_between.drag_start()

    @QtCore.Slot(int)
    def drag_move(self, value: int) -> None:
        """Slot triggered when the slider is moved.

        Args:
            value (int): The current value of the slider.
        """
        self.__active_between.drag_move(float(value))

    @QtCore.Slot()
    def drag_end(self) -> None:
        """Slot triggered when the slider drag ends."""
        self.__active_between.drag_end()


def main(unique_id: str = "") -> None:
    """Initializes and displays the main application window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
