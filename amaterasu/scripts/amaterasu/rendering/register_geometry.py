# ==============================================================================
#
# Register Geometry
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, Signal, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
        )
from maya import cmds
from maya.app.renderSetup.model import utils
from maya.app.renderSetup.views import viewCmds
from maya.app.renderSetup.model.expandedState import setExpandedStateValue
from maya.app.renderSetup.model.childNode import ChildNode
from maya.app.renderSetup.model.renderLayer import RenderLayer
from maya.app.renderSetup.model import collection
from maya.app.renderSetup.model.collection import Collection
from maya.app.renderSetup.model import selector
from maya.app.renderSetup.model.selector import SimpleSelector
from maya.app.renderSetup.model.override import AbsUniqueOverride
from maya.app.renderSetup.model.connectionOverride import MaterialOverride
from maya.app.renderSetup.model import typeIDs
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Register Geometry'
__version__: str = '1.01'
__doc__ = 'Register geometry to the selected layers.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

RENDERABLE_GEOMETRY_TAG: str = 'AMATERASU_RENDERABLE_GEOMETRY'
HIDE_GEOMETRY_TAG: str = 'AMATERASU_HIDE_GEOMETRY'
MATTE_OUT_GEOMETRY_SW_TAG: str = 'AMATERASU_MATTE_OUT_GEOMETRY_SW'
MATTE_OUT_GEOMETRY_AIMATTE_TAG: str = 'AMATERASU_MATTE_OUT_GEOMETRY_AIMATTE'
DISABLE_PRIMARY_VISIBILITY_TAG: str = 'DISABLE_PRIMARY_VISIBILITY'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class ContainerWidget(QWidget):
    '''Container Widget'''

    apply_clicked = Signal()
    add_clicked = Signal()
    remove_clicked = Signal()
    delete_clicked = Signal()

    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_label: widgets.FormLabel = widgets.FormLabel(label, self)
        main_layout.addWidget(self.__form_label, False)

        main_layout.addWidget(QWidget(self), True)

        self.__apply_btn: widgets.IconButton = widgets.IconButton(self)
        self.__apply_btn.set_icon('a_apply.png')
        self.__apply_btn.setFixedSize(QSize(24, 24))
        self.__apply_btn.clicked.connect(self.apply_callback)
        main_layout.addWidget(self.__apply_btn, False)

        self.__add_btn: widgets.IconButton = widgets.IconButton(self)
        self.__add_btn.set_icon('a_add.png')
        self.__add_btn.setFixedSize(QSize(24, 24))
        self.__add_btn.clicked.connect(self.add_callback)
        main_layout.addWidget(self.__add_btn, False)

        self.__remove_btn: widgets.IconButton = widgets.IconButton(self)
        self.__remove_btn.set_icon('a_remove.png')
        self.__remove_btn.setFixedSize(QSize(24, 24))
        self.__remove_btn.clicked.connect(self.remove_callback)
        main_layout.addWidget(self.__remove_btn, False)

        self.__delete_btn: widgets.IconButton = widgets.IconButton(self)
        self.__delete_btn.set_icon('a_trash.png')
        self.__delete_btn.setFixedSize(QSize(24, 24))
        self.__delete_btn.clicked.connect(self.delete_callback)
        main_layout.addWidget(self.__delete_btn, False)

    def label(self) -> str:
        '''Return label text.'''
        return self.__form_label.text()

    def set_label(self, label: str) -> None:
        '''Set label text.'''
        self.__form_label.setText(label)

    def label_widget(self) -> widgets.FormLabel:
        '''Return label widget.'''
        return self.__form_label

    def apply_button(self) -> widgets.IconButton:
        '''Return apply button.'''
        return self.__apply_btn

    def remove_button(self) -> widgets.IconButton:
        '''Return remove button.'''
        return self.__remove_btn

    def apply_callback(self) -> None:
        '''Emit signal of apply.'''
        self.apply_clicked.emit()

    def add_callback(self) -> None:
        '''Emit signal of add.'''
        self.add_clicked.emit()

    def remove_callback(self) -> None:
        '''Emit signal of remove.'''
        self.remove_clicked.emit()

    def delete_callback(self) -> None:
        '''Emit signal of delete.'''
        self.delete_clicked.emit()


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

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())

        widget: ContainerWidget = ContainerWidget('Renderable Geometry', self)
        widget.apply_clicked.connect(self.register_renderable_geometry_callback)
        widget.add_clicked.connect(self.add_renderable_geometry_callback)
        widget.remove_clicked.connect(self.remove_renderable_geometry_callback)
        widget.delete_clicked.connect(self.delete_renderable_geometry_callback)
        main_layout.addWidget(widget)

        widget = ContainerWidget('Hide Geometry', self)
        widget.apply_clicked.connect(self.register_hide_geometry_callback)
        widget.add_clicked.connect(self.add_hide_geometry_callback)
        widget.remove_clicked.connect(self.remove_hide_geometry_callback)
        widget.delete_clicked.connect(self.delete_hide_geometry_callback)
        main_layout.addWidget(widget)

        main_layout.addWidget(widgets.HorizontalLine(self))

        widget = ContainerWidget('Matte out Geometry(SW)', self)
        widget.apply_clicked.connect(
            self.register_matte_out_geometry_sw_callback
        )
        widget.add_clicked.connect(self.add_matte_out_geometry_sw_callback)
        widget.remove_clicked.connect(
            self.remove_matte_out_geometry_sw_callback
        )
        widget.delete_clicked.connect(
            self.delete_matte_out_geometry_sw_callback
        )
        main_layout.addWidget(widget)

        widget = ContainerWidget('Matte out Geometry(Arnold)', self)
        widget.apply_clicked.connect(
            self.register_matte_out_geometry_aimatte_callback
        )
        widget.add_clicked.connect(self.add_matte_out_geometry_aimatte_callback)
        widget.remove_clicked.connect(
            self.remove_matte_out_geometry_aimatte_callback
        )
        widget.delete_clicked.connect(
            self.delete_matte_out_geometry_aimatte_callback
        )
        main_layout.addWidget(widget)

        main_layout.addWidget(widgets.HorizontalLine(self))

        widget = ContainerWidget('Disable Primary Visibility', self)
        widget.apply_clicked.connect(
            self.register_disable_primary_visibility_callback
        )
        widget.add_clicked.connect(self.add_disable_primary_visibility_callback)
        widget.remove_clicked.connect(
            self.remove_disable_primary_visibility_callback
        )
        widget.delete_clicked.connect(
            self.delete_disable_primary_visibility_callback
        )
        main_layout.addWidget(widget)

        main_layout.addStretch(True)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
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
    def register_renderable_geometry_callback(self) -> None:
        '''Register renderable geometry callback.'''
        register_renderable_geometry()

    @widgets.undo
    def add_renderable_geometry_callback(self) -> None:
        '''Add renderable geometry callback.'''
        add_renderable_geometry()

    @widgets.undo
    def remove_renderable_geometry_callback(self) -> None:
        '''Remove renderable geometry callback.'''
        remove_renderable_geometry()

    @widgets.undo
    def delete_renderable_geometry_callback(self) -> None:
        '''Delete renderable geometry callback.'''
        delete_renderable_geometry()

    @widgets.undo
    def register_hide_geometry_callback(self) -> None:
        '''Register hide geometry callback.'''
        register_hide_geometry()

    @widgets.undo
    def add_hide_geometry_callback(self) -> None:
        '''Add hide geometry callback.'''
        add_hide_geometry()

    @widgets.undo
    def remove_hide_geometry_callback(self) -> None:
        '''Remove hide geometry callback.'''
        remove_hide_geometry()

    @widgets.undo
    def delete_hide_geometry_callback(self) -> None:
        '''Delete hide geometry callback.'''
        delete_hide_geometry()

    @widgets.undo
    def register_matte_out_geometry_sw_callback(self) -> None:
        '''Register matte out geometry (SW) callback.'''
        register_matte_out_geometry_sw()

    @widgets.undo
    def add_matte_out_geometry_sw_callback(self) -> None:
        '''Add matte out geometry (SW) callback.'''
        add_matte_out_geometry_sw()

    @widgets.undo
    def remove_matte_out_geometry_sw_callback(self) -> None:
        '''Remove matte out geometry (SW) callback.'''
        remove_matte_out_geometry_sw()

    @widgets.undo
    def delete_matte_out_geometry_sw_callback(self) -> None:
        '''Delete matte out geometry (SW) callback.'''
        delete_matte_out_geometry_sw()

    @widgets.undo
    def register_matte_out_geometry_aimatte_callback(self) -> None:
        '''Register matte out geometry (aiMatte) callback.'''
        register_matte_out_geometry_aimatte()

    @widgets.undo
    def add_matte_out_geometry_aimatte_callback(self) -> None:
        '''Add matte out geometry (aiMatte) callback.'''
        add_matte_out_geometry_aimatte()

    @widgets.undo
    def remove_matte_out_geometry_aimatte_callback(self) -> None:
        '''Remove matte out geometry (aiMatte) callback.'''
        remove_matte_out_geometry_aimatte()

    @widgets.undo
    def delete_matte_out_geometry_aimatte_callback(self) -> None:
        '''Delete matte out geometry (aiMatte) callback.'''
        delete_matte_out_geometry_aimatte()

    @widgets.undo
    def register_disable_primary_visibility_callback(self) -> None:
        '''Register matte out geometry (aiMatte) callback.'''
        register_disable_primary_visibility()

    @widgets.undo
    def add_disable_primary_visibility_callback(self) -> None:
        '''Add matte out geometry (aiMatte) callback.'''
        add_disable_primary_visibility()

    @widgets.undo
    def remove_disable_primary_visibility_callback(self) -> None:
        '''Remove matte out geometry (aiMatte) callback.'''
        remove_disable_primary_visibility()

    @widgets.undo
    def delete_disable_primary_visibility_callback(self) -> None:
        '''Delete matte out geometry (aiMatte) callback.'''
        delete_disable_primary_visibility()


# ==============================================================================
#
# Functions
#
# ==============================================================================
# Utility
def selected_render_layer() -> list[RenderLayer]:
    '''Return list of layers selected on window.'''
    selected_layers: list[str] = viewCmds.getSelection(
        True, False, False, False
    )
    if not selected_layers:
        return []

    return [utils.nameToUserNode(x) for x in selected_layers]


def find_objects_with_note(
    objects: list[ChildNode], note: str
) -> list[ChildNode]:
    '''Search for objects with a specific note.'''
    result: list[ChildNode] = []
    for object_ in objects:
        if object_.getNotes() == note:
            result.append(object_)
    return result


# ------------------------------------------------------------------------------
# Register Geometry
def register_renderable_geometry() -> bool:
    '''Register renderable geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer registration.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node registration.')
        return False

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == RENDERABLE_GEOMETRY_TAG:
                collection.delete(c)

        collect = layer.createCollection('Renderable_Geometry')
        collect.setNotes(RENDERABLE_GEOMETRY_TAG)
        setExpandedStateValue(collect, False)

        selector_: SimpleSelector = collect.getSelector()
        selector_.setFilterType(selector.Filters.kTransforms)
        selector_.staticSelection.set(nodes)

        override_: AbsUniqueOverride = collect.createAbsoluteOverride(
            nodes[0], 'visibility'
        )
        override_.setAttrValue(True)
    return True


def add_renderable_geometry() -> bool:
    '''Add renderable geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer addition.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node addition.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == RENDERABLE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            register_renderable_geometry()
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.add(nodes)

    return True


def remove_renderable_geometry() -> bool:
    '''Remove renderable geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer removal.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node removal.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == RENDERABLE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.remove(nodes)

    return True


def delete_renderable_geometry() -> bool:
    '''delete renderable geometry.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node deletion.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == RENDERABLE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            continue

        collection.delete(collect)

    return True


# ------------------------------------------------------------------------------
# Hide Geometry
def register_hide_geometry() -> bool:
    '''Register hide geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer registration.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node registration.')
        return False

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == HIDE_GEOMETRY_TAG:
                collection.delete(c)

        collect = layer.createCollection('Hide_Geometry')
        collect.setNotes(HIDE_GEOMETRY_TAG)
        setExpandedStateValue(collect, False)

        selector_: SimpleSelector = collect.getSelector()
        selector_.setFilterType(selector.Filters.kTransforms)
        selector_.staticSelection.set(nodes)

        override_: AbsUniqueOverride = collect.createAbsoluteOverride(
            nodes[0], 'visibility'
        )
        override_.setAttrValue(False)
    return True


def add_hide_geometry() -> bool:
    '''Add hide geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer addition.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node addition.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == HIDE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            register_hide_geometry()
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.add(nodes)

    return True


def remove_hide_geometry() -> bool:
    '''Remove hide geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer removal.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node removal.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == HIDE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.remove(nodes)

    return True


def delete_hide_geometry() -> bool:
    '''delete hide geometry.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node deletion.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == HIDE_GEOMETRY_TAG:
                collect = c

        if collect is None:
            continue

        collection.delete(collect)

    return True


# ------------------------------------------------------------------------------
# Matte out Geometry(SW)
def register_matte_out_geometry_sw() -> bool:
    '''Register matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer registration.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node registration.')
        return False

    material: str = 'matteout_MT'
    if not cmds.objExists(material):
        material = cmds.shadingNode(
            'useBackground', name=material, asShader=True
        )

    sg: str = 'matteout_MTSG'
    if not cmds.objExists(sg):
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)

    src_plug: str = f'{material}.outColor'
    dst_plug: str = f'{sg}.surfaceShader'
    if not cmds.isConnected(src_plug, dst_plug):
        cmds.connectAttr(src_plug, dst_plug, force=True)

    cmds.select(*nodes)
    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_SW_TAG:
                collection.delete(c)

        collect = layer.createCollection('Matte_Out_Geometry_SW')
        collect.setNotes(MATTE_OUT_GEOMETRY_SW_TAG)
        setExpandedStateValue(collect, False)

        selector_: SimpleSelector = collect.getSelector()
        selector_.setFilterType(selector.Filters.kTransforms)
        selector_.staticSelection.set(nodes)

        override_: MaterialOverride = collect.createOverride(
            sg, typeIDs.materialOverride
        )
        override_.setMaterial(sg)
    return True


def add_matte_out_geometry_sw() -> bool:
    '''Add matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer addition.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node addition.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_SW_TAG:
                collect = c

        if collect is None:
            register_matte_out_geometry_sw()
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.add(nodes)

    return True


def remove_matte_out_geometry_sw() -> bool:
    '''Remove matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer removal.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node removal.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_SW_TAG:
                collect = c

        if collect is None:
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.remove(nodes)

    return True


def delete_matte_out_geometry_sw() -> bool:
    '''delete matte out geometry.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node deletion.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_SW_TAG:
                collect = c

        if collect is None:
            continue

        collection.delete(collect)

    return True


# ------------------------------------------------------------------------------
# Matte out Geometry(aiMatte)
def register_matte_out_geometry_aimatte() -> bool:
    '''Register matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer registration.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node registration.')
        return False

    shapes: list[str] = (
        cmds.listRelatives(nodes[0], shapes=True, path=True) or []
    )
    if not shapes:
        _logger.error(
            'The selected nodes have no shapes, so the process cannot continue.'
        )
        return False

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_AIMATTE_TAG:
                collection.delete(c)

        collect = layer.createCollection('Matte_Out_Geometry_aiMatte')
        collect.setNotes(MATTE_OUT_GEOMETRY_AIMATTE_TAG)
        setExpandedStateValue(collect, False)

        selector_: SimpleSelector = collect.getSelector()
        selector_.setFilterType(selector.Filters.kTransforms)
        selector_.staticSelection.set(nodes)

        shape_collect: Collection = collect.createCollection('Matte_Out_Shape')
        setExpandedStateValue(shape_collect, False)
        shape_selector: SimpleSelector = shape_collect.getSelector()
        shape_selector.setFilterType(selector.Filters.kShapes)
        shape_selector.setPattern('*')
        aiMatte_override: AbsUniqueOverride = (
            shape_collect.createAbsoluteOverride(shapes[0], 'aiMatte')
        )
        aiMatte_override.setAttrValue(True)
    return True


def add_matte_out_geometry_aimatte() -> bool:
    '''Add matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer addition.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node addition.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_AIMATTE_TAG:
                collect = c

        if collect is None:
            register_matte_out_geometry_aimatte()
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.add(nodes)

    return True


def remove_matte_out_geometry_aimatte() -> bool:
    '''Remove matte out geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer removal.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node removal.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_AIMATTE_TAG:
                collect = c

        if collect is None:
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.remove(nodes)

    return True


def delete_matte_out_geometry_aimatte() -> bool:
    '''delete matte out geometry.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node deletion.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == MATTE_OUT_GEOMETRY_AIMATTE_TAG:
                collect = c

        if collect is None:
            continue

        collection.delete(collect)

    return True


# ------------------------------------------------------------------------------
# Disable Primary Visibility
def register_disable_primary_visibility() -> bool:
    '''Register disable primary visibility geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer registration.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node registration.')
        return False

    dummy_mesh: str = ''
    meshes: list[str] = cmds.ls(type='mesh')
    if not meshes:
        mesh: str = cmds.createNode('mesh')
        dummy_mesh = cmds.listRelatives(mesh, parent=True, path=True)[0]
        meshes.append(mesh)

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == DISABLE_PRIMARY_VISIBILITY_TAG:
                collection.delete(c)

        collect = layer.createCollection('Disable_Primary_Visibility_Geometry')
        collect.setNotes(DISABLE_PRIMARY_VISIBILITY_TAG)
        setExpandedStateValue(collect, False)

        selector_: SimpleSelector = collect.getSelector()
        selector_.setFilterType(selector.Filters.kTransforms)
        selector_.staticSelection.set(nodes)

        shape_collect: Collection = collect.createCollection(
            'Disable_Primary_Visibility_Shape'
        )
        setExpandedStateValue(shape_collect, False)
        shape_selector: SimpleSelector = shape_collect.getSelector()
        shape_selector.setFilterType(selector.Filters.kShapes)
        shape_selector.setPattern('*')
        aiMatte_override: AbsUniqueOverride = (
            shape_collect.createAbsoluteOverride(meshes[0], 'primaryVisibility')
        )
        aiMatte_override.setAttrValue(False)

    if dummy_mesh:
        cmds.delete(dummy_mesh)

    return True


def add_disable_primary_visibility() -> bool:
    '''Add disable primary visibility geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer addition.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node addition.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == DISABLE_PRIMARY_VISIBILITY_TAG:
                collect = c

        if collect is None:
            register_disable_primary_visibility()
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.add(nodes)

    return True


def remove_disable_primary_visibility() -> bool:
    '''Remove disable primary visibility geometry.'''
    nodes: list[str] = cmds.ls(selection=True, type='transform')
    if not nodes:
        _logger.error('Select nodes for layer removal.')
        return False

    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node removal.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == DISABLE_PRIMARY_VISIBILITY_TAG:
                collect = c

        if collect is None:
            continue

        selector_: SimpleSelector = collect.getSelector()
        selector_.staticSelection.remove(nodes)

    return True


def delete_disable_primary_visibility() -> bool:
    '''delete disable primary visibility geometry.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error('Select layer for node deletion.')
        return False

    for layer in layers:
        collect: Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == DISABLE_PRIMARY_VISIBILITY_TAG:
                collect = c

        if collect is None:
            continue

        collection.delete(collect)

    return True


# ------------------------------------------------------------------------------
def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
