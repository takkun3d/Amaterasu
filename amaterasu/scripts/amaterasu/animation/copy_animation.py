# ==============================================================================
#
# Copy Animation
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import (
        QWidget,
        QGridLayout,
        QLineEdit,
        QCheckBox,
        QComboBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QLineEdit,
            QCheckBox,
            QComboBox,
        )
from maya import cmds, mel
from ..lib import parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Copy Animation'
__version__: str = '1.20'
__doc__ = 'Copy animation to specific nodes from selected nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

MIRROR_CHANNELS: tuple[str, str, str] = ('translate', 'rotate', 'scale')
MIRROR_AXIS: tuple[str, str, str] = ('X', 'Y', 'Z')


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    hierarchy: parser.Variant[int] = parser.Variant(1)
    method: parser.Variant[int] = parser.Variant(2)
    reverse_tx: parser.Variant[bool] = parser.Variant(False)
    reverse_ty: parser.Variant[bool] = parser.Variant(False)
    reverse_tz: parser.Variant[bool] = parser.Variant(False)
    reverse_rx: parser.Variant[bool] = parser.Variant(False)
    reverse_ry: parser.Variant[bool] = parser.Variant(False)
    reverse_rz: parser.Variant[bool] = parser.Variant(False)
    reverse_sx: parser.Variant[bool] = parser.Variant(False)
    reverse_sy: parser.Variant[bool] = parser.Variant(False)
    reverse_sz: parser.Variant[bool] = parser.Variant(False)
    search: parser.Variant[str] = parser.Variant('_L_')
    replace: parser.Variant[str] = parser.Variant('_R_')


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
        self.__main_layout: widgets.FormLayout = widgets.FormLayout(
            option_widget
        )

        self.__main_layout.addRow(
            widgets.FrameWidget('Copy Options', False, False, self)
        )

        self.__hierarchy: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__hierarchy.set_labels(('Selected', 'Below'))
        self.__main_layout.addRow(
            widgets.FormLabel('Hierarchy'), self.__hierarchy
        )

        self.__main_layout.addRow(
            widgets.FrameWidget('Paste Options', False, False, self)
        )

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('X:X', '1:X', 'Search & Replace'))
        self.__method.button_group().buttonClicked.connect(
            self.set_valid_options
        )
        self.__main_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__search = QLineEdit(self)
        self.__main_layout.addRow(widgets.FormLabel('Search'), self.__search)
        self.__search_index = self.__main_layout.row_id()

        self.__replace = QLineEdit(self)
        self.__main_layout.addRow(widgets.FormLabel('Replace'), self.__replace)
        self.__replace_index = self.__main_layout.row_id()

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        transform_layout = QGridLayout(self)
        self.__main_layout.addRow(widgets.FormLabel('Mirror'), transform_layout)

        self.__preset_mirror = QComboBox(self)
        self.__preset_mirror.addItem('XY(Behavior)')
        self.__preset_mirror.addItem('YZ(Behavior)')
        self.__preset_mirror.addItem('XZ(Behavior)')
        self.__preset_mirror.addItem('XY(Orient)')
        self.__preset_mirror.addItem('YZ(Orient)')
        self.__preset_mirror.addItem('XZ(Orient)')
        self.__preset_mirror.addItem('Custom')
        self.__preset_mirror.setCurrentIndex(6)
        self.__preset_mirror.currentIndexChanged.connect(self.set_mirror_preset)
        transform_layout.addWidget(self.__preset_mirror, 0, 0, 1, 3)

        self.__tx = QCheckBox('tx', self)
        transform_layout.addWidget(self.__tx, 1, 0)

        self.__ty = QCheckBox('ty', self)
        transform_layout.addWidget(self.__ty, 1, 1)

        self.__tz = QCheckBox('tz', self)
        transform_layout.addWidget(self.__tz, 1, 2)

        self.__rx = QCheckBox('rx', self)
        transform_layout.addWidget(self.__rx, 2, 0)

        self.__ry = QCheckBox('ry', self)
        transform_layout.addWidget(self.__ry, 2, 1)

        self.__rz = QCheckBox('rz', self)
        transform_layout.addWidget(self.__rz, 2, 2)

        self.__sx = QCheckBox('sx', self)
        transform_layout.addWidget(self.__sx, 3, 0)

        self.__sy = QCheckBox('sy', self)
        transform_layout.addWidget(self.__sy, 3, 1)

        self.__sz = QCheckBox('sz', self)
        transform_layout.addWidget(self.__sz, 3, 2)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__method.set_check_id(settings.method.value())
        self.__hierarchy.set_check_id(settings.hierarchy.value())
        self.__search.setText(settings.search.value())
        self.__replace.setText(settings.replace.value())
        self.set_mirror_preset(self.__preset_mirror.currentIndex())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.method.set_value(self.__method.check_id())
        settings.hierarchy.set_value(self.__hierarchy.check_id())
        settings.search.set_value(self.__search.text())
        settings.replace.set_value(self.__replace.text())
        settings.reverse_tx.set_value(self.__tx.isChecked())
        settings.reverse_ty.set_value(self.__ty.isChecked())
        settings.reverse_tz.set_value(self.__tz.isChecked())
        settings.reverse_rx.set_value(self.__rx.isChecked())
        settings.reverse_ry.set_value(self.__ry.isChecked())
        settings.reverse_rz.set_value(self.__rz.isChecked())
        settings.reverse_sx.set_value(self.__sx.isChecked())
        settings.reverse_sy.set_value(self.__sy.isChecked())
        settings.reverse_sz.set_value(self.__sz.isChecked())
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
        enabled: bool = self.__method.check_id() == 2
        self.__main_layout.set_row_enabled(self.__search_index, enabled)
        self.__main_layout.set_row_enabled(self.__replace_index, enabled)

    @Slot(int)
    def set_mirror_preset(self, index: int) -> None:
        '''Set mirror presets.'''
        if index == 0:  # XY(Behavior)
            self.__tx.setChecked(True)
            self.__ty.setChecked(True)
            self.__tz.setChecked(False)
            self.__rx.setChecked(False)
            self.__ry.setChecked(False)
            self.__rz.setChecked(False)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        elif index == 1:  # YZ(Behavior)
            self.__tx.setChecked(True)
            self.__ty.setChecked(True)
            self.__tz.setChecked(True)
            self.__rx.setChecked(False)
            self.__ry.setChecked(False)
            self.__rz.setChecked(False)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        elif index == 2:  # XZ(Behavior)
            self.__tx.setChecked(True)
            self.__ty.setChecked(False)
            self.__tz.setChecked(True)
            self.__rx.setChecked(False)
            self.__ry.setChecked(False)
            self.__rz.setChecked(False)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        elif index == 3:  # XY(Orient)
            self.__tx.setChecked(False)
            self.__ty.setChecked(False)
            self.__tz.setChecked(False)
            self.__rx.setChecked(True)
            self.__ry.setChecked(True)
            self.__rz.setChecked(False)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        elif index == 4:  # YZ(Orient)
            self.__tx.setChecked(True)
            self.__ty.setChecked(False)
            self.__tz.setChecked(False)
            self.__rx.setChecked(False)
            self.__ry.setChecked(True)
            self.__rz.setChecked(True)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        elif index == 5:  # XZ(Orient)
            self.__tx.setChecked(False)
            self.__ty.setChecked(False)
            self.__tz.setChecked(False)
            self.__rx.setChecked(True)
            self.__ry.setChecked(False)
            self.__rz.setChecked(True)
            self.__sx.setChecked(False)
            self.__sy.setChecked(False)
            self.__sz.setChecked(False)
        else:  # Custom
            settings: Settings = Settings.instance(__name__, True)
            self.__tx.setChecked(settings.reverse_tx.value())
            self.__ty.setChecked(settings.reverse_ty.value())
            self.__tz.setChecked(settings.reverse_tz.value())
            self.__rx.setChecked(settings.reverse_rx.value())
            self.__ry.setChecked(settings.reverse_ry.value())
            self.__rz.setChecked(settings.reverse_rz.value())
            self.__sx.setChecked(settings.reverse_sx.value())
            self.__sy.setChecked(settings.reverse_sy.value())
            self.__sz.setChecked(settings.reverse_sz.value())

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
def children_nodes(node: str) -> list[str]:
    '''Return children nodes.'''
    result: list[str] = [node]
    children: list[str] = (
        cmds.listRelatives(node, children=True, path=True) or []
    )
    if not children:
        return result

    for child in children:
        result.extend(children_nodes(child))

    return result


def selected_attribute() -> list[str]:
    '''Return selected attribute at channel box.'''

    def __long_attr_name(nodes: list[str], attrs: list[str]) -> list[str]:
        '''Return long attribute name.'''
        if not attrs:
            return []

        for i, attr in enumerate(attrs):
            attrs[i] = cmds.attributeName(f'{nodes[0]}.{attr}', long=True)

        return attrs

    channel_box: str = mel.eval('$gChannelBoxName=$gChannelBoxName;')
    result: list[str] = []

    result += __long_attr_name(
        cmds.channelBox(channel_box, query=True, mainObjectList=True),
        cmds.channelBox(channel_box, query=True, selectedMainAttributes=True),
    )

    result += __long_attr_name(
        cmds.channelBox(channel_box, query=True, shapeObjectList=True),
        cmds.channelBox(channel_box, query=True, selectedShapeAttributes=True),
    )

    result += __long_attr_name(
        cmds.channelBox(channel_box, query=True, historyObjectList=True),
        cmds.channelBox(
            channel_box, query=True, selectedHistoryAttributes=True
        ),
    )

    return result


def apply(
    src_nodes: list[str],
    dst_nodes: list[str],
    mirror: list[list[bool]] | None = None,
) -> None:
    '''Copy Animation'''
    if mirror is None:
        mirror = [[False, False, False] * 3]

    selected_attr = selected_attribute()
    for src, dst in zip(src_nodes, dst_nodes):
        connected_curves: list[str] = []
        for curve_type in utility.ANIM_CURVE_TYPES:
            connected_curves.extend(
                cmds.listConnections(
                    src, plugs=True, connections=True, type=curve_type
                )
                or []
            )

        if not connected_curves:
            continue

        for i in range(0, len(connected_curves), 2):
            src_plug: str = connected_curves[i + 1]
            dst_plug: str = connected_curves[i]
            src_attr_name: str = '.'.join(src_plug.split('.')[1:])
            dst_attr_name: str = '.'.join(dst_plug.split('.')[1:])
            if selected_attr and dst_attr_name not in selected_attr:
                continue

            new_src_node: str = cmds.duplicate(src_plug.split('.')[0])[0]
            src_plug = f'{new_src_node}.{src_attr_name}'
            dst_plug = f'{dst}.{dst_attr_name}'
            cmds.connectAttr(src_plug, dst_plug, force=True)

            # Mirror
            for i, channel in enumerate(MIRROR_CHANNELS):
                for j, axis in enumerate(MIRROR_AXIS):
                    if not mirror[i][j]:
                        continue

                    if channel + axis != dst_attr_name:
                        continue

                    cmds.scaleKey(
                        new_src_node,
                        includeUpperBound=False,
                        timeScale=1.0,
                        timePivot=1,
                        floatScale=1.0,
                        floatPivot=1.0,
                        valueScale=-1.0,
                        valuePivot=0.0,
                    )


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Copy Animation from specific options.'''
    selection: list[str] = cmds.ls(selection=True)
    settings: Settings = Settings.instance(__name__, True)
    src_nodes: list[str] = []
    dst_nodes: list[str] = []

    # Method = X:X
    if settings.method.value() == 0:
        if not selection or len(selection) < 2:
            _logger.error('Select more than two nodes to copy animation.')
            return

        if len(selection) % 2 != 0:
            _logger.error('Destination node does not match source node.')
            return

        half_num: int = int(len(selection) / 2)
        src_nodes = selection[0:half_num]
        dst_nodes = selection[half_num:]

    # Method = 1:X
    elif settings.method.value() == 1:
        if not selection or len(selection) < 2:
            _logger.error('Select more than two nodes to copy animation.')
            return

        src_nodes = [selection[0]] * len(selection[1:])
        dst_nodes = selection[1:]

    # Method = Search % Replace
    else:
        if not selection:
            _logger.error('Select node(s) to copy animation.')
            return

        for src_node in selection:
            dst_node = src_node.replace(
                settings.search.value(), settings.replace.value()
            )
            if not cmds.objExists(dst_node):
                _logger.warning('Does not exists %s', dst_node)
                continue

            src_nodes.append(src_node)
            dst_nodes.append(dst_node)

    if settings.hierarchy.value() == 1:
        src_children_nodes: list[str] = []
        dst_children_nodes: list[str] = []
        for src, dst in zip(src_nodes, dst_nodes):
            # temp:list[str] = cmds.listRelatives(src, children=True, allDescendents=True, path=True)or []
            # temp.reverse()
            src_children_nodes.extend(children_nodes(src))
            dst_children_nodes.extend(children_nodes(dst))

        src_nodes = src_children_nodes
        dst_nodes = dst_children_nodes

    mirror: list[list[bool]] = [
        [
            settings.reverse_tx.value(),
            settings.reverse_ty.value(),
            settings.reverse_tz.value(),
        ],
        [
            settings.reverse_rx.value(),
            settings.reverse_ry.value(),
            settings.reverse_rz.value(),
        ],
        [
            settings.reverse_sx.value(),
            settings.reverse_sy.value(),
            settings.reverse_sz.value(),
        ],
    ]

    apply(src_nodes, dst_nodes, mirror)
    _logger.info('Done.')
