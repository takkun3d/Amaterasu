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
"""Constrains the specified node using matrix calculations."""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc, framework, utils, widgets
from amaterasu.base.qt import QtCore, QtWidgets

__product__: str = "Matrix Constraint"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)

PLUGIN_NAME: str = "quatNodes.mll"


class Settings(framework.ToolSettings):
    """Settings for the Matrix Constraint tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        space (framework.Variant[int]): The calculation space
            (0: World, 1: Local).
        follows_parent (framework.Variant[bool]): Whether local space
            calculations follow the parent transform.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    space: framework.Variant[int] = framework.Variant(1)  # 0:World 1:Local
    follows_parent: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Matrix Constraint tool."""

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

        self.__form_layout: widgets.FormLayout
        self.__space: QtWidgets.QComboBox
        self.__sources: widgets.NodePicker
        self.__target: widgets.NodePicker
        self.__follows_parent_idx: int

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_layout = widgets.FormLayout(parent)
        main_layout.addLayout(self.__form_layout)

        self.__space = QtWidgets.QComboBox(parent)
        self.__space.addItem("World")
        self.__space.addItem("Local")
        self.__space.currentIndexChanged.connect(self.set_valid_options)
        self.__form_layout.addRow(widgets.FormLabel("Space"), self.__space)

        self.__form_layout.addRow(widgets.HorizontalLine(parent))

        self.__sources = widgets.NodePicker(parent, multi_select=True)
        self.__sources.set_placeholder_text("Select in order: Parent -> Child.")
        self.__form_layout.addRow(widgets.FormLabel("Sources"), self.__sources)

        self.__target = widgets.NodePicker(parent, multi_select=False)
        self.__form_layout.addRow(widgets.FormLabel("Target"), self.__target)

        self.__form_layout.addRow(widgets.HorizontalLine(parent))

        follows_parent = QtWidgets.QCheckBox("Follows Parent", parent)
        self.__form_layout.addRow("", follows_parent)
        self.__follows_parent_idx = self.__form_layout.row_id()

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Build", parent)
        button.clicked.connect(self.apply)
        main_layout.addStretch(True)
        main_layout.addWidget(button)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.space.bind(
            setter=self.__space.setCurrentIndex,
            getter=self.__space.currentIndex,
        )
        settings.follows_parent.bind(
            setter=follows_parent.setChecked,
            getter=follows_parent.isChecked,
        )
        self.set_valid_options()

    @QtCore.Slot()
    def set_valid_options(self) -> None:
        """Synchronizes UI option states based on the selected space."""
        self.__form_layout.set_row_enabled(
            self.__follows_parent_idx, self.__space.currentIndex() == 1
        )

    @dcc.undo
    def apply(self) -> None:
        """Validates inputs and builds the matrix constraint."""
        self.save_settings()

        sources: list[str] = self.__sources.text_as_list()
        target: str = self.__target.text()
        if not sources or not target:
            _logger.error(
                "Sources and Target nodes are required to apply Matrix Constraint."
            )
            return

        settings: Settings = self.tool_settings()
        apply(
            sources,
            target,
            settings.space.value(),
            settings.follows_parent.value(),
        )
        _logger.info("Done.")


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


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig).
def cancel_joint_orient(prefix: str, target: str, decompose_mtx: str) -> str:
    """Creates quaternion nodes to cancel out joint orientation.

    Args:
        prefix (str): The naming prefix for created nodes.
        target (str): The target joint node name.
        decompose_mtx (str): The decomposeMatrix node driving the target.

    Returns:
        str: The output rotate plug name after canceling joint orient.
    """
    joint_orient_quat: str = cmds.createNode(
        "eulerToQuat", name=f"{prefix}_etq"
    )
    cmds.connectAttr(
        f"{target}.jointOrient", f"{joint_orient_quat}.inputRotate"
    )

    invert_joint_orient_quat: str = cmds.createNode(
        "quatInvert", name=f"{prefix}_qi"
    )
    cmds.connectAttr(
        f"{joint_orient_quat}.outputQuat",
        f"{invert_joint_orient_quat}.inputQuat",
    )

    remove_orient_prod: str = cmds.createNode("quatProd", name=f"{prefix}_qp")
    cmds.connectAttr(
        f"{decompose_mtx}.outputQuat",
        f"{remove_orient_prod}.input1Quat",
    )
    cmds.connectAttr(
        f"{invert_joint_orient_quat}.outputQuat",
        f"{remove_orient_prod}.input2Quat",
    )

    joint_orient_euler: str = cmds.createNode(
        "quatToEuler", name=f"{prefix}_qte"
    )
    cmds.connectAttr(
        f"{remove_orient_prod}.outputQuat",
        f"{joint_orient_euler}.inputQuat",
    )
    cmds.connectAttr(
        f"{target}.rotateOrder",
        f"{joint_orient_euler}.inputRotateOrder",
    )
    return f"{joint_orient_euler}.outputRotate"


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig).
def connect_mult_matrix(
    base_name: str,
    source_plugs: list[str],
    target_plug: str,
) -> str:
    """Creates a multMatrix node and connects the specified matrix plugs.

    Args:
        base_name (str): The naming prefix for the multMatrix node.
        source_plugs (list[str]): Ordered list of source matrix plugs.
        target_plug (str): The destination plug to connect the matrix sum to.

    Returns:
        str: The name of the created multMatrix node.
    """
    mult_matrix: str = cmds.createNode(
        "multMatrix", name=f"{base_name}_multMtx"
    )
    for i, plug in enumerate(source_plugs):
        cmds.connectAttr(plug, f"{mult_matrix}.matrixIn[{i}]")

    cmds.connectAttr(f"{mult_matrix}.matrixSum", target_plug)
    return mult_matrix


def apply(
    sources: list[str],
    target: str,
    space: int = 1,
    follows_parent: bool = True,
) -> None:
    """Builds a matrix constraint setup between the specified nodes.

    Args:
        sources (list[str]): Source transform nodes ordered from parent to
            child.
        target (str): The constrained target node name.
        space (int, optional): Calculation space (0: World, 1: Local).
            Defaults to 1.
        follows_parent (bool, optional): Whether local space calculations
            follow the parent transform. Defaults to True.
    """

    dcc.plugin.load(PLUGIN_NAME)

    base_name: str = extract_base_name(sources[-1])
    target_base_name: str = extract_base_name(target)
    prefix: str = f"{base_name}{target_base_name}"

    target_space: str = cmds.createNode(
        "transform",
        name=f"{prefix}Space_null",
        parent=target,
    )
    cmds.setAttr(f"{target_space}.visibility", False)
    cmds.setAttr(f"{target_space}.hiddenInOutliner", True)
    target_space = cmds.parent(target_space, sources[-1])[0]
    dcc.attribute.lock_and_hide([target_space], True, True, True, True)

    decompose_mtx: str = cmds.createNode(
        "decomposeMatrix",
        name=f"{prefix}_decomposeMtx",
    )
    cmds.connectAttr(
        f"{target}.rotateOrder", f"{decompose_mtx}.inputRotateOrder"
    )

    # World
    if space == 0:
        matrix_plugs: list[str] = [
            f"{target_space}.worldMatrix[0]",
            f"{target}.parentInverseMatrix[0]",
        ]

    # Local
    else:
        sources = list(reversed(sources))
        matrix_plugs = [f"{target_space}.matrix"] + [
            f"{node}.matrix" for node in sources
        ]
        if follows_parent:
            matrix_plugs.extend(
                [
                    f"{sources[-1]}.parentMatrix[0]",
                    f"{target}.parentInverseMatrix[0]",
                ]
            )

    connect_mult_matrix(prefix, matrix_plugs, f"{decompose_mtx}.inputMatrix")

    rotate_plug: str = f"{decompose_mtx}.outputRotate"
    if cmds.objectType(target) == "joint":
        rotate_plug = cancel_joint_orient(prefix, target, decompose_mtx)

    cmds.connectAttr(
        f"{decompose_mtx}.outputTranslate", f"{target}.translate", force=True
    )
    cmds.connectAttr(rotate_plug, f"{target}.rotate", force=True)
    cmds.connectAttr(
        f"{decompose_mtx}.outputScale", f"{target}.scale", force=True
    )
    cmds.connectAttr(
        f"{decompose_mtx}.outputShear", f"{target}.shear", force=True
    )

    # TODO: Consider moving outliner refresh to amaterasu.base (e.g., dcc.ui).
    for panel in cmds.getPanel(type="outlinerPanel") or []:
        cmds.outlinerEditor(panel, edit=True, refresh=True)

    dcc.node.hide_history([target, *sources])


def main(unique_id: str = "") -> None:
    """Initializes and displays the main application window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
