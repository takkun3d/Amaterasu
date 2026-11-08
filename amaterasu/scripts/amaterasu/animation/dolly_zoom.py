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

"""Applies a Dolly Zoom by adjusting camera distance relative to focal length."""

from __future__ import annotations
import math
from functools import partial
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Dolly Zoom"
__version__: str = "1.11"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Dolly Zoom tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Dolly Zoom tool."""

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
        self.resize(400, 10)
        self._current_focal_length: float = 35.0

        self.__camera_picker: widgets.NodePicker
        self.__target_picker: widgets.NodePicker
        self.__slider: widgets.DragSlider

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout = QtWidgets.QGridLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        picker_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(picker_layout, 0, 0, 1, 7)

        self.__camera_picker = widgets.NodePicker(parent, multi_select=False)
        picker_layout.addRow(widgets.FormLabel("Camera"), self.__camera_picker)

        self.__target_picker = widgets.NodePicker(parent, multi_select=False)
        picker_layout.addRow(widgets.FormLabel("Target"), self.__target_picker)

        main_layout.addWidget(widgets.HorizontalLine(parent), 1, 0, 1, 7)

        self.__slider = widgets.DragSlider(parent)
        self.__slider.drag_start.connect(self.drag_start)
        self.__slider.drag_move.connect(self.drag_move)
        self.__slider.drag_end.connect(self.drag_end)
        main_layout.addWidget(self.__slider, 2, 0, 1, 7)

        main_layout.addWidget(widgets.HorizontalLine(parent), 3, 0, 1, 7)

        offsets: list[tuple[str, float]] = [
            ("<<<", -5.0),
            ("<<", -1.0),
            ("<", -0.1),
            (">", 0.1),
            (">>", 1.0),
            (">>>", 5.0),
        ]
        for i, (label, val) in enumerate(offsets):
            button: QtWidgets.QPushButton = QtWidgets.QPushButton(label, parent)
            button.clicked.connect(partial(self.apply_offset, val))

            col: int = i if i < 3 else i + 1
            main_layout.addWidget(button, 4, col)

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
        """Prepares the camera state for interactive dolly zoom."""
        camera: str = self.__camera_picker.text()
        if not camera:
            _logger.error("A camera must be specified to apply Dolly Zoom.")
            return

        target: str = self.__target_picker.text()
        if not target:
            _logger.error("A target transform must be specified.")
            return

        camera_shapes: list[str] = (
            cmds.listRelatives(camera, type="camera") or []
        )
        if not camera_shapes:
            return

        self._current_focal_length = cmds.getAttr(
            f"{camera_shapes[0]}.focalLength"
        )

    @QtCore.Slot(int)
    def drag_move(self, value: int) -> None:
        """Updates the dolly zoom interactively.

        Args:
            value (int): The current slider value.
        """
        camera: str = self.__camera_picker.text()
        if not camera:
            return

        target: str = self.__target_picker.text()
        if not target:
            return

        focal_length: float = self._current_focal_length + (value / 20.0)
        apply(camera, target, focal_length)

    @QtCore.Slot()
    def drag_end(self) -> None:
        """Finalizes the interactive dolly zoom operation."""

    @dcc.undo
    def apply_offset(self, offset_value: float) -> None:
        """Applies a specific focal length offset to the dolly zoom.

        Args:
            offset_value (float): The amount to offset the focal length.
        """
        camera: str = self.__camera_picker.text()
        if not camera:
            _logger.error("A camera must be specified to apply Dolly Zoom.")
            return

        target: str = self.__target_picker.text()
        if not target:
            _logger.error("A target transform must be specified.")
            return

        apply(camera, target, 0.0, offset_value)


def apply(
    camera: str, target: str, focal_length: float, offset: float | None = None
) -> bool:
    """Calculates and applies the dolly zoom effect for the camera.

    Args:
        camera (str): The name of the camera transform node.
        target (str): The name of the target transform node.
        focal_length (float): The target focal length value.
        offset (float | None, optional): An additional offset applied to
            the current focal length. Defaults to None.

    Returns:
        bool: True if the operation succeeds, False otherwise.
    """
    camera_shapes: list[str] = cmds.listRelatives(camera, type="camera") or []
    if not camera_shapes:
        return False

    current_focal_length: float = cmds.getAttr(
        f"{camera_shapes[0]}.focalLength"
    )

    if offset is not None:
        focal_length = current_focal_length + offset

    if focal_length <= 1:
        return False

    # Distance
    p1: list[float] = cmds.xform(
        camera, query=True, worldSpace=True, translation=True
    )  # type: ignore
    p2: list[float] = cmds.xform(
        target, query=True, worldSpace=True, translation=True
    )  # type: ignore

    current_dist: float = math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))
    if current_dist == 0:
        return False

    # New Distance
    # Doubling the focal length doubles the distance.
    dist: float = current_dist * (focal_length / current_focal_length)

    # Calculate vector to move camera to new distance along target vector.
    # Vector = Normalize(CameraPosotion - TargetPosition) * New Distance
    target_vec: list[float] = [(a - b) for a, b in zip(p1, p2)]
    target_len: float = math.sqrt(sum(x**2 for x in target_vec))
    target_norm_vec: list[float] = [x / target_len for x in target_vec]
    new_pos: list[float] = [b + (v * dist) for b, v in zip(p2, target_norm_vec)]

    # Apply
    cmds.xform(camera, worldSpace=True, translation=new_pos)  # type: ignore
    cmds.setAttr(f"{camera_shapes[0]}.focalLength", focal_length)
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
