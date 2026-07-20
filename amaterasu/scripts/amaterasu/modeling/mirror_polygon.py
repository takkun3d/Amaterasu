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
"""Mirrors polygons to easily generate inverted meshes."""

from __future__ import annotations
from typing import Any
from maya import cmds

from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Mirror Polygon"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the tool.

    Attributes:
        window_geo (framework.Variant[str]): Geometry data of the window.
        axis (framework.Variant[int]): Mirror axis (0: X, 1: Y, 2: Z).
        flip_uvs (framework.Variant[bool]): Whether to flip UVs.
        uv_direction (framework.Variant[int]): UV flip direction.
        search (framework.Variant[str]): Search string for renaming.
        replace (framework.Variant[str]): Replace string for renaming.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    axis: framework.Variant[int] = framework.Variant(0)
    flip_uvs: framework.Variant[bool] = framework.Variant(True)
    uv_direction: framework.Variant[int] = framework.Variant(2)
    search: framework.Variant[str] = framework.Variant("_L_")
    replace: framework.Variant[str] = framework.Variant("_R_")


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Mirror Polygon tool."""

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

        axis: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        axis.addItems(["X", "Y", "Z"])
        main_layout.addRow(widgets.FormLabel("Axis"), axis)

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

        main_layout.addRow(
            widgets.FrameWidget("Rename Options", False, False, self)
        )

        search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Search"), search)

        replace: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Replace"), replace)

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
        settings.flip_uvs.bind(
            setter=flip_uvs.setChecked,
            getter=flip_uvs.isChecked,
        )
        settings.uv_direction.bind(
            setter=uv_direction.setCurrentIndex,
            getter=uv_direction.currentIndex,
        )
        settings.search.bind(
            setter=search.setText,
            getter=search.text,
        )
        settings.replace.bind(
            setter=replace.setText,
            getter=replace.text,
        )

        # Sync UV direction
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


def mirror_polygon(
    node: str,
    axis: int = 0,
    flip_uvs: bool = False,
    uv_direction: int = 0,
    search: str = "",
    replace: str = "",
) -> utils.DataResult[list[str]]:
    """Inverts a selected polygon based on specified parameters.

    Args:
        node (str): Transform node name to apply the mirror to.
        axis (int, optional): The mirror axis (0: X, 1: Y, 2: Z). Defaults to 0.
        flip_uvs (bool, optional): Whether to flip UVs. Defaults to False.
        uv_direction (int, optional): The UV flip direction (0: Local U,
            1: Local V, 2: World U, 3: World V). Defaults to 0.
        search (str, optional): Search string for renaming. Defaults to "".
        replace (str, optional): Replace string for renaming. Defaults to "".

    Returns:
        utils.DataResult[list[str]]: The result object containing the newly
            created node names as its value payload.
    """
    result: utils.DataResult[list[str]] = utils.DataResult([])
    mirror_scales: list[list[int]] = [[-1, 1, 1], [1, -1, 1], [1, 1, -1]]

    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        result.add_failure(node, "Node has no shape.")
        return result

    shape: str = shapes[0]
    if cmds.objectType(shape) != "mesh":
        result.add_failure(node, "Object is not a polygon mesh.")
        return result

    new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
    cmds.scale(
        mirror_scales[axis][0],
        mirror_scales[axis][1],
        mirror_scales[axis][2],
        new_node,
        relative=True,
    )

    try:
        cmds.makeIdentity(
            new_node,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )
    except RuntimeError:
        cmds.delete(new_node)
        result.add_failure(new_node, "Failed to freeze transformations.")
        return result

    cmds.polyNormal(
        new_node,
        normalMode=0,
        userNormalMode=False,
        constructionHistory=False,
    )
    cmds.setAttr(f"{new_node}.opposite", False)
    cmds.setAttr(f"{new_node}.doubleSided", True)

    if flip_uvs:
        kwargs: dict[str, Any] = {
            "flipType": uv_direction % 2,
            "local": True,
        }
        if uv_direction in (2, 3):
            kwargs["usePivot"] = True
            kwargs["pivotU"] = 0
            kwargs["pivotV"] = 0
        cmds.polyFlipUV(new_node, **kwargs)

    if search:
        try:
            base_name: str = node.split("|")[-1]
            new_name: str = base_name.replace(search, replace)
            new_node = cmds.rename(new_node, new_name)

        except RuntimeError:
            result.add_failure(
                base_name, "The new name contains invalid characters."
            )

    result.set_value([new_node])
    return result


def option(unique_id: str = "") -> None:
    """Shows the tool option window.

    Args:
        unique_id (str, optional): A unique ID for restoring window states.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Applies the mirror operation according to the settings.

    Args:
        settings (Settings | None, optional): The tool settings instance.
            Defaults to None, which loads the settings from the current
            instance.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        _logger.error("Select a polygon mesh to mirror.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: utils.DataResult[list[str]] = utils.DataResult([])
    for node in selection:
        r: utils.DataResult[list[str]] = mirror_polygon(
            node,
            settings.axis.value(),
            settings.flip_uvs.value(),
            settings.uv_direction.value(),
            settings.search.value(),
            settings.replace.value(),
        )
        result.merge(r)

    if result.value():
        cmds.select(*result.value())

    result.log(_logger)
