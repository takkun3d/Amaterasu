# ==============================================================================
#
# Pivot Shifter
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import itertools

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QCheckBox,
        QPushButton,
        QVBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QCheckBox,
            QPushButton,
            QVBoxLayout,
        )

from maya import cmds
from ..lib import logger, parser, widgets
from . import create_controller
from amaterasu.base import dcc

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Pivot Shifter'
__version__: str = '1.10'
__doc__ = 'Creates a controller based on a guide locator to drive the target object with an adjustable pivot.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

PLUGIN_NAME: str = 'quatNodes.mll'
WORLD_DAG_PATH: str = '|'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
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

        self.__targets: widgets.NodePicker = widgets.NodePicker(-1, self)
        form_layout.addRow(widgets.FormLabel('Targets'), self.__targets)

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
        self.__is_delete_guide.setChecked(settings.is_delete_guide.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
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
            _logger.error('Guide node is required to create Pivot Shifter rig.')
            return

        targets: list[str] = self.__targets.text_as_list()
        if not targets:
            _logger.error(
                'Target transform is required to create Pivot Shifter rig.'
            )
            return

        apply(
            guide,
            targets,
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
    targets: list[str],
    is_delete_guide: bool = True,
) -> None:
    '''Do it'''

    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)

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
    main_ctrl: str = create_controller.Cube().create(
        '', base_name, 'ctrl', 1.0, None, None, 0, controller_space
    )

    # Pivot
    pivot_ctrl: str = create_controller.Locator().create(
        '', f'{base_name}Pivot', 'ctrl', 1.5, None, None, 0, main_ctrl
    )
    cmds.connectAttr(f'{pivot_ctrl}.translate', f'{main_ctrl}.rotatePivot')
    cmds.connectAttr(f'{pivot_ctrl}.translate', f'{main_ctrl}.scalePivot')
    for attr, axis in itertools.product(['rotate', 'scale'], ['X', 'Y', 'Z']):
        cmds.setAttr(
            f'{pivot_ctrl}.{attr}{axis}',
            lock=True,
            keyable=False,
            channelBox=False,
        )
    cmds.setAttr(
        f'{pivot_ctrl}.visibility', lock=True, keyable=False, channelBox=False
    )

    # Setup per target
    target_spaces: list[str] = []
    for target in targets:
        target_base_name: str = target.split('|')[-1].split(':')[-1]
        target_base_name = target_base_name.split('_')[0]

        # Target Space
        target_space: str = cmds.createNode(
            'transform',
            name=f'{base_name}{target_base_name}Space_null',
            parent=target,
        )
        cmds.setAttr(f'{target_space}.visibility', False)
        cmds.setAttr(f'{target_space}.hiddenInOutliner', True)
        target_space = cmds.parent(target_space, main_ctrl)[0]

        for attr in ['translate', 'rotate', 'scale', 'visibility']:
            cmds.setAttr(
                f'{target_space}.{attr}',
                lock=True,
                keyable=False,
                channelBox=False,
            )

        # Mult Matrix
        mult_matrix: str = cmds.createNode(
            'multMatrix', name=f'{base_name}{target_base_name}_multMtx'
        )
        cmds.connectAttr(f'{target_space}.matrix', f'{mult_matrix}.matrixIn[0]')
        cmds.connectAttr(f'{main_ctrl}.matrix', f'{mult_matrix}.matrixIn[1]')
        cmds.connectAttr(
            f'{controller_space}.matrix', f'{mult_matrix}.matrixIn[2]'
        )
        cmds.connectAttr(
            f'{controller_space}.parentMatrix[0]',
            f'{mult_matrix}.matrixIn[3]',
        )
        cmds.connectAttr(
            f'{target}.parentInverseMatrix[0]', f'{mult_matrix}.matrixIn[4]'
        )

        # Decompose Matrix
        decompose_mtx: str = cmds.createNode(
            'decomposeMatrix',
            name=f'{base_name}{target_base_name}_decomposeMtx',
        )
        cmds.connectAttr(
            f'{mult_matrix}.matrixSum', f'{decompose_mtx}.inputMatrix'
        )

        # Cancels out joint orient.
        if cmds.objectType(target) == 'joint':
            # Euler to Quat
            joint_orient_quat: str = cmds.createNode(
                'eulerToQuat', name=f'{base_name}{target_base_name}_etq'
            )
            cmds.connectAttr(
                f'{target}.jointOrient', f'{joint_orient_quat}.inputRotate'
            )

            # Invert
            invert_joint_orient_quat: str = cmds.createNode(
                'quatInvert', name=f'{base_name}{target_base_name}_qi'
            )
            cmds.connectAttr(
                f'{joint_orient_quat}.outputQuat',
                f'{invert_joint_orient_quat}.inputQuat',
            )

            # Remove joint orient
            remove_orient_prod: str = cmds.createNode(
                'quatProd', name=f'{base_name}{target_base_name}_qp'
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputQuat',
                f'{remove_orient_prod}.input1Quat',
            )
            cmds.connectAttr(
                f'{invert_joint_orient_quat}.outputQuat',
                f'{remove_orient_prod}.input2Quat',
            )

            # Quat to Euler
            joint_orient_euler: str = cmds.createNode(
                'quatToEuler', name=f'{base_name}{target_base_name}_qte'
            )
            cmds.connectAttr(
                f'{remove_orient_prod}.outputQuat',
                f'{joint_orient_euler}.inputQuat',
            )
            cmds.connectAttr(
                f'{target}.rotateOrder',
                f'{joint_orient_euler}.inputRotateOrder',
            )

            # Target
            cmds.connectAttr(
                f'{decompose_mtx}.outputTranslate',
                f'{target}.translate',
                force=True,
            )
            cmds.connectAttr(
                f'{joint_orient_euler}.outputRotate',
                f'{target}.rotate',
                force=True,
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputScale',
                f'{target}.scale',
                force=True,
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputShear',
                f'{target}.shear',
                force=True,
            )

        # Transform
        else:
            # Target
            cmds.connectAttr(
                f'{decompose_mtx}.outputTranslate',
                f'{target}.translate',
                force=True,
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputRotate',
                f'{target}.rotate',
                force=True,
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputScale',
                f'{target}.scale',
                force=True,
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputShear',
                f'{target}.shear',
                force=True,
            )
        target_spaces.append(target_space)

    # Update Outliner
    for panel in cmds.getPanel(type='outlinerPanel'):
        cmds.outlinerEditor(panel, edit=True, refresh=True)

    # Clean up
    # history_visibility.main(
    #     [
    #         controller_space,
    #         main_ctrl,
    #         pivot_ctrl,
    #         *target_spaces,
    #         *targets,
    #     ],
    #     0,
    # )
    dcc.node.hide_history(
        [controller_space, main_ctrl, pivot_ctrl, *target_spaces, *targets]
    )
    if is_delete_guide:
        cmds.delete(guide)


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
