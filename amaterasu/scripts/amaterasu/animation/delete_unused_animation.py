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
"""Deletes unused animation curves from the selected nodes.

This module provides functionality to find and delete animation curves
that have no value changes over time. It offers options to preserve
compound attributes and ignore translation, rotation, and scale attributes.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Delete Unused Animation"
__version__: str = "1.31"
_logger: utils.Logger = utils.get_logger(__product__)

TRANSFORM_ATTRIBUTES: list[str] = [
    "tx",
    "ty",
    "tz",
    "rx",
    "ry",
    "rz",
    "sx",
    "sy",
    "sz",
    "translateX",
    "translateY",
    "translateZ",
    "rotateX",
    "rotateY",
    "rotateZ",
    "scaleX",
    "scaleY",
    "scaleZ",
]


class Settings(framework.ToolSettings):
    """Settings for the Delete Unused Animation tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        keep_compound_attr (framework.Variant[bool]): Whether to preserve
            animations on compound attributes if any child is animated.
        ignore_transforms (framework.Variant[bool]): Whether to ignore
            translation, rotation, and scale attributes.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    keep_compound_attr: framework.Variant[bool] = framework.Variant(True)
    ignore_transforms: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Delete Unused Animation tool."""

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

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        keep_compound_cb = QtWidgets.QCheckBox(
            "Preserve compound attributes.", self
        )
        main_layout.addRow(widgets.FormLabel(""), keep_compound_cb)

        ignore_transforms_cb = QtWidgets.QCheckBox(
            "Ignore Translation, Rotation, and Scale.", self
        )
        main_layout.addRow(widgets.FormLabel(""), ignore_transforms_cb)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.keep_compound_attr.bind(
            setter=keep_compound_cb.setChecked,
            getter=keep_compound_cb.isChecked,
        )
        settings.ignore_transforms.bind(
            setter=ignore_transforms_cb.setChecked,
            getter=ignore_transforms_cb.isChecked,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool logic and saves current settings."""
        self.save_settings()
        main(self.tool_settings())


def apply(
    nodes: list[str],
    keep_compound_attr: bool = True,
    ignore_transforms: bool = True,
) -> bool:
    """Deletes unused animation curves from the specified nodes.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        keep_compound_attr (bool, optional): Preserves animations on compound
            attributes if any child is animated. Defaults to True.
        ignore_transforms (bool, optional): Ignores translation, rotation,
            and scale attributes. Defaults to True.

    Returns:
        bool: True if the operation was successful.
    """
    delete_nodes: list[str] = []
    for node in nodes:
        connections: list[str] = cmds.listConnections(
            node,
            type="animCurve",
            source=True,
            destination=False,
            plugs=True,
            connections=True,
        )
        if not connections:
            continue

        compound_attr: dict[str, dict[str, str]] = {}
        for i in range(0, len(connections), 2):
            src_plug: str = connections[i]
            dst_plug: str = connections[i + 1]
            src_node: str = src_plug.split(".")[0]
            src_attr: str = ".".join(src_plug.split(".")[1:])
            anim_curve: str = dst_plug.split(".")[0]

            # Ignore Transformation
            if ignore_transforms and src_attr in TRANSFORM_ATTRIBUTES:
                continue

            values: set[float] = set(
                cmds.keyframe(anim_curve, query=True, valueChange=True)  # type: ignore
            )
            is_default_static: bool = True
            for value in set(values):
                if not dcc.attribute.is_default_value(
                    src_node, src_attr, value
                ):
                    is_default_static = False
                    break

            # compound attribute
            parent_attr: list[str] = cmds.attributeQuery(
                src_attr, node=src_node, listParent=True
            )  # type: ignore
            if keep_compound_attr and parent_attr:
                children_attr: list[str] = cmds.attributeQuery(
                    parent_attr[0], node=src_node, listChildren=True
                )  # type: ignore

                # Initialize compound_attr
                if parent_attr[0] not in compound_attr:
                    compound_attr[parent_attr[0]] = {}
                    for child_attr in children_attr:
                        compound_attr[parent_attr[0]][child_attr] = ""

                if is_default_static:
                    compound_attr[parent_attr[0]][src_attr] = anim_curve

            else:
                if is_default_static:
                    delete_nodes.append(anim_curve)

        # Check unused animation from compound_attr.
        if keep_compound_attr:
            for _, data in compound_attr.items():
                if "" in data.values():
                    continue

                delete_nodes += data.values()

        if delete_nodes:
            cmds.delete(*delete_nodes)

    return True


def option(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the unused animation deletion based on UI settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to
            use. If None, it initializes settings from the module name and
            reads them from the file. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True, long=True) or []
    if not selection:
        _logger.error("Select node(s) to delete unused animation.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: bool = apply(
        selection,
        settings.keep_compound_attr.value(),
        settings.ignore_transforms.value(),
    )
    if result:
        _logger.info("Done.")
