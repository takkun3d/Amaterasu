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
"""Tool for removing half of the polygons from selected meshes.

This module provides a UI and functions to automatically detect and delete
half of the polygons based on the specified axis, direction, and space.
"""

from __future__ import annotations
from maya.api import OpenMaya
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Remove Half"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Remove Half tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        axis (framework.Variant[int]): The axis to evaluate (0: X, 1: Y, 2: Z).
        direction (framework.Variant[int]): The direction to remove (0: -, 1: +).
        space (framework.Variant[int]): The coordinate space (0: Local, 1: World).
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    axis: framework.Variant[int] = framework.Variant(0)
    direction: framework.Variant[int] = framework.Variant(0)
    space: framework.Variant[int] = framework.Variant(1)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Remove Half tool."""

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
            unique_id (str, optional): A unique ID for restoring window states.
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
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        axis = QtWidgets.QComboBox(self)
        axis.addItems(["X", "Y", "Z"])
        main_layout.addRow(widgets.FormLabel("Axis"), axis)

        direction = QtWidgets.QComboBox(self)
        direction.addItems(["-", "+"])
        main_layout.addRow(widgets.FormLabel("Direction"), direction)

        space = QtWidgets.QComboBox(self)
        space.addItems(["Local", "World"])
        main_layout.addRow(widgets.FormLabel("Space"), space)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.axis.bind(
            setter=axis.setCurrentIndex,
            getter=axis.currentIndex,
        )
        settings.direction.bind(
            setter=direction.setCurrentIndex,
            getter=direction.currentIndex,
        )
        settings.space.bind(
            setter=space.setCurrentIndex,
            getter=space.currentIndex,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the main tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def remove_half_faces(
    selection: OpenMaya.MSelectionList,
    axis: int = 0,
    direction: int = 1,
    space: int = 1,
) -> bool:
    """Removes half of the polygons from the given selection.

    Args:
        selection (om.MSelectionList): The selected items to process.
        axis (int, optional): The axis to evaluate (0: X, 1: Y, 2: Z).
            Defaults to 0.
        direction (int, optional): The direction to remove (0: -, 1: +).
            Defaults to 1.
        space (int, optional): The coordinate space (0: Local, 1: World).
            Defaults to 1.

    Returns:
        bool: True if faces were successfully deleted, False otherwise.
    """
    sel_iter: OpenMaya.MItSelectionList = OpenMaya.MItSelectionList(selection)
    faces_to_delete: list[str] = []

    while not sel_iter.isDone():
        dag_path: OpenMaya.MDagPath = sel_iter.getDagPath()
        node_name: str = dag_path.fullPathName()
        try:
            poly_iter: OpenMaya.MItMeshPolygon = OpenMaya.MItMeshPolygon(
                dag_path
            )
        except RuntimeError:
            _logger.warning("Skipped %s: Not a polygon mesh.", node_name)
            sel_iter.next()
            continue

        center: OpenMaya.MPoint = OpenMaya.MPoint(0.0, 0.0, 0.0)
        if space == 0:
            trans_fn: OpenMaya.MFnTransform = OpenMaya.MFnTransform(dag_path)
            center = trans_fn.rotatePivot(OpenMaya.MSpace.kWorld)

        while not poly_iter.isDone():
            face_center: OpenMaya.MPoint = poly_iter.center(
                OpenMaya.MSpace.kWorld
            )
            is_delete: bool = False
            val: float = 0.0

            if axis == 0:
                val = face_center.x - center.x
            elif axis == 1:
                val = face_center.y - center.y
            elif axis == 2:
                val = face_center.z - center.z

            if direction == 1 and val > 0:
                is_delete = True
            elif direction == 0 and val < 0:
                is_delete = True

            if is_delete:
                faces_to_delete.append(f"{node_name}.f[{poly_iter.index()}]")

            poly_iter.next()
        sel_iter.next()

    if not faces_to_delete:
        return False

    cmds.delete(faces_to_delete)  # type: ignore
    return True


def option(unique_id: str = "") -> None:
    """Entry point for launching the tool window.

    Args:
        unique_id (str, optional): A unique ID for restoring window states.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Gathers current selection and applies removal settings.

    Args:
        settings (Settings | None, optional): Tool settings instance.
            If None, the default settings will be acquired and read.
            Defaults to None.
    """
    selection: OpenMaya.MSelectionList = (
        OpenMaya.MGlobal.getActiveSelectionList()
    )
    if selection.isEmpty():
        _logger.error("Select polygon meshes to remove half faces.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = remove_half_faces(
        selection,
        settings.axis.value(),
        settings.direction.value(),
        settings.space.value(),
    )

    if result:
        _logger.info("Done.")
