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
"""Clean up unwanted data and optimize selected polygons."""

from __future__ import annotations
from typing import Callable
import functools
from maya import cmds
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Poly Cleaner"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Poly Cleaner tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        unlock_transformations (framework.Variant[bool]): State for unlock.
        break_connections (framework.Variant[bool]): State for break connections.
        freeze_transformations (framework.Variant[bool]): State for freeze.
        reset_transformations (framework.Variant[bool]): State for reset.
        delete_history (framework.Variant[bool]): State for history deletion.
        delete_user_defined_attr (framework.Variant[bool]): State for attr.
        remove_intermediate_obj (framework.Variant[bool]): State for obj.
        freeze_vertex (framework.Variant[bool]): State for freeze vertex.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    unlock_transformations: framework.Variant[bool] = framework.Variant(True)
    break_connections: framework.Variant[bool] = framework.Variant(True)
    freeze_transformations: framework.Variant[bool] = framework.Variant(True)
    reset_transformations: framework.Variant[bool] = framework.Variant(True)
    delete_history: framework.Variant[bool] = framework.Variant(True)
    delete_user_defined_attr: framework.Variant[bool] = framework.Variant(True)
    remove_intermediate_obj: framework.Variant[bool] = framework.Variant(True)
    freeze_vertex: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Poly Cleaner tool."""

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
            unique_id (str, optional): A unique ID for restoring states.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        # Define UI generation data mapped to specific functions
        options_data: list[
            tuple[
                str,
                framework.Variant[bool],
                Callable[[list[str]], bool],
            ]
        ] = [
            (
                "Freeze Vertex",
                settings.freeze_vertex,
                freeze_vertex,
            ),
            (
                "Unlock Transformations",
                settings.unlock_transformations,
                unlock_transformations,
            ),
            (
                "Break Connections",
                settings.break_connections,
                break_connections,
            ),
            (
                "Freeze Transformations",
                settings.freeze_transformations,
                freeze_transformations,
            ),
            (
                "Reset Transformations",
                settings.reset_transformations,
                reset_transformations,
            ),
            (
                "Delete History",
                settings.delete_history,
                delete_history,
            ),
            (
                "Delete User Defined Attribute",
                settings.delete_user_defined_attr,
                delete_user_defined_attribute,
            ),
            (
                "Remove Intermediate Objects",
                settings.remove_intermediate_obj,
                remove_intermediate_objects,
            ),
        ]

        # Dynamically generate UI items and connect callbacks
        for label, setting_prop, func in options_data:
            item: widgets.ActionableCheckBox = widgets.ActionableCheckBox(
                label, "Optimize Now", self
            )
            item.clicked.connect(
                functools.partial(self.execute_single_optimization, func)
            )
            main_layout.addWidget(item)

            setting_prop.bind(
                setter=item.set_checked,
                getter=item.is_checked,
            )

        main_layout.addStretch()

    def create_custom_menu(self, menu_bar: QtWidgets.QMenuBar) -> None:
        """Creates a custom tool menu and appends it to the main menu bar.

        Args:
            menu_bar (QtWidgets.QMenuBar): The main menu bar of the window
                where the custom menu will be added.
        """
        tool_menu: QtWidgets.QMenu = menu_bar.addMenu("Tool")
        action: QtGui.QAction = tool_menu.addAction(
            "Check Face Material Assignments"
        )
        action.triggered.connect(self.check_face_material_assignments_callback)

    @dcc.undo
    def execute_single_optimization(
        self, optimize_func: Callable[[list[str]], bool]
    ) -> None:
        """Executes a specific optimization function on the valid selection.

        Args:
            optimize_func (Callable[[list[str]], bool]): The target function.
        """
        selection: list[str] = self.__selection_list()
        if selection:
            result: bool = optimize_func(selection)
            if result:
                _logger.info("Done.")

    @dcc.undo
    def check_face_material_assignments_callback(self) -> None:
        """Callback to check face material assignments."""
        result: list[str] = check_face_material_assignments()
        if result:
            QtWidgets.QMessageBox.critical(
                self, __product__, "Issues found. Correction required."
            )
        else:
            QtWidgets.QMessageBox.information(
                self, __product__, "No issues found."
            )

    @dcc.undo
    def apply(self) -> None:
        """Executes the main tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())

    def __selection_list(self) -> list[str]:
        """Gets the current valid selection list.

        Returns:
            list[str]: A list of selected transform nodes.
        """
        selection: list[str] = cmds.ls(selection=True, type="transform")
        if not selection:
            _logger.error("Select objects to clean up.")
            return []

        return selection


def freeze_vertex(nodes: list[str]) -> bool:
    """Freezes the vertices of the given meshes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != "mesh":
            continue

        temp: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        temp_mesh: str = cmds.listRelatives(temp, shapes=True, path=True)[0]

        empty_mesh: str = cmds.createNode("mesh")
        empty_mesh_transform: str = cmds.listRelatives(
            empty_mesh, parent=True, path=True
        )[0]

        cmds.connectAttr(f"{empty_mesh}.outMesh", f"{shape}.inMesh", force=True)
        cmds.disconnectAttr(f"{empty_mesh}.outMesh", f"{shape}.inMesh")
        cmds.connectAttr(f"{empty_mesh}.pnts", f"{shape}.pnts", force=True)
        cmds.disconnectAttr(f"{empty_mesh}.pnts", f"{shape}.pnts")
        cmds.connectAttr(f"{temp_mesh}.outMesh", f"{shape}.inMesh", force=True)
        cmds.disconnectAttr(f"{temp_mesh}.outMesh", f"{shape}.inMesh")

        cmds.delete(temp)
        cmds.delete(empty_mesh_transform)

    if nodes:
        cmds.select(*nodes)

    return True


def unlock_transformations(nodes: list[str]) -> bool:
    """Unlocks transformation attributes on the given nodes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    dcc.attribute.unlock_and_show(nodes, True, True, True, True)
    return True


def break_connections(nodes: list[str]) -> bool:
    """Breaks incoming connections to transformation attributes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    dcc.attribute.break_transform_connections(nodes, True, True, True, True)
    return True


def freeze_transformations(nodes: list[str]) -> bool:
    """Freezes transformation values on the given nodes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    for node in nodes:
        try:
            cmds.makeIdentity(
                node,
                apply=True,
                translate=True,
                rotate=True,
                scale=True,
                normal=False,
            )

        except RuntimeError:
            _logger.error("Failed to freeze transform : %s", node)

    return True


def reset_transformations(nodes: list[str]) -> bool:
    """Resets transformation values on the given nodes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    for node in nodes:
        try:
            cmds.makeIdentity(
                node, apply=False, translate=True, rotate=True, scale=True
            )

        except RuntimeError:
            _logger.error("Failed to reset transform : %s", node)

    return True


def delete_history(nodes: list[str]) -> bool:
    """Deletes construction history for the given nodes.

    Args:
        nodes (list[str]): A list of nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    dcc.node.delete_history(nodes)
    return True


def delete_user_defined_attribute(nodes: list[str]) -> bool:
    """Deletes all user-defined attributes on the given nodes and shapes.

    Args:
        nodes (list[str]): A list of nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    dcc.attribute.delete_user_defined(nodes)
    return True


def remove_intermediate_objects(nodes: list[str]) -> bool:
    """Removes intermediate objects from the given nodes.

    Args:
        nodes (list[str]): A list of transform nodes to process.

    Returns:
        bool: True if the operation was successful.
    """
    dcc.node.remove_intermediate_objects(nodes)
    return True


def check_face_material_assignments() -> list[str]:
    """Checks for face-level material assignments on selected objects.

    Returns:
        list[str]: A list of paths with face-level material assignments.
    """
    result: list[str] = []
    materials: list[str] = cmds.ls(materials=True)

    for material in materials:
        face_assignments: list[str] = []
        cmds.hyperShade(objects=material)
        for dag_path in cmds.ls(selection=True):
            if len(dag_path.split(".")) != 1:
                face_assignments.append(dag_path)

        if face_assignments:
            result += face_assignments

    if result:
        cmds.select(*result)
    else:
        cmds.select(clear=True)

    return result


def option(unique_id: str = "") -> None:
    """Entry point for launching the tool window.

    Args:
        unique_id (str, optional): A unique ID for restoring states.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Applies clean up operations according to the provided settings.

    Args:
        settings (Settings | None, optional): Tool settings instance.
            If None, the default settings will be acquired and read.
            Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select objects to clean up")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    execution_map: list[
        tuple[framework.Variant[bool], Callable[[list[str]], bool]]
    ] = [
        (settings.unlock_transformations, unlock_transformations),
        (settings.break_connections, break_connections),
        (settings.freeze_transformations, freeze_transformations),
        (settings.reset_transformations, reset_transformations),
        (settings.delete_history, delete_history),
        (settings.delete_user_defined_attr, delete_user_defined_attribute),
        (settings.remove_intermediate_obj, remove_intermediate_objects),
        (settings.freeze_vertex, freeze_vertex),
    ]

    for setting_prop, func in execution_map:
        if setting_prop.value():
            func(selection)

    _logger.info("Done.")
