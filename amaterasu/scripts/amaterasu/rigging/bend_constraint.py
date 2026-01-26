# ==============================================================================
#
# Bend Constraint
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
__product__: str = 'Bend Constraint'
__version__: str = '1.00'
__doc__ = 'Constrains the rotation of an object, excluding the twist component.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

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
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
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
    vector: tuple[float, float, float] = VECTOR[primary_axis]

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

    # Dst
    cmds.connectAttr(f'{angle}.euler', f'{dst_node}.rotate', force=True)
    history_visibility.main([dst_node], 0)

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    nodes: list[str] = cmds.ls(selection=True, type=['transform', 'joint'])
    if not nodes or len(nodes) != 2:
        _logger.error(
            'Select a source node and a destination node to create the bend constraint.'
        )
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(nodes[0], nodes[1], settings.primary_axis.value())
    if result:
        cmds.select(*nodes)
        _logger.info('Done.')
