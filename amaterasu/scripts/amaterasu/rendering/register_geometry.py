# ==============================================================================
#
# Register Geometry
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable

import logging

try:
    from PySide2.QtCore import Qt, Signal, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QCheckBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QCheckBox,
        )
from maya import cmds
from maya.app.renderSetup.model import (
    utils,
    expandedState,
    renderLayer,
    collection,
    selector,
    override,
    connectionOverride,
    typeIDs,
    renderSetup,
)  # type: ignore
from maya.app.renderSetup.views import viewCmds  # type: ignore
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Register Geometry'
__version__: str = '1.21'
__doc__ = 'Register geometry to the selected layers.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    collect_meshes: parser.Variant[bool] = parser.Variant(True)
    visible_only: parser.Variant[bool] = parser.Variant(True)


class RenderSetupGeometryManager:
    '''Render Setup Geometry Manager'''

    def __init__(self, tag: str, name: str) -> None:
        '''Initialize'''
        self.__tag: str = tag
        self.__name: str = name
        self.__collect_meshes_cb: Callable[[], bool] = lambda: False
        self.__visible_only_cb: Callable[[], bool] = lambda: False

    def tag(self) -> str:
        '''Returns tag'''
        return self.__tag

    def set_tag(self, tag: str) -> None:
        '''Set tag'''
        self.__tag = tag

    def name(self) -> str:
        '''Return name'''
        return self.__name

    def set_name(self, name: str) -> None:
        '''Set name'''
        self.__name = name

    def selected_layers(self) -> list[renderLayer.RenderLayer]:
        '''Return list of layers selected on window.'''
        selected_layers: list[str] = viewCmds.getSelection(renderLayers=True)
        if not selected_layers:
            return []

        return [utils.nameToUserNode(x) for x in selected_layers]

    def refresh_layer(self, layer: renderLayer.RenderLayer) -> None:
        '''Refresh layer if it is currently active.'''
        rs: renderSetup.RenderSetup = renderSetup.instance()
        # if rs.getVisibleRenderLayer() == layer:
        if rs.getVisibleRenderLayer().name() == layer.name():
            rs.switchToLayer(layer)

    def find_collection(
        self, layer: renderLayer.RenderLayer
    ) -> collection.Collection | None:
        '''Search for objects with a specific note.'''
        collect: collection.Collection | None = None
        for c in layer.getCollections():
            if c.getNotes() == self.tag():
                collect = c

        return collect

    def set_filter_callbacks(
        self, collect_cb: Callable[[], bool], visible_cb: Callable[[], bool]
    ) -> None:
        '''Set callbacks to get filter options'''
        self.__collect_meshes_cb = collect_cb
        self.__visible_only_cb = visible_cb

    def get_target_nodes(self) -> list[str]:
        '''Get target nodes based on selection and filters.'''
        nodes: list[str] = cmds.ls(selection=True, long=True)
        if not nodes:
            return []

        if self.__collect_meshes_cb():
            shapes: list[str] = (
                cmds.listRelatives(
                    *nodes, allDescendents=True, type='mesh', fullPath=True
                )
                or []
            )
            if shapes:
                parents: list[str] = (
                    cmds.listRelatives(*shapes, parent=True, fullPath=True)
                    or []
                )
                nodes = list(set(parents))

        if self.__visible_only_cb():
            nodes = cmds.ls(*nodes, visible=True, long=True)

        return nodes

    @widgets.undo
    def register(self) -> bool:
        '''Register collection to Render Layer.'''
        return True

    @widgets.undo
    def add(self) -> bool:
        '''Add geometry to my collection.'''
        # nodes: list[str] = cmds.ls(selection=True, type='transform')
        nodes: list[str] = self.get_target_nodes()
        if not nodes:
            _logger.error('Select nodes for layer addition.')
            return False

        layers: list[renderLayer.RenderLayer] = self.selected_layers()
        if not layers:
            _logger.error('Select layer for node addition.')
            return False

        for layer in layers:
            collect: collection.Collection | None = self.find_collection(layer)
            if collect is None:
                self.register()
                continue

            selector_: selector.SimpleSelector = collect.getSelector()
            selector_.staticSelection.add(nodes)
            self.refresh_layer(layer)

        return True

    @widgets.undo
    def remove(self) -> bool:
        '''Remove geometry from my collection.'''
        # nodes: list[str] = cmds.ls(selection=True, type='transform')
        nodes: list[str] = self.get_target_nodes()
        if not nodes:
            _logger.error('Select nodes for layer removal.')
            return False

        layers: list[renderLayer.RenderLayer] = self.selected_layers()
        if not layers:
            _logger.error('Select layer for node removal.')
            return False

        for layer in layers:
            collect: collection.Collection | None = self.find_collection(layer)
            if collect:
                selector_: selector.SimpleSelector = collect.getSelector()
                selector_.staticSelection.remove(nodes)
                self.refresh_layer(layer)
        return True

    @widgets.undo
    def delete(self) -> bool:
        '''Delete my collection.'''
        layers: list[renderLayer.RenderLayer] = self.selected_layers()
        if not layers:
            _logger.error('Select layer for node deletion.')
            return False

        for layer in layers:
            collect: collection.Collection | None = self.find_collection(layer)
            if collect:
                collection.delete(collect)
                self.refresh_layer(layer)

        return True


class AttrOverrideManager(RenderSetupGeometryManager):
    '''Attribute Override Manager'''

    def __init__(self, tag: str, name: str, attr: str, value: Any) -> None:
        '''Initialize'''
        super().__init__(tag, name)
        self.__attr_name: str = attr
        self.__value: Any = value

    def attr_name(self) -> str:
        '''Return attribute name.'''
        return self.__attr_name

    def set_attr_name(self, val: str) -> None:
        '''Set attribute name.'''
        self.__attr_name = val

    def value(self) -> Any:
        '''Returns value.'''
        return self.__value

    def set_value(self, value: Any) -> None:
        '''Set value.'''
        self.__value = value

    @widgets.undo
    def register(self) -> bool:
        '''Override'''
        # nodes: list[str] = cmds.ls(selection=True, type='transform')
        nodes: list[str] = self.get_target_nodes()
        if not nodes:
            _logger.error('Select nodes for layer registration.')
            return False

        layers: list[renderLayer.RenderLayer] = self.selected_layers()
        if not layers:
            _logger.error('Select layer for node registration.')
            return False

        for layer in layers:
            collect: collection.Collection | None = self.find_collection(layer)
            if collect:
                collection.delete(collect)

            collect = layer.createCollection(self.name())
            collect.setNotes(self.tag())
            expandedState.setExpandedStateValue(collect, False)

            selector_: selector.SimpleSelector = collect.getSelector()
            selector_.setFilterType(selector.Filters.kTransforms)
            selector_.staticSelection.set(nodes)

            override_: override.AbsUniqueOverride = (
                collect.createAbsoluteOverride(nodes[0], self.attr_name())
            )
            override_.setAttrValue(self.value())
            self.refresh_layer(layer)

        return True


class ShapeAttrOverrideManager(AttrOverrideManager):
    '''Shape Attribute Override Manager'''

    @widgets.undo
    def register(self) -> bool:
        '''Override'''
        # nodes: list[str] = cmds.ls(selection=True, type='transform')
        nodes: list[str] = self.get_target_nodes()
        if not nodes:
            _logger.error('Select nodes for layer registration.')
            return False

        layers: list[renderLayer.RenderLayer] = self.selected_layers()
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
            collect: collection.Collection | None = self.find_collection(layer)
            if collect:
                collection.delete(collect)

            collect = layer.createCollection(self.name())
            collect.setNotes(self.tag())
            expandedState.setExpandedStateValue(collect, False)

            selector_: selector.SimpleSelector = collect.getSelector()
            selector_.setFilterType(selector.Filters.kTransforms)
            selector_.staticSelection.set(nodes)

            shape_collect: collection.Collection = collect.createCollection(
                f'{self.name()}_Shape'
            )
            expandedState.setExpandedStateValue(shape_collect, False)
            shape_selector: selector.SimpleSelector = (
                shape_collect.getSelector()
            )
            shape_selector.setFilterType(selector.Filters.kShapes)
            shape_selector.setPattern('*')
            unique_override: override.AbsUniqueOverride = (
                shape_collect.createAbsoluteOverride(
                    meshes[0], self.attr_name()
                )
            )
            unique_override.setAttrValue(self.value())
            self.refresh_layer(layer)

        if dummy_mesh:
            cmds.delete(dummy_mesh)

        return True


class MaterialOverrideManager(RenderSetupGeometryManager):
    '''Material Override Manager'''

    @widgets.undo
    def register(self) -> bool:
        '''Override'''
        current_selection: list[str] = cmds.ls(selection=True)
        nodes: list[str] = self.get_target_nodes()
        if not nodes:
            _logger.error('Select nodes for layer registration.')
            return False

        layers: list[renderLayer.RenderLayer] = self.selected_layers()
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
            cmds.sets(
                renderable=True, noSurfaceShader=True, empty=True, name=sg
            )

        src_plug: str = f'{material}.outColor'
        dst_plug: str = f'{sg}.surfaceShader'
        if not cmds.isConnected(src_plug, dst_plug):
            cmds.connectAttr(src_plug, dst_plug, force=True)

        cmds.select(*current_selection)
        for layer in layers:
            collect: collection.Collection | None = self.find_collection(layer)
            if collect:
                collection.delete(collect)

            collect = layer.createCollection(self.name())
            collect.setNotes(self.tag())
            expandedState.setExpandedStateValue(collect, False)

            selector_: selector.SimpleSelector = collect.getSelector()
            selector_.setFilterType(selector.Filters.kTransforms)
            selector_.staticSelection.set(nodes)

            override_: connectionOverride.MaterialOverride = (
                collect.createOverride(sg, typeIDs.materialOverride)
            )
            override_.setMaterial(sg)
            self.refresh_layer(layer)

        return True


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
        self.__manager: RenderSetupGeometryManager | None = None

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

    def set_manager(self, manager: RenderSetupGeometryManager) -> None:
        '''Set manager'''
        self.__manager: RenderSetupGeometryManager = manager
        self.apply_clicked.connect(self.__manager.register)
        self.add_clicked.connect(self.__manager.add)
        self.remove_clicked.connect(self.__manager.remove)
        self.delete_clicked.connect(self.__manager.delete)


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

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())

        option_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(option_layout)

        self.__collect_meshes: QCheckBox = QCheckBox('Collect Meshes', self)
        option_layout.addWidget(self.__collect_meshes)

        self.__visible_only: QCheckBox = QCheckBox('Visible Only', self)
        option_layout.addWidget(self.__visible_only)

        main_layout.addWidget(widgets.HorizontalLine(self))

        manager: RenderSetupGeometryManager = AttrOverrideManager(
            tag='AMATERASU_RENDERABLE_GEOMETRY',
            name='Renderable_Geometry',
            attr='visibility',
            value=True,
        )
        main_layout.addWidget(
            self._create_container('Renderable Geometry', manager)
        )

        manager = AttrOverrideManager(
            tag='AMATERASU_HIDE_GEOMETRY',
            name='Hide_Geometry',
            attr='visibility',
            value=False,
        )
        main_layout.addWidget(self._create_container('Hide Geometry', manager))

        main_layout.addWidget(widgets.HorizontalLine(self))

        manager = MaterialOverrideManager(
            tag='AMATERASU_MATTE_OUT_GEOMETRY_SW',
            name='Matte_Out_Geometry_SW',
        )
        main_layout.addWidget(
            self._create_container('Matte out Geometry(SW)', manager)
        )

        manager = ShapeAttrOverrideManager(
            tag='AMATERASU_MATTE_OUT_GEOMETRY_AIMATTE',
            name='Matte_Out_Geometry_aiMatte',
            attr='aiMatte',
            value=True,
        )
        main_layout.addWidget(
            self._create_container('Matte out Geometry(Arnold)', manager)
        )

        main_layout.addWidget(widgets.HorizontalLine(self))

        manager = ShapeAttrOverrideManager(
            tag='DISABLE_PRIMARY_VISIBILITY',
            name='Disable_Primary_Visibility_Geometry',
            attr='primaryVisibility',
            value=False,
        )
        main_layout.addWidget(
            self._create_container('Disable Primary Visibility', manager)
        )

        manager = ShapeAttrOverrideManager(
            tag='AMATERASU_DISABLE_CASTS_SHADOWS',
            name='Disable_Casts_Shadows_Geometry',
            attr='castsShadows',
            value=False,
        )
        main_layout.addWidget(
            self._create_container('Disable Casts Shadows', manager)
        )

        manager = ShapeAttrOverrideManager(
            tag='AMATERASU_DISABLE_RECEIVE_SHADOWS',
            name='Disable_Receive_Shadows_Geometry',
            attr='receiveShadows',
            value=False,
        )
        main_layout.addWidget(
            self._create_container('Disable Receive Shadows', manager)
        )

        main_layout.addStretch(True)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__collect_meshes.setChecked(settings.collect_meshes.value())
        self.__visible_only.setChecked(settings.visible_only.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.collect_meshes.set_value(self.__collect_meshes.isChecked())
        settings.visible_only.set_value(self.__visible_only.isChecked())
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

    def _create_container(
        self, label: str, manager: RenderSetupGeometryManager
    ) -> ContainerWidget:
        '''Helper to create container and connect filters.'''
        manager.set_filter_callbacks(
            self.__collect_meshes.isChecked, self.__visible_only.isChecked
        )
        widget = ContainerWidget(label, self)
        widget.set_manager(manager)
        return widget


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
