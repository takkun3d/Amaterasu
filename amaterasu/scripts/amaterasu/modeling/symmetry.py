# ==============================================================================
#
# Symmetry
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QComboBox,
        QDoubleSpinBox,
        QSpinBox,
        QTreeView,
        QPushButton,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QComboBox,
            QDoubleSpinBox,
            QSpinBox,
            QTreeView,
            QPushButton,
            QMessageBox,
        )
from maya import cmds
from ..lib import parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Symmetry'
__version__: str = '1.01'
__doc__ = 'Generate fliped mesh or mirrored mesh from base mesh.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    axis: parser.Variant[int] = parser.Variant(0)
    direction: parser.Variant[int] = parser.Variant(1)
    threshold: parser.Variant[float] = parser.Variant(0.001)
    weight: parser.Variant[int] = parser.Variant(100)


class GeometryList(QWidget):
    '''Geometry list widget.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self.__model = QStandardItemModel(0, 1, self)

        self.__view = QTreeView(self)
        self.__view.setModel(self.__model)
        self.__view.setSelectionMode(QTreeView.ExtendedSelection)
        self.__view.setAlternatingRowColors(True)
        self.__view.setRootIsDecorated(False)
        self.__view.setFocusPolicy(Qt.NoFocus)
        main_layout.addWidget(self.__view)

        button_layout = QHBoxLayout(self)
        button_layout.addStretch(True)
        main_layout.addLayout(button_layout)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_add.png'))
        button.setIconSize(QSize(16, 16))
        button.clicked.connect(self.add_item)
        button_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_remove.png'))
        button.setIconSize(QSize(16, 16))
        button.clicked.connect(self.remove_item)
        button_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_trash.png'))
        button.setIconSize(QSize(16, 16))
        button.clicked.connect(self.clear_item)
        button_layout.addWidget(button)

    def set_header_text(self, text: str) -> None:
        '''Set header text.'''
        self.__model.setHeaderData(0, Qt.Horizontal, text)

    def get_mesh(self, root: str = '') -> list[str]:
        '''Return mesh list from selected node.'''
        result: list[str] = []
        if not root:
            selection: list[str] = cmds.ls(selection=True, type='transform')
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
                result.extend(self.get_mesh(node))

            else:
                result.append(node)

        return result

    def add_item(self, root: str = '') -> None:
        '''Add item from selected nodes.'''
        selection: list[str] = self.get_mesh()
        for node in selection:
            item = QStandardItem(node)
            self.__model.appendRow(item)

    def remove_item(self) -> None:
        '''Remove selected item on view.'''
        selection_model = self.__view.selectionModel()
        while True:
            indexes = selection_model.selectedIndexes()
            if not indexes:
                break
            self.__model.removeRow(indexes[0].row())

    def clear_item(self) -> None:
        '''Clear item.'''
        self.__model.removeRows(0, self.__model.rowCount())

    def items(self) -> list[str]:
        '''Return item list.'''
        result: list[str] = []
        for i in range(self.__model.rowCount()):
            result.append(self.__model.item(i, 0).text())
        return result


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        main_layout = QVBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)

        option_layout = widgets.FormLayout(self)
        main_layout.addLayout(option_layout)

        self.__axis: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__axis.set_labels(('X', 'Y', 'Z'))
        option_layout.addRow(widgets.FormLabel('Axis'), self.__axis)

        self.__direction: QComboBox = QComboBox(self)
        self.__direction.addItem('+')
        self.__direction.addItem('-')
        option_layout.addRow(widgets.FormLabel('Direction'), self.__direction)

        self.__threshold = QDoubleSpinBox(self)
        self.__threshold.setRange(0, 9999)
        self.__threshold.setDecimals(4)
        self.__threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__threshold.setMinimumWidth(80)
        option_layout.addRow(widgets.FormLabel('Threthold'), self.__threshold)

        self.__weight = QSpinBox(self)
        self.__weight.setRange(0, 100)
        self.__weight.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__weight.setMinimumWidth(80)
        option_layout.addRow(widgets.FormLabel('Revert Weight'), self.__weight)

        view_layout = QHBoxLayout(self)
        main_layout.addLayout(view_layout)

        self.__src_view = GeometryList(self)
        self.__src_view.set_header_text('Source Geometrys')
        view_layout.addWidget(self.__src_view)

        self.__dst_view = GeometryList(self)
        self.__dst_view.set_header_text('Destination Geometrys')
        view_layout.addWidget(self.__dst_view)

        main_layout.addWidget(widgets.HorizontalLine(self))

        button_layout = QHBoxLayout(self)
        main_layout.addLayout(button_layout)

        button = QPushButton('Mirror', self)
        button.clicked.connect(self.mirror)
        button_layout.addWidget(button)

        button = QPushButton('Flip', self)
        button.clicked.connect(self.flip)
        button_layout.addWidget(button)

        button = QPushButton('Revert', self)
        button.clicked.connect(self.revert)
        button_layout.addWidget(button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__axis.set_check_id(settings.axis.value())
        self.__direction.setCurrentIndex(settings.direction.value())
        self.__threshold.setValue(settings.threshold.value())
        self.__weight.setValue(settings.weight.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.axis.set_value(self.__axis.check_id())
        settings.direction.set_value(self.__direction.currentIndex())
        settings.threshold.set_value(self.__threshold.value())
        settings.weight.set_value(self.__weight.value())
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )

    def check_item(self) -> bool:
        '''Check item on view'''
        src: list[str] = self.__src_view.items()
        dst: list[str] = self.__dst_view.items()
        if not src:
            QMessageBox.critical(
                self, 'Error', 'Set node(s) to Source Geometry.'
            )
            return False

        if not dst:
            QMessageBox.critical(
                self, 'Error', 'Set node(s) to Destination Geometry.'
            )
            return False

        if len(src) != len(dst):
            QMessageBox.critical(
                self,
                'Error',
                'Match the number of Source Geometry and Destination Geometry.',
            )
            return False

        return True

    @widgets.undo
    def mirror(self) -> None:
        '''Mirror'''
        self.save_settings()
        if self.check_item():
            settings: Settings = Settings.instance(__name__, True)
            mirror(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.axis.value(),
                settings.direction.value(),
                settings.threshold.value(),
            )

    @widgets.undo
    def flip(self) -> None:
        '''Flip'''
        self.save_settings()
        if self.check_item():
            settings: Settings = Settings.instance(__name__, True)
            flip(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.axis.value(),
                settings.direction.value(),
                settings.threshold.value(),
            )

    @widgets.undo
    def revert(self) -> None:
        '''Revert'''
        if self.check_item():
            settings: Settings = Settings.instance(__name__, True)
            revert(
                self.__src_view.items(),
                self.__dst_view.items(),
                settings.weight.value(),
            )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def pair_vertex_list(
    node: str, axis: int, direction: int, threshold: float
) -> list[tuple[str, str]]:
    pos_vertexes: list[tuple[str, list[float]]] = []
    neg_vertexes: list[tuple[str, list[float]]] = []
    result: list[tuple[str, str]] = []

    if axis == 0:
        axis2: int = 1
        axis3: int = 2

    elif axis == 1:
        axis2 = 2
        axis3 = 0

    else:
        axis2 = 0
        axis3 = 1

    pivots: list[float] = cmds.xform(
        node, query=True, pivots=True, objectSpace=True
    )
    center: float = pivots[axis]

    for i in range(cmds.polyEvaluate(node, vertex=True)):
        vertex = f'{node}.vtx[{i}]'
        vertex_position: list[float] = cmds.pointPosition(vertex, local=True)

        if vertex_position[axis] > center:
            pos_vertexes.append((vertex, vertex_position))

        elif vertex_position[axis] < center:
            neg_vertexes.append((vertex, vertex_position))

    for i, pos_vertex in enumerate(pos_vertexes):
        for j, neg_vertex in enumerate(neg_vertexes):
            diff1 = abs(
                abs(center - pos_vertex[1][axis])
                - abs(center - neg_vertex[1][axis])
            )
            diff2 = abs(pos_vertex[1][axis2] - neg_vertex[1][axis2])
            diff3 = abs(pos_vertex[1][axis3] - neg_vertex[1][axis3])

            if diff1 <= threshold and diff2 <= threshold and diff3 <= threshold:
                id1: str = utility.poly_component_id(pos_vertex[0])
                id2: str = utility.poly_component_id(neg_vertex[0])
                result.append((id1, id2) if direction else (id2, id1))
                neg_vertexes.pop(j)
                break

    return result


def mirror(
    src_nodes: list[str],
    dst_nodes: list[str],
    axis: int = 0,
    direction: int = 1,
    threshold: float = 0.001,
) -> None:
    '''Mirror vertexes from specific axis.'''
    for src_node, dst_node in zip(src_nodes, dst_nodes):
        pair_vertexes = pair_vertex_list(src_node, axis, direction, threshold)
        for pair_vertex in pair_vertexes:
            vertex_a: str = f'{dst_node}.vtx[{pair_vertex[0]}]'
            vertex_b: str = f'{dst_node}.vtx[{pair_vertex[1]}]'
            position: list[float] = cmds.pointPosition(vertex_a, local=True)
            position[axis] *= -1.0
            cmds.xform(vertex_b, translation=position, objectSpace=True)

    _logger.info('Done.')


def flip(
    src_nodes: list[str],
    dst_nodes: list[str],
    axis: int = 0,
    direction: int = 1,
    threshold: float = 0.001,
) -> None:
    '''Flip vertexes from specific axis.'''
    for src_node, dst_node in zip(src_nodes, dst_nodes):
        pair_vertexes = pair_vertex_list(src_node, axis, direction, threshold)
        for pair_vertex in pair_vertexes:
            vertex_a: str = f'{dst_node}.vtx[{pair_vertex[0]}]'
            vertex_b: str = f'{dst_node}.vtx[{pair_vertex[1]}]'
            position_a: list[float] = cmds.pointPosition(vertex_a, local=True)
            position_b: list[float] = cmds.pointPosition(vertex_b, local=True)
            position_a[axis] *= -1.0
            position_b[axis] *= -1.0
            cmds.xform(vertex_a, translation=position_b, objectSpace=True)
            cmds.xform(vertex_b, translation=position_a, objectSpace=True)

    _logger.info('Done.')


def revert(
    src_nodes: list[str],
    dst_nodes: list[str],
    weight: int = 100,
) -> None:
    '''Revert vertexes from specific axis.'''
    bias: float = 1 - (weight / 100.0)

    for src_node, dst_node in zip(src_nodes, dst_nodes):
        for i in range(cmds.polyEvaluate(src_node, vertex=True)):
            vertex_a: str = f'{src_node}.vtx[{i}]'
            vertex_b: str = f'{dst_node}.vtx[{i}]'
            position_a: list[float] = cmds.pointPosition(vertex_a, local=True)
            position_b: list[float] = cmds.pointPosition(vertex_b, local=True)
            new_position: list[float] = [
                position_a[0] + ((position_b[0] - position_a[0]) * bias),
                position_a[1] + ((position_b[1] - position_a[1]) * bias),
                position_a[2] + ((position_b[2] - position_a[2]) * bias),
            ]
            cmds.xform(vertex_b, t=new_position, objectSpace=True)

    _logger.info('Done.')


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
