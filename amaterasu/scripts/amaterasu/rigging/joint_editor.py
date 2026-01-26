# ==============================================================================
#
# Joint Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
from functools import partial
from itertools import product

try:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QGridLayout,
        QLabel,
        QLineEdit,
        QPushButton,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QGridLayout,
            QLabel,
            QLineEdit,
            QPushButton,
        )
from maya import cmds
from ..lib import parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Joint Editor'
__version__: str = '1.22'
__doc__ = 'his tool helps to edit joint.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

ICON_SIZE: QSize = QSize(24, 24)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    across: parser.Variant[int] = parser.Variant(1)
    function: parser.Variant[int] = parser.Variant(0)
    search: parser.Variant[str] = parser.Variant('_L_')
    replace: parser.Variant[str] = parser.Variant('_R_')


class Axis:
    '''Axis'''

    X: int = 0
    Y: int = 1
    Z: int = 2

    @staticmethod
    def vector(axis: int) -> list[float]:
        '''Return vector as list.'''
        if axis == Axis.X:
            return [1, 0, 0]

        elif axis == Axis.Y:
            return [0, 1, 0]

        elif axis == Axis.Z:
            return [0, 0, 1]

        return []


class Node:
    '''Node'''

    def __init__(self, name: str) -> None:
        '''Initialize'''
        self.__name: str = name
        self.__locked_attrs: list[str] = []

    def name(self) -> str:
        '''Return name'''
        return self.__name

    def save_lock_status(self) -> None:
        '''Save lock status'''
        temp = cmds.listAttr(self.__name, locked=True)
        if not temp:
            temp = []
        self.__locked_attrs = temp

    def unlock_all_attribute(self) -> None:
        '''Unlock all attribute'''
        self.save_lock_status()
        for attr in self.__locked_attrs:
            cmds.setAttr(f'{self.__name}.{attr}', lock=False)

    def restore_lock_status(self) -> None:
        '''Restore lock status.'''
        for attr in self.__locked_attrs:
            cmds.setAttr(f'{self.__name}.{attr}', lock=True)

    def get_children(self, ad: bool = False) -> list[Node]:
        '''Return children nodes.'''
        children: list[str] = (
            cmds.listRelatives(
                self.__name, children=True, allDescendents=ad, path=True
            )
            or []
        )
        if not children:
            children = []

        result: list[Node] = []
        for child in children:
            result.append(Node(child))

        return result

    def get_all_children(self) -> list[Node]:
        '''Return all children nodes.'''
        return self.get_children(ad=True)

    def set_parent(self, parent: str = '') -> None:
        '''Set parent.'''
        self.unlock_all_attribute()
        if parent == '':
            self.__name = cmds.parent(self.__name, w=True)[0]
        else:
            self.__name = cmds.parent(self.__name, parent)[0]
        self.restore_lock_status()

    def lock_attribute(self, attr: str, keyable: bool = False) -> None:
        '''Lock attribute.'''
        cmds.setAttr(f'{self.__name}.{attr}', lock=True, keyable=keyable)

    def unlock_attribute(self, attr: str, keyable: bool = True) -> None:
        '''Unlock attribute.'''
        cmds.setAttr(f'{self.__name}.{attr}', lock=False, keyable=keyable)

    def set_attr(
        self, attr: str, *args: list[Any], **kwargs: dict[str, Any]
    ) -> None:
        '''Set value'''
        plug: str = f'{self.__name}.{attr}'
        is_locked: bool = cmds.getAttr(plug, lock=True)
        if is_locked:
            cmds.setAttr(plug, lock=False)

        cmds.setAttr(plug, *args, **kwargs)

        if is_locked:
            cmds.setAttr(plug, lock=True)


class Joint(Node):
    '''Joint'''

    def __init__(self, name: str) -> None:
        '''Initialize'''
        super().__init__(name)

        self.__name: str = name
        self.__primary: int = Axis.X
        self.__secondary: int = Axis.Y
        self.__children: list[Node] = []

    def set_primary(self, axis: int) -> None:
        '''Set primary axis.'''
        self.__primary = axis

    def set_secondary(self, axis: int) -> None:
        '''Set secondary axis.'''
        self.__secondary = axis

    def set_joint_orient(self, value: list[float] | None = None) -> None:
        '''Set joint orient.'''
        if value is None:
            value = [0, 0, 0]

        self.unparent_children()
        self.unlock_all_attribute()
        cmds.setAttr(f'{self.__name}.jo', *value)
        self.restore_unparented_children()
        self.restore_lock_status()

    def get_primary_vector(self, is_reverse: bool = False) -> list[float]:
        '''Return primary vector.'''
        vec: list[float] = [0.0, 0.0, 0.0]
        vec[self.__primary] = 1.0
        if is_reverse:
            vec[self.__primary] = -1.0

        return vec

    def get_secondary_vector(self, is_reverse: bool = False) -> list[float]:
        '''Return secondary vector.'''
        vec: list[float] = [0.0, 0.0, 0.0]
        vec[self.__secondary] = 1.0
        if is_reverse:
            vec[self.__secondary] = -1.0

        return vec

    def aim_at_child(self) -> None:
        '''Aim at child.'''
        children: list[Node] = self.get_children()
        if not children:
            return

        self.unparent_children()

        up_object = cmds.createNode('transform', parent=self.__name)
        cmds.setAttr(f'{up_object}.t', *self.get_secondary_vector())
        cmds.parent(up_object, world=True)

        self.unlock_all_attribute()
        aim_const: str = cmds.aimConstraint(
            self.__children[0].name(),
            self.__name,
            aimVector=self.get_primary_vector(),
            upVector=self.get_secondary_vector(),
            worldUpObject=up_object,
            worldUpType='object',
            weight=1,
        )
        cmds.delete(aim_const, up_object)
        cmds.makeIdentity(
            self.__name,
            apply=True,
            translate=False,
            rotate=True,
            scale=True,
            normal=False,
        )

        self.restore_unparented_children()
        self.restore_lock_status()

    def unparent_children(self) -> None:
        '''Unparent children.'''
        self.__children = self.get_children()
        for child in self.__children:
            child.set_parent()

    def restore_unparented_children(self) -> None:
        '''Restore unparent children.'''
        for child in self.__children:
            child.set_parent(self.__name)

    def reverse_primary_axis(self) -> None:
        '''Reverse primary axis.'''
        self.unparent_children()

        aim_object: str = cmds.createNode('transform', parent=self.__name)
        cmds.setAttr(f'{aim_object}.t', *self.get_primary_vector(1))
        cmds.parent(aim_object, world=True)

        up_object: str = cmds.createNode('transform', parent=self.__name)
        cmds.setAttr(f'{up_object}.t', *self.get_secondary_vector())
        cmds.parent(up_object, world=True)

        self.unlock_all_attribute()
        aim_const: str = cmds.aimConstraint(
            aim_object,
            self.__name,
            aimVector=self.get_primary_vector(),
            upVector=self.get_secondary_vector(),
            worldUpObject=up_object,
            worldUpType='object',
            weight=1,
        )
        cmds.delete(aim_const, aim_object, up_object)
        cmds.makeIdentity(
            self.__name,
            apply=True,
            translate=False,
            rotate=True,
            scale=True,
            normal=False,
        )

        self.restore_unparented_children()
        self.restore_lock_status()

    def twist(self, degree: float) -> None:
        '''Twist joint.'''
        self.unparent_children()
        self.unlock_all_attribute()

        cmds.makeIdentity(
            self.__name,
            apply=True,
            translate=False,
            rotate=True,
            scale=True,
            normal=False,
        )
        attr: list[str] = ['jox', 'joy', 'joz']
        plug: str = f'{self.__name}.{attr[self.__primary]}'
        cmds.setAttr(plug, degree + cmds.getAttr(plug))

        self.restore_unparented_children()
        self.restore_lock_status()

    def mirror(
        self, across: int, function: int, search: str = '', replace: str = ''
    ) -> None:
        '''
        Mirror joint
        across = 0:XY / 1:YZ / 2:XZ
        function = 0:Behavior / 1:Orientation
        '''
        self.unlock_all_attribute()
        children = self.get_all_children()
        for child in children:
            child.unlock_all_attribute()

        kwargs: dict[str, Any] = {}
        if not function:
            kwargs['mb'] = True

        across_table: list[str] = ['mxy', 'myz', 'mxz']
        kwargs[across_table[across]] = True

        kwargs['sr'] = [search, replace]
        cmds.mirrorJoint(self.__name, **kwargs)

        self.restore_lock_status()
        for child in children:
            child.restore_lock_status()

    def set_position(self, pos: list[float], world_space: bool = False) -> None:
        '''Set position.'''
        self.unparent_children()
        self.unlock_all_attribute()

        cmds.xform(self.__name, translation=pos, worldSpace=world_space)

        self.restore_unparented_children()
        self.restore_lock_status()


class Creator(QWidget):
    '''Create joint widget.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = widgets.FormLayout(self)
        main_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Pos
        layout = QHBoxLayout(self)
        main_layout.addRow(widgets.FormLabel('Pos'), layout)

        self.__pos = widgets.ThreeDoubleSpinBox(self)
        layout.addWidget(self.__pos)

        button = QPushButton('Get', self)
        button.clicked.connect(partial(self.set_position, self.__pos))
        layout.addWidget(button)

        # Aim Pos
        layout = QHBoxLayout(self)
        main_layout.addRow(widgets.FormLabel('Aim Pos'), layout)

        self.__aim = widgets.ThreeDoubleSpinBox(self)
        layout.addWidget(self.__aim)

        button = QPushButton('Get', self)
        button.clicked.connect(partial(self.set_position, self.__aim))
        layout.addWidget(button)

        # Up Pos
        layout = QHBoxLayout(self)
        main_layout.addRow(widgets.FormLabel('Up Pos'), layout)

        self.__up = widgets.ThreeDoubleSpinBox(self)
        layout.addWidget(self.__up)

        button = QPushButton('Get', self)
        button.clicked.connect(partial(self.set_position, self.__up))
        layout.addWidget(button)

        button = QPushButton('Create', self)
        button.clicked.connect(self.apply)
        main_layout.addRow(button)

    def set_position(self, widget: widgets.ThreeDoubleSpinBox) -> None:
        '''Set position to widget.'''
        pos: list[float] = [0.0, 0.0, 0.0]
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            return

        bb: Any = cmds.polyEvaluate(selection, boundingBoxComponent=True)
        if bb == ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)):
            bb = cmds.polyEvaluate(selection, boundingBox=True)

        pos[0] = (bb[0][0] + bb[0][1]) / 2.0
        pos[1] = (bb[1][0] + bb[1][1]) / 2.0
        pos[2] = (bb[2][0] + bb[2][1]) / 2.0
        widget.set_value(pos[0], pos[1], pos[2])

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        create_joint(
            self.__pos.value(),
            self.__aim.value(),
            self.__up.value(),
            Axis.vector(Axis.X),
            False,
        )


class MirrorJoint(QWidget):
    '''Mirror Joint Widget.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout = widgets.FormLayout()
        main_layout.addLayout(layout)

        self.__across: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__across.set_labels(('XY', 'YZ', 'XZ'))
        layout.addRow(widgets.FormLabel('Across'), self.__across)

        self.__function: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__function.set_labels(('Behavior', 'Orientation'))
        layout.addRow(widgets.FormLabel('Function'), self.__function)

        self.__search = QLineEdit(self)
        layout.addRow(widgets.FormLabel('Search'), self.__search)

        self.__replace = QLineEdit(self)
        layout.addRow(widgets.FormLabel('Replace'), self.__replace)

        button = QPushButton('Mirror Joint', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load Settings'''
        settings: Settings = Settings.instance(__name__, True)
        self.__across.set_check_id(settings.across.value())
        self.__function.set_check_id(settings.function.value())
        self.__search.setText(settings.search.value())
        self.__replace.setText(settings.replace.value())

    def save_settings(self) -> None:
        '''Save Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.across.set_value(self.__across.check_id())
        settings.function.set_value(self.__function.check_id())
        settings.search.set_value(self.__search.text())
        settings.replace.set_value(self.__replace.text())

    def reset_settings(self) -> None:
        '''Reset Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        settings: Settings = Settings.instance(__name__, True)
        joints: list[str] = cmds.ls(selection=True, type='joint')
        for joint in joints:
            j: Joint = Joint(joint)
            j.mirror(
                settings.across.value(),
                settings.function.value(),
                settings.search.value(),
                settings.replace.value(),
            )


class PrimaryJointOrient(QWidget):
    '''Primary Joint Orient'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_aim.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Aim at Child')
        button.clicked.connect(self.aim_at_child)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_reverse_aim.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Reverse')
        button.clicked.connect(self.reverse_axis)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_aim2.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Same as Parent')
        button.clicked.connect(self.set_same_as_parent)
        layout.addWidget(button)

        layout.addStretch()

    @widgets.undo
    def aim_at_child(self) -> None:
        '''Aim at child.'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        amin_at_child(joints)

    @widgets.undo
    def reverse_axis(self) -> None:
        '''Reverse axis.'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        reverse_axis(joints)

    @widgets.undo
    def set_same_as_parent(self) -> None:
        '''Set same as parent.'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        set_same_as_parent(joints)


class SecondaryJointOrient(QWidget):
    '''Secondary Joint Orient'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_rotate_right.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Rotate 90')
        button.clicked.connect(partial(self.rotate, 90.0))
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_rotate_left.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Rotate -90')
        button.clicked.connect(partial(self.rotate, -90.0))
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_rotate_180.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Reverse')
        button.clicked.connect(partial(self.rotate, 180.0))
        layout.addWidget(button)

        layout.addStretch()

    @widgets.undo
    def rotate(self, degree: float) -> None:
        '''Rotate'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        for joint in joints:
            j: Joint = Joint(joint)
            j.set_primary(Axis.X)
            j.set_secondary(Axis.Y)
            j.twist(degree)

        if joints:
            cmds.select(*joints)


class TransformLocker(QWidget):
    '''Transform Locker.'''

    lock_button_icon: str = 'a_lock_joint.png'
    unlock_button_icon: str = 'a_unlock_joint.png'
    lock_button_label: str = 'Lock Transform'
    unlock_button_label: str = 'Unlock Transform'

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name(self.lock_button_icon))
        button.setIconSize(ICON_SIZE)
        button.setToolTip(self.lock_button_label)
        button.clicked.connect(self.lock)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name(self.unlock_button_icon))
        button.setIconSize(ICON_SIZE)
        button.setToolTip(self.unlock_button_label)
        button.clicked.connect(self.unlock)
        layout.addWidget(button)

    @widgets.undo
    def lock(self) -> None:
        '''Lock'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        for attr, axis in product(['t', 'r', 's'], ['', 'x', 'y', 'z']):
            lock_attribute(joints, (attr + axis))

        lock_attribute(joints, 'v')

    @widgets.undo
    def unlock(self) -> None:
        '''Unlock'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        for attr, axis in product(['t', 'r', 's'], ['', 'x', 'y', 'z']):
            unlock_attribute(joints, (attr + axis))

        unlock_attribute(joints, 'v')


class JointOrientLocker(TransformLocker):
    '''Joint Orient Locker.'''

    lock_button_icon: str = 'a_lock_joint_orient.png'
    unlock_button_icon: str = 'a_unlock_joint_orient.png'
    lock_button_label: str = 'Lock Joint Orient'
    unlock_button_label: str = 'Unlock Joint Orient'

    @widgets.undo
    def lock(self) -> None:
        '''Lock[override]'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        lock_attribute(joints, 'jo')

    @widgets.undo
    def unlock(self) -> None:
        '''Unlock[override]'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        unlock_attribute(joints, 'jo', False)


class LockAndHide(QWidget):
    '''Lock and Hide'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_lock.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Lock And Hide Joints')
        button.clicked.connect(self.lock_and_hide)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_unlock.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Unlock and Show Joints')
        button.clicked.connect(self.unlock_and_show)
        layout.addWidget(button)

    @widgets.undo
    def lock_and_hide(self) -> None:
        '''Lock and Hide'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        for attr in ['t', 'r', 's']:
            for axis in ['', 'x', 'y', 'z']:
                plug = attr + axis
                lock_attribute(joints, plug)

        lock_attribute(joints, 'v')
        lock_attribute(joints, 'jo')
        for joint in joints:
            safe_set_attr(joint + '.v', False)

    def unlock_and_show(self) -> None:
        '''Unlock And Show'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        if not joints:
            return

        for attr, axis in product(['t', 'r', 's'], ['', 'x', 'y', 'z']):
            unlock_attribute(joints, (attr + axis))

        unlock_attribute(joints, 'v')
        unlock_attribute(joints, 'jo')
        for joint in joints:
            safe_set_attr(joint + '.v', True)


class JointUtility(QWidget):
    '''Joint Utility'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_align_v.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Straight Line')
        button.clicked.connect(self.straight_line)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_scale.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Fix segment scale compensate')
        button.clicked.connect(self.fix_segment_scale)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_one.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Set radius to 1 for all joints')
        button.clicked.connect(self.set_radius_to_one)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_remove_color.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Remove color for all joints')
        button.clicked.connect(self.remove_color)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.setIcon(widgets.icon_from_file_name('a_select.png'))
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Select end joints for all')
        button.clicked.connect(self.select_end_joint)
        layout.addWidget(button)

        layout.addStretch()

    def normalize_joint(self) -> None:
        '''Normalize joint.'''
        pass

    def straight_line(self) -> None:
        '''Straight line'''
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select joints which align in straight line.')
            return

        if len(selection) != 2:
            _logger.error('Must select start joint and end joint.')
            return

        straight_line(selection[0], selection[1])
        cmds.select(*selection)

    def fix_segment_scale(self) -> None:
        '''Fix segment scale.'''
        joints: list[str] = cmds.ls(selection=True, type='joint')
        for joint in joints:

            cmds.setAttr(f'{joint}.ssc', False)

            parent: list[str] = (
                cmds.listRelatives(joint, parent=True, path=True) or []
            )
            if not parent:
                continue

            src_plug = f'{parent[0]}.s'
            dst_plug = f'{joint}.is'
            if cmds.isConnected(src_plug, dst_plug):
                continue

            cmds.connectAttr(src_plug, dst_plug, force=True)

    def set_radius_to_one(self) -> None:
        '''Set radius to 1.'''
        joints: list[str] = cmds.ls(type='joint')
        if not joints:
            return

        for joint in joints:
            cmds.setAttr(f'{joint}.radius', 1)

    def remove_color(self) -> None:
        '''Remove Color'''
        joints: list[str] = cmds.ls(type='joint')
        if not joints:
            return

        for joint in joints:
            cmds.setAttr(f'{joint}.useObjectColor', 0)

    def select_end_joint(self) -> None:
        '''Select End Joint.'''
        joints: list[str] = cmds.ls(type='joint')
        if not joints:
            return

        end_joint: list[str] = []
        for joint in joints:
            childlen: list[str] = (
                cmds.listRelatives(joint, children=True, path=True) or []
            )
            if not childlen:
                end_joint.append(joint)

        cmds.select(end_joint, replace=True)


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
        main_layout.addWidget(Creator(self))

        main_layout.addWidget(widgets.HorizontalLine())

        self.__mirror_joint_option = MirrorJoint(self)
        main_layout.addWidget(self.__mirror_joint_option)

        main_layout.addWidget(widgets.HorizontalLine())

        axis_layout = QGridLayout(self)
        main_layout.addLayout(axis_layout)

        axis_layout.addWidget(QLabel('Primary Axis'), 0, 0)
        axis_layout.addWidget(PrimaryJointOrient(self), 1, 0)

        axis_layout.addWidget(widgets.VerticalLine(), 0, 1, 2, 1)

        axis_layout.addWidget(QLabel('Secondary Axis'), 0, 2)
        axis_layout.addWidget(SecondaryJointOrient(self), 1, 2)

        main_layout.addWidget(widgets.HorizontalLine())

        main_layout.addWidget(QLabel('Lock & Unlocker'))
        layout = QHBoxLayout()
        main_layout.addLayout(layout)
        layout.addWidget(TransformLocker(self))
        layout.addWidget(widgets.VerticalLine())
        layout.addWidget(JointOrientLocker(self))
        layout.addWidget(widgets.VerticalLine())
        layout.addWidget(LockAndHide(self))
        layout.addStretch()

        main_layout.addWidget(widgets.HorizontalLine())

        main_layout.addWidget(QLabel('Utility'))
        main_layout.addWidget(JointUtility(self))

        main_layout.addStretch()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__mirror_joint_option.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        self.__mirror_joint_option.save_settings()
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.__mirror_joint_option.reset_settings()
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
def amin_at_child(
    joints: list[str], primary_axis: int = Axis.X, secondary_axis: int = Axis.Y
) -> None:
    '''Aim at child'''
    for joint in joints:
        j = Joint(joint)
        j.set_primary(primary_axis)
        j.set_secondary(secondary_axis)
        j.aim_at_child()

    if joints:
        cmds.select(*joints)


def reverse_axis(
    joints: list[str], primary_axis: int = Axis.X, secondary_axis: int = Axis.Y
) -> None:
    '''Reverse axis.'''
    for joint in joints:
        j = Joint(joint)
        j.set_primary(primary_axis)
        j.set_secondary(secondary_axis)
        j.reverse_primary_axis()

    if joints:
        cmds.select(*joints)


def set_same_as_parent(
    joints: list[str], primary_axis: int = Axis.X, secondary_axis: int = Axis.Y
) -> None:
    '''Set same as parent.'''
    temp: list[str] = []
    for joint in joints:
        parent: list[str] = (
            cmds.listRelatives(joint, parent=True, path=True) or []
        )
        if parent is not None:
            temp.append(joint)

    if not temp:
        return

    for joint in temp:
        j = Joint(joint)
        j.set_primary(primary_axis)
        j.set_secondary(secondary_axis)
        j.set_joint_orient([0, 0, 0])

    if joints:
        cmds.select(*joints)


def lock_attribute(joints: list[str], attr: str, keyable: bool = False) -> None:
    '''Lock attribute.'''
    for joint in joints:
        cmds.setAttr(f'{joint}.{attr}', lock=True, keyable=keyable)


def unlock_attribute(
    joints: list[str], attr: str, keyable: bool = True
) -> None:
    '''Unlock attribute.'''
    for joint in joints:
        cmds.setAttr(f'{joint}.{attr}', lock=False, keyable=keyable)


def create_joint(
    pos: list[float],
    aim_pos: list[float],
    up_pos: list[float],
    aim_vec: list[float],
    is_end_joint: bool = False,
) -> str:
    '''Create Joint'''
    joint = cmds.createNode('joint')
    cmds.xform(joint, translation=pos, worldSpace=True)

    aim = cmds.createNode('transform')
    cmds.xform(aim, translation=aim_pos, worldSpace=True)

    up = cmds.createNode('transform')
    cmds.xform(up, translation=up_pos, worldSpace=True)

    aim_const: str = cmds.aimConstraint(
        aim,
        joint,
        aimVector=aim_vec,
        worldUpObject=up,
        worldUpType='object',
        weight=1,
    )

    cmds.delete(aim_const, aim, up)
    cmds.makeIdentity(
        joint,
        apply=True,
        translate=False,
        rotate=True,
        scale=False,
        normal=False,
    )

    if is_end_joint:
        endJoint = cmds.createNode('joint', name=f'{joint}End', parent=joint)
        cmds.xform(endJoint, translation=aim_pos, worldSpace=True)
        cmds.setAttr(f'{endJoint}.jo', 0, 0, 0)

    return joint


def straight_line(start_joint: str, end_joint: str) -> None:
    '''Straint line.'''
    chain_joint: list[str] = []
    temp = start_joint
    while True:
        childJoint: list[str] = (
            cmds.listRelatives(temp, children=True, path=True) or []
        )
        if not childJoint:
            return False

        if childJoint[0] == end_joint:
            break

        chain_joint.append(childJoint[0])
        temp = childJoint[0]

    start_pos = utility.Vector(
        cmds.xform(start_joint, query=True, translation=True, worldSpace=True)
    )
    endPos = utility.Vector(
        cmds.xform(end_joint, query=True, translation=True, worldSpace=True)
    )
    vector = endPos.vector(start_pos)
    all_length = joint_length(start_joint, end_joint)

    pos_list: list[utility.Vector] = []
    for joint in chain_joint:
        pos = utility.Vector(
            cmds.xform(joint, query=True, translation=True, worldSpace=True)
        )
        length = joint_length(start_joint, joint)
        result = start_pos + vector * (length / all_length)
        pos_list.append(result)

    for joint, pos in zip(chain_joint, pos_list):
        j = Joint(joint)
        j.set_position(pos.as_float3(), True)


def joint_length(start_joint: str, end_joint: str) -> float:
    '''Joint Length'''
    temp: str = start_joint
    length: float = 0.0
    is_end: bool = False
    while True:
        child_joint: list[str] = (
            cmds.listRelatives(temp, children=True, path=True) or []
        )
        if not child_joint:
            return 0

        if child_joint[0] == end_joint:
            is_end = True

        pos_a = utility.Vector(
            cmds.xform(temp, query=True, translation=True, worldSpace=True)
        )
        pos_b = utility.Vector(
            cmds.xform(
                child_joint[0], query=True, translation=True, worldSpace=True
            )
        )
        length += pos_b.length(pos_a)
        temp = child_joint[0]
        if is_end:
            break

    return length


def is_lock(plug: str) -> bool:
    '''Is lock.'''
    return cmds.getAttr(plug, lock=True)


def safe_set_attr(plug: str, value: Any) -> None:
    '''Save set attribute.'''
    locked: bool = False
    if is_lock(plug):
        cmds.setAttr(plug, lock=False, keyable=True)
        locked = True

    cmds.setAttr(plug, value)
    if locked:
        cmds.setAttr(plug, lock=True, keyable=False)


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
