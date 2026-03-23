# ==============================================================================
#
# Bind Pose Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
        )
from maya import cmds
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Bind Pose Editor'
__version__: str = '1.00'
__doc__ = 'This tool manages bind poses by easily adding, removing, and merging members.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class NodeListWidget(QListWidget):
    '''Node List Widget'''

    node_renamed = Signal(str, str)  # (old_name, new_name)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.itemChanged.connect(self.on_item_changed)

    def add_node(self, node: str) -> QListWidgetItem:
        '''Add node'''
        item: QListWidgetItem = QListWidgetItem(node)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setData(Qt.UserRole, node)
        self.addItem(item)
        return item

    def add_nodes(self, nodes: list[str]) -> list[QListWidgetItem]:
        '''Add nodes'''
        result: list[QListWidgetItem] = []
        for node in nodes:
            result.append(self.add_node(node))

        return result

    def revert_text(self, item: QListWidgetItem, text: str) -> None:
        '''Revert text'''
        self.blockSignals(True)
        item.setText(text)
        self.blockSignals(False)

    @widgets.undo
    def on_item_changed(self, item: QListWidgetItem) -> None:
        '''Item changed'''
        old_name: str = item.data(Qt.UserRole)
        new_name: str = item.text()
        if old_name == new_name or not new_name.strip():
            self.revert_text(item, old_name)
            return

        if not cmds.objExists(old_name):
            self.revert_text(item, old_name)
            return

        try:
            new_name = cmds.rename(old_name, new_name)
            self.blockSignals(True)
            item.setText(new_name)
            item.setData(Qt.UserRole, new_name)
            self.blockSignals(False)
            self.node_renamed.emit(old_name, new_name)

        except RuntimeError as e:
            _logger.error('Failed to rename: %s', e)
            self.revert_text(item, old_name)


class DagPoseManager(QWidget):
    '''Dag Pose Manager'''

    item_changed: Signal = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        header_layout: QHBoxLayout = QHBoxLayout(self)
        header_layout.setSpacing(0)
        main_layout.addLayout(header_layout)

        label: QLabel = QLabel('Dag Pose', self)
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_add.png')
        button.setToolTip('Create new dag pose')
        button.clicked.connect(self.create_dag_pose)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_reset.png')
        button.setToolTip('Reset dag pose')
        button.clicked.connect(self.reset_dag_pose)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_human.png')
        button.setToolTip('Go to bind pose')
        button.clicked.connect(self.go_to_bind_pose)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_group_human.png')
        button.setToolTip('Combine dag pose')
        button.clicked.connect(self.combine_dag_pose)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_trash.png')
        button.setToolTip('Delete dag pose')
        button.clicked.connect(self.delete_pose)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_update.png')
        button.setToolTip('Update UI')
        button.clicked.connect(self.update_ui)
        header_layout.addWidget(button)

        self.__list: NodeListWidget = NodeListWidget(self)
        self.__list.setSelectionMode(QListWidget.ExtendedSelection)
        self.__list.setAlternatingRowColors(True)
        self.__list.itemSelectionChanged.connect(self.selection_changed)
        self.__list.node_renamed.connect(lambda *args: self.selection_changed())
        main_layout.addWidget(self.__list)
        self.update_ui()

    def update_ui(self) -> None:
        '''Update UI'''
        self.__list.clear()
        self.__list.add_nodes(cmds.ls(type='dagPose'))

    def texts(self) -> list[str]:
        '''Return texts from list'''
        return [self.__list.item(i).text() for i in range(self.__list.count())]

    def selected_texts(self) -> list[str]:
        '''Return selected items'''
        return [item.text() for item in self.__list.selectedItems()]

    @widgets.undo
    def selection_changed(self) -> None:
        '''Selection changed'''
        selection: list[str] = self.selected_texts()
        if selection:
            cmds.select(selection[0])
            self.item_changed.emit(selection[0])

        else:
            self.item_changed.emit('')

    @widgets.undo
    def create_dag_pose(self) -> None:
        '''Create New DagPose'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            _logger.error('Select transforms to create bind pose.')
            return

        dag_pose: str = cmds.dagPose(selection, save=True, selection=False)  # type: ignore

        self.__list.clearSelection()
        item: QListWidgetItem = self.__list.add_node(dag_pose)
        item.setSelected(True)
        self.__list.scrollToItem(item)

    @widgets.undo
    def reset_dag_pose(self) -> None:
        '''Reset DagPose'''
        dag_poses: list[str] = self.selected_texts()
        if not dag_poses:
            return

        for dag_pose in dag_poses:
            members: list[str] = get_members(dag_pose)
            if members:
                cmds.dagPose(*members, name=dag_pose, reset=True)

    @widgets.undo
    def go_to_bind_pose(self) -> None:
        '''Go to bind pose'''
        dag_poses: list[str] = self.selected_texts()
        if not dag_poses:
            return

        for dag_pose in dag_poses:
            cmds.dagPose(dag_pose, restore=True)

    @widgets.undo
    def combine_dag_pose(self) -> None:
        '''Combine DagPose'''
        dag_poses: list[str] = self.selected_texts()
        if not dag_poses or len(dag_poses) == 1:
            _logger.error('Select two more items to combine from list.')
            return

        dag_pose: str = combine_bind_pose(dag_poses[0], dag_poses[1:])

        items: list[QListWidgetItem] = self.__list.selectedItems()
        self.__list.clearSelection()
        for item in items:
            self.__list.takeItem(self.__list.row(item))

        item: QListWidgetItem = self.__list.add_node(dag_pose)
        item.setSelected(True)

    @widgets.undo
    def delete_pose(self) -> None:
        '''Delete DagPose'''
        dag_poses: list[str] = self.selected_texts()
        if not dag_poses:
            return

        cmds.delete(*dag_poses)

        items: list[QListWidgetItem] = self.__list.selectedItems()
        self.__list.clearSelection()
        for item in items:
            self.__list.takeItem(self.__list.row(item))


class DagPoseMemberManager(QWidget):
    '''Dag Pose Member Manager'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.__current_pose: str = ''

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        header_layout: QHBoxLayout = QHBoxLayout(self)
        header_layout.setSpacing(0)
        main_layout.addLayout(header_layout)

        label: QLabel = QLabel('Members', self)
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_add.png')
        button.setToolTip('Add members')
        button.clicked.connect(self.add_member)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_remove.png')
        button.setToolTip('Remove members')
        button.clicked.connect(self.remove_member)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_human.png')
        button.setToolTip('Go to bind pose')
        button.clicked.connect(self.go_to_bind_pose)
        header_layout.addWidget(button)

        self.__list: NodeListWidget = NodeListWidget(self)
        self.__list.setSelectionMode(QListWidget.ExtendedSelection)
        self.__list.setAlternatingRowColors(True)
        self.__list.itemSelectionChanged.connect(self.selection_changed)
        main_layout.addWidget(self.__list)

    def update_ui(self, bind_pose: str = '') -> None:
        '''Update UI'''
        self.__list.clear()
        self.__current_pose = bind_pose
        if not bind_pose:
            return

        self.__list.add_nodes(get_members(bind_pose))

    def texts(self) -> list[str]:
        '''Return texts from list'''
        return [self.__list.item(i).text() for i in range(self.__list.count())]

    def selected_texts(self) -> list[str]:
        '''Return selected items'''
        return [item.text() for item in self.__list.selectedItems()]

    @widgets.undo
    def selection_changed(self) -> None:
        '''Selection changed'''
        cmds.select(*self.selected_texts())

    @widgets.undo
    def add_member(self) -> None:
        '''Add member from selected nodes.'''
        if not self.__current_pose:
            return

        selects: list[str] = cmds.ls(selection=True, type='transform')
        if not selects:
            _logger.error('Please select to add member to bind pose.')
            return

        existing_members: list[str] = self.texts()
        selects = list(set(selects) - set(existing_members))
        if not selects:
            return

        cmds.dagPose(
            *selects, name=self.__current_pose, addToPose=True, selection=True
        )
        self.__list.add_nodes(selects)

    @widgets.undo
    def remove_member(self) -> None:
        '''Remove member from selected item in list.'''
        selected_items: list[QListWidgetItem] = self.__list.selectedItems()
        if not self.__current_pose or not selected_items:
            return

        members: list[str] = self.selected_texts()
        cmds.dagPose(
            *members, name=self.__current_pose, remove=True, selection=True
        )

        current_members: list[str] = get_members(self.__current_pose)
        self.__list.clearSelection()
        for item in selected_items:
            if item.text() in current_members:
                _logger.warning('Can not remove member: %s', item.text())
                continue

            self.__list.takeItem(self.__list.row(item))

    @widgets.undo
    def go_to_bind_pose(self) -> None:
        '''Go to bind pose'''
        if not self.__current_pose:
            return

        go_to_bind_pose(self.__current_pose, self.selected_texts())


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        unique_id: str = '',
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        main_layout: QHBoxLayout = QHBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__dag_pose_mgr: DagPoseManager = DagPoseManager(self)
        main_layout.addWidget(self.__dag_pose_mgr)

        self.__members_mgr: DagPoseMemberManager = DagPoseMemberManager(self)
        main_layout.addWidget(self.__members_mgr)

        self.__dag_pose_mgr.item_changed.connect(self.__members_mgr.update_ui)

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


# ==============================================================================
#
# Functions
#
# ==============================================================================
def get_members(bind_pose: str) -> list[str]:
    '''Returns members from dagPose.'''
    return cmds.dagPose(bind_pose, query=True, members=True) or []  # type: ignore


def go_to_bind_pose(bind_pose: str, targets: list[str] | None = None) -> None:
    '''Go to bind pose'''
    if targets is None:
        targets = []

    members: list[str] = get_members(bind_pose)
    matrix_dict: dict[str, list[float]] = {}
    for member in members:
        if member in targets:
            continue

        matrix_dict[member] = cmds.xform(
            member,
            query=True,
            matrix=True,
            objectSpace=True,
        )  # type: ignore

    cmds.dagPose(bind_pose, restore=True)

    # Restore old position
    for member, matrix in matrix_dict.items():
        cmds.xform(member, matrix=matrix, objectSpace=True)  # type: ignore


def combine_bind_pose(base_bind_pose: str, source_bind_poses: list[str]) -> str:
    '''Combine bind pose'''
    members: set[str] = set(get_members(base_bind_pose))
    cmds.dagPose(base_bind_pose, restore=True)
    cmds.delete(base_bind_pose)

    for source_bind_pose in source_bind_poses:
        members = members | set(get_members(source_bind_pose))
        cmds.dagPose(source_bind_pose, restore=True)
        cmds.delete(source_bind_pose)

    return cmds.dagPose(
        *list(members),
        name=base_bind_pose,
        save=True,
        selection=True,
        bindPose=True,
    )  # type:ignore


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
