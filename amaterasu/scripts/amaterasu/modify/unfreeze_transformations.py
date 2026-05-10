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
"""Restores transformations of a frozen model using a reference object."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Unfreeze transformations"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Unfreeze Transformations tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry data.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class SolidOptionWidget(QtWidgets.QWidget):
    """Tab widget for applying solid (affine) unfreeze transformations."""

    applied = QtCore.Signal(str, list)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the SolidOptionWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        layout: widgets.FormLayout = widgets.FormLayout(self)
        layout.setFieldGrowthPolicy(
            widgets.FormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.__src: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=False
        )
        layout.addRow(widgets.FormLabel("Source"), self.__src)

        self.__dsts: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=True
        )
        layout.addRow(widgets.FormLabel("Destinations"), self.__dsts)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply Solid Unfreeze", self
        )
        button.clicked.connect(self._emit_apply)
        layout.addRow(button)

        layout.addRow(
            QtWidgets.QLabel(
                "<div align='right'><strong>*Requires non-planar polygon geometry.</strong></div>"
            ),
        )

    def _emit_apply(self) -> None:
        """Emits the applied signal with the current input data."""
        self.applied.emit(
            self.__src.text(),
            self.__dsts.text_as_list(),
        )


class PlanarOptionWidget(QtWidgets.QWidget):
    """Tab widget for applying planar (triangle) unfreeze transformations."""

    applied = QtCore.Signal(str, list)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the PlanarOptionWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        layout: widgets.FormLayout = widgets.FormLayout(self)
        layout.setFieldGrowthPolicy(
            widgets.FormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.__src: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=False
        )
        layout.addRow(widgets.FormLabel("Source"), self.__src)

        self.__dsts: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=True
        )
        layout.addRow(widgets.FormLabel("Destinations"), self.__dsts)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply Planar Unfreeze", self
        )
        button.clicked.connect(self._emit_apply)
        layout.addRow(button)

        layout.addRow(
            QtWidgets.QLabel(
                "<div align='right'><strong>*Requires polygon geometry.</strong></div>"
            )
        )

    def _emit_apply(self) -> None:
        """Emits the applied signal with the current input data."""
        self.applied.emit(
            self.__src.text(),
            self.__dsts.text_as_list(),
        )


class ManualOptionWidget(QtWidgets.QWidget):
    """Tab widget for applying manual component-aligned unfreeze transformations."""

    applied = QtCore.Signal(str, str, str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the ManualOptionWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
        """
        super().__init__(parent, flag)

        layout: widgets.FormLayout = widgets.FormLayout(self)
        layout.setFieldGrowthPolicy(
            widgets.FormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.__pivot: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=False
        )
        layout.addRow(widgets.FormLabel("Pivot"), self.__pivot)

        self.__aim: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=False
        )
        layout.addRow(widgets.FormLabel("Aim (X+)"), self.__aim)

        self.__up: widgets.NodePicker = widgets.NodePicker(
            self, multi_select=False
        )
        layout.addRow(widgets.FormLabel("Up (Y+)"), self.__up)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Apply Manual Unfreeze", self
        )
        button.clicked.connect(self._emit_apply)
        layout.addRow(button)

        layout.addRow(
            QtWidgets.QLabel(
                "<div align='right'><strong>*Affects Translate & Rotate only.</strong></div>"
            ),
        )

    def _emit_apply(self) -> None:
        """Emits the applied signal with the current input data."""
        self.applied.emit(
            self.__pivot.text(),
            self.__aim.text(),
            self.__up.text(),
        )


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for Unfreeze Transformations."""

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
        self.resize(450, 250)

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The parent widget to attach the UI elements to.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        tabs: QtWidgets.QTabWidget = QtWidgets.QTabWidget(self)
        main_layout.addWidget(tabs)

        tab_solid: SolidOptionWidget = SolidOptionWidget(self)
        tab_solid.applied.connect(self.apply_solid)
        tabs.addTab(tab_solid, "Solid")

        tab_planar: PlanarOptionWidget = PlanarOptionWidget(self)
        tab_planar.applied.connect(self.apply_planar)
        tabs.addTab(tab_planar, "Planar")

        tab_manual: ManualOptionWidget = ManualOptionWidget(self)
        tab_manual.applied.connect(self.apply_manual)
        tabs.addTab(tab_manual, "Manual")

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    @dcc.undo
    def apply_solid(self, src: str, dsts: list[str]) -> None:
        """Executes the solid unfreeze transformation triggered by the tab's signal.

        Args:
            src (str): The name of the source reference node.
            dsts (list[str]): A list of destination node names to unfreeze.
        """
        self.save_settings()

        if not src or not dsts:
            _logger.warning("Source and Destination nodes are required.")
            return

        result: utils.Result = dcc.space.apply_affine_transformation(src, dsts)
        result.log(_logger)

    @dcc.undo
    def apply_planar(self, src: str, dsts: list[str]) -> None:
        """Executes the planar unfreeze transformation triggered by the tab's signal.

        Args:
            src (str): The name of the source reference node.
            dsts (list[str]): A list of destination node names to unfreeze.
        """
        self.save_settings()

        if not src or not dsts:
            _logger.warning("Source and Destination nodes are required.")
            return

        result: utils.Result = dcc.space.apply_triangle_transformation(
            src, dsts
        )
        result.log(_logger)

    @dcc.undo
    def apply_manual(self, pivot: str, aim: str, up: str) -> None:
        """Executes the manual unfreeze transformation triggered by the tab's signal.

        Args:
            pivot (str): The node or component representing the origin pivot.
            aim (str): The node or component representing the X+ aim target.
            up (str): The node or component representing the Y+ up target.
        """
        self.save_settings()

        if not pivot or not aim or not up:
            _logger.warning("Pivot, Aim, and Up fields are all required.")
            return

        targets: list[str] = cmds.ls(selection=True, type="transform")
        if not targets:
            _logger.warning("Select node(s) to apply manual unfreeze.")
            return

        result: utils.Result = dcc.space.apply_align_to_components(
            pivot, aim, up, targets
        )
        result.log(_logger)


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
