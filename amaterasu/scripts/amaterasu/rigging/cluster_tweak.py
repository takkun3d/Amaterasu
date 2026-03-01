# ==============================================================================
#
# Cluster Tweak
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QLineEdit,
        QCheckBox,
        QPushButton,
        QVBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QLineEdit,
            QCheckBox,
            QPushButton,
            QVBoxLayout,
        )
from maya import cmds
from ..lib import parser, widgets
from . import create_controller
from ..modify import history_visibility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Cluster Tweak'
__version__: str = '1.10'
__doc__ = 'Creates a matrix-driven tweak rig for a Cluster deformer based on a guide locator.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

WORLD_DAG_PATH: str = '|'
SYSTEM_GROUP: str = 'clusterTweakSetup_grp'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    system_group: parser.Variant[str] = parser.Variant(SYSTEM_GROUP)
    is_delete_guide: parser.Variant[bool] = parser.Variant(True)


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

        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        form_layout: widgets.FormLayout = widgets.FormLayout(self)
        main_layout.addLayout(form_layout)

        self.__guide: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Guide'), self.__guide)

        self.__cluster: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Cluster Handle'), self.__cluster)

        self.__system_group: QLineEdit = QLineEdit(self)
        form_layout.addRow(
            widgets.FormLabel('System Group'), self.__system_group
        )

        self.__is_delete_guide: QCheckBox = QCheckBox('Delete Guide', self)
        form_layout.addRow('', self.__is_delete_guide)

        button: QPushButton = QPushButton('Build', self)
        button.clicked.connect(self.apply)
        main_layout.addStretch(True)
        main_layout.addWidget(button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__system_group.setText(settings.system_group.value())
        self.__is_delete_guide.setChecked(settings.is_delete_guide.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.system_group.set_value(self.__system_group.text())
        settings.is_delete_guide.set_value(self.__is_delete_guide.isChecked())
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

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        settings: Settings = Settings.instance(__name__, True)
        guide: str = self.__guide.text()
        if not guide:
            _logger.error('Guide node is required to create cluster tweak rig.')
            return

        cluster: str = self.__cluster.text()
        if not cluster:
            _logger.error(
                'Cluster Handle is required to create cluster tweak rig.'
            )
            return

        apply(
            guide,
            cluster,
            settings.system_group.value(),
            settings.is_delete_guide.value(),
        )
        _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    guide: str,
    cluster_handle: str,
    parent: str = SYSTEM_GROUP,
    is_delete_guide: bool = True,
) -> None:
    '''Do it'''
    if not cmds.objExists(parent):
        parent = cmds.createNode('transform', name=parent)

    base_name: str = guide.split('|')[-1].split(':')[-1]
    base_name = base_name.split('_')[0]

    guide_parent_temp: list[str] = (
        cmds.listRelatives(guide, parent=True, path=True) or []
    )
    guide_parent: str = WORLD_DAG_PATH
    if guide_parent_temp:
        guide_parent = guide_parent_temp[0]

    # Controller Space
    controller_space: str = cmds.createNode(
        'transform', name=f'{base_name}Space_null', parent=guide_parent
    )
    cmds.matchTransform(controller_space, guide)

    # Controller
    cluster_ctrl: str = create_controller.Sphere().create(
        '', base_name, 'ctrl', 1.0, None, None, 0, controller_space
    )

    # Cluster Space
    cluster_space: str = cmds.createNode(
        'transform', name=f'{base_name}ClusterSpace_null', parent=parent
    )
    cmds.matchTransform(cluster_space, guide)

    # Cluster Handle
    cluster_handle = cmds.parent(cluster_handle, cluster_space)[0]
    cmds.setAttr(f'{cluster_handle}.translate', 0, 0, 0, type='double3')
    cmds.setAttr(f'{cluster_handle}.rotate', 0, 0, 0, type='double3')
    cmds.setAttr(f'{cluster_handle}.scale', 1, 1, 1, type='double3')
    cmds.setAttr(f'{cluster_handle}.visibility', False)
    cmds.makeIdentity(
        cluster_handle, apply=True, translate=True, rotate=True, scale=True
    )
    cmds.xform(
        cluster_handle,
        rotatePivot=(0, 0, 0),
        scalePivot=(0, 0, 0),
        worldSpace=False,
    )
    cmds.connectAttr(f'{cluster_ctrl}.translate', f'{cluster_handle}.translate')
    cmds.connectAttr(f'{cluster_ctrl}.rotate', f'{cluster_handle}.rotate')
    cmds.connectAttr(f'{cluster_ctrl}.scale', f'{cluster_handle}.scale')
    cmds.connectAttr(f'{cluster_ctrl}.shear', f'{cluster_handle}.shear')

    # Cluster Handle Shape
    cluster_handle_shapes: list[str] = (
        cmds.listRelatives(cluster_handle, shapes=True, path=True) or []
    )
    cmds.setAttr(f'{cluster_handle_shapes[0]}.origin', 0, 0, 0, type='double3')

    # Calc Matrix
    cluster_matrix: str = cmds.createNode(
        'multMatrix', name=f'{base_name}_multMtx'
    )
    cmds.connectAttr(
        f'{cluster_handle}.matrix', f'{cluster_matrix}.matrixIn[0]'
    )
    cmds.connectAttr(f'{cluster_space}.matrix', f'{cluster_matrix}.matrixIn[1]')

    # Cluster
    cluster: str = cmds.listConnections(
        f'{cluster_handle}.worldMatrix[0]', source=False, destination=True
    )[0]
    cmds.connectAttr(
        f'{cluster_matrix}.matrixSum', f'{cluster}.matrix', force=True
    )
    cmds.connectAttr(
        f'{controller_space}.inverseMatrix', f'{cluster}.bindPreMatrix'
    )
    cmds.disconnectAttr(
        f'{controller_space}.inverseMatrix', f'{cluster}.bindPreMatrix'
    )

    # Clean up
    history_visibility.main(
        [
            controller_space,
            cluster_ctrl,
            cluster_handle,
            cluster,
        ],
        0,
    )
    if is_delete_guide:
        cmds.delete(guide)


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
