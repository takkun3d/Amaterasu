# ==============================================================================
#
# Motion Denoiser
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import math
import cmath

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import (
        QWidget,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QLabel,
        QSlider,
        QCheckBox,
        QPushButton,
        QHBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import (
            QWidget,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox,
            QLabel,
            QSlider,
            QCheckBox,
            QPushButton,
            QHBoxLayout,
        )

try:
    import numpy as np

    HAS_NUMPY: bool = True

except ImportError:
    HAS_NUMPY = False

from maya import cmds
from ..lib import parser, widgets
from ..development import package_installer


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Motion Denoiser'
__version__: str = '1.00'
__doc__ = (
    'Removes noise and jitter from animation curves to create smooth motion.'
)
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class CurveSmoother:
    '''Provides signal processing algorithms to smooth animation curve data.'''

    @staticmethod
    def moving_average(
        data: list[float], window_size: int, strength: float = 1.0
    ) -> list[float]:
        '''
        Simple Moving Average
        The simplest smoothing method that calculates the average of values within a specified window.
        '''
        window_size = max(3, window_size)
        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # Make kernel. windows_size=5 : [0.2, 0.2, 0.2, 0.2, 0.2]
            kernel: Any = np.ones(window_size) / window_size

            # Padding
            # Extend the data by copying the edge values.
            pad_size: int = window_size // 2
            padded: Any = np.pad(np_data, (pad_size, pad_size), mode='edge')

            # Convolution
            # Compute only the valid range.
            new_data = np.convolve(padded, kernel, mode='valid')
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()

        else:
            result: list[float] = []
            offset: int = window_size // 2
            for i in range(len(data)):
                start: int = max(0, i - offset)
                end: int = min(len(data), i + offset + 1)
                segment: list[float] = data[start:end]
                result.append(sum(segment) / len(segment))

            for i in range(len(result)):
                result[i] = data[i] * (1.0 - strength) + result[i] * strength
            return result

    @staticmethod
    def gaussian(
        data: list[float], window_size: int, sigma: float, strength: float = 1.0
    ) -> list[float]:
        '''
        Gaussian Convolution
        Mix with the center being dense, fading out towards the edges.
        '''
        # Force an odd window size to prevent center shift.
        window_size = max(3, window_size)
        if window_size % 2 == 0:
            window_size += 1

        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # Generate the bell curve values centered at zero.
            # [-3, -2, -1, 0, 1, 2, 3]
            x: Any = np.arange(-window_size // 2 + 1, window_size // 2 + 1)

            # Gaussian function formula : e^(-x^2 / 2σ^2)
            kernel: Any = np.exp(-(x**2) / (2 * sigma**2))

            # Normalization
            kernel /= np.sum(kernel)

            # Padding
            # Extend the data by copying the edge values.
            pad_size: int = window_size // 2
            padded = np.pad(np_data, (pad_size, pad_size), mode='edge')

            # Convolution
            # Compute only the valid range.
            new_data = np.convolve(padded, kernel, mode='valid')
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()

        else:
            kernel: list[float] = []
            center: int = window_size // 2
            for i in range(window_size):
                x: int = i - center
                weight: float = math.exp(-(x**2) / (2 * sigma**2))
                kernel.append(weight)

            k_sum: float = sum(kernel)
            kernel = [w / k_sum for w in kernel]

            result: list[float] = []
            offset: int = window_size // 2
            N: int = len(data)
            for i in range(N):
                val: float = 0.0
                w_sum: float = 0.0
                for k in range(window_size):
                    idx: int = i + (k - offset)
                    if 0 <= idx < N:
                        val += data[idx] * kernel[k]
                        w_sum += kernel[k]
                result.append(val / w_sum)

            for i in range(len(result)):
                result[i] = data[i] * (1.0 - strength) + result[i] * strength
            return result

    @staticmethod
    def fft_cutoff(
        data: list[float], cutoff_ratio: float, strength: float = 1.0
    ) -> list[float]:
        '''
        Frequency Domain Filter
        Transform time-domain data into frequency and cut off high-frequency noise.
        '''
        N: int = len(data)
        keep: int = int(N * cutoff_ratio)

        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # FFT
            fft_data: Any = np.fft.fft(np_data)

            # Cut off
            # [Low freq ... High freq ... Low freq]
            fft_data[keep : N - keep] = 0

            # IFFT
            # Inverse transform to the time domain.
            # The result is complex, so extract the real component.
            new_data = np.fft.ifft(fft_data).real
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()

        else:
            freqs: list[float] = []
            for k in range(N):
                s: float = 0.0
                for n in range(N):
                    s += data[n] * cmath.exp(-2j * math.pi * k * n / N)
                freqs.append(s)

            filtered: list[float] = []
            for k in range(N):
                if k < keep or k > (N - keep):
                    filtered.append(freqs[k])
                else:
                    filtered.append(0)

            result: list[float] = []
            for n in range(N):
                ss: complex = 0.0
                for k in range(N):
                    ss += filtered[k] * cmath.exp(2j * math.pi * k * n / N)
                result.append(ss.real / N)

            for i in range(len(result)):
                result[i] = data[i] * (1.0 - strength) + result[i] * strength
            return result


class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    algorithm: parser.Variant[int] = parser.Variant(2)
    ma_radius: parser.Variant[int] = parser.Variant(1)
    g_radius: parser.Variant[int] = parser.Variant(2)
    g_sigma: parser.Variant[float] = parser.Variant(3.0)
    lpf_cutoff: parser.Variant[float] = parser.Variant(0.2)
    strength: parser.Variant[int] = parser.Variant(100)
    hierarchy: parser.Variant[bool] = parser.Variant(True)


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
        self.__main_layout: widgets.FormLayout = widgets.FormLayout(
            option_widget
        )

        if not HAS_NUMPY:
            notice_layout: QHBoxLayout = QHBoxLayout(self)
            self.__main_layout.addRow(notice_layout)

            label: QLabel = QLabel(
                'Processing will be slower without NumPy.',
                self,
            )
            label.setStyleSheet('color: #FF5555; font-weight: bold;')
            notice_layout.addWidget(label)

            button: QPushButton = QPushButton('Install', self)
            button.setMaximumWidth(70)
            button.clicked.connect(package_installer.main)
            notice_layout.addWidget(button)

            self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__algorithm: QComboBox = QComboBox(self)
        self.__algorithm.addItem('Moving Average')
        self.__algorithm.addItem('Gaussian')
        self.__algorithm.addItem('Low-Pass Filter')
        self.__algorithm.currentIndexChanged.connect(self.set_valid_options)
        self.__main_layout.addRow(
            widgets.FormLabel('Algorithm'), self.__algorithm
        )

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__param_stack: widgets.AdaptiveStackedWidget = (
            widgets.AdaptiveStackedWidget(self)
        )
        self.__main_layout.addRow(self.__param_stack)

        # Moving Average
        widget: QWidget = QWidget(self)
        self.__param_stack.addWidget(widget)
        layout: widgets.FormLayout = widgets.FormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__ma_radius: QSpinBox = QSpinBox(self)
        self.__ma_radius.setMinimumWidth(70)
        self.__ma_radius.setRange(1, 99)
        layout.addRow(widgets.FormLabel('Radius'), self.__ma_radius)

        # Gaussian
        widget: QWidget = QWidget(self)
        self.__param_stack.addWidget(widget)
        layout: widgets.FormLayout = widgets.FormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__g_radius: QSpinBox = QSpinBox(self)
        self.__g_radius.setMinimumWidth(70)
        self.__g_radius.setRange(1, 99)
        layout.addRow(widgets.FormLabel('Radius'), self.__g_radius)

        self.__g_sigma: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__g_sigma.setMinimumWidth(70)
        self.__g_sigma.setRange(0.1, 20.0)
        layout.addRow(widgets.FormLabel('Blur'), self.__g_sigma)

        # Low-Pass Filter
        widget: QWidget = QWidget(self)
        self.__param_stack.addWidget(widget)
        layout: widgets.FormLayout = widgets.FormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__lpf_cutoff: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__lpf_cutoff.setMinimumWidth(70)
        self.__lpf_cutoff.setRange(0.01, 1.0)
        self.__lpf_cutoff.setSingleStep(0.05)
        layout.addRow(widgets.FormLabel('Cutoff'), self.__lpf_cutoff)

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        # Strength
        strength_layout: QHBoxLayout = QHBoxLayout(self)

        self.__strength: QSlider = QSlider(Qt.Horizontal, self)
        self.__strength.setRange(0, 100)
        strength_layout.addWidget(self.__strength)

        strength_label: QLabel = QLabel('', self)
        strength_label.setMinimumWidth(40)
        strength_label.setAlignment(Qt.AlignCenter)
        strength_layout.addWidget(strength_label)

        self.__strength.valueChanged.connect(
            lambda v: strength_label.setText(f'{v}%')
        )

        self.__main_layout.addRow(
            widgets.FormLabel('Strength'), strength_layout
        )

        # Hierarchy
        self.__hierarchy: QCheckBox = QCheckBox('Include Hierarchy', self)
        self.__main_layout.addRow('', self.__hierarchy)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__algorithm.setCurrentIndex(settings.algorithm.value())
        self.__ma_radius.setValue(settings.ma_radius.value())
        self.__g_radius.setValue(settings.g_radius.value())
        self.__g_sigma.setValue(settings.g_sigma.value())
        self.__lpf_cutoff.setValue(settings.lpf_cutoff.value())
        self.__strength.setValue(settings.strength.value())
        self.__hierarchy.setChecked(settings.hierarchy.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.algorithm.set_value(self.__algorithm.currentIndex())
        settings.ma_radius.set_value(self.__ma_radius.value())
        settings.g_radius.set_value(self.__g_radius.value())
        settings.g_sigma.set_value(self.__g_sigma.value())
        settings.lpf_cutoff.set_value(self.__lpf_cutoff.value())
        settings.strength.set_value(self.__strength.value())
        settings.hierarchy.set_value(self.__hierarchy.isChecked())
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
        index: int = self.__algorithm.currentIndex()
        self.__param_stack.setCurrentIndex(index)

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
def apply(
    curve: str,
    algorithm: int,
    param: dict[str, Any],
    strength: float,
) -> bool:
    '''Applies the selected smoothing filter to the specified animation curve.'''
    times: list[float] = cmds.keyframe(curve, query=True, timeChange=True)
    values: list[float] = cmds.keyframe(curve, query=True, valueChange=True)
    if not times or len(values) < 3:
        return False

    if algorithm == 0:
        new_values: list[float] = CurveSmoother.moving_average(
            values,
            param['MA_RADIUS'] * 2 + 1,
            strength,
        )

    elif algorithm == 1:
        new_values = CurveSmoother.gaussian(
            values,
            param['G_RADIUS'] * 2 + 1,
            param['G_SIGMA'],
            strength,
        )

    else:
        new_values = CurveSmoother.fft_cutoff(
            values,
            param['LPF_CUTOFF'],
            strength,
        )

    for i, t in enumerate(times):
        cmds.keyframe(
            curve,
            edit=True,
            time=(t, t),
            valueChange=new_values[i],
        )

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    settings: Settings = Settings.instance(__name__, True)
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node or keyframe to appling anim filter.')
        return

    if settings.hierarchy.value():
        children: list[str] = (
            cmds.listRelatives(*selection, allDescendents=True, fullPath=True)
            or []
        )
        selection.extend(children)

    curves: list[str] = cmds.keyframe(*selection, query=True, name=True) or []
    if not curves:
        _logger.error('Does not exist animation curve.')
        return

    algorithm: int = settings.algorithm.value()
    param: dict[str, Any] = {
        'MA_RADIUS': settings.ma_radius.value(),
        'G_RADIUS': settings.g_radius.value(),
        'G_SIGMA': settings.g_sigma.value(),
        'LPF_CUTOFF': settings.lpf_cutoff.value(),
    }
    strength: float = settings.strength.value() / 100.0

    cmds.waitCursor(state=True)
    cmds.refresh(suspend=True)
    try:
        for curve in curves:
            apply(curve, algorithm, param, strength)

        _logger.info(f'Done : Smoothed {len(curves)} curves.')

    except Exception as e:
        _logger.error(e)

    finally:
        cmds.waitCursor(state=False)
        cmds.refresh(suspend=False)
        cmds.refresh()
