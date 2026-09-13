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
"""Provides vertical lens shift for perspective correction."""

from __future__ import annotations
import math
from functools import partial
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Shift Lens"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Shift Lens tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Shift Lens tool."""

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
        self.resize(400, 20)
        self._initial_rotate_x: float = 0.0

        self.__camera_picker: widgets.NodePicker
        self.__slider: widgets.DragSlider

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout = QtWidgets.QGridLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        picker_layout: widgets.FormLayout = widgets.FormLayout()
        self.__camera_picker = widgets.NodePicker(parent, multi_select=False)
        picker_layout.addRow(widgets.FormLabel("Camera"), self.__camera_picker)
        main_layout.addLayout(picker_layout, 0, 0, 1, 7)

        main_layout.addWidget(widgets.HorizontalLine(parent), 1, 0, 1, 7)

        self.__slider = widgets.DragSlider(parent)
        self.__slider.drag_start.connect(self.drag_start)
        self.__slider.drag_move.connect(self.drag_move)
        self.__slider.drag_end.connect(self.drag_end)
        main_layout.addWidget(self.__slider, 2, 0, 1, 7)

        main_layout.addWidget(widgets.HorizontalLine(parent), 3, 0, 1, 7)

        offsets: list[tuple[str, float]] = [
            ("<<<", 5),
            ("<<", 1),
            ("<", 0.1),
            ("Auto", 0),
            (">", -0.1),
            (">>", -1),
            (">>>", -5),
        ]
        for i, (label, val) in enumerate(offsets):
            button: QtWidgets.QPushButton = QtWidgets.QPushButton(label, parent)
            if label == "Auto":
                button.clicked.connect(self.apply_auto)
            else:
                button.clicked.connect(partial(self.apply_offset, val))

            main_layout.addWidget(button, 4, i)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    def set_camera(self, camera: str) -> None:
        """Sets the target camera for the widget.

        Args:
            camera (str): The name of the camera node.
        """
        self.__camera_picker.set_text(camera)

    @QtCore.Slot()
    def drag_start(self) -> None:
        """Prepares the camera state for interactive lens shifting."""
        camera: str = self.__camera_picker.text()
        if not camera:
            _logger.error("A camera must be specified to shift the lens.")
            return

        camera_shapes: list[str] = (
            cmds.listRelatives(camera, type="camera") or []
        )
        if not camera_shapes:
            return

        rotate: list[float] = cmds.xform(
            camera, query=True, rotation=True, worldSpace=True
        )  # type: ignore
        self._initial_rotate_x = rotate[0]

    @QtCore.Slot(int)
    def drag_move(self, value: int) -> None:
        """Updates the lens shift interactively.

        Args:
            value (int): The current slider value.
        """
        camera: str = self.__camera_picker.text()
        if not camera:
            return

        rotate_x: float = self._initial_rotate_x * (1.0 - (value / 100.0))
        apply(camera, rotate_x)

    @QtCore.Slot()
    def drag_end(self) -> None:
        """Finalizes the interactive lens shifting operation."""

    @dcc.undo
    def apply_offset(self, offset_value: float) -> None:
        """Applies a specific offset to the lens shift.

        Args:
            offset_value (float): The amount to offset the rotation X.
        """
        camera: str = self.__camera_picker.text()
        if not camera:
            _logger.error("A camera must be specified to shift the lens.")
            return

        apply(camera, 0.0, offset_value)

    @dcc.undo
    def apply_auto(self) -> None:
        """Resets the lens shift rotation X to zero."""
        camera: str = self.__camera_picker.text()
        if not camera:
            _logger.error("A camera must be specified to shift the lens.")
            return

        apply(camera, 0.0)


def apply(camera: str, rotate_x: float, offset: float | None = None) -> bool:
    """Calculates and applies the vertical film offset for the camera.

    Args:
        camera (str): The name of the transform node for the camera.
        rotate_x (float): The target X-axis rotation value in degrees.
        offset (float | None, optional): An additional offset applied to
            the current rotation. Defaults to None.

    Returns:
        bool: True if the operation succeeds, False otherwise.
    """
    camera_shapes: list[str] = cmds.listRelatives(camera, type="camera") or []
    if not camera_shapes:
        return False

    rotate: list[float] = cmds.xform(
        camera, query=True, rotation=True, worldSpace=True
    )  # type: ignore
    focal_length: float = cmds.getAttr(f"{camera_shapes[0]}.focalLength")
    current_offset_v: float = cmds.getAttr(
        f"{camera_shapes[0]}.verticalFilmOffset"
    )
    if offset is not None:
        rotate_x = rotate[0] + offset

    # Check Aim Camera.(Maya defult)
    aim_target: str = ""
    look_at_nodes: list[str] = (
        cmds.listConnections(
            camera, type="lookAt", source=True, destination=False
        )
        or []
    )
    if look_at_nodes:
        target_nodes: list[str] = (
            cmds.listConnections(
                f"{look_at_nodes[0]}.target[0].targetParentMatrix",
                type="transform",
                source=True,
                destination=False,
            )
            or []
        )
        if target_nodes:
            aim_target = target_nodes[0]

    # Calculate film offset x amout.
    # 25.4 is mm to inch
    offset_amount: float = (focal_length / 25.4) * (
        math.tan(math.radians(rotate[0])) - math.tan(math.radians(rotate_x))
    )

    # Apply(Camera)
    if not aim_target:
        cmds.xform(
            camera, rotation=(rotate_x, rotate[1], rotate[2]), worldSpace=True
        )

    # Apply(Aim Camera)
    else:
        # Get World Positions
        camera_position: list[float] = cmds.xform(
            camera, query=True, worldSpace=True, translation=True
        )  # type: ignore
        target_position: list[float] = cmds.xform(
            aim_target, query=True, worldSpace=True, translation=True
        )  # type: ignore

        # Calculate Horizontal Distance (XZ plane only)
        dx: float = target_position[0] - camera_position[0]
        dz: float = target_position[2] - camera_position[2]
        horizontal_distance: float = math.sqrt(dx * dx + dz * dz)

        # Calculate New Height Difference
        height_difference: float = horizontal_distance * math.tan(
            math.radians(rotate_x)
        )

        # Calculate translate Y
        translate_y: float = camera_position[1] + height_difference

        # Apply
        cmds.xform(
            aim_target,
            translation=(target_position[0], translate_y, target_position[2]),
            worldSpace=True,
        )

    cmds.setAttr(
        f"{camera_shapes[0]}.verticalFilmOffset",
        current_offset_v + offset_amount,
    )
    return True


def main(unique_id: str = "", camera: str | None = None) -> None:
    """Initializes and displays the main application window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
        camera (str | None, optional): The initial camera to set.
            Defaults to None.
    """
    window = MainWindow(unique_id=unique_id)
    if camera is not None:
        window.set_camera(camera)

    window.show()
