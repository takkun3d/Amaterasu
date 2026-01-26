# ==============================================================================
#
# Add Attribute
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from typing import Any
from distutils.util import strtobool

try:
    from PySide2.QtCore import Qt, Slot, QObject
    from PySide2.QtGui import QValidator, QIntValidator, QDoubleValidator
    from PySide2.QtWidgets import QWidget, QCheckBox, QLineEdit

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot, QObject
        from PySide6.QtGui import QValidator, QIntValidator, QDoubleValidator
        from PySide6.QtWidgets import QWidget, QCheckBox, QLineEdit
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Add Attribute'
__version__: str = '1.20'
__doc__ = 'Add attribute to selected nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

MTOA_SHAPE_LIST: tuple[str, str, str] = ('mesh', 'nurbsSurface', 'nurbsCurve')
MTOA_ATTR_TAG: str = 'mtoa_constant_'
VECTOR_ATTR_TYPE: tuple[str, str, str] = ('X', 'Y', 'Z')
COLOR_ATTR_TYPE: tuple[str, str, str] = ('R', 'G', 'B')


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    mtoa: parser.Variant[bool] = parser.Variant(True)
    attr_name: parser.Variant[str] = parser.Variant('')
    make_attr: parser.Variant[int] = parser.Variant(0)
    data_type: parser.Variant[int] = parser.Variant(0)
    min_value: parser.Variant[str] = parser.Variant('')
    max_value: parser.Variant[str] = parser.Variant('')
    default_value: parser.Variant[str] = parser.Variant('0')
    enum_value: parser.Variant[str] = parser.Variant('')


class BoolValidator(QValidator):
    '''Boolean Validator'''

    def __init__(self, parent: QObject | None = None) -> None:
        '''Initialize'''
        super().__init__()

    def fixup(self, input: str) -> None:
        '''[Override] fixup'''
        self.parent().setText('off')

    def validate(self, input: str, pos: int) -> QValidator.State:
        '''[Override] validate'''
        if pos == 0:
            return QValidator.Acceptable

        try:
            strtobool(input)
            return QValidator.Acceptable

        except ValueError:
            return QValidator.Invalid


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
        self.resize(500, 300)

        option_widget: QWidget = self.option_widget()
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        self.__mtoa = QCheckBox('Insert mtoa_constant_', self)
        main_layout.addRow('', self.__mtoa)

        self.__attr_name = QLineEdit(self)
        main_layout.addRow(
            widgets.FormLabel('Attribute Name'), self.__attr_name
        )

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__make_attr: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__make_attr.set_labels(('Keyable', 'Displayable', 'Hidden'))
        main_layout.addRow(
            widgets.FormLabel('Make Attribute'), self.__make_attr
        )

        self.__data_type: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__data_type.set_labels(
            (
                'Vector',
                'Integer',
                'String',
                'Float',
                'Boolean',
                'Enum',
                'Color',
                'Border',
            )
        )
        self.__data_type.button_group().idClicked.connect(
            self.set_valid_options
        )
        main_layout.addRow(widgets.FormLabel('Data Type'), self.__data_type)

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__min_value = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Min Value'), self.__min_value)
        self.__min_value_index: int = main_layout.row_id()

        self.__max_value = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Max Value'), self.__max_value)
        self.__max_value_index: int = main_layout.row_id()

        self.__default_value = QLineEdit(self)
        main_layout.addRow(
            widgets.FormLabel('Default Value'), self.__default_value
        )
        self.__default_value_index: int = main_layout.row_id()

        self.__enum_value = QLineEdit(self)
        self.__enum_value.setPlaceholderText('Red:Green:Blue:')
        main_layout.addRow(widgets.FormLabel('Enum Value'), self.__enum_value)
        self.__enum_value_index: int = main_layout.row_id()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__mtoa.setChecked(settings.mtoa.value())
        self.__attr_name.setText(settings.attr_name.value())
        self.__make_attr.set_check_id(settings.make_attr.value())
        self.__data_type.set_check_id(settings.data_type.value())
        self.__min_value.setText(settings.min_value.value())
        self.__max_value.setText(settings.max_value.value())
        self.__default_value.setText(settings.default_value.value())
        self.__enum_value.setText(settings.enum_value.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.mtoa.set_value(self.__mtoa.isChecked())
        settings.attr_name.set_value(self.__attr_name.text())
        settings.make_attr.set_value(self.__make_attr.check_id())
        settings.data_type.set_value(self.__data_type.check_id())
        settings.min_value.set_value(self.__min_value.text())
        settings.max_value.set_value(self.__max_value.text())
        settings.default_value.set_value(self.__default_value.text())
        settings.enum_value.set_value(self.__enum_value.text())
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
        '''Apply[override]'''
        self.save_settings()
        main()

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        layout: widgets.FormLayout = self.option_widget().layout()
        layout.set_row_enabled(self.__min_value_index, False)
        layout.set_row_enabled(self.__max_value_index, False)
        layout.set_row_enabled(self.__default_value_index, False)
        layout.set_row_enabled(self.__enum_value_index, False)

        data_type: int = self.__data_type.check_id()
        if data_type == 1:
            layout.set_row_enabled(self.__min_value_index, True)
            self.__min_value.setValidator(QIntValidator())
            if self.__min_value.text():
                self.__min_value.setText(str(int(self.__min_value.text())))

            layout.set_row_enabled(self.__max_value_index, True)
            self.__max_value.setValidator(QIntValidator())
            if self.__max_value.text():
                self.__max_value.setText(str(int(self.__max_value.text())))

            layout.set_row_enabled(self.__default_value_index, True)
            self.__default_value.setValidator(QIntValidator())
            if self.__default_value.text():
                try:
                    value: str = str(int(self.__default_value.text()))
                except ValueError:
                    value = '0'
                self.__default_value.setText(value)

        elif data_type == 2:
            layout.set_row_enabled(self.__min_value_index, False)
            layout.set_row_enabled(self.__max_value_index, False)
            layout.set_row_enabled(self.__default_value_index, True)
            self.__default_value.setValidator(None)  # type: ignore

        elif data_type == 3:
            layout.set_row_enabled(self.__min_value_index, True)
            self.__min_value.setValidator(QDoubleValidator())
            if self.__min_value.text():
                self.__min_value.setText(str(float(self.__min_value.text())))

            layout.set_row_enabled(self.__max_value_index, True)
            self.__max_value.setValidator(QDoubleValidator())
            if self.__max_value.text():
                self.__max_value.setText(str(float(self.__max_value.text())))

            layout.set_row_enabled(self.__default_value_index, True)
            self.__default_value.setValidator(QDoubleValidator())
            if self.__default_value.text():
                try:
                    value = str(float(self.__default_value.text()))
                except ValueError:
                    value = '0'
                self.__default_value.setText(value)

        elif data_type == 4:
            layout.set_row_enabled(self.__min_value_index, False)
            layout.set_row_enabled(self.__max_value_index, False)
            layout.set_row_enabled(self.__default_value_index, True)
            self.__default_value.setValidator(BoolValidator())
            if self.__default_value.text():
                try:
                    value = str(strtobool(self.__default_value.text()))
                except ValueError:
                    value = '0'
                self.__default_value.setText(value)

        elif data_type == 5:
            layout.set_row_enabled(self.__enum_value_index, True)

        elif data_type == 7:
            pass


# ==============================================================================
#
# Functions
#
# ==============================================================================
def __value_flags(
    data_type: int,
    min_value: str = '',
    max_value: str = '',
    default_value: str = '',
) -> dict[str, int | float]:
    '''Return dict data of argument for maya.cmds.'''
    value_option: dict[str, int | float] = {}
    if data_type == 1:
        if min_value != '':
            value_option['minValue'] = int(min_value)
        if max_value != '':
            value_option['maxValue'] = int(max_value)
        if default_value != '':
            value_option['defaultValue'] = int(default_value)

    if data_type == 3:
        if min_value != '':
            value_option['minValue'] = float(min_value)
        if max_value != '':
            value_option['maxValue'] = float(max_value)
        if default_value != '':
            value_option['defaultValue'] = float(default_value)

    return value_option


def add_vector_attr(
    node: str,
    attr_name: str,
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add vector attribute.'''
    if not command_arg:
        command_arg = {}

    cmds.addAttr(node, longName=attr_name, attributeType='double3')
    for xyz in VECTOR_ATTR_TYPE:
        cmds.addAttr(
            node,
            longName=f'{attr_name}{xyz}',
            parent=attr_name,
            attributeType='double',
        )

    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    for xyz in VECTOR_ATTR_TYPE:
        cmds.setAttr(f'{node}.{attr_name}{xyz}', edit=True, **command_arg)
    return True


def add_long_attr(
    node: str,
    attr_name: str,
    min_value: str = '',
    max_value: str = '',
    default_value: str = '',
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add long attribute.'''
    if not command_arg:
        command_arg = {}

    value_flag: dict[str, int | float] = __value_flags(
        1, min_value, max_value, default_value
    )
    cmds.addAttr(node, longName=attr_name, attributeType='long', **value_flag)
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    return True


def add_string_attr(
    node: str,
    attr_name: str,
    default_value: str = '',
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add string attribute.'''
    if not command_arg:
        command_arg = {}
    cmds.addAttr(node, longName=attr_name, dataType='string')
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    if default_value:
        cmds.setAttr(f'{node}.{attr_name}', default_value, type='string')
    return True


def add_double_attr(
    node: str,
    attr_name: str,
    min_value: str = '',
    max_value: str = '',
    default_value: str = '',
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add doubule attribute.'''
    if not command_arg:
        command_arg = {}

    value_flag: dict[str, int | float] = __value_flags(
        3, min_value, max_value, default_value
    )
    cmds.addAttr(node, longName=attr_name, attributeType='double', **value_flag)
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    return True


def add_bool_attr(
    node: str,
    attr_name: str,
    default_value: str = '0',
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add bool attribute.'''
    if not command_arg:
        command_arg = {}
    cmds.addAttr(node, longName=attr_name, attributeType='bool')
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    if default_value:
        try:
            cmds.setAttr(f'{node}.{attr_name}', strtobool(default_value))
        except ValueError:
            cmds.setAttr(f'{node}.{attr_name}', False)
    return True


def add_enum_attr(
    node: str,
    attr_name: str,
    enum_value: str,
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add enum attribute.'''
    if not command_arg:
        command_arg = {}
    cmds.addAttr(
        node, longName=attr_name, attributeType='enum', enumName=enum_value
    )
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    return True


def add_color_attr(
    node: str,
    attr_name: str,
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add color attribute.'''
    if not command_arg:
        command_arg = {}

    cmds.addAttr(
        node, longName=attr_name, attributeType='float3', usedAsColor=True
    )
    for rgb in COLOR_ATTR_TYPE:
        cmds.addAttr(
            node,
            longName=f'{attr_name}{rgb}',
            parent=attr_name,
            attributeType='float',
        )

    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    for rgb in COLOR_ATTR_TYPE:
        cmds.setAttr(f'{node}.{attr_name}{rgb}', edit=True, **command_arg)
    return True


def add_border_attr(
    node: str,
    attr_name: str,
    command_arg: dict[str, Any] | None = None,
) -> bool:
    '''Add border attribute.'''
    if not command_arg:
        command_arg = {}

    # Copy label name from attribute name.
    enum_value: str = attr_name

    # Invalid characters.
    attr_name = attr_name.replace(' ', '_')
    attr_name = attr_name.replace('/', '_')

    cmds.addAttr(
        node,
        longName=attr_name,
        attributeType='enum',
        enumName=f'{enum_value}:',
        niceName='--------------------',
        minValue=0,
        maxValue=0,
    )
    cmds.setAttr(f'{node}.{attr_name}', edit=True, **command_arg)
    return True


def apply(
    nodes: list[str],
    mtoa: bool,
    attr_name: str,
    make_attr: int,  # 0 Keyable , 1 Displayable, 2 Hidden
    data_type: int,  # 0 Vec, 1 Int, 2 String, 3 Float, 4 Bool, 5 Enum, 6 Color
    min_value: str = '',
    max_value: str = '',
    default_value: str = '',
    enum_value: str = '',
) -> bool:
    '''Add attribute to target nodes.'''

    result: bool = True

    command_arg: dict[str, Any] = {}
    if make_attr == 0:
        command_arg['keyable'] = True
    elif make_attr == 1:
        command_arg['channelBox'] = True

    base_attr_name: str = attr_name
    for node in nodes:
        if mtoa:
            if cmds.objectType(node) == 'transform':
                shapes: list[str] | None = cmds.listRelatives(
                    node, shapes=True, path=True
                )
                if not shapes:
                    _logger.error('Failed get shape : %s', node)
                    result = False
                    continue

                node = shapes[0]

            if cmds.objectType(node) in MTOA_SHAPE_LIST:
                attr_name = f'{MTOA_ATTR_TAG}{base_attr_name}'

        if cmds.attributeQuery(attr_name, node=node, exists=True):
            _logger.error(
                'Found no valid items to add the attribute to. : %s', node
            )
            result = False
            continue

        if data_type == 0:
            add_vector_attr(node, attr_name, command_arg)

        elif data_type == 1:
            add_long_attr(
                node,
                attr_name,
                min_value,
                max_value,
                default_value,
                command_arg,
            )

        elif data_type == 2:
            add_string_attr(node, attr_name, default_value, command_arg)

        elif data_type == 3:
            add_double_attr(
                node,
                attr_name,
                min_value,
                max_value,
                default_value,
                command_arg,
            )
        elif data_type == 4:
            add_bool_attr(node, attr_name, default_value, command_arg)

        elif data_type == 5:
            add_enum_attr(node, attr_name, enum_value, command_arg)

        if data_type == 6:
            add_color_attr(node, attr_name, command_arg)

        if data_type == 7:
            add_border_attr(node, attr_name, command_arg)

    return result


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node to add attribute.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        selection,
        settings.mtoa.value(),
        settings.attr_name.value(),
        settings.make_attr.value(),
        settings.data_type.value(),
        settings.min_value.value(),
        settings.max_value.value(),
        settings.default_value.value(),
        settings.enum_value.value(),
    )
    if result:
        _logger.info('Done.')
