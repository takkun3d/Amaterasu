# ==============================================================================
#
# Matrix Constraint
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import (
        QWidget,
        QComboBox,
        QCheckBox,
        QPushButton,
        QVBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import (
            QWidget,
            QComboBox,
            QCheckBox,
            QPushButton,
            QVBoxLayout,
        )

from maya import cmds
from ..lib import parser, widgets
from ..modify import history_visibility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Matrix Constraint'
__version__: str = '1.00'
__doc__ = 'Constrains the specified node using matrix calculations.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

PLUGIN_NAME: str = 'quatNodes.mll'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    space: parser.Variant[int] = parser.Variant(1)  # 0:World 1:Local
    follows_parent: parser.Variant[bool] = parser.Variant(True)


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
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_layout: widgets.FormLayout = widgets.FormLayout(self)
        main_layout.addLayout(self.__form_layout)

        self.__space: QComboBox = QComboBox(self)
        self.__space.addItem('World')
        self.__space.addItem('Local')
        self.__space.currentIndexChanged.connect(self.set_valid_options)
        self.__form_layout.addRow(widgets.FormLabel('Space'), self.__space)

        self.__form_layout.addRow(widgets.HorizontalLine(self))

        self.__sources: widgets.NodePicker = widgets.NodePicker(-1, self)
        self.__sources.set_placeholder_text(
            '*Select in order: Parent -> Child.'
        )
        self.__form_layout.addRow(widgets.FormLabel('Sources'), self.__sources)

        self.__target: widgets.NodePicker = widgets.NodePicker(1, self)
        self.__form_layout.addRow(widgets.FormLabel('Target'), self.__target)

        self.__form_layout.addRow(widgets.HorizontalLine(self))

        self.__follows_parent: QCheckBox = QCheckBox('Follows Parent', self)
        self.__form_layout.addRow('', self.__follows_parent)
        self.__follows_parent_idx: int = self.__form_layout.row_id()

        button: QPushButton = QPushButton('Build', self)
        button.clicked.connect(self.apply)
        main_layout.addStretch(True)
        main_layout.addWidget(button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__space.setCurrentIndex(settings.space.value())
        self.__follows_parent.setChecked(settings.follows_parent.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.space.set_value(self.__space.currentIndex())
        settings.follows_parent.set_value(self.__follows_parent.isChecked())
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

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        self.__form_layout.set_row_enabled(
            self.__follows_parent_idx, (self.__space.currentIndex() == 1)
        )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        settings: Settings = Settings.instance(__name__, True)
        sources: list[str] = self.__sources.text_as_list()
        if not sources:
            _logger.error('Source node is required to apply Matrix Constraint.')
            return

        target: str = self.__target.text()
        if not target:
            _logger.error('Target node is required to apply Matrix Constraint.')
            return

        apply(
            sources,
            target,
            settings.space.value(),
            settings.follows_parent.value(),
        )
        _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    sources: list[str],
    target: str,
    space: int = 1,
    follows_parent: bool = True,
) -> None:
    '''Do it'''

    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)

    base_name: str = sources[0].split('|')[-1].split(':')[-1]
    base_name = base_name.split('_')[0]

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
    target_space = cmds.parent(target_space, sources[0])[0]

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

    if space == 0:
        # Calc Matrix
        cmds.connectAttr(
            f'{target}.parentInverseMatrix[0]',
            f'{mult_matrix}.matrixIn[1]',
        )

    else:
        # Reverse sources.
        sources = list(reversed(sources))

        # Calc Matrix
        i: int = 0
        for i, node in enumerate(sources, 1):
            cmds.connectAttr(f'{node}.matrix', f'{mult_matrix}.matrixIn[{i}]')

        if follows_parent:
            cmds.connectAttr(
                f'{sources[-1]}.parentMatrix[0]',
                f'{mult_matrix}.matrixIn[{i+1}]',
            )
            cmds.connectAttr(
                f'{target}.parentInverseMatrix[0]',
                f'{mult_matrix}.matrixIn[{i+2}]',
            )

    # Decompose Matrix
    decompose_mtx: str = cmds.createNode(
        'decomposeMatrix',
        name=f'{base_name}{target_base_name}_decomposeMtx',
    )
    cmds.connectAttr(f'{mult_matrix}.matrixSum', f'{decompose_mtx}.inputMatrix')

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

    # Update Outliner
    for panel in cmds.getPanel(type='outlinerPanel'):
        cmds.outlinerEditor(panel, edit=True, refresh=True)

    # Clean up
    history_visibility.main(
        [
            target,
            *sources,
        ],
        0,
    )


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
