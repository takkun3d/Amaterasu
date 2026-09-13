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
"""Changes the animation of the selected nodes or curves to a cycle.

This module provides functionality to apply cycle and infinity settings
to animation curves associated with the specified nodes or curves.
"""

from __future__ import annotations
from typing import Any
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Cycle Keyframe"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Cycle Keyframe tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        method (framework.Variant[int]): Cycle generation method.
            0 for None, 1 for Start -> End, 2 for End -> Start.
        target (framework.Variant[int]): Target selection mode.
            0 for Node, 1 for Curve.
        tangent (framework.Variant[bool]): Whether to copy the tangent.
        display_infinities (framework.Variant[bool]): Infinity display mode.
        pre_infinity (framework.Variant[int]): Pre-infinity setting index.
        post_infinity (framework.Variant[int]): Post-infinity setting index.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    method: framework.Variant[int] = framework.Variant(0)
    target: framework.Variant[int] = framework.Variant(0)
    tangent: framework.Variant[bool] = framework.Variant(True)
    display_infinities: framework.Variant[bool] = framework.Variant(True)
    pre_infinity: framework.Variant[int] = framework.Variant(2)
    post_infinity: framework.Variant[int] = framework.Variant(2)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Cycle Keyframe tool."""

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

        main_layout.addRow(
            widgets.FrameWidget("Cycle Options", False, False, self)
        )

        target: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        target.addItems(["Selected Node", "Selected Curve"])
        main_layout.addRow(widgets.FormLabel("Target"), target)

        method: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        method.addItems(["None", "Start -> End", "End -> Start"])
        main_layout.addRow(widgets.FormLabel("Method"), method)

        tangent: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Copy Tangent", self)
        main_layout.addRow("", tangent)

        main_layout.addRow(
            widgets.FrameWidget("Infinities Options", False, False, self)
        )

        display_infinities: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Display Infinities", self
        )
        main_layout.addRow("", display_infinities)

        infinities: list[str] = [
            "Constant",
            "Linear",
            "Cycle",
            "Cycle with Offset",
            "Oscillate",
        ]

        pre_infinity: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        pre_infinity.addItems(infinities)
        main_layout.addRow(widgets.FormLabel("Pre Infinity"), pre_infinity)

        post_infinity: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        post_infinity.addItems(infinities)
        main_layout.addRow(widgets.FormLabel("Post Infinity"), post_infinity)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.target.bind(
            setter=target.setCurrentIndex,
            getter=target.currentIndex,
        )
        settings.method.bind(
            setter=method.setCurrentIndex,
            getter=method.currentIndex,
        )
        settings.tangent.bind(
            setter=tangent.setChecked,
            getter=tangent.isChecked,
        )
        settings.display_infinities.bind(
            setter=display_infinities.setChecked,
            getter=display_infinities.isChecked,
        )
        settings.pre_infinity.bind(
            setter=pre_infinity.setCurrentIndex,
            getter=pre_infinity.currentIndex,
        )
        settings.post_infinity.bind(
            setter=post_infinity.setCurrentIndex,
            getter=post_infinity.currentIndex,
        )

        method.currentIndexChanged.connect(
            lambda idx: tangent.setEnabled(idx != 0)
        )
        tangent.setEnabled(method.currentIndex() != 0)

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    nodes: list[str],
    method: int = 0,
    tangent: bool = True,
    display_infinities: bool = True,
    pre_infinity: int = 2,
    post_infinity: int = 2,
) -> bool:
    """Applies cycle settings to the animation curves of given nodes.

    Args:
        nodes (list[str]): A list of Maya node or curve names to process.
        method (int, optional): The cycle generation method. 0 for None,
            1 for Start -> End, 2 for End -> Start. Defaults to 0.
        tangent (bool, optional): Whether to copy the tangent. Defaults to True.
        display_infinities (bool, optional): Whether to display infinities
            in the Graph Editor. Defaults to True.
        pre_infinity (int, optional): The pre-infinity mode index.
            Defaults to 2.
        post_infinity (int, optional): The post-infinity mode index.
            Defaults to 2.

    Returns:
        bool: True if the operation was successful.
    """
    cmds.animCurveEditor(
        "graphEditor1GraphEd",
        edit=True,
        displayInfinities="on" if display_infinities else "off",
    )

    if pre_infinity >= 2:
        pre_infinity += 1

    if post_infinity >= 2:
        post_infinity += 1

    connected_curves: list[str] = []
    for node in nodes:
        if cmds.objectType(node) in dcc.animation.ANIM_CURVES_TYPE:
            connected_curves.append(node)
        else:
            connected_curves.extend(dcc.animation.get_anim_curves(node))

    for curve in connected_curves:
        if method != 0:
            indexes: list[int] = cmds.keyframe(
                curve, query=True, indexValue=True
            )  # type: ignore
            values: list[Any] = cmds.keyframe(
                curve, query=True, valueChange=True
            )  # type: ignore
            in_tangents: list[float] = cmds.keyTangent(
                curve, query=True, inAngle=True
            )  # type: ignore
            out_tangents: list[float] = cmds.keyTangent(
                curve, query=True, outAngle=True
            )  # type: ignore

            if not indexes:
                continue

            src_seek: int = 0 if method == 1 else -1
            dst_seek: int = -1 if method == 1 else 0
            index: tuple[int, int] = (indexes[dst_seek], indexes[dst_seek])

            cmds.keyframe(
                curve, edit=True, index=index, valueChange=values[src_seek]  # type: ignore
            )
            if tangent:
                cmds.keyTangent(
                    curve,
                    edit=True,
                    index=index,  # type: ignore
                    inAngle=in_tangents[src_seek],
                    outAngle=out_tangents[src_seek],
                )

        cmds.setAttr(f"{curve}.preInfinity", pre_infinity)
        cmds.setAttr(f"{curve}.postInfinity", post_infinity)

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
    """Executes the cycle application based on the current UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance.
            If None, it initializes settings from the module name.
            Defaults to None.
    """
    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    selection: list[str] = []
    if settings.target.value() == 0:
        selection = cmds.ls(selection=True, long=True)
        if not selection:
            _logger.error("Select node(s) to apply a cycle.")
            return

    else:
        selection = cmds.keyframe(query=True, selected=True, name=True)  # type: ignore
        if not selection:
            _logger.error("Select curve(s) to apply a cycle.")
            return

    result: bool = apply(
        selection,
        settings.method.value(),
        settings.tangent.value(),
        settings.display_infinities.value(),
        settings.pre_infinity.value(),
        settings.post_infinity.value(),
    )
    if result:
        _logger.info("Done.")
