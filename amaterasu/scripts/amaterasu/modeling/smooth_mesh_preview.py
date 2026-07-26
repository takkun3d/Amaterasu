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
"""Applies smooth mesh preview settings to selected polygon meshes."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, widgets, utils

__product__: str = "Smooth Mesh Preview"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Smooth Mesh Preview tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        display_smooth_mesh (framework.Variant[int]): Display state index.
        use_global_smooth_draw_type (framework.Variant[bool]): Global draw flag.
        smooth_draw_type (framework.Variant[int]): Subdivision method index.
        display_subd_comps (framework.Variant[bool]): Display components flag.
        smooth_level (framework.Variant[int]): Preview division levels.
        use_smooth_preview_for_render (framework.Variant[bool]): Render flag.
        render_smooth_level (framework.Variant[int]): Render division levels.
        osd_vert_boundary (framework.Variant[int]): OSD Vertex boundary rule.
        osd_fvar_boundary (framework.Variant[int]): OSD UV boundary smoothing.
        osd_fvar_propagate_corners (framework.Variant[bool]): Propagate corners.
        osd_smooth_triangles (framework.Variant[bool]): OSD Smooth triangles.
        osd_crease_method (framework.Variant[int]): OSD Crease method index.
        enable_open_cl (framework.Variant[bool]): OpenCL acceleration flag.
        smooth_tess_level (framework.Variant[int]): Adaptive tessellation level.
        boundary_rule (framework.Variant[int]): Maya boundary rules index.
        continuity (framework.Variant[float]): Maya continuity value.
        smooth_uvs (framework.Variant[bool]): Smooth UVs flag.
        propagate_edge_hardness (framework.Variant[bool]): Propagate edge flag.
        keep_map_borders (framework.Variant[int]): Map borders rule index.
        keep_border (framework.Variant[bool]): Preserve geometry borders flag.
        keep_hard_edge (framework.Variant[bool]): Preserve hard edges flag.
    """

    window_geo: framework.Variant[str] = framework.Variant("")

    # Smooth Mesh
    display_smooth_mesh: framework.Variant[int] = framework.Variant(2)
    use_global_smooth_draw_type: framework.Variant[bool] = framework.Variant(
        False
    )
    smooth_draw_type: framework.Variant[int] = framework.Variant(0)

    # Subdivision Levels
    display_subd_comps: framework.Variant[bool] = framework.Variant(False)
    smooth_level: framework.Variant[int] = framework.Variant(2)
    use_smooth_preview_for_render: framework.Variant[bool] = framework.Variant(
        True
    )
    render_smooth_level: framework.Variant[int] = framework.Variant(2)

    # OpenSubdiv Controls
    osd_vert_boundary: framework.Variant[int] = framework.Variant(0)
    osd_fvar_boundary: framework.Variant[int] = framework.Variant(3)
    osd_fvar_propagate_corners: framework.Variant[bool] = framework.Variant(
        False
    )
    osd_smooth_triangles: framework.Variant[bool] = framework.Variant(False)
    osd_crease_method: framework.Variant[int] = framework.Variant(0)
    enable_open_cl: framework.Variant[bool] = framework.Variant(True)
    smooth_tess_level: framework.Variant[int] = framework.Variant(7)

    # Maya Catmull-Clark Controls
    boundary_rule: framework.Variant[int] = framework.Variant(1)
    continuity: framework.Variant[float] = framework.Variant(1.0)
    smooth_uvs: framework.Variant[bool] = framework.Variant(True)
    propagate_edge_hardness: framework.Variant[bool] = framework.Variant(True)
    keep_map_borders: framework.Variant[int] = framework.Variant(1)
    keep_border: framework.Variant[bool] = framework.Variant(False)
    keep_hard_edge: framework.Variant[bool] = framework.Variant(False)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Smooth Mesh Preview tool."""

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

        # ----------------------------------------------------------------------
        # Smooth Mesh
        # ----------------------------------------------------------------------
        main_layout.addRow(
            widgets.FrameWidget("Smooth Mesh", False, False, parent)
        )

        display_smooth_mesh = QtWidgets.QComboBox(parent)
        display_smooth_mesh.addItems(
            ["OFF", "Cage + Smooth Mesh", "Smooth Mesh"]
        )
        main_layout.addRow(
            widgets.FormLabel("Smooth Mesh Preview"), display_smooth_mesh
        )

        use_global_draw = QtWidgets.QCheckBox(
            "Use Global Subdivision Method", parent
        )
        main_layout.addRow("", use_global_draw)

        smooth_draw_type = QtWidgets.QComboBox(parent)
        smooth_draw_type.addItems(
            [
                "Maya Catmull-Clark",
                "OpenSubdiv Catmull-Clark",
                "OpenSubdiv Catmull-Clark Adaptive",
            ]
        )
        main_layout.addRow(
            widgets.FormLabel("Subdivision Method"), smooth_draw_type
        )

        # ----------------------------------------------------------------------
        # Subdivision Levels
        # ----------------------------------------------------------------------
        main_layout.addRow(
            widgets.FrameWidget("Subdivision Levels", False, False, parent)
        )

        display_subd = QtWidgets.QCheckBox("Display Subdivisions", parent)
        main_layout.addRow("", display_subd)

        smooth_level = QtWidgets.QSpinBox(parent)
        smooth_level.setRange(0, 10)
        smooth_level.setMinimumWidth(70)
        main_layout.addRow(
            widgets.FormLabel("Preview Division Levels"), smooth_level
        )

        use_preview = QtWidgets.QCheckBox(
            "Use Preview Level for Rendering", parent
        )
        main_layout.addRow("", use_preview)

        render_level = QtWidgets.QSpinBox(parent)
        render_level.setRange(0, 10)
        render_level.setMinimumWidth(70)
        main_layout.addRow(
            widgets.FormLabel("Render Division Levels"), render_level
        )

        # ----------------------------------------------------------------------
        # OpenSubdiv Controls
        # ----------------------------------------------------------------------
        opensubdiv: widgets.FrameWidget = widgets.FrameWidget(
            "OpenSubdiv Controls", True, True, parent
        )
        main_layout.addRow(opensubdiv)

        opensubdiv_layout: widgets.FormLayout = widgets.FormLayout(self)
        opensubdiv.setLayout(opensubdiv_layout)

        osd_vert_boundary = QtWidgets.QComboBox(parent)
        osd_vert_boundary.addItems(["Sharp edges and corners", "Sharp edges"])
        opensubdiv_layout.addRow(
            widgets.FormLabel("Vertex Boundary"), osd_vert_boundary
        )

        osd_fvar_boundary = QtWidgets.QComboBox(parent)
        osd_fvar_boundary.addItems(
            [
                "None",
                "Preserve Edges and Corners",
                "Preserve Edges",
                "Maya Catmull-Clark",
            ]
        )
        opensubdiv_layout.addRow(
            widgets.FormLabel("UV Boundary Smoothing"), osd_fvar_boundary
        )

        osd_fvar_propagate = QtWidgets.QCheckBox("Propagate UV Corners", parent)
        opensubdiv_layout.addRow("", osd_fvar_propagate)

        osd_smooth_triangles = QtWidgets.QCheckBox("Smooth Triangles", parent)
        opensubdiv_layout.addRow("", osd_smooth_triangles)

        osd_crease_method = QtWidgets.QComboBox(parent)
        osd_crease_method.addItems(["Normal", "Chaikin"])
        opensubdiv_layout.addRow(
            widgets.FormLabel("Crease Method"), osd_crease_method
        )

        enable_open_cl = QtWidgets.QCheckBox("OpenCL Acceleration", parent)
        opensubdiv_layout.addRow("", enable_open_cl)

        smooth_tess = QtWidgets.QSpinBox(parent)
        smooth_tess.setRange(1, 10)
        smooth_tess.setMinimumWidth(70)
        opensubdiv_layout.addRow(
            widgets.FormLabel("Adaptive Tessellation Level"), smooth_tess
        )

        # ----------------------------------------------------------------------
        # Maya Catmull-Clark Controls
        # ----------------------------------------------------------------------
        maya_catmull_clark: widgets.FrameWidget = widgets.FrameWidget(
            "Maya Catmull-Clark Controls", True, True, parent
        )
        main_layout.addRow(maya_catmull_clark)

        maya_catmull_clark_layout: widgets.FormLayout = widgets.FormLayout(self)
        maya_catmull_clark.setLayout(maya_catmull_clark_layout)

        boundary_rule = QtWidgets.QComboBox(parent)
        boundary_rule.addItems(["Legacy", "Crease All", "Crease Edges"])
        maya_catmull_clark_layout.addRow(
            widgets.FormLabel("Boundary Rules"), boundary_rule
        )

        continuity = QtWidgets.QDoubleSpinBox(parent)
        continuity.setRange(0.0, 1.0)
        continuity.setSingleStep(0.1)
        continuity.setMinimumWidth(70)
        maya_catmull_clark_layout.addRow(
            widgets.FormLabel("Continuity"), continuity
        )

        smooth_uvs = QtWidgets.QCheckBox("Smooth UVs", parent)
        maya_catmull_clark_layout.addRow("", smooth_uvs)

        propagate_edge = QtWidgets.QCheckBox("Propagate Edge Hardness", parent)
        maya_catmull_clark_layout.addRow("", propagate_edge)

        keep_map_borders = QtWidgets.QComboBox(parent)
        keep_map_borders.addItems(
            ["Do not smooth", "Smooth internal", "Smooth all"]
        )
        maya_catmull_clark_layout.addRow(
            widgets.FormLabel("Map Borders"), keep_map_borders
        )

        keep_border = QtWidgets.QCheckBox("Geometry borders", parent)
        maya_catmull_clark_layout.addRow(
            widgets.FormLabel("Preserve"), keep_border
        )

        keep_hard_edge = QtWidgets.QCheckBox("Hard edges", parent)
        maya_catmull_clark_layout.addRow("", keep_hard_edge)

        # ======================================================================
        # Event
        # ======================================================================
        smooth_draw_type.currentIndexChanged.connect(
            lambda idx: (
                maya_catmull_clark.set_collapsed(idx != 0),  # type: ignore
                opensubdiv.set_collapsed(idx == 0),  # type: ignore
            )
        )
        initial_idx: int = smooth_draw_type.currentIndex()
        maya_catmull_clark.set_collapsed(initial_idx != 0)
        opensubdiv.set_collapsed(initial_idx == 0)

        # ======================================================================
        # Bind Settings
        # ======================================================================
        settings: Settings = self.tool_settings()

        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

        # Smooth Mesh Bindings
        settings.display_smooth_mesh.bind(
            setter=display_smooth_mesh.setCurrentIndex,
            getter=display_smooth_mesh.currentIndex,
        )
        settings.use_global_smooth_draw_type.bind(
            setter=use_global_draw.setChecked,
            getter=use_global_draw.isChecked,
        )
        settings.smooth_draw_type.bind(
            setter=smooth_draw_type.setCurrentIndex,
            getter=smooth_draw_type.currentIndex,
        )

        # Subdivision Levels Bindings
        settings.display_subd_comps.bind(
            setter=display_subd.setChecked,
            getter=display_subd.isChecked,
        )
        settings.smooth_level.bind(
            setter=smooth_level.setValue,
            getter=smooth_level.value,
        )
        settings.use_smooth_preview_for_render.bind(
            setter=use_preview.setChecked,
            getter=use_preview.isChecked,
        )
        settings.render_smooth_level.bind(
            setter=render_level.setValue,
            getter=render_level.value,
        )

        # OpenSubdiv Controls Bindings
        settings.osd_vert_boundary.bind(
            setter=osd_vert_boundary.setCurrentIndex,
            getter=osd_vert_boundary.currentIndex,
        )
        settings.osd_fvar_boundary.bind(
            setter=osd_fvar_boundary.setCurrentIndex,
            getter=osd_fvar_boundary.currentIndex,
        )
        settings.osd_fvar_propagate_corners.bind(
            setter=osd_fvar_propagate.setChecked,
            getter=osd_fvar_propagate.isChecked,
        )
        settings.osd_smooth_triangles.bind(
            setter=osd_smooth_triangles.setChecked,
            getter=osd_smooth_triangles.isChecked,
        )
        settings.osd_crease_method.bind(
            setter=osd_crease_method.setCurrentIndex,
            getter=osd_crease_method.currentIndex,
        )
        settings.enable_open_cl.bind(
            setter=enable_open_cl.setChecked,
            getter=enable_open_cl.isChecked,
        )
        settings.smooth_tess_level.bind(
            setter=smooth_tess.setValue,
            getter=smooth_tess.value,
        )

        # Maya Catmull-Clark Controls Bindings
        settings.boundary_rule.bind(
            setter=boundary_rule.setCurrentIndex,
            getter=boundary_rule.currentIndex,
        )
        settings.continuity.bind(
            setter=continuity.setValue,
            getter=continuity.value,
        )
        settings.smooth_uvs.bind(
            setter=smooth_uvs.setChecked,
            getter=smooth_uvs.isChecked,
        )
        settings.propagate_edge_hardness.bind(
            setter=propagate_edge.setChecked,
            getter=propagate_edge.isChecked,
        )
        settings.keep_map_borders.bind(
            setter=keep_map_borders.setCurrentIndex,
            getter=keep_map_borders.currentIndex,
        )
        settings.keep_border.bind(
            setter=keep_border.setChecked,
            getter=keep_border.isChecked,
        )
        settings.keep_hard_edge.bind(
            setter=keep_hard_edge.setChecked,
            getter=keep_hard_edge.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Applies the smooth mesh preview operation."""
        self.save_settings()
        main(self.tool_settings())


def apply(nodes: list[str], settings: Settings) -> bool:
    """Applies smooth mesh preview parameters to the given nodes.

    Args:
        nodes (list[str]): A list of polygon nodes to modify.
        settings (Settings): The tool settings containing preview parameters.

    Returns:
        bool: True if the operation was successful, False otherwise.
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

        # Smooth Mesh
        cmds.setAttr(
            f"{shape}.displaySmoothMesh",
            settings.display_smooth_mesh.value(),
        )
        cmds.setAttr(
            f"{shape}.useGlobalSmoothDrawType",
            settings.use_global_smooth_draw_type.value(),
        )
        cmds.setAttr(
            f"{shape}.smoothDrawType",
            [0, 2, 3][settings.smooth_draw_type.value()],
        )

        # Subdivisions Level
        cmds.setAttr(
            f"{shape}.displaySubdComps",
            settings.display_subd_comps.value(),
        )
        cmds.setAttr(f"{shape}.smoothLevel", settings.smooth_level.value())
        cmds.setAttr(
            f"{shape}.useSmoothPreviewForRender",
            settings.use_smooth_preview_for_render.value(),
        )
        cmds.setAttr(
            f"{shape}.renderSmoothLevel",
            settings.render_smooth_level.value(),
        )

        # OpenSubdiv Controls
        cmds.setAttr(
            f"{shape}.osdVertBoundary",
            [1, 2][settings.osd_vert_boundary.value()],
        )
        cmds.setAttr(
            f"{shape}.osdFvarBoundary",
            settings.osd_fvar_boundary.value(),
        )
        cmds.setAttr(
            f"{shape}.osdFvarPropagateCorners",
            settings.osd_fvar_propagate_corners.value(),
        )
        cmds.setAttr(
            f"{shape}.osdSmoothTriangles",
            settings.osd_smooth_triangles.value(),
        )
        cmds.setAttr(
            f"{shape}.osdCreaseMethod",
            settings.osd_crease_method.value(),
        )
        cmds.setAttr(
            f"{shape}.enableOpenCL",
            settings.enable_open_cl.value(),
        )
        cmds.setAttr(
            f"{shape}.smoothTessLevel",
            settings.smooth_tess_level.value(),
        )

        # Maya Catmull-Clark Controls
        cmds.setAttr(
            f"{shape}.boundaryRule",
            settings.boundary_rule.value(),
        )
        cmds.setAttr(
            f"{shape}.continuity",
            settings.continuity.value(),
        )
        cmds.setAttr(f"{shape}.smoothUVs", settings.smooth_uvs.value())
        cmds.setAttr(
            f"{shape}.propagateEdgeHardness",
            settings.propagate_edge_hardness.value(),
        )
        cmds.setAttr(
            f"{shape}.keepMapBorders",
            [2, 1, 0][settings.keep_map_borders.value()],
        )
        cmds.setAttr(
            f"{shape}.keepBorder",
            settings.keep_border.value(),
        )
        cmds.setAttr(
            f"{shape}.keepHardEdge",
            settings.keep_hard_edge.value(),
        )

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
    """Applies the smooth mesh preview based on the current UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to use.
            If None, it initializes settings from the module name and reads
            them from the file. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error(
            "Select polygon meshes to apply Smooth Mesh Preview settings."
        )
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = apply(selection, settings)
    if result:
        _logger.info("Done.")
