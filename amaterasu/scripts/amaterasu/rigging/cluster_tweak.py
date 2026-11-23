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
"""Creates a matrix-driven tweak rig for a cluster deformer."""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc, framework, utils, widgets
from amaterasu.base.qt import QtCore, QtWidgets

from . import create_controller

__product__: str = "Cluster Tweak"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

WORLD_DAG_PATH: str = "|"
SYSTEM_GROUP: str = "clusterTweakSetup_grp"


class Settings(framework.ToolSettings):
    """Settings for the Cluster Tweak tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        system_group (framework.Variant[str]): The parent group name for
            cluster system nodes.
        delete_guide (framework.Variant[bool]): Whether to delete the guide
            node after building the rig.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    system_group: framework.Variant[str] = framework.Variant(SYSTEM_GROUP)
    delete_guide: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Cluster Tweak tool."""

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

        self.__guide: widgets.NodePicker
        self.__cluster: widgets.NodePicker

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        form_layout: widgets.FormLayout = widgets.FormLayout(parent)
        main_layout.addLayout(form_layout)

        self.__guide = widgets.NodePicker(parent, multi_select=False)
        form_layout.addRow(widgets.FormLabel("Guide"), self.__guide)

        self.__cluster = widgets.NodePicker(parent, multi_select=False)
        form_layout.addRow(widgets.FormLabel("Cluster Handle"), self.__cluster)

        system_group: QtWidgets.QLineEdit = QtWidgets.QLineEdit(parent)
        form_layout.addRow(widgets.FormLabel("System Group"), system_group)

        delete_guide: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Delete Guide", parent
        )
        form_layout.addRow("", delete_guide)

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
        settings.system_group.bind(
            setter=system_group.setText,
            getter=system_group.text,
        )
        settings.delete_guide.bind(
            setter=delete_guide.setChecked,
            getter=delete_guide.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Validates inputs and builds the cluster tweak rig."""
        self.save_settings()

        guide: str = self.__guide.text()
        if not guide:
            _logger.error(
                "A guide node is required to create a cluster tweak rig."
            )
            return

        cluster: str = self.__cluster.text()
        if not cluster:
            _logger.error(
                "A cluster handle is required to create a cluster tweak rig."
            )
            return

        settings: Settings = self.tool_settings()
        apply(
            guide,
            cluster,
            settings.system_group.value(),
            settings.delete_guide.value(),
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


def apply(
    guide: str,
    cluster_handle: str,
    system_group: str = SYSTEM_GROUP,
    delete_guide: bool = True,
) -> None:
    """Builds a matrix-driven tweak rig for a cluster deformer.

    Args:
        guide (str): The guide transform node used for placement and naming.
        cluster_handle (str): The cluster handle transform node to rig.
        system_group (str, optional): The parent group name for cluster system
            nodes. Defaults to SYSTEM_GROUP.
        delete_guide (bool, optional): Whether to delete the guide node after
            building the rig. Defaults to True.
    """
    if not cmds.objExists(system_group):
        system_group = cmds.createNode("transform", name=system_group)

    base_name: str = extract_base_name(guide)

    parents: list[str] = cmds.listRelatives(guide, parent=True, path=True) or []
    guide_parent: str = parents[0] if parents else WORLD_DAG_PATH

    controller_space: str = cmds.createNode(
        "transform",
        name=f"{base_name}Space_null",
        parent=guide_parent,
    )
    cmds.matchTransform(controller_space, guide)

    cluster_ctrl: str = create_controller.Sphere().create(
        "", base_name, "ctrl", 1.0, None, None, 0, controller_space
    )

    cluster_space: str = cmds.createNode(
        "transform",
        name=f"{base_name}ClusterSpace_null",
        parent=system_group,
    )
    cmds.matchTransform(cluster_space, guide)

    cluster_handle = cmds.parent(cluster_handle, cluster_space)[0]
    cmds.setAttr(f"{cluster_handle}.translate", 0, 0, 0, type="double3")
    cmds.setAttr(f"{cluster_handle}.rotate", 0, 0, 0, type="double3")
    cmds.setAttr(f"{cluster_handle}.scale", 1, 1, 1, type="double3")
    cmds.setAttr(f"{cluster_handle}.visibility", False)
    cmds.makeIdentity(
        cluster_handle, apply=True, translate=True, rotate=True, scale=True
    )
    cmds.xform(
        cluster_handle,
        rotatePivot=(0, 0, 0),
        scalePivot=(0, 0, 0),
        worldSpace=False,
    )
    cmds.connectAttr(f"{cluster_ctrl}.translate", f"{cluster_handle}.translate")
    cmds.connectAttr(f"{cluster_ctrl}.rotate", f"{cluster_handle}.rotate")
    cmds.connectAttr(f"{cluster_ctrl}.scale", f"{cluster_handle}.scale")
    cmds.connectAttr(f"{cluster_ctrl}.shear", f"{cluster_handle}.shear")
    cmds.connectAttr(
        f"{cluster_ctrl}.rotateOrder", f"{cluster_handle}.rotateOrder"
    )

    cluster_handle_shapes: list[str] = (
        cmds.listRelatives(cluster_handle, shapes=True, path=True) or []
    )
    cmds.setAttr(f"{cluster_handle_shapes[0]}.origin", 0, 0, 0, type="double3")

    cluster_matrix: str = cmds.createNode(
        "multMatrix", name=f"{base_name}_multMtx"
    )
    cmds.connectAttr(
        f"{cluster_handle}.matrix", f"{cluster_matrix}.matrixIn[0]"
    )
    cmds.connectAttr(f"{cluster_space}.matrix", f"{cluster_matrix}.matrixIn[1]")

    cluster_inv_mtx: list[float] = cmds.getAttr(
        f"{cluster_space}.inverseMatrix"
    )  # type: ignore
    cluster: str = cmds.listConnections(
        f"{cluster_handle}.worldMatrix[0]",
        source=False,
        destination=True,
        type="cluster",
    )[0]
    cmds.connectAttr(
        f"{cluster_matrix}.matrixSum", f"{cluster}.matrix", force=True
    )
    cmds.setAttr(f"{cluster}.bindPreMatrix", cluster_inv_mtx, type="matrix")

    dcc.attribute.lock_and_hide(
        [system_group, cluster_space, cluster_handle],
        translate=True,
        rotate=True,
        scale=True,
        visibility=True,
    )
    dcc.node.hide_history(
        [controller_space, cluster_ctrl, cluster_handle, cluster]
    )
    if delete_guide:
        cmds.delete(guide)


def main(unique_id: str = "") -> None:
    """Initializes and displays the main application window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
