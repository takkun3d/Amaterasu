# ==============================================================================
#
# Renamer
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import re

try:
    from PySide2.QtCore import Qt, Slot, QItemSelectionModel, QModelIndex
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLineEdit,
        QSpinBox,
        QPushButton,
        QLabel,
        QGridLayout,
        QTreeView,
        QTabWidget,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot, QItemSelectionModel, QModelIndex
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QLineEdit,
            QSpinBox,
            QPushButton,
            QLabel,
            QGridLayout,
            QTreeView,
            QTabWidget,
        )
from maya import cmds
from maya.api import OpenMaya
from maya.app.renderSetup.model import utils
from maya.app.renderSetup.views import viewCmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Renamer'
__version__: str = '1.30'
__doc__ = 'A tool to rename selected nodes at once.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

RENDER_SETUP_NODES: tuple[str, ...] = (
    'renderSetupLayer',
    'collection',
    'connectionOverride',
    'shaderOverride',
    'materialOverride',
    'absOverride',
    'relOverride',
)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    find_str: parser.Variant[str] = parser.Variant('')
    replace_str: parser.Variant[str] = parser.Variant('')
    base_name: parser.Variant[str] = parser.Variant('')
    start_number: parser.Variant[str] = parser.Variant('0')
    padding: parser.Variant[int] = parser.Variant(1)
    suffix: parser.Variant[str] = parser.Variant('')
    insert_str: parser.Variant[str] = parser.Variant('')
    insert_to: parser.Variant[int] = parser.Variant(0)


class StringAndNumber(QWidget):
    '''String and number option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        form_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(form_layout)

        self.__base_name: QLineEdit = QLineEdit(self)
        form_layout.addRow(widgets.FormLabel('Base Name'), self.__base_name)

        self.__start_number: QLineEdit = QLineEdit(self)
        self.__start_number.setToolTip('Can be input string : [A-Z][a-z][0-9]')
        form_layout.addRow(widgets.FormLabel('Start'), self.__start_number)

        self.__padding: QSpinBox = QSpinBox(self)
        self.__padding.setRange(1, 256)
        self.__padding.setButtonSymbols(QSpinBox.NoButtons)
        self.__padding.setMinimumWidth(70)
        form_layout.addRow(widgets.FormLabel('Padding'), self.__padding)

        self.__suffix: QLineEdit = QLineEdit(self)
        form_layout.addRow(widgets.FormLabel('Suffix'), self.__suffix)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__base_name.setText(settings.base_name.value())
        self.__start_number.setText(settings.start_number.value())
        self.__padding.setValue(settings.padding.value())
        self.__suffix.setText(settings.suffix.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.base_name.set_value(self.__base_name.text())
        settings.start_number.set_value(self.__start_number.text())
        settings.padding.set_value(self.__padding.value())
        settings.suffix.set_value(self.__suffix.text())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    @widgets.undo
    def apply(self) -> None:
        '''Do it'''
        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)
        base_name: str = settings.base_name.value()
        start: str = settings.start_number.value()
        padding: int = settings.padding.value()
        suffix: str = settings.suffix.value()
        find: str = ''
        replace: str = ''
        number: int = 0
        if re.search('^[0-9]*$', start):
            find = '^.*$'
            replace = f'{base_name}@i<{padding}>{suffix}'
            number = int(start)

        elif re.search('^[a-zA-Z]*$', start):
            tag: str = 'j'
            if re.search('^[A-Z]*$', start):
                tag = 'J'

            find = '^.*$'
            replace = f'{base_name}@{tag}<{padding}>{suffix}'
            number = char_to_num(start.upper())

        else:
            _logger.error('Start has no legal characters.')
            return

        rename(find, replace, number)


class InsertStringTo(QWidget):
    '''Insert string to fist/last option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        form_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(form_layout)

        self.__insert_str: QLineEdit = QLineEdit(self)
        form_layout.addRow(widgets.FormLabel('String'), self.__insert_str)

        self.__insert_to: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__insert_to.set_labels(('First', 'Last'))
        form_layout.addRow(widgets.FormLabel('Insert to'), self.__insert_to)

        button = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__insert_str.setText(settings.insert_str.value())
        self.__insert_to.set_check_id(settings.insert_to.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.insert_str.set_value(self.__insert_str.text())
        settings.insert_to.set_value(self.__insert_to.check_id())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    @widgets.undo
    def apply(self) -> None:
        '''Do it'''
        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)
        find: str = ''
        replace: str = ''
        if settings.insert_to.value() == 0:
            find = '^.*$'
            replace = f'{settings.insert_str.value()}@g<0>'

        else:
            find = '^.*$'
            replace = f'@g<0>{settings.insert_str.value()}'

        rename(find, replace)


class FindAndReplace(QWidget):
    '''Find and replace option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        form_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(form_layout)

        self.__find_str: QLineEdit = QLineEdit(self)
        self.__find_str.setToolTip('Any character is *')
        form_layout.addRow(widgets.FormLabel('Find'), self.__find_str)

        self.__replace_str: QLineEdit = QLineEdit(self)
        form_layout.addRow(widgets.FormLabel('Replace'), self.__replace_str)

        button = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__find_str.setText(settings.find_str.value())
        self.__replace_str.setText(settings.replace_str.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.find_str.set_value(self.__find_str.text())
        settings.replace_str.set_value(self.__replace_str.text())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    @widgets.undo
    def apply(self) -> None:
        '''Do it'''
        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)
        find_str: str = settings.find_str.value()
        replace_str: str = settings.replace_str.value()
        rename(find_str.replace('*', '.*'), replace_str)


class NameRefiner(QWidget):
    '''A toolset for refining and standardizing node names in the scene.'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        button = QPushButton('Normalize Shape Name', self)
        button.clicked.connect(self.normalize_shape_name)
        main_layout.addWidget(button)

        button = QPushButton('Normalize Shading Engine Name', self)
        button.clicked.connect(self.normalize_shading_engine_name)
        main_layout.addWidget(button)

        button = QPushButton('Remove \'pasted__\'', self)
        button.clicked.connect(self.remove_pasted)
        main_layout.addWidget(button)

        main_layout.addStretch(True)

    @widgets.undo
    def normalize_shape_name(self) -> None:
        '''Do it'''
        normalize_shape_name_from_selection()

    @widgets.undo
    def normalize_shading_engine_name(self) -> None:
        '''Do it'''
        normalize_shading_engine_name_from_selection()

    @widgets.undo
    def remove_pasted(self) -> None:
        '''Do it'''
        remove_pasted()


class SameNameFinder(QWidget):
    '''Same name finder'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QGridLayout = QGridLayout(self)

        self.__model = QStandardItemModel(0, 1, self)
        self.__model.setHeaderData(0, Qt.Horizontal, 'Node')
        self.__model.itemChanged.connect(self.item_changed_callback)

        self.__selection_model = QItemSelectionModel(self.__model)
        self.__selection_model.selectionChanged.connect(self.select_callback)

        self.__view = QTreeView(self)
        self.__view.setSelectionMode(QTreeView.ExtendedSelection)
        self.__view.setAlternatingRowColors(True)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__selection_model)
        main_layout.addWidget(self.__view, 0, 0, 1, 2)

        button = QPushButton('Update', self)
        button.clicked.connect(self.update_view)
        main_layout.addWidget(button, 1, 0)

        button = QPushButton('Expand Selected', self)
        button.clicked.connect(self.expand_selected)
        main_layout.addWidget(button, 1, 1)

    @Slot()
    def update_view(self) -> None:
        '''Update my view'''
        self.__model.removeRows(0, self.__model.rowCount())
        same_nodes: list[str] = find_same_name_node()
        same_name_groups: dict[str, QStandardItem] = {}
        for node in same_nodes:
            short_name: str = node.split('|')[-1]
            if short_name not in same_name_groups:
                same_name_groups[short_name] = QStandardItem()
                same_name_groups[short_name].setEditable(False)
                same_name_groups[short_name].setText(short_name)
                same_name_groups[short_name].setData(f'*{short_name}*')
                # same_name_groups[short_name].setIcon()
                self.__model.appendRow(same_name_groups[short_name])

            item: QStandardItem = QStandardItem()
            item.setText(node)
            item.setData(node)
            item.setEditable(True)
            same_name_groups[short_name].setChild(
                same_name_groups[short_name].rowCount(), item
            )

    @Slot()
    def expand_selected(self) -> None:
        '''Expand selected in my view.'''
        indexes: list[QModelIndex] = self.__selection_model.selectedIndexes()
        for index in indexes:
            self.__view.expand(index)

    @widgets.undo
    def item_changed_callback(self, item: QStandardItem) -> None:
        '''Item changed callback.'''
        self.__model.blockSignals(True)
        try:
            new_name: str = cmds.rename(item.data(), item.text().split('|')[-1])
            item.setText(new_name)
            item.setData(new_name)
        except RuntimeError:
            _logger.error('Failed rename : %s', item.data())
            item.setText(item.data())

        self.__model.blockSignals(False)

    @widgets.undo
    def select_callback(self, *args: Any, **kwargs: Any) -> None:
        '''select callback.'''
        indexes: list[QModelIndex] = self.__selection_model.selectedIndexes()
        if not indexes:
            return

        nodes: list[str] = []
        for index in indexes:
            nodes.append(self.__model.itemFromIndex(index).data())

        if nodes:
            cmds.select(*nodes)
        else:
            cmds.select(clear=True)


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

        main_layout: QGridLayout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        option_widget.setLayout(main_layout)

        self.__string_and_number: StringAndNumber = StringAndNumber(self)
        self.__insert_string_to: InsertStringTo = InsertStringTo(self)
        self.__find_and_replace: FindAndReplace = FindAndReplace(self)

        self.__tab = QTabWidget(self)
        self.__tab.setDocumentMode(True)
        self.__tab.addTab(self.__string_and_number, 'String && Number')
        self.__tab.addTab(self.__insert_string_to, 'Insert String To')
        self.__tab.addTab(self.__find_and_replace, 'Find && Replace')
        self.__tab.addTab(NameRefiner(self), 'Refine')
        self.__tab.addTab(SameNameFinder(self), 'Same Name')
        main_layout.addWidget(self.__tab, 0, 0)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__string_and_number.load_settings()
        self.__insert_string_to.load_settings()
        self.__find_and_replace.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        self.__string_and_number.save_settings()
        self.__insert_string_to.save_settings()
        self.__find_and_replace.save_settings()
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


# ==============================================================================
#
# Functions
#
# ==============================================================================
def num_to_char(v: int, padding: int, is_lower: bool = False) -> str:
    '''Number to character'''
    result: str = ''
    abc: list[str] = [chr(x) for x in range(65, 91)]
    while v > 0:
        result = abc[(v % len(abc)) - 1] + result
        v = int((v - 1) / len(abc))

    if len(result) < padding:
        d: int = padding - len(result)
        result = ('A' * d) + result

    if is_lower:
        result = result.lower()

    return result


def char_to_num(chars: str) -> int:
    '''Character to number'''
    num: int = 0
    for c in chars:
        num = num * 26 + (ord(c) - 64)
    return num


def normalize_shape_name(node: str) -> None:
    '''Normalize shape name from transform.'''
    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        return

    is_solo: bool = len(shapes) == 1
    for i, shape in enumerate(shapes):
        try:
            short_name: str = node.split('|')[-1]
            if is_solo:
                cmds.rename(shape, f'{short_name}Shape')
            else:
                cmds.rename(shape, f'{short_name}{i}Shape')

        except RuntimeError as error:
            _logger.error('Failed to rename : %s', error)


def normalize_shape_name_from_selection() -> None:
    '''Normalize shape name from transform.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select nodes to normalize shape name.')
        return

    for node in selection:
        normalize_shape_name(node)

    _logger.info('Done.')


def normalize_shading_engine_name(node: str) -> None:
    '''Normalize shading engine name from material.'''
    # Ignore default matrials.
    if node in [
        'lambert1',
        'particleCloud1',
        'shaderGlow1',
        'standardSurface1',
    ]:
        return

    shading_engine: list[str] = (
        cmds.listConnections(
            node, source=False, destination=True, type='shadingEngine'
        )
        or []
    )
    if not shading_engine:
        return

    try:
        cmds.rename(shading_engine[0], f'{node}SG')
    except RuntimeError as error:
        _logger.error('Failed to rename : %s', error)


def normalize_shading_engine_name_from_selection() -> None:
    '''Normalize shading engine name from transform.'''
    selection: list[str] = cmds.ls(selection=True, materials=True)
    if not selection:
        _logger.error('Select nodes to normalize shading engine name.')
        return

    for node in selection:
        normalize_shading_engine_name(node)

    _logger.info('Done.')


def remove_pasted() -> None:
    '''Removes the 'pasted__' prefix from all scene nodes.'''
    cmds.select('pasted__*')
    cmds.select('pasted__*', add=True, allDependencyNodes=True)
    nodes: list[str] = cmds.ls(selection=True)
    if not nodes:
        _logger.info('No \'pasted__\' nodes found.')

    rename('pasted__', '')
    _logger.info('Done.')


def find_same_name_node() -> list[str]:
    '''Find same name node in scene.'''
    result: list[str] = []
    iter_dag: OpenMaya.MItDag = OpenMaya.MItDag(
        OpenMaya.MItDag.kDepthFirst, OpenMaya.MFn.kBase
    )
    dag_fn: OpenMaya.MFnDagNode = OpenMaya.MFnDagNode()
    while not iter_dag.isDone():
        dag_fn.setObject(iter_dag.currentItem())
        if not dag_fn.isInstanced():
            path: OpenMaya.MDagPath = dag_fn.getPath()
            node_name: str = path.partialPathName()
            if len(node_name.split('|')) >= 2:
                result.append(node_name)

        iter_dag.next()
    return result


def expression_to_string(
    string: str, find: str, replace: str, number: int = 0
) -> str:
    '''Return new name fron expression.'''
    # @g<*>
    for i in range(9):
        u2: re.Match[str] | None = re.search(rf'@g<[{i}]>', replace)
        if u2:
            myid = int(re.sub(r'@g<|>', '', u2.group(0)))
            match_value: re.Match[str] | None = re.search(find, string)
            if match_value:
                value: str = match_value.group(myid)
                replace = re.sub(rf'@g<{i}>', value, replace)

            else:
                replace = re.sub(rf'@g<{i}>', '', replace)

    temp: str = re.sub(find, replace, string)

    # @u<*>
    for i in range(9):
        upper_cmd: re.Match[str] | None = re.search(rf'@u<[{i}]>', temp)
        if upper_cmd:
            myid = int(re.sub(r'@u<|>', '', upper_cmd.group(0)))
            match_value = re.search(find, string)
            if match_value:
                value = match_value.group(myid).upper()
            temp = re.sub(rf'@u<{i}>', value, temp)

    # @l<*>
    for i in range(9):
        lower_cmd: re.Match[str] | None = re.search(rf'@l<[{i}]>', temp)
        if lower_cmd:
            myid = int(re.sub(r'@l<|>', '', lower_cmd.group(0)))
            match_value = re.search(find, string)
            if match_value:
                value = match_value.group(myid).lower()
            temp = re.sub(rf'@l<{i}>', value, temp)

    # @ul<*>
    for i in range(9):
        swap_cmd: re.Match[str] | None = re.search(rf'@ul<[{i}]>', temp)
        if swap_cmd:
            myid = int(re.sub(r'@ul<|>', '', swap_cmd.group(0)))
            match_value = re.search(find, string)
            if match_value:
                value = match_value.group(myid).swapcase()
            temp = re.sub(rf'@ul<{i}>', value, temp)

    # @i<*>
    number_cmd: re.Match[str] | None = re.search(r'@i<[0-9]*>', temp)
    if number_cmd:
        padding: str = re.sub(r'@i<|>', '', number_cmd.group(0))
        number_format: str = f'%.{padding}i'
        replace_str: str = number_format % number
        temp = re.sub(rf'@i<{padding}>', replace_str, temp)

    # @J<*>
    number_cmd = re.search(r'@J<[0-9]*>', temp)
    if number_cmd:
        padding_num: int = int(re.sub(r'@J<|>', '', number_cmd.group(0)))
        replace_str = num_to_char(number, padding_num)
        temp = re.sub(rf'@J<{padding_num}>', replace_str, temp)

    # @j<*>
    number_cmd = re.search(r'@j<[0-9]*>', temp)
    if number_cmd:
        padding_num = int(re.sub(r'@j<|>', '', number_cmd.group(0)))
        replace_str = num_to_char(number, padding_num, True)
        temp = re.sub(rf'@j<{padding_num}>', replace_str, temp)

    return temp


def rename(find: str, replace: str, number: int = 0) -> None:
    '''Renaem nodes form selection'''
    default_number: int = number
    has_error: bool = False

    selection = OpenMaya.MGlobal.getActiveSelectionList(True)
    rs_selection: list[str] = viewCmds.getSelection(False, False, False, False)
    if not selection and not rs_selection:
        _logger.error('Select nodes or render layer to rename.')
        return

    # From Selection
    for i in range(selection.length()):
        try:
            # Dag Node
            full_path: str = selection.getDagPath(i).fullPathName()
            short_name: str = full_path.split('|')[-1]

        except TypeError:
            # DG Node
            mobject: OpenMaya.MObject = selection.getDependNode(i)
            full_path = OpenMaya.MFnDependencyNode(mobject).name()
            short_name = full_path

        new_name: str = expression_to_string(short_name, find, replace, number)
        number += 1
        if short_name == new_name:
            continue

        try:
            cmds.rename(full_path, new_name)

        except RuntimeError as error:
            _logger.error('Failed to rename : %s', error)
            has_error = True

    # From Render Setup Nodes
    number = default_number
    for i in range(len(rs_selection)):
        new_name = expression_to_string(rs_selection[i], find, replace, number)
        number += 1
        if rs_selection[i] == new_name:
            continue

        try:
            layer = utils.nameToUserNode(rs_selection[i])
            layer.setName(new_name)

        except RuntimeError as error:
            _logger.error('Failed to rename : %s', error)
            has_error = True

    if not has_error:
        _logger.info('Done')


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
