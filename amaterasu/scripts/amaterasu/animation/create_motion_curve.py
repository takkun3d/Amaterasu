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
"""Creates an animation tail using a CV curve from the selected objects."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Create Motion Curve"
__version__: str = "1.11"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Create Motion Curve tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        method (framework.Variant[int]): Mode for time range
            (0: Time Range, 1: Start/End).
        start_frame (framework.Variant[int]): The start frame for the curve.
        end_frame (framework.Variant[int]): The end frame for the curve.
        step_frame (framework.Variant[float]): The frame step interval.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    method: framework.Variant[int] = framework.Variant(0)
    start_frame: framework.Variant[int] = framework.Variant(1)
    end_frame: framework.Variant[int] = framework.Variant(10)
    step_frame: framework.Variant[float] = framework.Variant(1.0)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Create Motion Curve tool."""

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

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        method: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        method.addItems(["Time Range", "Start/End"])
        main_layout.addRow(widgets.FormLabel("Method"), method)

        start_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        start_frame.setRange(-9999, 9999)
        start_frame.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel("Start Frame"), start_frame)
        start_frame_idx: int = main_layout.row_id()

        end_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        end_frame.setRange(-9999, 9999)
        end_frame.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel("End Frame"), end_frame)
        end_frame_idx: int = main_layout.row_id()

        step_frame: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        step_frame.setRange(0.001, 9999)
        step_frame.setDecimals(3)
        step_frame.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel("Step Frame"), step_frame)

        # Settings Binding
        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.method.bind(
            setter=method.setCurrentIndex,
            getter=method.currentIndex,
        )
        settings.start_frame.bind(
            setter=start_frame.setValue,
            getter=start_frame.value,
        )
        settings.end_frame.bind(
            setter=end_frame.setValue,
            getter=end_frame.value,
        )
        settings.step_frame.bind(
            setter=step_frame.setValue,
            getter=step_frame.value,
        )

        method.currentIndexChanged.connect(
            lambda idx: main_layout.set_row_enabled(start_frame_idx, idx != 0)
        )
        method.currentIndexChanged.connect(
            lambda idx: main_layout.set_row_enabled(end_frame_idx, idx != 0)
        )

        initial_idx: int = method.currentIndex()
        main_layout.set_row_enabled(start_frame_idx, initial_idx != 0)
        main_layout.set_row_enabled(end_frame_idx, initial_idx != 0)

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    nodes: list[str],
    start_frame: int = 1,
    end_frame: int = 10,
    step_frame: float = 1,
    group_name: str = "motion_curve_grp",
) -> bool:
    """Creates an animation tail with a CV curve from the selection.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        start_frame (int, optional): The starting frame. Defaults to 1.
        end_frame (int, optional): The ending frame. Defaults to 10.
        step_frame (float, optional): The frame step interval. Defaults to 1.0.
        group_name (str, optional): The name of the group for the curves.
            Defaults to "motion_curve_grp".

    Returns:
        bool: True if the operation was successful.
    """
    if not cmds.objExists(group_name):
        group_name = cmds.group(name=group_name, empty=True)

    current_time: float = cmds.currentTime(query=True)
    cmds.currentTime(start_frame, update=True)
    curves: list[str] = []
    for node in nodes:
        point: list[float] = cmds.xform(
            node, query=True, worldSpace=True, translation=True
        )  # type: ignore
        cleanup_name: str = node.replace("[", "")
        cleanup_name = cleanup_name.replace("]", "")
        cleanup_name = cleanup_name.replace(".", "_")

        curve: str = cmds.curve(name=f"{cleanup_name}_crv", point=point)  # type: ignore
        curve = cmds.parent(curve, group_name)[0]
        curves.append(curve)

    current_frame: float = float(start_frame)
    while current_frame < end_frame:
        current_frame = current_frame + step_frame
        cmds.currentTime(current_frame, update=True)  # type: ignore
        for i, node in enumerate(nodes):
            point = cmds.xform(
                node, query=True, worldSpace=True, translation=True
            )  # type: ignore
            cmds.curve(curves[i], append=True, point=point)  # type: ignore

    cmds.currentTime(current_time, update=True)  # type: ignore
    return True


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the motion curve creation based on UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to
            use. If None, it initializes settings from the module name and
            reads them from the file. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True, flatten=True)
    if not selection:
        _logger.error("Select objects or components to create a motion curve.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    start_frame: int = settings.start_frame.value()
    end_frame: int = settings.end_frame.value()

    if settings.method.value() == 0:
        start_frame = int(cmds.playbackOptions(query=True, min=True))  # type: ignore
        end_frame = int(cmds.playbackOptions(query=True, max=True))  # type: ignore

    result: bool = apply(
        selection,
        start_frame,
        end_frame,
        settings.step_frame.value(),
    )
    if result:
        _logger.info("Done.")
