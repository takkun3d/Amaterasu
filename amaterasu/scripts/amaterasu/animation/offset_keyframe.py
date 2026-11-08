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
"""Offsets keyframe times for selected nodes."""

from __future__ import annotations
from functools import partial
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Offset Keyframe"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Offset Keyframe tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        offset_value (framework.Variant[int]): Base offset amount.
        delay (framework.Variant[bool]): Whether to apply sequential delay.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    offset_value: framework.Variant[int] = framework.Variant(2)
    delay: framework.Variant[bool] = framework.Variant(False)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Offset Keyframe tool."""

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
            unique_id (str, optional): A unique identifier for restoring
                window states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(200, 20)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        offset_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(offset_layout)

        def __add_offset_button(icon_name: str, multiplier: int) -> None:
            button: widgets.IconButton = widgets.IconButton(parent)
            button.set_icon(dcc.get_icon_path(icon_name))
            button.clicked.connect(partial(self.apply, multiplier))
            button.setMaximumSize(24, 24)
            offset_layout.addWidget(button)

        __add_offset_button("a_previous3.png", -3)
        __add_offset_button("a_previous2.png", -2)
        __add_offset_button("a_previous.png", -1)

        offset: QtWidgets.QSpinBox = QtWidgets.QSpinBox(parent)
        offset.setRange(-99999, 99999)
        offset_layout.addWidget(offset)

        __add_offset_button("a_next.png", 1)
        __add_offset_button("a_next2.png", 2)
        __add_offset_button("a_next3.png", 3)

        delay: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Apply sequential delay to each selection.", parent
        )
        main_layout.addWidget(delay)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.offset_value.bind(
            setter=offset.setValue,
            getter=offset.value,
        )
        settings.delay.bind(
            setter=delay.setChecked,
            getter=delay.isChecked,
        )

    @dcc.undo
    def apply(self, multiplier: int) -> None:
        """Executes the offset logic with the given multiplier.

        Args:
            multiplier (int, optional): The multiplier for the offset value.
        """
        self.save_settings()
        settings: Settings = self.tool_settings()

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error("Select node(s) to offset keyframe times.")
            return

        offset_value: int = settings.offset_value.value() * multiplier
        apply(selection, offset_value, settings.delay.value())


def apply(nodes: list[str], offset_value: int, delay: bool = False) -> bool:
    """Offsets keyframe times for selected nodes.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        offset_value (int): The amount of time to offset the keyframes.
        delay (bool, optional): Whether to apply a sequential delay
            for each node. Defaults to False.

    Returns:
        bool: True if the operation was successful.
    """
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


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
