# ==============================================================================
#
# Perspective Guide
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from itertools import product

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QCheckBox, QSpinBox, QDoubleSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QCheckBox,
            QSpinBox,
            QDoubleSpinBox,
        )
from maya import cmds
from ..lib import parser, widgets
from ..edit import combine_shapes
from ..modify import lock_hide_transform
from ..modify import history_visibility
from ..display import drawing_color


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Perspective Guide'
__version__: str = '1.10'
__doc__ = 'Generates perspective grids and an eye level guide for the selected camera.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

EL_COLOR: tuple[float, float, float] = (0.2, 0.7, 1.0)
VP_COLOR: tuple[float, float, float] = (0.65, 0.2, 1.0)
EL_WIDTH: float = 4
VP_WIDTH: float = 2


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    radius: parser.Variant[int] = parser.Variant(100)
    division: parser.Variant[int] = parser.Variant(8)
    eye_level: parser.Variant[bool] = parser.Variant(True)
    vp_x: parser.Variant[bool] = parser.Variant(True)
    vp_y: parser.Variant[bool] = parser.Variant(True)
    vp_z: parser.Variant[bool] = parser.Variant(True)


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

        self.__radius: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__radius.setMinimumWidth(70)
        self.__radius.setRange(0, 10000000)
        main_layout.addRow(widgets.FormLabel('Radius'), self.__radius)

        self.__division: QSpinBox = QSpinBox(self)
        self.__division.setRange(2, 64)
        self.__division.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel('Division'), self.__division)

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__eye_level: QCheckBox = QCheckBox('Eye Level', self)
        main_layout.addRow('', self.__eye_level)

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__vp_x: QCheckBox = QCheckBox('X (Horizontal))', self)
        main_layout.addRow(widgets.FormLabel('Vanishing Point'), self.__vp_x)

        self.__vp_y: QCheckBox = QCheckBox('Y (Vertical)', self)
        main_layout.addRow('', self.__vp_y)

        self.__vp_z: QCheckBox = QCheckBox('Z (Depth))', self)
        main_layout.addRow('', self.__vp_z)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__radius.setValue(settings.radius.value())
        self.__division.setValue(settings.division.value())
        self.__eye_level.setChecked(settings.eye_level.value())
        self.__vp_x.setChecked(settings.vp_x.value())
        self.__vp_y.setChecked(settings.vp_y.value())
        self.__vp_z.setChecked(settings.vp_z.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.radius.set_value(self.__radius.value())
        settings.division.set_value(self.__division.value())
        settings.eye_level.set_value(self.__eye_level.isChecked())
        settings.vp_x.set_value(self.__vp_x.isChecked())
        settings.vp_y.set_value(self.__vp_y.isChecked())
        settings.vp_z.set_value(self.__vp_z.isChecked())
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
def create_vanishing_point(
    base_name: str,
    parent: str,
    axis: int = 0,
    radius: float = 9999,
    division: int = 16,
) -> str:
    '''Create vanishing point.'''
    step: float = 180.0 / division
    axis_name: tuple[str, str, str] = ('Horizontal', 'Vertical', 'Depth')
    curves: list[str] = []
    for i in range(division):
        angle = step * i
        normal: tuple[tuple[float, float, float], ...] = (
            (0, 0, 1),
            (1, 0, 0),
            (0, 1, 0),
        )
        rotate_mask: tuple[tuple[float, float, float], ...] = (
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        )
        curve: str = cmds.circle(
            name=f'{base_name}{axis_name[axis]}{i}_crv',
            radius=radius,
            normal=normal[axis],
            sections=64,
            degree=3,
            constructionHistory=False,
        )[0]
        rotate: tuple[float, float, float] = (
            angle * rotate_mask[axis][0],
            angle * rotate_mask[axis][1],
            angle * rotate_mask[axis][2],
        )
        cmds.setAttr(f'{curve}.rotate', *rotate, type='double3')
        for attr, _axis in product(['t', 'r', 's'], ['x', 'y', 'z']):
            cmds.setAttr(f'{curve}.{attr}{_axis}', lock=True)

        curve = cmds.parent(curve, parent)[0]
        for attr, _axis in product(['t', 'r', 's'], ['x', 'y', 'z']):
            cmds.setAttr(f'{curve}.{attr}{_axis}', lock=False)

        cmds.makeIdentity(
            curve, apply=True, translate=True, rotate=True, scale=True
        )

        if i == 0:
            cmds.setAttr(f'{curve}.lineWidth', VP_WIDTH)

        drawing_color.apply(mode=1, rgb=VP_COLOR, selection=[curve])
        curves.append(curve)

    combine_shapes.apply(curves[0], curves[1:])
    cmds.setAttr(f'{curves[0]}.tx', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{curves[0]}.ty', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{curves[0]}.tz', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{curves[0]}.sx', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{curves[0]}.sy', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{curves[0]}.sz', lock=True, keyable=False, channelBox=False)
    history_visibility.main(
        cmds.listRelatives(curves[0], shapes=True, path=True),
        0,
    )
    curves[0] = cmds.rename(curves[0], f'{base_name}{axis_name[axis]}_crv')
    return curves[0]


def apply(
    camera: str,
    radius: float = 9999,
    division: int = 16,
    is_eye_level: bool = True,
    is_vp_x: bool = True,
    is_vp_y: bool = True,
    is_vp_z: bool = True,
) -> bool:
    '''Do it.'''
    base_name: str = camera.split('|')[-1]
    base_name = camera.split('_')[0]

    # Decompose
    camera_decompose: str = cmds.createNode(
        'decomposeMatrix', name=f'{base_name}_decomposeMtx'
    )
    cmds.connectAttr(
        f'{camera}.worldMatrix[0]', f'{camera_decompose}.inputMatrix'
    )

    # Group
    group: str = cmds.createNode('transform', name=f'{base_name}PerspGuide_grp')
    cmds.connectAttr(
        f'{camera_decompose}.outputTranslate', f'{group}.translate'
    )
    history_visibility.main([group], 0)
    cmds.setAttr(f'{group}.tx', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{group}.ty', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{group}.tz', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{group}.rx', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{group}.ry', lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f'{group}.rz', lock=True, keyable=False, channelBox=False)

    # Eye Level
    if is_eye_level:
        eye_level: str = cmds.circle(
            name=f'{base_name}EyeLevel_crv',
            radius=radius,
            normal=(0, 1, 0),
            sections=64,
            degree=3,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{eye_level}.lineWidth', EL_WIDTH)
        drawing_color.apply(mode=1, rgb=EL_COLOR, selection=[eye_level])
        history_visibility.main(
            cmds.listRelatives(eye_level, shapes=True, path=True),
            0,
        )
        lock_hide_transform.lock([eye_level], False)
        eye_level = cmds.parent(eye_level, group)[0]

    # Vanishing Point
    if is_vp_x:
        create_vanishing_point(base_name, group, 0, radius * 1.001, division)

    if is_vp_y:
        create_vanishing_point(base_name, group, 1, radius * 1.002, division)

    if is_vp_z:
        create_vanishing_point(base_name, group, 2, radius * 1.003, division)

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection or len(selection) != 1:
        _logger.error('Select camera to create perspective guide.')
        return

    camera: str = selection[0]
    shapes: list[str] = (
        cmds.listRelatives(camera, type='camera', shapes=True, path=True) or []
    )
    if not shapes:
        _logger.error('Select camera to create perspective guide.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        camera,
        settings.radius.value(),
        settings.division.value(),
        settings.eye_level.value(),
        settings.vp_x.value(),
        settings.vp_y.value(),
        settings.vp_z.value(),
    )
    if result:
        cmds.select(*selection)
        _logger.info('Done.')
