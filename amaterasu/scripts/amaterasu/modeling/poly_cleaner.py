# ==============================================================================
#
# Poly Cleaner
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import itertools

try:
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QCheckBox,
        QPushButton,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QCheckBox,
            QPushButton,
            QMessageBox,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Poly Cleaner'
__version__: str = '1.00'
__doc__ = 'Remove dust data from selected polygons.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    unlock_transformations: parser.Variant[bool] = parser.Variant(True)
    break_connections: parser.Variant[bool] = parser.Variant(True)
    freeze_transformations: parser.Variant[bool] = parser.Variant(True)
    reset_transformations: parser.Variant[bool] = parser.Variant(True)
    delete_history: parser.Variant[bool] = parser.Variant(True)
    delete_user_defined_attr: parser.Variant[bool] = parser.Variant(True)
    remove_intermediate_obj: parser.Variant[bool] = parser.Variant(True)
    freeze_vertex: parser.Variant[bool] = parser.Variant(True)


class OptionItem(QWidget):
    clicked = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__check: QCheckBox = QCheckBox(self)
        layout.addWidget(self.__check, True)

        self.__apply: QPushButton = QPushButton(self)
        self.__apply.setMinimumWidth(80)
        self.__apply.clicked.connect(self.clicked)
        layout.addWidget(self.__apply, False)

    def set_label_text(self, text: str) -> None:
        '''Set text to label.'''
        self.__check.setText(text)

    def set_button_text(self, text: str) -> None:
        '''Set text to button.'''
        self.__apply.setText(text)

    def set_checked(self, value: bool) -> None:
        '''Set check.'''
        self.__check.setChecked(value)

    def is_checked(self) -> bool:
        '''Return checked.'''
        return self.__check.isChecked()


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

        # ======================================================================
        # Widget
        # ======================================================================
        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)

        self.__freeze_vertex: OptionItem = OptionItem(self)
        self.__freeze_vertex.set_label_text('Freeze Vertex')
        self.__freeze_vertex.set_button_text('Optimize Now')
        self.__freeze_vertex.clicked.connect(self.freeze_vertex_callback)
        main_layout.addWidget(self.__freeze_vertex)

        self.__unlock_transformations: OptionItem = OptionItem(self)
        self.__unlock_transformations.set_label_text('Unlock Transformations')
        self.__unlock_transformations.set_button_text('Optimize Now')
        self.__unlock_transformations.clicked.connect(
            self.unlock_transformations_callback
        )
        main_layout.addWidget(self.__unlock_transformations)

        self.__break_connections: OptionItem = OptionItem(self)
        self.__break_connections.set_label_text('Break Connections')
        self.__break_connections.set_button_text('Optimize Now')
        self.__break_connections.clicked.connect(self.break_connectionsCallback)
        main_layout.addWidget(self.__break_connections)

        self.__freeze_transformations: OptionItem = OptionItem(self)
        self.__freeze_transformations.set_label_text('Freeze Transformations')
        self.__freeze_transformations.set_button_text('Optimize Now')
        self.__freeze_transformations.clicked.connect(
            self.freeze_transformations_callback
        )
        main_layout.addWidget(self.__freeze_transformations)

        self.__reset_transformations: OptionItem = OptionItem(self)
        self.__reset_transformations.set_label_text('Reset Transformations')
        self.__reset_transformations.set_button_text('Optimize Now')
        self.__reset_transformations.clicked.connect(
            self.reset_transformations_callback
        )
        main_layout.addWidget(self.__reset_transformations)

        self.__delete_history: OptionItem = OptionItem(self)
        self.__delete_history.set_label_text('Delete History')
        self.__delete_history.set_button_text('Optimize Now')
        self.__delete_history.clicked.connect(self.delete_history_callback)
        main_layout.addWidget(self.__delete_history)

        self.__delete_user_defined_attr: OptionItem = OptionItem(self)
        self.__delete_user_defined_attr.set_label_text(
            'Delete User Defined Attribute'
        )
        self.__delete_user_defined_attr.set_button_text('Optimize Now')
        self.__delete_user_defined_attr.clicked.connect(
            self.delete_user_defined_attr_callback
        )
        main_layout.addWidget(self.__delete_user_defined_attr)

        self.__remove_intermediate_obj: OptionItem = OptionItem(self)
        self.__remove_intermediate_obj.set_label_text(
            'Remove Intermediate Objects'
        )
        self.__remove_intermediate_obj.set_button_text('Optimize Now')
        self.__remove_intermediate_obj.clicked.connect(
            self.removeIntermediateObjCallback
        )
        main_layout.addWidget(self.__remove_intermediate_obj)

        # button: QPushButton = QPushButton('Check Facets Assign', self)
        # button.clicked.connect(self.check_facets_assign_callback)
        # main_layout.addWidget(button)
        main_layout.addStretch()

        # ======================================================================
        # Menu
        # ======================================================================
        menu_bar = self.menu_bar()
        view_menu = menu_bar.addMenu('Tool')
        menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)
        action = view_menu.addAction('Check Facets Assign')
        action.triggered.connect(self.check_facets_assign_callback)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__freeze_vertex.set_checked(settings.freeze_vertex.value())
        self.__unlock_transformations.set_checked(
            settings.unlock_transformations.value()
        )
        self.__break_connections.set_checked(settings.break_connections.value())
        self.__freeze_transformations.set_checked(
            settings.freeze_transformations.value()
        )
        self.__reset_transformations.set_checked(
            settings.reset_transformations.value()
        )
        self.__delete_history.set_checked(settings.delete_history.value())
        self.__delete_user_defined_attr.set_checked(
            settings.delete_user_defined_attr.value()
        )
        self.__remove_intermediate_obj.set_checked(
            settings.remove_intermediate_obj.value()
        )

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.freeze_vertex.set_value(self.__freeze_vertex.is_checked())
        settings.unlock_transformations.set_value(
            self.__unlock_transformations.is_checked()
        )
        settings.break_connections.set_value(
            self.__break_connections.is_checked()
        )
        settings.freeze_transformations.set_value(
            self.__freeze_transformations.is_checked()
        )
        settings.reset_transformations.set_value(
            self.__reset_transformations.is_checked()
        )
        settings.delete_history.set_value(self.__delete_history.is_checked())
        settings.delete_user_defined_attr.set_value(
            self.__delete_user_defined_attr.is_checked()
        )
        settings.remove_intermediate_obj.set_value(
            self.__remove_intermediate_obj.is_checked()
        )
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
    def freeze_vertex_callback(self) -> None:
        '''Freeze vertex.'''
        selection: list[str] = self.__selection_list()
        if selection:
            freeze_vertex(selection)
            _logger.info('Done.')

    @widgets.undo
    def unlock_transformations_callback(self) -> None:
        '''Unlock transformations.'''
        selection: list[str] = self.__selection_list()
        if selection:
            unlock_transformations(selection)
            _logger.info('Done.')

    @widgets.undo
    def break_connectionsCallback(self) -> None:
        '''Break connections.'''
        selection: list[str] = self.__selection_list()
        if selection:
            break_connections(selection)
            _logger.info('Done.')

    @widgets.undo
    def freeze_transformations_callback(self) -> None:
        '''Freeze transformations.'''
        selection: list[str] = self.__selection_list()
        if selection:
            freeze_transformations(selection)
            _logger.info('Done.')

    @widgets.undo
    def reset_transformations_callback(self) -> None:
        '''Reset transformations.'''
        selection: list[str] = self.__selection_list()
        if selection:
            reset_transformations(selection)
            _logger.info('Done.')

    @widgets.undo
    def delete_history_callback(self) -> None:
        '''Delete history.'''
        selection: list[str] = self.__selection_list()
        if selection:
            delete_history(selection)
            _logger.info('Done.')

    @widgets.undo
    def delete_user_defined_attr_callback(self) -> None:
        '''Delete user defined attr.'''
        selection: list[str] = self.__selection_list()
        if selection:
            delete_user_defined_attribute(selection)
            _logger.info('Done.')

    @widgets.undo
    def removeIntermediateObjCallback(self) -> None:
        '''Remove intermediate object.'''
        selection: list[str] = self.__selection_list()
        if selection:
            remove_intermediate_objects(selection)
            _logger.info('Done.')

    @widgets.undo
    def check_facets_assign_callback(self) -> None:
        '''Check facets assign.'''
        result: list[str] = check_facets_assign()
        if result:
            QMessageBox.critical(
                self, __product__, 'Selected that, so correct it.'
            )
        else:
            QMessageBox.information(self, __product__, 'Done. No problem.')

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        main()

    def __selection_list(self) -> list[str]:
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            _logger.error('Select objects to cleanup')
            return []

        return selection


# ==============================================================================
#
# Functions
#
# ==============================================================================
def freeze_vertex(nodes: list[str]) -> bool:
    '''Freeze vertex.'''
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != 'mesh':
            continue

        temp: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        temp_mesh: str = cmds.listRelatives(temp, shapes=True, path=True)[0]

        empty_mesh: str = cmds.createNode('mesh')
        empty_mesh_transform: str = cmds.listRelatives(
            empty_mesh, parent=True, path=True
        )[0]

        cmds.connectAttr(f'{empty_mesh}.outMesh', f'{shape}.inMesh', force=True)
        cmds.disconnectAttr(f'{empty_mesh}.outMesh', f'{shape}.inMesh')
        cmds.connectAttr(f'{empty_mesh}.pnts', f'{shape}.pnts', force=True)
        cmds.disconnectAttr(f'{empty_mesh}.pnts', f'{shape}.pnts')
        cmds.connectAttr(f'{temp_mesh}.outMesh', f'{shape}.inMesh', force=True)
        cmds.disconnectAttr(f'{temp_mesh}.outMesh', f'{shape}.inMesh')

        cmds.delete(temp)
        cmds.delete(empty_mesh_transform)

    if nodes:
        cmds.select(*nodes)

    return True


def unlock_transformations(nodes: list[str]) -> bool:
    '''Unlock transformations.'''
    for node in nodes:
        attrs: list[str] = ['t', 'r', 's']
        axiss: list[str] = ['', 'x', 'y', 'z']
        for attr, axis in itertools.product(attrs, axiss):
            try:
                cmds.setAttr(f'{node}.{attr}{axis}', lock=False, keyable=True)

            except RuntimeError:
                _logger.error('Failed to unlock attribute : %s', node)

    return True


def break_connections(nodes: list[str]) -> bool:
    '''Break connections.'''
    for node in nodes:
        attrs: list[str] = ['t', 'r', 's']
        axiss: list[str] = ['', 'x', 'y', 'z']
        for attr, axis in itertools.product(attrs, axiss):
            dst_plug: str = f'{node}.{attr}{axis}'
            if not cmds.connectionInfo(dst_plug, id=True):
                continue

            src_plug: str = cmds.connectionInfo(
                dst_plug, sourceFromDestination=True
            )
            try:
                cmds.disconnectAttr(src_plug, dst_plug)

            except RuntimeError:
                _logger.error('Failed to break connection : %s', dst_plug)

    return True


def freeze_transformations(nodes: list[str]) -> bool:
    '''Freeze transformations'''
    for node in nodes:
        try:
            cmds.makeIdentity(
                node,
                apply=True,
                translate=True,
                rotate=True,
                scale=True,
                normal=False,
            )

        except RuntimeError:
            _logger.error('Failed to freeze transform : %s', node)

    return True


def reset_transformations(nodes: list[str]) -> bool:
    '''Reset transformations.'''
    for node in nodes:
        try:
            cmds.makeIdentity(
                node, apply=False, translate=True, rotate=True, scale=True
            )

        except RuntimeError:
            _logger.error('Failed to reset transform : %s', node)

    return True


def delete_history(nodes: list[str]) -> bool:
    '''Delete history.'''
    for node in nodes:
        try:
            cmds.delete(node, channels=True)

        except RuntimeError:
            _logger.error('Failed to delete node : %s', node)

    return True


def delete_user_defined_attribute(nodes: list[str]) -> bool:
    '''Delete user defined attribute.'''
    for node in nodes:
        attrs: list[str] = cmds.listAttr(node, userDefined=True) or []
        for attr in attrs:
            try:
                cmds.deleteAttr(node, attribute=attr)

            except RuntimeError:
                _logger.error('Failed to delete attribute : %s', node)

        shapes = cmds.listRelatives(node, shapes=True, path=True) or []
        delete_user_defined_attribute(shapes)

    return True


def remove_intermediate_objects(nodes: list[str]) -> bool:
    '''Remove intermediate objects.'''
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        for shape in shapes:
            if cmds.getAttr(f'{shape}.io'):
                cmds.delete(shape)

    return True


def check_facets_assign() -> list[str]:
    '''Check object of facets assign.'''
    result: list[str] = []
    materials: list[str] = cmds.ls(materials=True)

    for material in materials:
        facets_assign: list[str] = []
        cmds.hyperShade(objects=material)
        for dag_path in cmds.ls(selection=True):
            if len(dag_path.split('.')) != 1:
                facets_assign.append(dag_path)

        if facets_assign:
            result += facets_assign

    if result:
        cmds.select(*result)
    else:
        cmds.select(clear=True)

    return result


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select objects to cleanup')
        return

    settings: Settings = Settings.instance(__name__, True)
    if settings.unlock_transformations.value():
        unlock_transformations(selection)

    if settings.break_connections.value():
        break_connections(selection)

    if settings.freeze_transformations.value():
        freeze_transformations(selection)

    if settings.reset_transformations.value():
        reset_transformations(selection)

    if settings.delete_history.value():
        delete_history(selection)

    if settings.delete_user_defined_attr.value():
        delete_user_defined_attribute(selection)

    if settings.remove_intermediate_obj.value():
        remove_intermediate_objects(selection)

    if settings.freeze_vertex.value():
        freeze_vertex(selection)

    _logger.info('Done.')
