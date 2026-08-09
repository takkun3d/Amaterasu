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
"""Separates polygons from the selected object."""

from __future__ import annotations
from typing import Any
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, widgets, utils

__product__: str = "Separate"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)

SMOOTH_MESH_ATTRS: list[str] = [
    "displaySmoothMesh",
    "useGlobalSmoothDrawType",
    "smoothDrawType",
    "displaySubdComps",
    "smoothLevel",
    "useSmoothPreviewForRender",
    "renderSmoothLevel",
    "osdVertBoundary",
    "osdFvarBoundary",
    "osdFvarPropagateCorners",
    "osdSmoothTriangles",
    "osdCreaseMethod",
    "showDisplacements",
    "loadTiledTextures",
    "smoothTessLevel",
    "boundaryRule",
    "continuity",
    "smoothUVs",
    "propagateEdgeHardness",
    "keepMapBorders",
    "keepHardEdge",
    "keepBorder",
]


class Settings(framework.ToolSettings):
    """Settings for the Separate tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        keep_smooth (framework.Variant[bool]): Flag to retain smooth mesh
            preview options.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    keep_smooth: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Separate tool."""

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

        keep_smooth: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Keep Smooth Mesh Preview Options", self
        )
        main_layout.addRow(widgets.FormLabel(""), keep_smooth)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.keep_smooth.bind(
            setter=keep_smooth.setChecked,
            getter=keep_smooth.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Applies the separate operation."""
        self.save_settings()
        main(self.tool_settings())


def apply(nodes: list[str], keep_smooth: bool = True) -> bool:
    """Separates polygons of the given nodes.

    Args:
        nodes (list[str]): A list of polygon nodes to separate.
        keep_smooth (bool, optional): Retains smooth mesh preview settings.
            Defaults to True.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    result: list[str] = []
    for node in nodes:
        smooth_mesh_values: list[Any] = []
        if keep_smooth:
            for attr in SMOOTH_MESH_ATTRS:
                smooth_mesh_values.append(cmds.getAttr(f"{node}.{attr}"))

        original_name: str = node.split("|")[-1]
        temp: list[str] = cmds.listRelatives(node, parent=True, path=True) or []
        parent: str = ""
        if temp:
            parent = temp[0]

        if parent:
            cmds.lockNode(parent, lock=True)

        try:
            separated_objects: list[str] = cmds.polySeparate(
                node, constructionHistory=False
            )  # type: ignore
        except RuntimeError:
            if parent:
                cmds.lockNode(parent, lock=False)
            _logger.error("Failed to separate.")
            return False

        # Unparent separate group.
        for i, _node in enumerate(separated_objects):
            if parent:
                separated_objects[i] = cmds.parent(_node, parent)[0]
            else:
                separated_objects[i] = cmds.parent(_node, world=True)[0]

        # Delete separate group (original node).
        if cmds.objExists(node):
            cmds.delete(node)

        # Cleanup separated nodes.
        for _node in separated_objects:
            if keep_smooth:
                for attr, value in zip(SMOOTH_MESH_ATTRS, smooth_mesh_values):
                    cmds.setAttr(f"{_node}.{attr}", value)

            surface_shaders: list[str] = dcc.mesh.get_shading_groups(_node)
            if surface_shaders and len(surface_shaders) == 1:
                cmds.sets(_node, edit=True, forceElement=surface_shaders[0])

            try:
                _node = cmds.rename(_node, original_name)
            except RuntimeError:
                pass

            result.append(_node)

        if parent:
            cmds.lockNode(parent, lock=False)

    if result:
        cmds.select(*result)

    return True


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Applies the separate operation based on the current UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to use.
            If None, it initializes settings from the module name and reads
            them from the file. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select polygons to separate.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = apply(selection, settings.keep_smooth.value())
    if result:
        _logger.info("Done.")
