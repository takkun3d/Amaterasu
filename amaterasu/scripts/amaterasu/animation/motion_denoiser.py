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
"""Removes noise and jitter from animation curves to create smooth motion."""

from __future__ import annotations
from typing import Any
import math
import cmath

try:
    import numpy as np
    import numpy.typing as npt

    HAS_NUMPY: bool = True

except ImportError:
    HAS_NUMPY = False

from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets
from amaterasu.development import package_installer

__product__: str = "Motion Denoiser"
__version__: str = "1.11"
_logger: utils.Logger = utils.get_logger(__product__)


class CurveSmoother:
    """Provides signal processing algorithms to smooth animation curve data."""

    @staticmethod
    def moving_average(
        data: list[float], window_size: int, strength: float = 1.0
    ) -> list[float]:
        """Calculates the simple moving average of the given data.

        This is the simplest smoothing method that calculates the average of
        values within a specified window.

        Args:
            data (list[float]): The input animation curve data to be smoothed.
            window_size (int): The size of the moving window.
            strength (float, optional): The blend strength. Defaults to 1.0.

        Returns:
            list[float]: The smoothed animation curve data.
        """
        window_size = max(3, window_size)
        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # Make kernel. windows_size=5 : [0.2, 0.2, 0.2, 0.2, 0.2]
            kernel: Any = np.ones(window_size) / window_size

            # Padding
            # Extend the data by copying the edge values.
            pad_size: int = window_size // 2
            padded: Any = np.pad(np_data, (pad_size, pad_size), mode="edge")

            # Convolution
            # Compute only the valid range.
            new_data: npt.NDArray[np.float64] = np.convolve(
                padded, kernel, mode="valid"
            )
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()  # type: ignore

        else:
            result: list[float] = []
            offset: int = window_size // 2
            for i in range(len(data)):
                start: int = max(0, i - offset)
                end: int = min(len(data), i + offset + 1)
                segment: list[float] = data[start:end]
                result.append(sum(segment) / len(segment))

            for i, res in enumerate(result):
                result[i] = data[i] * (1.0 - strength) + res * strength

            return result

    @staticmethod
    def gaussian(
        data: list[float], window_size: int, sigma: float, strength: float = 1.0
    ) -> list[float]:
        """Applies a Gaussian convolution to the given data.

        Mixes values with a higher density at the center, fading out towards
        the edges.

        Args:
            data (list[float]): The input animation curve data to be smoothed.
            window_size (int): The size of the moving window.
            sigma (float): The standard deviation of the Gaussian distribution.
            strength (float, optional): The blend strength. Defaults to 1.0.

        Returns:
            list[float]: The smoothed animation curve data.
        """
        # Force an odd window size to prevent center shift.
        window_size = max(3, window_size)
        if window_size % 2 == 0:
            window_size += 1

        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # Generate the bell curve values centered at zero.
            # [-3, -2, -1, 0, 1, 2, 3]
            x_np: Any = np.arange(-window_size // 2 + 1, window_size // 2 + 1)

            # Gaussian function formula : e^(-x^2 / 2σ^2)
            kernel_np: Any = np.exp(-(x_np**2) / (2 * sigma**2))

            # Normalization
            kernel_np /= np.sum(kernel_np)

            # Padding
            # Extend the data by copying the edge values.
            pad_size: int = window_size // 2
            padded: npt.NDArray[np.float64] = np.pad(
                np_data, (pad_size, pad_size), mode="edge"
            )

            # Convolution
            # Compute only the valid range.
            new_data: npt.NDArray[np.float64] = np.convolve(
                padded, kernel_np, mode="valid"
            )
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()  # type: ignore

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
            length: int = len(data)
            for i in range(length):
                val: float = 0.0
                w_sum: float = 0.0
                for k in range(window_size):
                    idx: int = i + (k - offset)
                    if 0 <= idx < length:
                        val += data[idx] * kernel[k]
                        w_sum += kernel[k]

                result.append(val / w_sum)

            for i, res in enumerate(result):
                result[i] = data[i] * (1.0 - strength) + res * strength

            return result

    @staticmethod
    def fft_cutoff(
        data: list[float], cutoff_ratio: float, strength: float = 1.0
    ) -> list[float]:
        """Filters out high-frequency noise using Fast Fourier Transform.

        Transforms time-domain data into the frequency domain and removes
        frequencies above the specified cutoff ratio.

        Args:
            data (list[float]): The input animation curve data to be smoothed.
            cutoff_ratio (float): The ratio of frequencies to keep.
            strength (float, optional): The blend strength. Defaults to 1.0.

        Returns:
            list[float]: The smoothed animation curve data.
        """
        length: int = len(data)
        keep: int = int(length * cutoff_ratio)

        if HAS_NUMPY:
            np_data: Any = np.array(data)

            # FFT
            fft_data: Any = np.fft.fft(np_data)

            # Cut off
            # [Low freq ... High freq ... Low freq]
            fft_data[keep : length - keep] = 0

            # IFFT
            # Inverse transform to the time domain.
            # The result is complex, so extract the real component.
            new_data: npt.NDArray[np.float64] = np.fft.ifft(fft_data).real
            new_data = np_data * (1.0 - strength) + new_data * strength
            return new_data.tolist()  # type: ignore

        else:
            freqs: list[complex] = []
            for k in range(length):
                s: complex = 0.0
                for n in range(length):
                    s += data[n] * cmath.exp(-2j * math.pi * k * n / length)

                freqs.append(s)

            filtered: list[complex] = []
            for k in range(length):
                if k < keep or k > (length - keep):
                    filtered.append(freqs[k])
                else:
                    filtered.append(0)

            result: list[float] = []
            for n in range(length):
                ss: complex = 0.0
                for k in range(length):
                    ss += filtered[k] * cmath.exp(2j * math.pi * k * n / length)

                result.append(ss.real / length)

            for i, res in enumerate(result):
                result[i] = data[i] * (1.0 - strength) + res * strength

            return result


class Settings(framework.ToolSettings):
    """Settings for the Motion Denoiser tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        algorithm (framework.Variant[int]): Index of the selected algorithm.
        ma_radius (framework.Variant[int]): Radius for average.
        g_radius (framework.Variant[int]): Radius for gaussian blur.
        g_sigma (framework.Variant[float]): Sigma for gaussian blur.
        lpf_cutoff (framework.Variant[float]): Cutoff ratio for LPF.
        strength (framework.Variant[int]): Blend strength percentage.
        hierarchy (framework.Variant[bool]): Include hierarchy state.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    algorithm: framework.Variant[int] = framework.Variant(2)
    ma_radius: framework.Variant[int] = framework.Variant(1)
    g_radius: framework.Variant[int] = framework.Variant(2)
    g_sigma: framework.Variant[float] = framework.Variant(3.0)
    lpf_cutoff: framework.Variant[float] = framework.Variant(0.2)
    strength: framework.Variant[int] = framework.Variant(100)
    hierarchy: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Motion Denoiser tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): A unique ID for restoring window
                states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)
        self.__algorithm: QtWidgets.QComboBox
        self.__param_stack: widgets.AdaptiveStackedWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)

        form_layout = widgets.FormLayout(self)
        main_layout.addLayout(form_layout)

        if not HAS_NUMPY:
            notice_layout = QtWidgets.QHBoxLayout()
            form_layout.addRow(notice_layout)

            label: QtWidgets.QLabel = QtWidgets.QLabel(
                "Processing will be slower without NumPy.", parent
            )
            label.setStyleSheet("color: #FF5555; font-weight: bold;")
            notice_layout.addWidget(label)

            button: QtWidgets.QPushButton = QtWidgets.QPushButton(
                "Install", parent
            )
            button.setMaximumWidth(70)
            button.clicked.connect(package_installer.main)
            notice_layout.addWidget(button)

            form_layout.addRow(widgets.HorizontalLine(parent))

        self.__algorithm = QtWidgets.QComboBox(parent)
        self.__algorithm.addItem("Moving Average")
        self.__algorithm.addItem("Gaussian")
        self.__algorithm.addItem("Low-Pass Filter")
        form_layout.addRow(widgets.FormLabel("Algorithm"), self.__algorithm)

        form_layout.addRow(widgets.HorizontalLine(parent))

        self.__param_stack = widgets.AdaptiveStackedWidget(parent)
        form_layout.addRow(self.__param_stack)

        # Moving Average
        ma_widget = QtWidgets.QWidget(parent)
        self.__param_stack.addWidget(ma_widget)
        ma_layout = widgets.FormLayout(ma_widget)
        ma_layout.setContentsMargins(0, 0, 0, 0)
        ma_radius = QtWidgets.QSpinBox(parent)
        ma_radius.setMinimumWidth(70)
        ma_radius.setRange(1, 99)
        ma_layout.addRow(widgets.FormLabel("Radius"), ma_radius)

        # Gaussian
        g_widget = QtWidgets.QWidget(parent)
        self.__param_stack.addWidget(g_widget)
        g_layout = widgets.FormLayout(g_widget)
        g_layout.setContentsMargins(0, 0, 0, 0)
        g_radius = QtWidgets.QSpinBox(parent)
        g_radius.setMinimumWidth(70)
        g_radius.setRange(1, 99)
        g_layout.addRow(widgets.FormLabel("Radius"), g_radius)

        g_sigma = QtWidgets.QDoubleSpinBox(parent)
        g_sigma.setMinimumWidth(70)
        g_sigma.setRange(0.1, 20.0)
        g_layout.addRow(widgets.FormLabel("Blur"), g_sigma)

        # Low-Pass Filter
        lpf_widget = QtWidgets.QWidget(parent)
        self.__param_stack.addWidget(lpf_widget)
        lpf_layout = widgets.FormLayout(lpf_widget)
        lpf_layout.setContentsMargins(0, 0, 0, 0)
        lpf_cutoff = QtWidgets.QDoubleSpinBox(parent)
        lpf_cutoff.setMinimumWidth(70)
        lpf_cutoff.setRange(0.01, 1.0)
        lpf_cutoff.setSingleStep(0.05)
        lpf_layout.addRow(widgets.FormLabel("Cutoff"), lpf_cutoff)

        form_layout.addRow(widgets.HorizontalLine(parent))

        # Strength
        strength_layout = QtWidgets.QHBoxLayout()
        strength = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, parent)
        strength.setRange(0, 100)
        strength_layout.addWidget(strength)

        strength_label = QtWidgets.QLabel("", parent)
        strength_label.setMinimumWidth(40)
        strength_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        strength_layout.addWidget(strength_label)

        strength.valueChanged.connect(lambda v: strength_label.setText(f"{v}%"))

        form_layout.addRow(widgets.FormLabel("Strength"), strength_layout)

        # Hierarchy
        hierarchy = QtWidgets.QCheckBox("Include Hierarchy", parent)
        form_layout.addRow("", hierarchy)

        main_layout.addStretch(1)

        # Settings Binding
        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.algorithm.bind(
            setter=self.__algorithm.setCurrentIndex,
            getter=self.__algorithm.currentIndex,
        )
        settings.ma_radius.bind(
            setter=ma_radius.setValue,
            getter=ma_radius.value,
        )
        settings.g_radius.bind(
            setter=g_radius.setValue,
            getter=g_radius.value,
        )
        settings.g_sigma.bind(
            setter=g_sigma.setValue,
            getter=g_sigma.value,
        )
        settings.lpf_cutoff.bind(
            setter=lpf_cutoff.setValue,
            getter=lpf_cutoff.value,
        )
        settings.strength.bind(
            setter=strength.setValue,
            getter=strength.value,
        )
        settings.hierarchy.bind(
            setter=hierarchy.setChecked,
            getter=hierarchy.isChecked,
        )

        # Events
        self.__algorithm.currentIndexChanged.connect(self.set_valid_options)
        self.set_valid_options(self.__algorithm.currentIndex())

    def set_valid_options(self, index: int) -> None:
        """Synchronizes stacked widgets with the selected algorithm.

        Args:
            index (int): The currently selected algorithm index.
        """
        self.__param_stack.setCurrentIndex(index)

    @dcc.undo
    def apply(self) -> None:
        """Applies the settings and executes the denoiser."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    curve: str,
    algorithm: int,
    param: dict[str, Any],
    strength: float,
) -> bool:
    """Applies the selected smoothing filter to the specified animation curve.

    Args:
        curve (str): The name of the animation curve.
        algorithm (int): The index of the selected algorithm.
        param (dict[str, Any]): Parameters for the selected algorithm.
        strength (float): The blend strength.

    Returns:
        bool: True if successful, False otherwise.
    """
    times: list[float] = cmds.keyframe(curve, query=True, timeChange=True)  # type: ignore
    values: list[float] = cmds.keyframe(curve, query=True, valueChange=True)  # type: ignore
    if not times or len(values) < 3:
        return False

    if algorithm == 0:
        new_values: list[float] = CurveSmoother.moving_average(
            values,
            param["MA_RADIUS"] * 2 + 1,
            strength,
        )

    elif algorithm == 1:
        new_values = CurveSmoother.gaussian(
            values,
            param["G_RADIUS"] * 2 + 1,
            param["G_SIGMA"],
            strength,
        )

    else:
        new_values = CurveSmoother.fft_cutoff(
            values,
            param["LPF_CUTOFF"],
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


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window.
            Defaults to "".
    """
    window = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the denoiser process based on tool settings.

    Args:
        settings (Settings | None, optional): The tool settings instance.
            Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error(
            "Select a node or keyframe to apply the animation filter."
        )
        return

    if settings is None:
        settings = Settings.instance(__name__, True)

    if settings.hierarchy.value():
        children: list[str] = (
            cmds.listRelatives(*selection, allDescendents=True, fullPath=True)
            or []
        )
        selection.extend(children)

    curves: list[str] = cmds.keyframe(*selection, query=True, name=True) or []  # type: ignore
    if not curves:
        _logger.error("No animation curves found.")
        return

    algorithm: int = settings.algorithm.value()
    param: dict[str, Any] = {
        "MA_RADIUS": settings.ma_radius.value(),
        "G_RADIUS": settings.g_radius.value(),
        "G_SIGMA": settings.g_sigma.value(),
        "LPF_CUTOFF": settings.lpf_cutoff.value(),
    }
    strength: float = settings.strength.value() / 100.0

    cmds.waitCursor(state=True)
    cmds.refresh(suspend=True)
    try:
        for curve in curves:
            apply(curve, algorithm, param, strength)

        _logger.info("Done : Smoothed %s curves.", len(curves))

    except Exception:  # pylint: disable=broad-exception-caught
        _logger.exception("An unexpected error occurred during smoothing.")

    finally:
        cmds.waitCursor(state=False)
        cmds.refresh(suspend=False)
        cmds.refresh()
