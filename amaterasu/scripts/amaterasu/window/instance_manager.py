# ==============================================================================
#
# Instance Manager
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt, QItemSelectionModel, QModelIndex
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import QWidget, QGridLayout, QTreeView, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QItemSelectionModel, QModelIndex
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QTreeView,
            QPushButton,
        )
from maya import cmds
from maya.api.OpenMaya import MItDag, MFn, MFnDagNode, MDagPathArray, MDagPath
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Instance Manager'
__version__: str = '1.10'
__doc__ = 'Find instance nodes in the scene.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


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

        option_widget: QWidget = self.option_widget()
        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__model: QStandardItemModel = QStandardItemModel(0, 1, self)
        self.__model.setHeaderData(0, Qt.Horizontal, 'Node')

        self.__selection_model: QItemSelectionModel = QItemSelectionModel(
            self.__model
        )
        self.__selection_model.selectionChanged.connect(self.select_callback)

        self.__view: QTreeView = QTreeView(self)
        self.__view.setSelectionMode(QTreeView.ExtendedSelection)
        self.__view.setAlternatingRowColors(True)
        self.__view.setRootIsDecorated(False)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__selection_model)
        main_layout.addWidget(self.__view, 0, 0, 1, 3)

        button: QPushButton = QPushButton('Instance to Object', self)
        button.clicked.connect(self.release_callback)
        main_layout.addWidget(button, 1, 0)

        button = QPushButton('Delete', self)
        button.clicked.connect(self.delete_callback)
        main_layout.addWidget(button, 1, 1)

        button = QPushButton('Update', self)
        button.clicked.connect(self.initialize)
        main_layout.addWidget(button, 1, 2)
        self.initialize()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
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

    def initialize(self) -> None:
        '''Initialize view.'''
        self.__model.removeRows(0, self.__model.rowCount())
        instance_list: list[str] = instances()
        for instance in instance_list:
            item: QStandardItem = QStandardItem()
            item.setText(instance)
            item.setData(instance)
            self.__model.appendRow(item)

    @widgets.undo
    def select_callback(self, *args: Any, **kwargs: Any) -> None:
        '''select callback'''
        nodes: list[str] = self.__node_list()
        if not nodes:
            cmds.select(clear=True)
        else:
            cmds.select(*nodes)

    @widgets.undo
    def release_callback(self) -> None:
        '''release callback'''
        nodes: list[str] = self.__node_list()
        for node in nodes:
            instance_to_object(node)
        self.initialize()
        _logger.info('Done')

    @widgets.undo
    def delete_callback(self) -> None:
        '''delete callback'''
        nodes: list[str] = self.__node_list()
        for node in nodes:
            delete_instance(node)
        self.initialize()
        _logger.info('Done')

    def __node_list(self) -> list[str]:
        '''Return node list from selected item in view.'''
        indexes: list[QModelIndex] = self.__selection_model.selectedIndexes()
        if not indexes:
            return []
        nodes: list[str] = []
        for index in indexes:
            nodes.append(self.__model.item(index.row(), 0).text())
        return nodes


# ==============================================================================
#
# Functions
#
# ==============================================================================
def instance_to_object(node: str) -> None:
    '''Instance to object.'''
    if cmds.objectType(node, isAType='shape'):
        parent: list[str] = (
            cmds.listRelatives(node, parent=True, path=True) or []
        )
        if not parent:
            _logger.error('Does not exists parent : %s', node)
            return
        node = parent[0]

    new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
    delete_instance(node)
    cmds.rename(new_node, node.split('|')[-1])


def delete_instance(node: str) -> None:
    '''Delete instance'''
    if cmds.objectType(node, isAType='shape'):
        cmds.parent(node, removeObject=True, shape=True)
    else:
        cmds.parent(node, removeObject=True)


def instances() -> list[str]:
    '''Return instance node in the scene.'''
    result: list[str] = []
    dag_iiter: MItDag = MItDag(MItDag.kDepthFirst, MFn.kBase)
    dag_fn: MFnDagNode = MFnDagNode()
    while not dag_iiter.isDone():
        dag_fn.setObject(dag_iiter.currentItem())
        paths: MDagPathArray = dag_fn.getAllPaths()
        path: MDagPath = dag_fn.getPath()
        for i in range(len(paths)):
            if path.partialPathName() == paths[i].partialPathName():
                continue

            if paths[i].partialPathName() in result:
                continue

            dag_fn.setObject(paths[i])
            dag_fn.setObject(dag_fn.parent(0))
            if dag_fn.isInstanced():
                continue

            result.append(paths[i].partialPathName())
        dag_iiter.next()
    return result


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
