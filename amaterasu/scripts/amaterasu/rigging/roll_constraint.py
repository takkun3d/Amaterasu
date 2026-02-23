# ==============================================================================
#
# Roll Constraint
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget
from maya import cmds
from ..lib import parser, widgets
from ..modify import history_visibility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Roll Constraint'
__version__: str = '1.10'
__doc__ = 'Constrains the rotation of an object, using only the roll component.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

PLUGIN_NAME: str = 'quatNodes.mll'
VECTOR: list[tuple[float, float, float]] = [
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
]


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    primary_axis: parser.Variant[int] = parser.Variant(0)


class MainWindow(widgets.StandardToolWidget):
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
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        self.__primary_axis: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__primary_axis.set_labels(('X', 'Y', 'Z'))
        main_layout.addRow(
            widgets.FormLabel('Primary Axis'), self.__primary_axis
        )

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__primary_axis.set_check_id(settings.primary_axis.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.primary_axis.set_value(self.__primary_axis.check_id())
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
        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(src_node: str, dst_node: str, primary_axis: int = 0) -> bool:
    '''Applies the constraint using the specified primary axis.'''
    #
    base_name: str = src_node.split('|')[-1].split(':')[-1]
    base_name = base_name.split('_')[0]
    roll_weight_attr: str = 'rollWeight'
    vector: tuple[float, float, float] = VECTOR[primary_axis]
    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)

    # Rotate Vector
    rotate_vector: str = cmds.createNode(
        'rotateVector', name=f'{base_name}Vector_rv'
    )
    cmds.setAttr(f'{rotate_vector}.input', *vector, type='double3')
    cmds.connectAttr(f'{src_node}.rotate', f'{rotate_vector}.rotate')
    cmds.connectAttr(f'{src_node}.rotateOrder', f'{rotate_vector}.rotateOrder')

    # Angle
    angle: str = cmds.createNode('angleBetween', name=f'{base_name}Angle_ab')
    cmds.setAttr(f'{angle}.vector1', *vector, type='double3')
    cmds.connectAttr(f'{rotate_vector}.output', f'{angle}.vector2')

    # Axis Angle To Quat
    bend_quat: str = cmds.createNode(
        'axisAngleToQuat', name=f'{base_name}BendQuat_atq'
    )
    cmds.connectAttr(f'{angle}.angle', f'{bend_quat}.inputAngle')
    cmds.connectAttr(f'{angle}.axis', f'{bend_quat}.inputAxis')

    # Quat Invert
    bend_invert_quat: str = cmds.createNode(
        'quatInvert', name=f'{base_name}BendInvertQuat_qi'
    )
    cmds.connectAttr(f'{bend_quat}.outputQuat', f'{bend_invert_quat}.inputQuat')

    # Euler to Quat
    quat: str = cmds.createNode('eulerToQuat', name=f'{base_name}Quat_etq')
    cmds.connectAttr(f'{src_node}.rotate', f'{quat}.inputRotate')
    cmds.connectAttr(f'{src_node}.rotateOrder', f'{quat}.inputRotateOrder')

    # Quat Prod
    roll_quat: str = cmds.createNode('quatProd', name=f'{base_name}RollQuat_qp')
    cmds.connectAttr(f'{quat}.outputQuat', f'{roll_quat}.input1Quat')
    cmds.connectAttr(
        f'{bend_invert_quat}.outputQuat', f'{roll_quat}.input2Quat'
    )

    # Quat Slerp
    slerp: str = cmds.createNode(
        'quatSlerp', name=f'{base_name}RollSlerp_qslerp'
    )
    if not cmds.attributeQuery(roll_weight_attr, node=src_node, exists=True):
        cmds.addAttr(
            src_node,
            longName=roll_weight_attr,
            attributeType='double',
            defaultValue=0.5,
        )
        cmds.setAttr(f'{src_node}.{roll_weight_attr}', edit=True, keyable=True)
    cmds.setAttr(f'{slerp}.input1QuatX', 0)
    cmds.setAttr(f'{slerp}.input1QuatY', 0)
    cmds.setAttr(f'{slerp}.input1QuatZ', 0)
    cmds.setAttr(f'{slerp}.input1QuatW', 1)
    cmds.connectAttr(f'{roll_quat}.outputQuat', f'{slerp}.input2Quat')
    cmds.connectAttr(f'{src_node}.{roll_weight_attr}', f'{slerp}.inputT')

    # Quat to Euler
    roll_euler: str = cmds.createNode(
        'quatToEuler', name=f'{base_name}RollEuler_qte'
    )
    cmds.connectAttr(f'{slerp}.outputQuat', f'{roll_euler}.inputQuat')
    cmds.connectAttr(
        f'{dst_node}.rotateOrder', f'{roll_euler}.inputRotateOrder'
    )

    # Dst
    cmds.connectAttr(f'{roll_euler}.outputRotate', f'{dst_node}.rotate')
    history_visibility.main([dst_node], 0)

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    nodes: list[str] = cmds.ls(selection=True, type=['transform', 'joint'])
    if not nodes or len(nodes) != 2:
        _logger.error(
            'Select a source node and a destination node to create the roll constraint.'
        )
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(nodes[0], nodes[1], settings.primary_axis.value())
    if result:
        cmds.select(*nodes)
        _logger.info('Done.')
