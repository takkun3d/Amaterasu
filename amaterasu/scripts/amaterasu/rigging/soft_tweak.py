# ==============================================================================
#
# Soft Tweak
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
__product__: str = 'Soft Tweak'
__version__: str = '1.20'
__doc__ = 'Create soft tweak rig.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

WORLD_DAG_PATH: str = '|'
SYSTEM_GROUP: str = 'softTweakSetup_grp'


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

        self.__geometries: widgets.NodePicker = widgets.NodePicker(-1, self)
        form_layout.addRow(widgets.FormLabel('Geometries'), self.__geometries)

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
            _logger.error('Guide node is required to create soft tweak rig.')
            return

        geometries: list[str] = self.__geometries.text_as_list()
        if not geometries:
            _logger.error('Geometry is required to create soft tweak rig.')
            return

        apply(
            guide,
            geometries,
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
    geometries: list[str],
    parent: str = SYSTEM_GROUP,
    is_delete_guide: bool = True,
) -> bool:
    ''''''
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

    # Pivot Controller
    soft_mod_pivot: str = create_controller.Locator().create(
        '', f'{base_name}Pivot', 'ctrl', 1.5, None, None, 0, controller_space
    )

    # Controller
    soft_mod_ctrl: str = create_controller.Sphere().create(
        '', base_name, 'ctrl', 1.0, None, None, 0, soft_mod_pivot
    )

    # Soft Mod Space
    soft_mod_space: str = cmds.createNode(
        'transform', name=f'{base_name}SoftModSpace_null', parent=parent
    )
    cmds.matchTransform(soft_mod_space, guide)

    # Soft Mod
    soft_mod, soft_mod_handle = cmds.softMod(
        geometries,
        name=f'{base_name}_softMod',
        falloffAroundSelection=False,
    )
    soft_mod_handle = cmds.parent(soft_mod_handle, soft_mod_space)[0]
    cmds.setAttr(f'{soft_mod_handle}.translate', 0, 0, 0, type='double3')
    cmds.setAttr(f'{soft_mod_handle}.rotate', 0, 0, 0, type='double3')
    cmds.setAttr(f'{soft_mod_handle}.scale', 1, 1, 1, type='double3')
    cmds.setAttr(f'{soft_mod_handle}.visibility', False)
    cmds.makeIdentity(
        soft_mod_handle, apply=True, translate=True, rotate=True, scale=True
    )
    cmds.xform(
        soft_mod_handle,
        rotatePivot=(0, 0, 0),
        scalePivot=(0, 0, 0),
        worldSpace=False,
    )

    # Soft Mod Handle Shape
    soft_mod_handle_shapes: list[str] = (
        cmds.listRelatives(soft_mod_handle, shapes=True, path=True) or []
    )
    cmds.setAttr(f'{soft_mod_handle_shapes[0]}.origin', 0, 0, 0, type='double3')

    # Calc Matrix
    soft_mod_matrix: str = cmds.createNode(
        'multMatrix', name=f'{base_name}_multMtx'
    )
    cmds.connectAttr(
        f'{soft_mod_pivot}.matrix', f'{soft_mod_matrix}.matrixIn[0]'
    )
    cmds.connectAttr(
        f'{controller_space}.matrix', f'{soft_mod_matrix}.matrixIn[1]'
    )

    # Matrix Constraint
    soft_mod_decompose: str = cmds.createNode(
        'decomposeMatrix', name=f'{base_name}_decomposeMtx'
    )
    cmds.connectAttr(
        f'{soft_mod_matrix}.matrixSum', f'{soft_mod_decompose}.inputMatrix'
    )
    cmds.connectAttr(
        f'{soft_mod_decompose}.outputTranslate', f'{soft_mod_space}.translate'
    )
    cmds.connectAttr(
        f'{soft_mod_decompose}.outputRotate', f'{soft_mod_space}.rotate'
    )
    cmds.connectAttr(
        f'{soft_mod_decompose}.outputScale', f'{soft_mod_space}.scale'
    )
    cmds.connectAttr(
        f'{soft_mod_decompose}.outputShear', f'{soft_mod_space}.shear'
    )

    # Soft Mod
    cmds.connectAttr(f'{soft_mod_space}.translate', f'{soft_mod}.falloffCenter')
    cmds.connectAttr(
        f'{soft_mod_space}.inverseMatrix', f'{soft_mod}.bindPreMatrix'
    )

    # Connect controller to soft-mod handle.
    cmds.connectAttr(
        f'{soft_mod_ctrl}.translate', f'{soft_mod_handle}.translate'
    )
    cmds.connectAttr(f'{soft_mod_ctrl}.rotate', f'{soft_mod_handle}.rotate')
    cmds.connectAttr(f'{soft_mod_ctrl}.scale', f'{soft_mod_handle}.scale')
    cmds.connectAttr(f'{soft_mod_ctrl}.shear', f'{soft_mod_handle}.shear')

    # Add Border attributes to controller.
    cmds.addAttr(
        soft_mod_ctrl,
        longName='softMod',
        attributeType='enum',
        enumName='SoftMod:',
        niceName='--------------------',
        minValue=0,
        maxValue=0,
    )
    cmds.setAttr(f'{soft_mod_ctrl}.softMod', edit=True, channelBox=True)

    # Add envelope attributes to controller.
    cmds.addAttr(
        soft_mod_ctrl,
        longName='envelope',
        attributeType='double',
        minValue=0,
        maxValue=1,
        defaultValue=1,
    )
    cmds.setAttr(f'{soft_mod_ctrl}.envelope', edit=True, keyable=True)
    cmds.connectAttr(f'{soft_mod_ctrl}.envelope', f'{soft_mod}.envelope')

    # Add fall-off-radius attributes to controller.
    cmds.addAttr(
        soft_mod_ctrl,
        longName='falloffRadius',
        attributeType='double',
        minValue=0,
        defaultValue=1,
    )
    cmds.setAttr(f'{soft_mod_ctrl}.falloffRadius', edit=True, keyable=True)
    cmds.connectAttr(
        f'{soft_mod_ctrl}.falloffRadius', f'{soft_mod}.falloffRadius'
    )

    # Add interpolation attributes to controller.
    cmds.addAttr(
        soft_mod_ctrl,
        longName='interpolation',
        attributeType='enum',
        enumName='none:linear:smooth:spline',
        defaultValue=2,
    )
    cmds.setAttr(f'{soft_mod_ctrl}.interpolation', edit=True, channelBox=True)
    cmds.connectAttr(
        f'{soft_mod_ctrl}.interpolation',
        f'{soft_mod}.falloffCurve[0].falloffCurve_Interp',
    )

    # Clean up
    history_visibility.main(
        [
            controller_space,
            soft_mod_pivot,
            soft_mod_ctrl,
            soft_mod_handle,
            soft_mod,
        ],
        0,
    )
    if is_delete_guide:
        cmds.delete(guide)

    return True


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
