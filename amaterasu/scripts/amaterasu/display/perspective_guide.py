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
"""Generates perspective grids and an eye level guide for the selected camera.

This module provides tools to create a visual perspective guide, including
vanishing points and eye-level indicators, attached to a selected Maya camera.
"""

from __future__ import annotations
from itertools import product
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import utils, framework, dcc, widgets
from amaterasu.edit import combine_shapes
from amaterasu.modify import lock_hide_transform, history_visibility

__product__: str = "Perspective Guide"
__version__: str = "1.11"
_logger: utils.Logger = utils.get_logger(__product__)

EL_COLOR: list[float] = [0.2, 0.7, 1.0]
VP_COLOR: list[float] = [0.65, 0.2, 1.0]
EL_WIDTH: float = 4.0
VP_WIDTH: float = 2.0


class Settings(framework.ToolSettings):
    """Settings for the Perspective Guide tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        radius (framework.Variant[int]): The radius of the perspective guide curves.
        division (framework.Variant[int]): The number of divisions for the vanishing points.
        eye_level (framework.Variant[bool]): Whether to generate the eye-level guide.
        vp_x (framework.Variant[bool]): Whether to generate the horizontal vanishing point (X-axis).
        vp_y (framework.Variant[bool]): Whether to generate the vertical vanishing point (Y-axis).
        vp_z (framework.Variant[bool]): Whether to generate the depth vanishing point (Z-axis).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    radius: framework.Variant[int] = framework.Variant(100)
    division: framework.Variant[int] = framework.Variant(8)
    eye_level: framework.Variant[bool] = framework.Variant(True)
    vp_x: framework.Variant[bool] = framework.Variant(True)
    vp_y: framework.Variant[bool] = framework.Variant(True)
    vp_z: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Perspective Guide tool.

    This window provides a user interface to configure the radius, divisions,
    and visibility of specific perspective guides before applying them to a camera.
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
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the widget.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
                custom UI elements should be added.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        radius: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        radius.setMinimumWidth(70)
        radius.setRange(0, 10000000)
        main_layout.addRow(widgets.FormLabel("Radius"), radius)

        division: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        division.setRange(2, 64)
        division.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel("Division"), division)

        main_layout.addRow(widgets.HorizontalLine(self))

        eye_level: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Eye Level", self)
        main_layout.addRow("", eye_level)

        main_layout.addRow(widgets.HorizontalLine(self))

        vp_x: QtWidgets.QCheckBox = QtWidgets.QCheckBox("X (Horizontal)", self)
        main_layout.addRow(widgets.FormLabel("Vanishing Point"), vp_x)

        vp_y: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Y (Vertical)", self)
        main_layout.addRow("", vp_y)

        vp_z: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Z (Depth)", self)
        main_layout.addRow("", vp_z)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.radius.bind(
            setter=radius.setValue,
            getter=radius.value,
        )
        settings.division.bind(
            setter=division.setValue,
            getter=division.value,
        )
        settings.eye_level.bind(
            setter=eye_level.setChecked,
            getter=eye_level.isChecked,
        )
        settings.vp_x.bind(
            setter=vp_x.setChecked,
            getter=vp_x.isChecked,
        )
        settings.vp_y.bind(
            setter=vp_y.setChecked,
            getter=vp_y.isChecked,
        )
        settings.vp_z.bind(
            setter=vp_z.setChecked,
            getter=vp_z.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by saving settings and calling main()."""
        self.save_settings()
        main(self.tool_settings())


def create_vanishing_point(
    base_name: str,
    parent: str,
    axis: int = 0,
    radius: float = 9999,
    division: int = 16,
) -> str:
    """Creates a vanishing point guide for a specific axis.

    Args:
        base_name (str): The base name for the generated curve nodes.
        parent (str): The name of the parent group node.
        axis (int, optional): The axis index (0 for X/Horizontal, 1 for Y/Vertical,
            2 for Z/Depth). Defaults to 0.
        radius (float, optional): The radius of the guide curves. Defaults to 9999.
        division (int, optional): The number of line divisions to generate.
            Defaults to 16.

    Returns:
        str: The name of the combined curve node representing the vanishing point.
    """
    step: float = 180.0 / division
    axis_name: tuple[str, str, str] = ("Horizontal", "Vertical", "Depth")
    curves: list[str] = []
    for i in range(division):
        angle: float = step * i
        normal: tuple[tuple[float, float, float], ...] = (
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        rotate_mask: tuple[tuple[float, float, float], ...] = (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        curve: str = cmds.circle(
            name=f"{base_name}{axis_name[axis]}{i}_crv",
            radius=radius,
            normal=normal[axis],
            sections=64,
            degree=3,
            constructionHistory=False,
        )[
            0
        ]  # type: ignore
        rotate: tuple[float, float, float] = (
            angle * rotate_mask[axis][0],
            angle * rotate_mask[axis][1],
            angle * rotate_mask[axis][2],
        )
        cmds.setAttr(f"{curve}.rotate", *rotate, type="double3")
        for attr, _axis in product(["t", "r", "s"], ["x", "y", "z"]):
            cmds.setAttr(f"{curve}.{attr}{_axis}", lock=True)

        curve = cmds.parent(curve, parent)[0]
        for attr, _axis in product(["t", "r", "s"], ["x", "y", "z"]):
            cmds.setAttr(f"{curve}.{attr}{_axis}", lock=False)

        cmds.makeIdentity(
            curve, apply=True, translate=True, rotate=True, scale=True
        )

        if i == 0:
            cmds.setAttr(f"{curve}.lineWidth", VP_WIDTH)

        dcc.node.set_rgb_color(rgb=VP_COLOR, nodes=[curve])
        curves.append(curve)

    combine_shapes.apply(curves[0], curves[1:])
    for attr, _axis in product(["t", "s"], ["x", "y", "z"]):
        cmds.setAttr(
            f"{curves[0]}.{attr}{_axis}",
            lock=True,
            keyable=False,
            channelBox=False,
        )
    history_visibility.main(
        cmds.listRelatives(curves[0], shapes=True, path=True),
        0,
    )
    curves[0] = cmds.rename(curves[0], f"{base_name}{axis_name[axis]}_crv")
    return curves[0]


def apply(
    camera: str,
    radius: float = 9999,
    division: int = 16,
    is_eye_level: bool = True,
    is_vp_x: bool = True,
    is_vp_y: bool = True,
    is_vp_z: bool = True,
) -> utils.Result:
    """Applies the perspective guide to the specified camera.

    Generates the necessary hierarchy and curves based on the provided settings
    and attaches them to the camera's decomposed matrix.

    Args:
        camera (str): The name of the camera to attach the guide to.
        radius (float, optional): The radius of the guide curves.
            Defaults to 9999.
        division (int, optional): The number of divisions for the vanishing points.
            Defaults to 16.
        is_eye_level (bool, optional): Whether to generate the eye-level guide.
            Defaults to True.
        is_vp_x (bool, optional): Whether to generate the X-axis vanishing point.
            Defaults to True.
        is_vp_y (bool, optional): Whether to generate the Y-axis vanishing point.
            Defaults to True.
        is_vp_z (bool, optional): Whether to generate the Z-axis vanishing point.
            Defaults to True.

    Returns:
        utils.Result: An object containing the merged results of the operation.
    """
    result: utils.Result = utils.Result()
    base_name: str = camera.split("|")[-1]
    base_name = camera.split("_")[0]

    # Decompose
    camera_decompose: str = cmds.createNode(
        "decomposeMatrix", name=f"{base_name}_decomposeMtx"
    )
    cmds.connectAttr(
        f"{camera}.worldMatrix[0]", f"{camera_decompose}.inputMatrix"
    )

    # Group
    group: str = cmds.createNode("transform", name=f"{base_name}PerspGuide_grp")
    cmds.connectAttr(
        f"{camera_decompose}.outputTranslate", f"{group}.translate"
    )
    history_visibility.main([group], 0)
    for attr, _axis in product(["t", "r"], ["x", "y", "z"]):
        cmds.setAttr(
            f"{group}.{attr}{_axis}", lock=True, keyable=False, channelBox=False
        )

    # Eye Level
    if is_eye_level:
        eye_level: str = cmds.circle(
            name=f"{base_name}EyeLevel_crv",
            radius=radius,
            normal=(0, 1, 0),
            sections=64,
            degree=3,
            constructionHistory=False,
        )[
            0
        ]  # type: ignore
        cmds.setAttr(f"{eye_level}.lineWidth", EL_WIDTH)
        dcc.node.set_rgb_color(rgb=EL_COLOR, nodes=[eye_level])
        history_visibility.main(
            cmds.listRelatives(eye_level, shapes=True, path=True),
            0,
        )
        lock_hide_transform.lock([eye_level], False)
        eye_level = cmds.parent(eye_level, group)[0]

    # Vanishing Point
    if is_vp_x:
        create_vanishing_point(base_name, group, 0, radius * 1.001, division)

    if is_vp_y:
        create_vanishing_point(base_name, group, 1, radius * 1.002, division)

    if is_vp_z:
        create_vanishing_point(base_name, group, 2, radius * 1.003, division)

    return result


def option(unique_id: str = "") -> None:
    """Show the tool window.

    Args:
        unique_id (str, optional): Unique ID for the tool window instance.
        Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the tool's main functionality on the current selection.

    Args:
        settings (Settings | None, optional): The tool settings instance to use.
            If None, a new instance is retrieved automatically.
            Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection or len(selection) != 1:
        _logger.error("Select camera to create perspective guide.")
        return

    camera: str = selection[0]
    shapes: list[str] = (
        cmds.listRelatives(camera, type="camera", shapes=True, path=True) or []
    )
    if not shapes:
        _logger.error("Select camera to create perspective guide.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)

    result: utils.Result = apply(
        camera,
        settings.radius.value(),
        settings.division.value(),
        settings.eye_level.value(),
        settings.vp_x.value(),
        settings.vp_y.value(),
        settings.vp_z.value(),
    )
    result.log(_logger)
    cmds.select(*selection)
