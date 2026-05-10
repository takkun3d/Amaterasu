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
"""Adds custom attributes to selected nodes.

This module provides a tool to batch-add various types of attributes
(Vector, Integer, String, Float, Boolean, Enum, Color, Separator) to selected nodes.
It also supports Arnold (mtoa) constant attribute formatting.
"""

from __future__ import annotations
from typing import Any
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Add Attribute"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)

MTOA_SHAPE_LIST: tuple[str, str, str] = ("mesh", "nurbsSurface", "nurbsCurve")
MTOA_ATTR_TAG: str = "mtoa_constant_"


class Settings(framework.ToolSettings):
    """Settings for the Add Attribute tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        mtoa (framework.Variant[bool]): Whether to insert the Arnold mtoa_constant_ prefix.
        attr_name (framework.Variant[str]): The base name of the attribute.
        make_attr (framework.Variant[int]): The state of the attribute
            (0: Keyable, 1: Displayable, 2: Hidden).
        data_type (framework.Variant[int]): The data type index of the attribute.
        min_value (framework.Variant[str]): The minimum value limit.
        max_value (framework.Variant[str]): The maximum value limit.
        default_value (framework.Variant[str]): The default value.
        enum_value (framework.Variant[str]): The enum string definition.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    mtoa: framework.Variant[bool] = framework.Variant(True)
    attr_name: framework.Variant[str] = framework.Variant("")
    make_attr: framework.Variant[int] = framework.Variant(0)
    data_type: framework.Variant[int] = framework.Variant(0)
    min_value: framework.Variant[str] = framework.Variant("")
    max_value: framework.Variant[str] = framework.Variant("")
    default_value: framework.Variant[str] = framework.Variant("0")
    enum_value: framework.Variant[str] = framework.Variant("")


class BoolValidator(QtGui.QValidator):
    """Validator for boolean string inputs."""

    def fixup(self, input_str: str) -> str:
        """Attempts to fix an invalid input string.

        Args:
            input_str (str): The invalid string.

        Returns:
            str: The corrected string ("off" by default).
        """
        return "off"

    def validate(self, input_str: str, pos: int) -> QtGui.QValidator.State:
        """Validates the input string against boolean formats.

        Args:
            input_str (str): The string to validate.
            pos (int): The cursor position.

        Returns:
            QtGui.QValidator.State: Acceptable or Invalid.
        """
        if pos == 0:
            return QtGui.QValidator.State.Acceptable

        try:
            _str_to_bool(input_str)
            return QtGui.QValidator.State.Acceptable

        except ValueError:
            return QtGui.QValidator.State.Invalid


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Add Attribute tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the window instance.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(500, 300)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        mtoa: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Insert mtoa_constant_", self
        )
        main_layout.addRow("", mtoa)

        attr_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Attribute Name"), attr_name)

        main_layout.addRow(widgets.HorizontalLine(self))

        make_attr: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        make_attr.addItems(["Keyable", "Displayable", "Hidden"])
        main_layout.addRow(widgets.FormLabel("Make Attribute"), make_attr)

        data_type: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        data_type.addItems(
            [
                "Vector",
                "Integer",
                "String",
                "Float",
                "Boolean",
                "Enum",
                "Color",
                "Separator",
            ]
        )
        main_layout.addRow(widgets.FormLabel("Data Type"), data_type)

        main_layout.addRow(widgets.HorizontalLine(self))

        min_value: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Min Value"), min_value)
        min_idx: int = main_layout.row_id()

        max_value: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Max Value"), max_value)
        max_idx: int = main_layout.row_id()

        default_value: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Default Value"), default_value)
        def_idx: int = main_layout.row_id()

        enum_value: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        enum_value.setPlaceholderText("Red:Green:Blue:")
        main_layout.addRow(widgets.FormLabel("Enum Value"), enum_value)
        enum_idx: int = main_layout.row_id()

        def update_ui_states() -> None:
            """Updates the enabled states of value inputs based on the selected data type."""
            dt: int = data_type.currentIndex()

            # Reset all
            main_layout.set_row_enabled(min_idx, False)
            main_layout.set_row_enabled(max_idx, False)
            main_layout.set_row_enabled(def_idx, False)
            main_layout.set_row_enabled(enum_idx, False)
            default_value.setValidator(None)  # type: ignore

            if dt == 1:  # Integer
                main_layout.set_row_enabled(min_idx, True)
                main_layout.set_row_enabled(max_idx, True)
                main_layout.set_row_enabled(def_idx, True)
                min_value.setValidator(QtGui.QIntValidator())
                max_value.setValidator(QtGui.QIntValidator())
                default_value.setValidator(QtGui.QIntValidator())

            elif dt == 2:  # String
                main_layout.set_row_enabled(def_idx, True)

            elif dt == 3:  # Float
                main_layout.set_row_enabled(min_idx, True)
                main_layout.set_row_enabled(max_idx, True)
                main_layout.set_row_enabled(def_idx, True)
                min_value.setValidator(QtGui.QDoubleValidator())
                max_value.setValidator(QtGui.QDoubleValidator())
                default_value.setValidator(QtGui.QDoubleValidator())

            elif dt == 4:  # Boolean
                main_layout.set_row_enabled(def_idx, True)
                default_value.setValidator(BoolValidator(default_value))

            elif dt == 5:  # Enum
                main_layout.set_row_enabled(enum_idx, True)

        data_type.currentIndexChanged.connect(lambda _: update_ui_states())
        update_ui_states()

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.mtoa.bind(
            setter=mtoa.setChecked,
            getter=mtoa.isChecked,
        )
        settings.attr_name.bind(
            setter=attr_name.setText,
            getter=attr_name.text,
        )
        settings.make_attr.bind(
            setter=make_attr.setCurrentIndex,
            getter=make_attr.currentIndex,
        )
        settings.data_type.bind(
            setter=data_type.setCurrentIndex,
            getter=data_type.currentIndex,
        )
        settings.min_value.bind(
            setter=min_value.setText,
            getter=min_value.text,
        )
        settings.max_value.bind(
            setter=max_value.setText,
            getter=max_value.text,
        )
        settings.default_value.bind(
            setter=default_value.setText,
            getter=default_value.text,
        )
        settings.enum_value.bind(
            setter=enum_value.setText,
            getter=enum_value.text,
        )

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by applying the configured settings."""
        self.save_settings()
        main(self.tool_settings())


def _str_to_bool(val: str) -> bool:
    """Converts a string representation of truth to True or False.

    Args:
        val (str): The string to evaluate.

    Returns:
        bool: True if 'y', 'yes', 't', 'true', 'on', or '1'.
              False if 'n', 'no', 'f', 'false', 'off', or '0'.

    Raises:
        ValueError: If the input cannot be evaluated to a boolean.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True

    if val in ("n", "no", "f", "false", "off", "0"):
        return False

    raise ValueError(f"Invalid truth value {val}")


def _add_attributes(
    nodes: list[str],
    attr_name: str,
    data_type: int,
    make_attr: int = 0,
    mtoa: bool = True,
    min_value: str = "",
    max_value: str = "",
    default_value: str = "",
    enum_value: str = "",
) -> utils.Result:
    """Core logic to add attributes to the target nodes without UI dependencies.

    Args:
        nodes (list[str]): List of target node names.
        attr_name (str): The base name of the attribute.
        data_type (int): The type of attribute (0: Vector, 1: Int, etc.).
        make_attr (int, optional): 0 for Keyable, 1 for Displayable, 2 for Hidden.
            Defaults to 0.
        mtoa (bool, optional): Whether to insert the Arnold mtoa_constant_ prefix.
            Defaults to True.
        min_value (str, optional): Minimum value limit. Defaults to "".
        max_value (str, optional): Maximum value limit. Defaults to "".
        default_value (str, optional): Default value. Defaults to "".
        enum_value (str, optional): Enum string definition. Defaults to "".

    Returns:
        utils.Result: An object containing execution details and error logs.
    """
    result = utils.Result()

    if not attr_name:
        result.add_failure("Global", "Attribute name cannot be empty.")
        return result

    command_arg: dict[str, Any] = {}
    if make_attr == 0:
        command_arg["keyable"] = True

    elif make_attr == 1:
        command_arg["channelBox"] = True

    for node in nodes:
        current_attr_name: str = attr_name

        if mtoa:
            if cmds.objectType(node) == "transform":
                shapes: list[str] = (
                    cmds.listRelatives(node, shapes=True, path=True) or []
                )
                if not shapes:
                    result.add_failure(node, "Failed to get shape node.")
                    continue

                node = shapes[0]

            if cmds.objectType(node) in MTOA_SHAPE_LIST:
                current_attr_name = f"{MTOA_ATTR_TAG}{attr_name}"

        if cmds.attributeQuery(current_attr_name, node=node, exists=True):
            result.add_failure(
                node, f"Attribute '{current_attr_name}' already exists."
            )
            continue

        try:
            if data_type == 0:
                dcc.attribute.add_vector(node, current_attr_name, **command_arg)

            elif data_type == 1:
                min_int_val: int | None = int(min_value) if min_value else None
                max_int_val: int | None = int(max_value) if max_value else None
                def_int_val: int | None = (
                    int(default_value) if default_value else None
                )
                dcc.attribute.add_integer(
                    node,
                    current_attr_name,
                    min_int_val,
                    max_int_val,
                    def_int_val,
                    **command_arg,
                )

            elif data_type == 2:
                dcc.attribute.add_string(
                    node, current_attr_name, default_value, **command_arg
                )

            elif data_type == 3:
                min_float_val: float | None = (
                    float(min_value) if min_value else None
                )
                max_float_val: float | None = (
                    float(max_value) if max_value else None
                )
                def_float_val: float | None = (
                    float(default_value) if default_value else None
                )
                dcc.attribute.add_float(
                    node,
                    current_attr_name,
                    min_float_val,
                    max_float_val,
                    def_float_val,
                    **command_arg,
                )

            elif data_type == 4:
                def_bool_val: bool = (
                    _str_to_bool(default_value) if default_value else False
                )
                dcc.attribute.add_boolean(
                    node, current_attr_name, def_bool_val, **command_arg
                )

            elif data_type == 5:
                dcc.attribute.add_enum(
                    node, current_attr_name, enum_value, **command_arg
                )

            elif data_type == 6:
                dcc.attribute.add_color(node, current_attr_name, **command_arg)

            elif data_type == 7:
                dcc.attribute.add_separator(
                    node, current_attr_name, **command_arg
                )

        except RuntimeError as e:
            result.add_failure(node, f"Failed to add attribute: {e}")

    return result


def option(unique_id: str = "") -> None:
    """Shows the tool's option window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main(settings: Settings | None = None) -> None:
    """Executes the add attribute operation on the current selection.

    Args:
        settings (Settings | None, optional): The settings instance to use.
            If None, reads from disk. Defaults to None.
    """
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        _logger.warning("Select node to add attribute.")
        return

    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    result: utils.Result = _add_attributes(
        nodes=selection,
        attr_name=settings.attr_name.value(),
        data_type=settings.data_type.value(),
        make_attr=settings.make_attr.value(),
        mtoa=settings.mtoa.value(),
        min_value=settings.min_value.value(),
        max_value=settings.max_value.value(),
        default_value=settings.default_value.value(),
        enum_value=settings.enum_value.value(),
    )
    result.log(_logger)
