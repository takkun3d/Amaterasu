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
        smooth_uvs (framework.Variant[bool]): Smooth UVs flag.
        propagate_edge_hardness (framework.Variant[bool]): Propagate edge flag.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
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

    # Maya Catmull-Clark Controls
    smooth_uvs: framework.Variant[bool] = framework.Variant(True)
    propagate_edge_hardness: framework.Variant[bool] = framework.Variant(False)


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
        self.resize(400, 350)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        # Smooth Mesh Preview Options
        main_layout.addRow(
            widgets.FrameWidget(
                "Smooth Mesh Preview Options", False, False, parent
            )
        )

        display_smooth_mesh = QtWidgets.QComboBox(parent)
        display_smooth_mesh.addItems(
            ["OFF", "Cage + Smooth Mesh", "Smooth Mesh"]
        )
        main_layout.addRow(
            widgets.FormLabel("Smooth Mesh Preview"), display_smooth_mesh
        )

        use_global_draw = QtWidgets.QCheckBox(
            "Use global subdivision method", parent
        )
        main_layout.addRow("", use_global_draw)

        smooth_draw_type = QtWidgets.QComboBox(parent)
        smooth_draw_type.addItem("Maya Catmull-Clark", 0)
        smooth_draw_type.addItem("OpenSubdiv Catmull-Clark", 2)
        smooth_draw_type.addItem("OpenSubdiv Catmull-Clark Adaptive", 3)
        main_layout.addRow(
            widgets.FormLabel("Subdivision Method"), smooth_draw_type
        )

        # Smooth Options
        main_layout.addRow(
            widgets.FrameWidget("Smooth Options", False, False, parent)
        )

        display_subd = QtWidgets.QCheckBox("Display Subdivisions", parent)
        main_layout.addRow("", display_subd)

        smooth_level = QtWidgets.QSpinBox(parent)
        smooth_level.setRange(0, 10)
        smooth_level.setMinimumWidth(70)
        smooth_level.setButtonSymbols(
            QtWidgets.QSpinBox.ButtonSymbols.NoButtons
        )
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
        render_level.setButtonSymbols(
            QtWidgets.QSpinBox.ButtonSymbols.NoButtons
        )
        main_layout.addRow(
            widgets.FormLabel("Render Division Levels"), render_level
        )

        # Maya Catmull-Clark Options
        main_layout.addRow(
            widgets.FrameWidget(
                "Maya Catmull-Clark Options", False, False, parent
            )
        )

        smooth_uvs = QtWidgets.QCheckBox("Smooth UVs", parent)
        main_layout.addRow("", smooth_uvs)

        propagate_edge = QtWidgets.QCheckBox("Propagate Edge Hardness", parent)
        main_layout.addRow("", propagate_edge)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.display_smooth_mesh.bind(
            setter=display_smooth_mesh.setCurrentIndex,
            getter=display_smooth_mesh.currentIndex,
        )
        settings.use_global_smooth_draw_type.bind(
            setter=use_global_draw.setChecked, getter=use_global_draw.isChecked
        )
        settings.smooth_draw_type.bind(
            setter=smooth_draw_type.setCurrentIndex,
            getter=smooth_draw_type.currentIndex,
        )
        settings.display_subd_comps.bind(
            setter=display_subd.setChecked, getter=display_subd.isChecked
        )
        settings.smooth_level.bind(
            setter=smooth_level.setValue, getter=smooth_level.value
        )
        settings.use_smooth_preview_for_render.bind(
            setter=use_preview.setChecked, getter=use_preview.isChecked
        )
        settings.render_smooth_level.bind(
            setter=render_level.setValue, getter=render_level.value
        )
        settings.smooth_uvs.bind(
            setter=smooth_uvs.setChecked, getter=smooth_uvs.isChecked
        )
        settings.propagate_edge_hardness.bind(
            setter=propagate_edge.setChecked, getter=propagate_edge.isChecked
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
    draw_type_mapping: list[int] = [0, 2, 3]
    mapped_draw_type: int = draw_type_mapping[settings.smooth_draw_type.value()]

    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != "mesh":
            continue

        try:
            cmds.setAttr(
                f"{shape}.displaySmoothMesh",
                settings.display_smooth_mesh.value(),
            )
            cmds.setAttr(
                f"{shape}.useGlobalSmoothDrawType",
                settings.use_global_smooth_draw_type.value(),
            )
            cmds.setAttr(f"{shape}.smoothDrawType", mapped_draw_type)
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
            cmds.setAttr(f"{shape}.smoothUVs", settings.smooth_uvs.value())
            cmds.setAttr(
                f"{shape}.propagateEdgeHardness",
                settings.propagate_edge_hardness.value(),
            )
        except RuntimeError:
            pass

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
        _logger.error("Select polygon node to set Smooth Mesh Preview.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = apply(selection, settings)
    if result:
        _logger.info("Done.")
