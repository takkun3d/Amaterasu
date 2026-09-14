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
"""Copies animation from selected nodes to specific target nodes."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Copy Animation"
__version__: str = "1.31"
_logger: utils.Logger = utils.get_logger(__product__)

MIRROR_CHANNELS: tuple[str, str, str] = ("translate", "rotate", "scale")
MIRROR_AXES: tuple[str, str, str] = ("X", "Y", "Z")


class Settings(framework.ToolSettings):
    """Settings for the Copy Animation tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        hierarchy (framework.Variant[int]): 0 for Selected, 1 for Below.
        method (framework.Variant[int]): 0 for X:X, 1 for 1:X, 2 for Replace.
        reverse_tx (framework.Variant[bool]): Reverse translate X flag.
        reverse_ty (framework.Variant[bool]): Reverse translate Y flag.
        reverse_tz (framework.Variant[bool]): Reverse translate Z flag.
        reverse_rx (framework.Variant[bool]): Reverse rotate X flag.
        reverse_ry (framework.Variant[bool]): Reverse rotate Y flag.
        reverse_rz (framework.Variant[bool]): Reverse rotate Z flag.
        reverse_sx (framework.Variant[bool]): Reverse scale X flag.
        reverse_sy (framework.Variant[bool]): Reverse scale Y flag.
        reverse_sz (framework.Variant[bool]): Reverse scale Z flag.
        search (framework.Variant[str]): String to search in node names.
        replace (framework.Variant[str]): String to replace in node names.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    hierarchy: framework.Variant[int] = framework.Variant(1)
    method: framework.Variant[int] = framework.Variant(2)
    reverse_tx: framework.Variant[bool] = framework.Variant(False)
    reverse_ty: framework.Variant[bool] = framework.Variant(False)
    reverse_tz: framework.Variant[bool] = framework.Variant(False)
    reverse_rx: framework.Variant[bool] = framework.Variant(False)
    reverse_ry: framework.Variant[bool] = framework.Variant(False)
    reverse_rz: framework.Variant[bool] = framework.Variant(False)
    reverse_sx: framework.Variant[bool] = framework.Variant(False)
    reverse_sy: framework.Variant[bool] = framework.Variant(False)
    reverse_sz: framework.Variant[bool] = framework.Variant(False)
    search: framework.Variant[str] = framework.Variant("_L_")
    replace: framework.Variant[str] = framework.Variant("_R_")


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Copy Animation tool."""

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
            unique_id (str, optional): A unique ID for restoring window
                states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)
        self.__tx: QtWidgets.QCheckBox
        self.__ty: QtWidgets.QCheckBox
        self.__tz: QtWidgets.QCheckBox
        self.__rx: QtWidgets.QCheckBox
        self.__ry: QtWidgets.QCheckBox
        self.__rz: QtWidgets.QCheckBox
        self.__sx: QtWidgets.QCheckBox
        self.__sy: QtWidgets.QCheckBox
        self.__sz: QtWidgets.QCheckBox

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        # Copy Options
        main_layout.addRow(
            widgets.FrameWidget("Copy Options", False, False, parent)
        )
        hierarchy: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        hierarchy.addItems(["Selected", "Below"])
        main_layout.addRow(widgets.FormLabel("Hierarchy"), hierarchy)

        # Paste Options
        main_layout.addRow(
            widgets.FrameWidget("Paste Options", False, False, parent)
        )
        method: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        method.addItems(["X:X", "1:X", "Search & Replace"])
        main_layout.addRow(widgets.FormLabel("Method"), method)

        search_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Search"), search_edit)
        search_idx: int = main_layout.row_id()

        replace_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Replace"), replace_edit)
        replace_idx: int = main_layout.row_id()

        main_layout.addRow(widgets.HorizontalLine(parent))

        # Mirror Options
        transform_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
        main_layout.addRow(widgets.FormLabel("Mirror"), transform_layout)

        preset_mirror = QtWidgets.QComboBox(self)
        preset_mirror.addItems(
            [
                "XY (Behavior)",
                "YZ (Behavior)",
                "XZ (Behavior)",
                "XY (Orient)",
                "YZ (Orient)",
                "XZ (Orient)",
                "Custom",
            ]
        )
        transform_layout.addWidget(preset_mirror, 0, 0, 1, 3)

        self.__tx = QtWidgets.QCheckBox("tx", self)
        transform_layout.addWidget(self.__tx, 1, 0)

        self.__ty = QtWidgets.QCheckBox("ty", self)
        transform_layout.addWidget(self.__ty, 1, 1)

        self.__tz = QtWidgets.QCheckBox("tz", self)
        transform_layout.addWidget(self.__tz, 1, 2)

        self.__rx = QtWidgets.QCheckBox("rx", self)
        transform_layout.addWidget(self.__rx, 2, 0)

        self.__ry = QtWidgets.QCheckBox("ry", self)
        transform_layout.addWidget(self.__ry, 2, 1)

        self.__rz = QtWidgets.QCheckBox("rz", self)
        transform_layout.addWidget(self.__rz, 2, 2)

        self.__sx = QtWidgets.QCheckBox("sx", self)
        transform_layout.addWidget(self.__sx, 3, 0)

        self.__sy = QtWidgets.QCheckBox("sy", self)
        transform_layout.addWidget(self.__sy, 3, 1)

        self.__sz = QtWidgets.QCheckBox("sz", self)
        transform_layout.addWidget(self.__sz, 3, 2)

        # Settings Binding
        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.hierarchy.bind(
            setter=hierarchy.setCurrentIndex,
            getter=hierarchy.currentIndex,
        )
        settings.method.bind(
            setter=method.setCurrentIndex,
            getter=method.currentIndex,
        )
        settings.search.bind(
            setter=search_edit.setText,
            getter=search_edit.text,
        )
        settings.replace.bind(
            setter=replace_edit.setText,
            getter=replace_edit.text,
        )
        settings.reverse_tx.bind(
            setter=self.__tx.setChecked,
            getter=self.__tx.isChecked,
        )
        settings.reverse_ty.bind(
            setter=self.__ty.setChecked,
            getter=self.__ty.isChecked,
        )
        settings.reverse_tz.bind(
            setter=self.__tz.setChecked,
            getter=self.__tz.isChecked,
        )
        settings.reverse_rx.bind(
            setter=self.__rx.setChecked,
            getter=self.__rx.isChecked,
        )
        settings.reverse_ry.bind(
            setter=self.__ry.setChecked,
            getter=self.__ry.isChecked,
        )
        settings.reverse_rz.bind(
            setter=self.__rz.setChecked,
            getter=self.__rz.isChecked,
        )
        settings.reverse_sx.bind(
            setter=self.__sx.setChecked,
            getter=self.__sx.isChecked,
        )
        settings.reverse_sy.bind(
            setter=self.__sy.setChecked,
            getter=self.__sy.isChecked,
        )
        settings.reverse_sz.bind(
            setter=self.__sz.setChecked,
            getter=self.__sz.isChecked,
        )

        method.currentIndexChanged.connect(
            lambda idx: main_layout.set_row_enabled(search_idx, idx == 2)
        )
        method.currentIndexChanged.connect(
            lambda idx: main_layout.set_row_enabled(replace_idx, idx == 2)
        )
        preset_mirror.currentIndexChanged.connect(self._apply_mirror_preset)

        initial_method: int = method.currentIndex()
        main_layout.set_row_enabled(search_idx, initial_method == 2)
        main_layout.set_row_enabled(replace_idx, initial_method == 2)
        preset_mirror.setCurrentIndex(6)

    def _apply_mirror_preset(self, index: int) -> None:
        """Applies predefined checkbox states based on the preset index.

        Args:
            index (int): The index of the selected preset.
        """
        if index >= 6:  # Custom
            return

        presets: dict[int, list[bool]] = {
            0: [True, True, False, False, False, False],  # XY(Behavior)
            1: [True, True, True, False, False, False],  # YZ(Behavior)
            2: [True, False, True, False, False, False],  # XZ(Behavior)
            3: [False, False, False, True, True, False],  # XY(Orient)
            4: [True, False, False, False, True, True],  # YZ(Orient)
            5: [False, False, False, True, False, True],  # XZ(Orient)
        }
        self.__tx.setChecked(presets[index][0])
        self.__ty.setChecked(presets[index][1])
        self.__tz.setChecked(presets[index][2])
        self.__rx.setChecked(presets[index][3])
        self.__ry.setChecked(presets[index][4])
        self.__rz.setChecked(presets[index][5])
        self.__sx.setChecked(False)
        self.__sy.setChecked(False)
        self.__sz.setChecked(False)

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    src_nodes: list[str],
    dst_nodes: list[str],
    mirror: list[list[bool]] | None = None,
) -> None:
    """Copies animation curves between nodes and applies mirroring if set.

    Args:
        src_nodes (list[str]): A list of source Maya nodes.
        dst_nodes (list[str]): A list of destination Maya nodes.
        mirror (list[list[bool]] | None, optional): A 3x3 matrix representing
            mirror flags for translate, rotate, and scale. Defaults to None.
    """
    if mirror is None:
        mirror = [[False, False, False] * 3]

    selected_attr: list[str] = dcc.selection.get_selected_channel_box_plugs(
        is_attribute_only=True
    )
    for src, dst in zip(src_nodes, dst_nodes):
        connected_curves: list[str] = []
        for curve_type in dcc.animation.ANIM_CURVES_TYPE:
            connected_curves.extend(
                cmds.listConnections(
                    src, plugs=True, connections=True, type=curve_type
                )
                or []
            )

        if not connected_curves:
            continue

        for i in range(0, len(connected_curves), 2):
            src_plug: str = connected_curves[i + 1]
            dst_plug: str = connected_curves[i]
            src_attr_name: str = ".".join(src_plug.split(".")[1:])
            dst_attr_name: str = ".".join(dst_plug.split(".")[1:])
            if selected_attr and dst_attr_name not in selected_attr:
                continue

            new_src_node: str = cmds.duplicate(src_plug.split(".")[0])[0]
            src_plug = f"{new_src_node}.{src_attr_name}"
            dst_plug = f"{dst}.{dst_attr_name}"
            cmds.connectAttr(src_plug, dst_plug, force=True)

            # Mirror
            for i, channel in enumerate(MIRROR_CHANNELS):
                for j, axis in enumerate(MIRROR_AXES):
                    if not mirror[i][j]:
                        continue

                    if channel + axis != dst_attr_name:
                        continue

                    cmds.scaleKey(
                        new_src_node,
                        includeUpperBound=False,
                        timeScale=1.0,
                        timePivot=1,
                        floatScale=1.0,
                        floatPivot=1.0,
                        valueScale=-1.0,
                        valuePivot=0.0,
                    )


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the copy animation process based on tool settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to
            use. If None, it initializes settings from the module.
            Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select node(s) to copy animation.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    src_nodes: list[str] = []
    dst_nodes: list[str] = []

    # Method = X:X
    if settings.method.value() == 0:
        if len(selection) < 2:
            _logger.error("Select more than two nodes to copy animation.")
            return

        if len(selection) % 2 != 0:
            _logger.error(
                "The number of source and destination nodes does not match."
            )
            return

        half_num: int = int(len(selection) / 2)
        src_nodes = selection[0:half_num]
        dst_nodes = selection[half_num:]

    # Method = 1:X
    elif settings.method.value() == 1:
        if len(selection) < 2:
            _logger.error("Select more than two nodes to copy animation.")
            return

        src_nodes = [selection[0]] * len(selection[1:])
        dst_nodes = selection[1:]

    # Method = Search % Replace
    else:
        for src_node in selection:
            dst_node: str = src_node.replace(
                settings.search.value(), settings.replace.value()
            )
            if not cmds.objExists(dst_node):
                _logger.warning("Target node does not exist: %s", dst_node)
                continue

            src_nodes.append(src_node)
            dst_nodes.append(dst_node)

    if settings.hierarchy.value() == 1:
        src_children_nodes: list[str] = []
        dst_children_nodes: list[str] = []
        for src, dst in zip(src_nodes, dst_nodes):
            src_children_nodes.extend(dcc.node.get_children([src]))
            dst_children_nodes.extend(dcc.node.get_children([dst]))

        src_nodes = src_children_nodes
        dst_nodes = dst_children_nodes

    mirror: list[list[bool]] = [
        [
            settings.reverse_tx.value(),
            settings.reverse_ty.value(),
            settings.reverse_tz.value(),
        ],
        [
            settings.reverse_rx.value(),
            settings.reverse_ry.value(),
            settings.reverse_rz.value(),
        ],
        [
            settings.reverse_sx.value(),
            settings.reverse_sy.value(),
            settings.reverse_sz.value(),
        ],
    ]

    apply(src_nodes, dst_nodes, mirror)
    _logger.info("Done.")
