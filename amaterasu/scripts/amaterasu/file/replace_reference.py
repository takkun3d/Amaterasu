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
"""Replaces the reference file for selected nodes with a specified file.

This tool provides a UI to select a new Maya scene file and replace the
currently selected references with it. It also offers options to
automatically update the namespace and reference node name to match
the new file.
"""

from __future__ import annotations
import os
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Replace Reference"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Replace Reference tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
        file_path (framework.Variant[str]): The path of the replacement file.
        update_namespace (framework.Variant[bool]): Whether to update the namespace.
        update_node_name (framework.Variant[bool]): Whether to update the reference node name.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    file_path: framework.Variant[str] = framework.Variant("")
    update_namespace: framework.Variant[bool] = framework.Variant(True)
    update_node_name: framework.Variant[bool] = framework.Variant(True)


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Replace Reference tool.

    Provides a user interface for selecting a replacement file and configuring
    the replacement options before applying them to the selected references.
    """

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
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the widget.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)
        self.__file_path: widgets.BrowseWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
                custom UI elements should be added.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        self.__file_path = widgets.BrowseWidget(parent)
        self.__file_path.set_icon("a_folder.png")
        self.__file_path.clicked.connect(self.__open_file_dialog)
        main_layout.addRow(widgets.FormLabel("File"), self.__file_path)

        update_namespace: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Update Namespace", parent
        )
        main_layout.addRow("", update_namespace)

        update_reference_name: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Update Reference Name", parent
        )
        main_layout.addRow("", update_reference_name)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.file_path.bind(
            setter=self.__file_path.set_text,
            getter=self.__file_path.text,
        )
        settings.update_namespace.bind(
            setter=update_namespace.setChecked,
            getter=update_namespace.isChecked,
        )
        settings.update_node_name.bind(
            setter=update_reference_name.setChecked,
            getter=update_reference_name.isChecked,
        )

    def __open_file_dialog(self) -> None:
        """Opens a file dialog to select a Maya scene file."""
        current_dir: str = os.path.dirname(self.__file_path.text())
        result: tuple[str, str] = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Specific Maya Scene File",
            current_dir,
            "Maya Files (*.ma *.mb)",
        )
        if result[0]:
            self.__file_path.set_text(result[0])

    @dcc.undo
    def apply(self) -> None:
        """Executes the tool's main logic by applying the configured settings."""
        self.save_settings()
        settings: Settings = self.tool_settings()
        result: utils.Result = apply(
            settings.file_path.value(),
            settings.update_namespace.value(),
            settings.update_node_name.value(),
        )
        result.log(_logger)


def apply(
    file_path: str,
    update_namespace: bool = True,
    update_node_name: bool = True,
) -> utils.Result:
    """Replaces the reference for selected nodes safely.

    Args:
        file_path (str): The path to the new Maya scene file.
        update_namespace (bool, optional): If True, updates the namespace
            to match the new filename. Defaults to True.
        update_node_name (bool, optional): If True, updates the reference
            node name to match the new filename. Defaults to True.

    Returns:
        utils.Result: An object containing the merged results of the
            replacement operations.
    """
    result: utils.Result = utils.Result()

    if not os.path.exists(file_path):
        result.set_error(f"Does not exist file : {file_path}")
        return result

    references: list[str] = dcc.reference.get_selected_reference_nodes()

    if not references:
        result.set_error(
            "Select node or Reference Editor item to replace reference file."
        )
        return result

    for reference in references:
        rep_res: utils.Result = dcc.reference.replace(reference, file_path)
        if rep_res.status() != utils.ResultStatus.SUCCESS:
            result.merge(rep_res)
            continue

        if update_namespace:
            ns_res: utils.Result = dcc.reference.update_namespace(reference)
            result.merge(ns_res)

        if update_node_name:
            name_res: utils.Result = dcc.reference.update_name(reference)
            result.merge(name_res)

    return result


def main(unique_id: str = "") -> None:
    """Shows the tool window.

    Args:
        unique_id (str, optional): Unique ID for the tool window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
