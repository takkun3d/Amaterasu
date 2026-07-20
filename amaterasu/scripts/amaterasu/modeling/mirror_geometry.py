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
"""Mirrors geometry to easily generate inverted meshes."""

from __future__ import annotations
from maya import cmds

from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Mirror Geometry"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the tool.

    Attributes:
        window_geo (framework.Variant[str]): Geometry data of the window.
        cut_mesh (framework.Variant[bool]): Whether to cut the geometry.
        axis (framework.Variant[int]): Mirror axis (0: X, 1: Y, 2: Z).
        direction (framework.Variant[int]): Mirror direction (0: Pos, 1: Neg).
        merge (framework.Variant[bool]): Whether to merge vertices.
        soft_edge (framework.Variant[bool]): Whether to apply soft edges.
        threshold (framework.Variant[float]): Threshold distance for merging.
        flip_uvs (framework.Variant[bool]): Whether to flip UVs.
        uv_direction (framework.Variant[int]): UV flip direction.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    cut_mesh: framework.Variant[bool] = framework.Variant(True)
    axis: framework.Variant[int] = framework.Variant(0)
    direction: framework.Variant[int] = framework.Variant(1)
    merge: framework.Variant[bool] = framework.Variant(True)
    soft_edge: framework.Variant[bool] = framework.Variant(True)
    threshold: framework.Variant[float] = framework.Variant(0.001)
    flip_uvs: framework.Variant[bool] = framework.Variant(True)
    uv_direction: framework.Variant[int] = framework.Variant(2)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Mirror Geometry tool."""

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

        main_layout.addRow(
            widgets.FrameWidget("Mirror Options", False, False, self)
        )

        cut_mesh: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self)
        cut_mesh.setText("Cut Geometry")
        main_layout.addRow("", cut_mesh)

        axis: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        axis.addItems(["X", "Y", "Z"])
        main_layout.addRow(widgets.FormLabel("Axis"), axis)

        direction: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        direction.addItems(["+", "-"])
        main_layout.addRow(widgets.FormLabel("Direction"), direction)

        main_layout.addRow(
            widgets.FrameWidget("Merge Options", False, False, self)
        )

        merge: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self)
        merge.setText("Merge")
        main_layout.addRow("", merge)

        soft_edge: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self)
        soft_edge.setText("Apply Soft Edge")
        main_layout.addRow("", soft_edge)
        soft_edge_id: int = main_layout.row_id()

        threshold: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox(self)
        threshold.setRange(0, 999)
        threshold.setDecimals(5)
        main_layout.addRow(widgets.FormLabel("Threshold"), threshold)
        threshold_id: int = main_layout.row_id()

        main_layout.addRow(
            widgets.FrameWidget("UV Options", False, False, self)
        )

        flip_uvs: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self)
        flip_uvs.setText("Flip UVs")
        main_layout.addRow("", flip_uvs)

        uv_direction: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        uv_direction.addItems(["Local U", "Local V", "World U", "World V"])
        main_layout.addRow(widgets.FormLabel("Direction"), uv_direction)
        uv_direction_id: int = main_layout.row_id()

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.cut_mesh.bind(
            setter=cut_mesh.setChecked,
            getter=cut_mesh.isChecked,
        )
        settings.axis.bind(
            setter=axis.setCurrentIndex,
            getter=axis.currentIndex,
        )
        settings.direction.bind(
            setter=direction.setCurrentIndex,
            getter=direction.currentIndex,
        )
        settings.merge.bind(
            setter=merge.setChecked,
            getter=merge.isChecked,
        )
        settings.soft_edge.bind(
            setter=soft_edge.setChecked,
            getter=soft_edge.isChecked,
        )
        settings.threshold.bind(
            setter=threshold.setValue,
            getter=threshold.value,
        )
        settings.flip_uvs.bind(
            setter=flip_uvs.setChecked,
            getter=flip_uvs.isChecked,
        )
        settings.uv_direction.bind(
            setter=uv_direction.setCurrentIndex,
            getter=uv_direction.currentIndex,
        )

        # Sync soft edge
        merge.toggled.connect(
            lambda checked: main_layout.set_row_enabled(soft_edge_id, checked)
        )
        main_layout.set_row_enabled(soft_edge_id, merge.isChecked())

        # Sync merge
        merge.toggled.connect(
            lambda checked: main_layout.set_row_enabled(threshold_id, checked)
        )
        main_layout.set_row_enabled(threshold_id, merge.isChecked())

        # sync uv direction
        flip_uvs.toggled.connect(
            lambda checked: main_layout.set_row_enabled(
                uv_direction_id, checked
            )
        )
        main_layout.set_row_enabled(uv_direction_id, flip_uvs.isChecked())

    @dcc.undo
    def apply(self) -> None:
        """Applies the mirror operation based on current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    nodes: list[str],
    cut_mesh: bool = True,
    axis: int = 0,  # x=0, y=1, z=2
    direction: int = 1,  # Positive(+)=0, Negative(-)=1
    merge: bool = True,
    soft_edge: bool = True,
    threshold: float = 0.001,
    flip_uvs: bool = False,
    uv_direction: int = 0,
) -> bool:
    """Inverts selected polygons based on specified parameters.

    Args:
        nodes (list[str]): List of transform node names to apply the mirror to.
        cut_mesh (bool): Whether to cut the mesh along the mirror axis.
        axis (int): The mirror axis (0: X, 1: Y, 2: Z).
        direction (int): The mirror direction (0: Positive, 1: Negative).
        merge (bool): Whether to merge vertices on the mirror axis.
        soft_edge (bool): Whether to apply soft edges to merged vertices.
        threshold (float): The distance threshold for merging vertices.
        flip_uvs (bool): Whether to flip UVs for the mirrored geometry.
        uv_direction (int): The UV flip direction.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    smoothing_angle: float = 180.0 if soft_edge else 0.0
    uv_direction = uv_direction + 1 if flip_uvs else 0
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            _logger.warning("Node has no shape: %s", node)
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != "mesh":
            _logger.warning("Object is not a polygon mesh: %s", shape)
            continue

        cmds.polyMirrorFace(
            shape,
            cutMesh=cut_mesh,
            axis=axis,
            axisDirection=direction,
            mirrorAxis=1,  # object
            mirrorPosition=0.0,
            mergeMode=merge,
            mergeThresholdType=1,  # Custom
            mergeThreshold=threshold,
            smoothingAngle=smoothing_angle,
            flipUVs=uv_direction,
            constructionHistory=False,
        )  # type: ignore

    cmds.select(*nodes)
    return True


def option(unique_id: str = "") -> None:
    """Shows the tool option window.

    Args:
        unique_id (str): A unique ID for restoring window states.
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Applies the operation according to the settings.

    Args:
        settings (Settings | None): The tool settings instance. Defaults to
            None, which loads the settings from the current instance.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select a polygon mesh to mirror.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = apply(
        selection,
        settings.cut_mesh.value(),
        settings.axis.value(),
        settings.direction.value(),
        settings.merge.value(),
        settings.soft_edge.value(),
        settings.threshold.value(),
        settings.flip_uvs.value(),
        settings.uv_direction.value(),
    )
    if result:
        _logger.info("Done.")
