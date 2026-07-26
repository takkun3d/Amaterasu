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
"""Generates a flipped or mirrored mesh from a base mesh."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, widgets, utils

__product__: str = "Symmetry"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Symmetry tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        axis (framework.Variant[int]): The axis index (0: X, 1: Y, 2: Z).
        direction (framework.Variant[int]): The direction index (0: +, 1: -).
        threshold (framework.Variant[float]): The distance threshold.
        weight (framework.Variant[int]): The revert weight percentage.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    axis: framework.Variant[int] = framework.Variant(0)
    direction: framework.Variant[int] = framework.Variant(1)
    threshold: framework.Variant[float] = framework.Variant(0.001)
    weight: framework.Variant[int] = framework.Variant(100)


class MeshListWidget(QtWidgets.QWidget):
    """Widget for displaying and managing a list of geometries."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self.__tree = QtWidgets.QTreeWidget(self)
        self.__tree.setColumnCount(1)
        self.__tree.setHeaderLabel("")
        self.__tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.__tree.setAlternatingRowColors(True)
        self.__tree.setRootIsDecorated(False)
        self.__tree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        main_layout.addWidget(self.__tree)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(True)
        main_layout.addLayout(button_layout)

        button = widgets.IconButton(self)
        button.set_icon(dcc.get_icon_path("a_add.png"))
        button.setIconSize(QtCore.QSize(16, 16))
        button.clicked.connect(self.add_items)  # pylint: disable=no-member
        button_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(dcc.get_icon_path("a_remove.png"))
        button.setIconSize(QtCore.QSize(16, 16))
        button.clicked.connect(self.remove_items)  # pylint: disable=no-member
        button_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(dcc.get_icon_path("a_trash.png"))
        button.setIconSize(QtCore.QSize(16, 16))
        button.clicked.connect(self.clear_items)  # pylint: disable=no-member
        button_layout.addWidget(button)

    def set_header_text(self, text: str) -> None:
        """Sets the header text for the list view.

        Args:
            text (str): The header text to display.
        """
        self.__tree.setHeaderLabel(text)

    def get_meshes(self, root: str = "") -> list[str]:
        """Returns a list of meshes from the selected node.

        Args:
            root (str, optional): The root node to query. Defaults to "".

        Returns:
            list[str]: A list of mesh node names.
        """
        result: list[str] = []
        if not root:
            selection: list[str] = cmds.ls(selection=True, type="transform")
            if not selection:
                return result
        else:
            selection = cmds.listRelatives(root, children=True, path=True) or []
            if not selection:
                return result

        for node in selection:
            shapes: list[str] = (
                cmds.listRelatives(node, shapes=True, path=True) or []
            )
            if not shapes:
                result.extend(self.get_meshes(node))
            else:
                result.append(node)

        return result

    def add_items(self) -> None:
        """Adds items from the current selection to the list."""
        selection: list[str] = self.get_meshes()
        for node in selection:
            # Prevent duplicates
            if not self.__tree.findItems(
                node, QtCore.Qt.MatchFlag.MatchExactly, 0
            ):
                item = QtWidgets.QTreeWidgetItem([node])
                self.__tree.addTopLevelItem(item)

    def remove_items(self) -> None:
        """Removes the selected items from the view."""
        for item in self.__tree.selectedItems():
            index: int = self.__tree.indexOfTopLevelItem(item)
            self.__tree.takeTopLevelItem(index)

    def clear_items(self) -> None:
        """Clears all items from the list."""
        self.__tree.clear()

    def items(self) -> list[str]:
        """Returns the list of item text entries.

        Returns:
            list[str]: A list of item strings currently in the view.
        """
        return [
            self.__tree.topLevelItem(i).text(0)
            for i in range(self.__tree.topLevelItemCount())
        ]


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the Symmetry tool."""

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
        self.resize(400, 400)
        self.__src_view: MeshListWidget
        self.__dst_view: MeshListWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        option_layout = widgets.FormLayout(parent)
        main_layout.addLayout(option_layout)

        axis: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        axis.addItems(["X", "Y", "Z"])
        option_layout.addRow(widgets.FormLabel("Axis"), axis)

        direction: QtWidgets.QComboBox = QtWidgets.QComboBox(parent)
        direction.addItems(["+", "-"])
        option_layout.addRow(widgets.FormLabel("Direction"), direction)

        threshold = QtWidgets.QDoubleSpinBox(parent)
        threshold.setRange(0, 9999)
        threshold.setDecimals(4)
        threshold.setMinimumWidth(80)
        option_layout.addRow(widgets.FormLabel("Threshold"), threshold)

        weight = QtWidgets.QSpinBox(parent)
        weight.setRange(0, 100)
        weight.setMinimumWidth(80)
        option_layout.addRow(widgets.FormLabel("Revert Weight"), weight)

        main_layout.addWidget(widgets.HorizontalLine(parent))

        view_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(view_layout)

        self.__src_view = MeshListWidget(parent)
        self.__src_view.set_header_text("Source Geometries")
        view_layout.addWidget(self.__src_view)

        self.__dst_view = MeshListWidget(parent)
        self.__dst_view.set_header_text("Destination Geometries")
        view_layout.addWidget(self.__dst_view)

        main_layout.addWidget(widgets.HorizontalLine(parent))

        button_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout)

        mirror_btn = QtWidgets.QPushButton("Mirror", parent)
        mirror_btn.clicked.connect(self.mirror_action)
        button_layout.addWidget(mirror_btn)

        flip_btn = QtWidgets.QPushButton("Flip", parent)
        flip_btn.clicked.connect(self.flip_action)
        button_layout.addWidget(flip_btn)

        revert_btn = QtWidgets.QPushButton("Revert", parent)
        revert_btn.clicked.connect(self.revert_action)
        button_layout.addWidget(revert_btn)

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
        settings.threshold.bind(
            setter=threshold.setValue,
            getter=threshold.value,
        )
        settings.weight.bind(
            setter=weight.setValue,
            getter=weight.value,
        )

    def validate_geometries(self) -> bool:
        """Checks if the required items are set in the views.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        src: list[str] = self.__src_view.items()
        dst: list[str] = self.__dst_view.items()

        if not src:
            QtWidgets.QMessageBox.critical(
                self, "Error", "Set node(s) for the source geometry."
            )
            return False

        if not dst:
            QtWidgets.QMessageBox.critical(
                self, "Error", "Set node(s) for the destination geometry."
            )
            return False

        if len(src) != len(dst):
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "The number of source and destination geometries must match.",
            )
            return False

        return True

    @dcc.undo
    def mirror_action(self) -> None:
        """Executes the mirror operation."""
        self.save_settings()
        if self.validate_geometries():
            settings: Settings = self.tool_settings()
            mirror(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.axis.value(),
                settings.direction.value(),
                settings.threshold.value(),
            )

    @dcc.undo
    def flip_action(self) -> None:
        """Executes the flip operation."""
        self.save_settings()
        if self.validate_geometries():
            settings: Settings = self.tool_settings()
            flip(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.axis.value(),
                settings.direction.value(),
                settings.threshold.value(),
            )

    @dcc.undo
    def revert_action(self) -> None:
        """Executes the revert operation."""
        self.save_settings()
        if self.validate_geometries():
            settings: Settings = self.tool_settings()
            revert(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.weight.value(),
            )


def get_vertex_pairs(
    node: str, axis: int, direction: int, threshold: float
) -> list[tuple[int, int]]:
    """Finds matching vertex pairs across a specified axis.

    Args:
        node (str): The name of the polygon mesh node.
        axis (int): The axis to mirror across (0: X, 1: Y, 2: Z).
        direction (int): The search direction (0: positive, 1: negative).
        threshold (float): The distance threshold for matching vertices.

    Returns:
        list[tuple[str, str]]: A list of paired vertex string IDs.
    """
    pos_vertices: list[tuple[str, list[float]]] = []
    neg_vertices: list[tuple[str, list[float]]] = []
    result: list[tuple[int, int]] = []

    axis2: int = (axis + 1) % 3
    axis3: int = (axis + 2) % 3

    pivots: list[float] = cmds.xform(
        node, query=True, pivots=True, objectSpace=True
    )  # type: ignore
    center: float = pivots[axis]

    for i in range(cmds.polyEvaluate(node, vertex=True)):
        vertex: str = f"{node}.vtx[{i}]"
        vertex_position: list[float] = cmds.pointPosition(vertex, local=True)

        if vertex_position[axis] > center:
            pos_vertices.append((vertex, vertex_position))
        elif vertex_position[axis] < center:
            neg_vertices.append((vertex, vertex_position))

    for i, pos_vertex in enumerate(pos_vertices):
        for j, neg_vertex in enumerate(neg_vertices):
            diff1: float = abs(
                abs(center - pos_vertex[1][axis])
                - abs(center - neg_vertex[1][axis])
            )
            diff2: float = abs(pos_vertex[1][axis2] - neg_vertex[1][axis2])
            diff3: float = abs(pos_vertex[1][axis3] - neg_vertex[1][axis3])

            if diff1 <= threshold and diff2 <= threshold and diff3 <= threshold:
                id1: int = dcc.mesh.get_index(pos_vertex[0])
                id2: int = dcc.mesh.get_index(neg_vertex[0])
                result.append((id1, id2) if direction else (id2, id1))
                neg_vertices.pop(j)
                break

    return result


def mirror(
    src_nodes: list[str],
    dst_nodes: list[str],
    axis: int = 0,
    direction: int = 1,
    threshold: float = 0.001,
) -> None:
    """Mirrors vertices from a specific axis.

    Args:
        src_nodes (list[str]): The source polygon mesh nodes.
        dst_nodes (list[str]): The destination polygon mesh nodes.
        axis (int, optional): The axis index. Defaults to 0.
        direction (int, optional): The direction index. Defaults to 1.
        threshold (float, optional): The distance threshold. Defaults to 0.001.
    """
    for src_node, dst_node in zip(src_nodes, dst_nodes):
        pair_vertices: list[tuple[int, int]] = get_vertex_pairs(
            src_node, axis, direction, threshold
        )
        for pair_vertex in pair_vertices:
            vertex_a: str = f"{dst_node}.vtx[{pair_vertex[0]}]"
            vertex_b: str = f"{dst_node}.vtx[{pair_vertex[1]}]"
            position: list[float] = cmds.pointPosition(vertex_a, local=True)
            position[axis] *= -1.0
            cmds.xform(vertex_b, translation=position, objectSpace=True)  # type: ignore

    _logger.info("Done.")


def flip(
    src_nodes: list[str],
    dst_nodes: list[str],
    axis: int = 0,
    direction: int = 1,
    threshold: float = 0.001,
) -> None:
    """Flips vertices from a specific axis.

    Args:
        src_nodes (list[str]): The source polygon mesh nodes.
        dst_nodes (list[str]): The destination polygon mesh nodes.
        axis (int, optional): The axis index. Defaults to 0.
        direction (int, optional): The direction index. Defaults to 1.
        threshold (float, optional): The distance threshold. Defaults to 0.001.
    """
    for src_node, dst_node in zip(src_nodes, dst_nodes):
        pair_vertices: list[tuple[int, int]] = get_vertex_pairs(
            src_node, axis, direction, threshold
        )
        for pair_vertex in pair_vertices:
            vertex_a: str = f"{dst_node}.vtx[{pair_vertex[0]}]"
            vertex_b: str = f"{dst_node}.vtx[{pair_vertex[1]}]"
            position_a: list[float] = cmds.pointPosition(vertex_a, local=True)
            position_b: list[float] = cmds.pointPosition(vertex_b, local=True)
            position_a[axis] *= -1.0
            position_b[axis] *= -1.0
            cmds.xform(vertex_a, translation=position_b, objectSpace=True)  # type: ignore
            cmds.xform(vertex_b, translation=position_a, objectSpace=True)  # type: ignore

    _logger.info("Done.")


def revert(
    src_nodes: list[str],
    dst_nodes: list[str],
    weight: int = 100,
) -> None:
    """Reverts vertices from a specific axis based on the provided weight.

    Args:
        src_nodes (list[str]): The source polygon mesh nodes.
        dst_nodes (list[str]): The destination polygon mesh nodes.
        weight (int, optional): The weight percentage for reverting.
            Defaults to 100.
    """
    bias: float = 1.0 - (weight / 100.0)

    for src_node, dst_node in zip(src_nodes, dst_nodes):
        for i in range(cmds.polyEvaluate(src_node, vertex=True)):
            vertex_a: str = f"{src_node}.vtx[{i}]"
            vertex_b: str = f"{dst_node}.vtx[{i}]"
            position_a: list[float] = cmds.pointPosition(vertex_a, local=True)
            position_b: list[float] = cmds.pointPosition(vertex_b, local=True)
            new_position: list[float] = [
                position_a[0] + ((position_b[0] - position_a[0]) * bias),
                position_a[1] + ((position_b[1] - position_a[1]) * bias),
                position_a[2] + ((position_b[2] - position_a[2]) * bias),
            ]
            cmds.xform(vertex_b, t=new_position, objectSpace=True)  # type: ignore

    _logger.info("Done.")


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
