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
"""Constrains the rotation of an object, excluding the twist component."""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc, framework, utils, widgets
from amaterasu.base.qt import QtCore, QtWidgets

__product__: str = "Bend Constraint"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

PLUGIN_NAME: str = "quatNodes.mll"
AXIS_VECTORS: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)


class Settings(framework.ToolSettings):
    """Settings for the Bend Constraint tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        primary_axis (framework.Variant[int]): The primary axis index
            (0: X, 1: Y, 2: Z).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    primary_axis: framework.Variant[int] = framework.Variant(0)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Bend Constraint tool."""

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
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        primary_axis: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        primary_axis.addItems(["X", "Y", "Z"])
        main_layout.addRow(widgets.FormLabel("Primary Axis"), primary_axis)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.primary_axis.bind(
            setter=primary_axis.setCurrentIndex,
            getter=primary_axis.currentIndex,
        )

    @dcc.undo
    def apply(self) -> None:
        """Saves the current settings and applies the bend constraint."""
        self.save_settings()
        main()


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig or dcc.node).
def extract_base_name(node: str) -> str:
    """Extracts the short base name from a DAG path or namespaced node.

    Args:
        node (str): The full or partial node name.

    Returns:
        str: The extracted base name prefix.
    """
    short_name: str = node.split("|")[-1].split(":")[-1]
    return short_name.split("_")[0]


def apply(source: str, target: str, primary_axis: int = 0) -> None:
    """Applies a bend constraint using the specified primary axis.

    Args:
        source (str): The source transform node driving the rotation.
        target (str): The target node to be constrained.
        primary_axis (int, optional): The primary axis index
            (0: X, 1: Y, 2: Z). Defaults to 0.
    """
    dcc.plugin.load(PLUGIN_NAME)

    base_name: str = extract_base_name(source)
    vector: tuple[float, float, float] = AXIS_VECTORS[primary_axis]

    rotate_vector: str = cmds.createNode(
        "rotateVector", name=f"{base_name}Vector_rv"
    )
    cmds.setAttr(f"{rotate_vector}.input", *vector, type="double3")
    cmds.connectAttr(f"{source}.rotate", f"{rotate_vector}.rotate")
    cmds.connectAttr(f"{source}.rotateOrder", f"{rotate_vector}.rotateOrder")

    angle: str = cmds.createNode("angleBetween", name=f"{base_name}Angle_ab")
    cmds.setAttr(f"{angle}.vector1", *vector, type="double3")
    cmds.connectAttr(f"{rotate_vector}.output", f"{angle}.vector2")

    axis_angle_quat: str = cmds.createNode(
        "axisAngleToQuat", name=f"{base_name}_aatq"
    )
    cmds.connectAttr(f"{angle}.axis", f"{axis_angle_quat}.inputAxis")
    cmds.connectAttr(f"{angle}.angle", f"{axis_angle_quat}.inputAngle")

    quat_euler: str = cmds.createNode("quatToEuler", name=f"{base_name}_qte")
    cmds.connectAttr(f"{axis_angle_quat}.outputQuat", f"{quat_euler}.inputQuat")
    cmds.connectAttr(f"{target}.rotateOrder", f"{quat_euler}.inputRotateOrder")

    cmds.connectAttr(
        f"{quat_euler}.outputRotate", f"{target}.rotate", force=True
    )
    dcc.node.hide_history([target, source])


def option(unique_id: str = "") -> None:
    """Initializes and displays the option window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    """Applies the bend constraint to the selected nodes using saved settings."""
    nodes: list[str] = cmds.ls(selection=True, type=["transform", "joint"])
    if not nodes or len(nodes) != 2:
        _logger.error(
            "Select a source node and a target node to create a bend "
            "constraint."
        )
        return

    settings: Settings = Settings.instance(__name__, True)
    apply(nodes[0], nodes[1], settings.primary_axis.value())
    cmds.select(*nodes)
    _logger.info("Done.")
