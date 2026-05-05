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
"""Sets random values for attributes selected in the Maya Channel Box.

This module provides a tool to assign random values to selected attributes.
It supports absolute and relative value generation, custom or attribute-based
value ranges, and uniform scaling.
"""

from __future__ import annotations
from itertools import product
import random
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Random Value"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Random Value tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        seed (framework.Variant[int]): The random seed value. 0 means unseeded.
        method (framework.Variant[int]): The mode of application
            (0: Absolute, 1: Relatives).
        range (framework.Variant[int]): The range mode
            (0: Custom, 1: Attribute Min/Max).
        random_min (framework.Variant[float]): The custom minimum random value.
        random_max (framework.Variant[float]): The custom maximum random value.
        uniform_scale (framework.Variant[bool]): Whether to apply the same random value to XYZ scales.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    seed: framework.Variant[int] = framework.Variant(0)
    method: framework.Variant[int] = framework.Variant(1)
    range: framework.Variant[int] = framework.Variant(1)
    random_min: framework.Variant[float] = framework.Variant(-10.0)
    random_max: framework.Variant[float] = framework.Variant(10.0)
    uniform_scale: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Random Value tool.

    This window provides a UI for configuring random value generation parameters
    and applying them to the selected attributes in the Channel Box.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the window instance.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        seed_spin = QtWidgets.QSpinBox(self)
        seed_spin.setRange(-999999, 999999)
        seed_spin.setMaximumWidth(80)
        seed_spin.setToolTip("If set to 0, result changes every time.")
        main_layout.addRow(widgets.FormLabel("Seed"), seed_spin)

        method = QtWidgets.QComboBox(self)
        method.addItems(["Absolute", "Relatives"])
        main_layout.addRow(widgets.FormLabel("Method"), method)

        main_layout.addRow(widgets.HorizontalLine(parent))

        range_mode = QtWidgets.QComboBox(self)
        range_mode.addItems(["Custom", "Attribute Min/Max"])
        main_layout.addRow(widgets.FormLabel("Range"), range_mode)

        range_value = widgets.DoubleRangeWidget(parent)
        main_layout.addRow("", range_value)

        main_layout.addRow(widgets.HorizontalLine(parent))

        uniform_scale_check = QtWidgets.QCheckBox("Uniform Scale", parent)
        main_layout.addWidget(uniform_scale_check)

        range_mode.currentIndexChanged.connect(
            lambda index: range_value.setEnabled(index == 0)
        )

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.seed.bind(setter=seed_spin.setValue, getter=seed_spin.value)
        settings.method.bind(
            setter=method.setCurrentIndex,
            getter=method.currentIndex,
        )
        settings.range.bind(
            setter=range_mode.setCurrentIndex,
            getter=range_mode.currentIndex,
        )
        settings.random_min.bind(
            setter=range_value.set_min_value,
            getter=range_value.min_value,
        )
        settings.random_max.bind(
            setter=range_value.set_max_value,
            getter=range_value.max_value,
        )
        settings.uniform_scale.bind(
            setter=uniform_scale_check.setChecked,
            getter=uniform_scale_check.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by applying the configured settings."""
        self.save_settings()
        main(self.tool_settings())


def _set_random_values(
    plugs: list[str],
    seed: int = 0,
    method: int = 0,
    range_mode: int = 1,
    min_value: float = -10,
    max_value: float = 10,
    uniform_scale: bool = False,
) -> utils.Result:
    """Core logic to calculate and assign random values to the specified plugs.

    Args:
        plugs (list[str]): A list of attribute plugs (e.g., 'pCube1.tx').
        seed (int, optional): The random seed. Defaults to 0 (unseeded).
        method (int, optional): 0 for Absolute assignment,
            1 for Relative addition. Defaults to 0.
        range_mode (int, optional): 0 for Custom range,
            1 for Attribute Min/Max. Defaults to 1.
        min_value (float, optional): Custom minimum limit. Defaults to -10.
        max_value (float, optional): Custom maximum limit. Defaults to 10.
        uniform_scale (bool, optional): If True, sx, sy, sz will receive identical values.
            Defaults to False.

    Returns:
        utils.Result: An object containing the success status and
            execution details/errors.
    """
    result = utils.Result()
    if seed != 0:
        random.seed(seed)

    scale_cache: dict[str, float] = {}
    scale_attrs: list[str] = ["sx", "sy", "sz"]

    for plug in plugs:
        temp: list[str] = plug.split('.')
        node: str = temp[0]
        attr: str = '.'.join(temp[1:])

        attr_min: float | None
        attr_max: float | None
        attr_min, attr_max = dcc.attribute.get_range(node, attr)

        range_min: float = attr_min if attr_min is not None else min_value
        range_max: float = attr_max if attr_max is not None else max_value
        if range_mode == 0:  # Custom
            range_min = min_value
            range_max = max_value

        value: float = random.uniform(range_min, range_max)
        if method == 1:  # Relatives
            value += float(cmds.getAttr(plug))

        # Clamp the value if min/max attributes are defined.
        value = max(attr_min, value) if attr_min is not None else value
        value = min(attr_max, value) if attr_max is not None else value

        if uniform_scale and attr in scale_attrs and node not in scale_cache:
            scale_cache[node] = value
            continue

        try:
            cmds.setAttr(plug, value)

        except RuntimeError as e:
            result.add_failure(plug, f"Failed to set value: {e}")

    if uniform_scale:
        for node, attr in product(scale_cache.keys(), scale_attrs):
            plug = f"{node}.{attr}"
            try:
                cmds.setAttr(plug, scale_cache[node])

            except RuntimeError as e:
                result.add_failure(plug, f"Failed to set uniform scale: {e}")

    return result


def option(unique_id: str = "") -> None:
    """Shows the tool's option window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the random value operation on the attributes selected in
    the Channel Box.

    Args:
        settings (Settings | None, optional): The settings instance to use.
            If None, reads from disk. Defaults to None.
    """
    plugs: list[str] = dcc.selection.get_selected_channel_box_plugs()
    if not plugs:
        _logger.error("Select attribute to set random value in Channel Box.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: utils.Result = _set_random_values(
        plugs,
        settings.seed.value(),
        settings.method.value(),
        settings.range.value(),
        settings.random_min.value(),
        settings.random_max.value(),
        settings.uniform_scale.value(),
    )
    result.log(_logger)
