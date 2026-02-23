# ==============================================================================
#
# Separate
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QCheckBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QCheckBox
from maya import cmds
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Separate'
__version__: str = '1.20'
__doc__ = 'Separate polygons from selected it.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

SMOOTH_MESH_ATTRS: list[str] = [
    'displaySmoothMesh',
    'useGlobalSmoothDrawType',
    'smoothDrawType',
    'displaySubdComps',
    'smoothLevel',
    'useSmoothPreviewForRender',
    'renderSmoothLevel',
    'osdVertBoundary',
    'osdFvarBoundary',
    'osdFvarPropagateCorners',
    'osdSmoothTriangles',
    'osdCreaseMethod',
    'showDisplacements',
    'loadTiledTextures',
    'smoothTessLevel',
    'boundaryRule',
    'continuity',
    'smoothUVs',
    'propagateEdgeHardness',
    'keepMapBorders',
    'keepHardEdge',
    'keepBorder',
]


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    keep_smooth: parser.Variant[bool] = parser.Variant(True)


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

        self.__keep_smooth: QCheckBox = QCheckBox(
            'Keep Smooth Mesh Preview Options', self
        )
        main_layout.addRow(widgets.FormLabel(''), self.__keep_smooth)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__keep_smooth.setChecked(settings.keep_smooth.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.keep_smooth.set_value(self.__keep_smooth.isChecked())
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
def apply(nodes: list[str], keep_smooth: bool = True) -> bool:
    '''Separate polygons.'''
    result: list[str] = []
    for node in nodes:
        smooth_mesh_values: list[Any] = []
        if keep_smooth:
            for attr in SMOOTH_MESH_ATTRS:
                smooth_mesh_values.append(cmds.getAttr(f'{node}.{attr}'))

        original_name: str = nodes[0].split('|')[-1]
        temp: list[str] = (
            cmds.listRelatives(nodes[0], parent=True, path=True) or []
        )
        parent: str = ''
        if temp:
            parent = temp[0]

        if parent:
            cmds.lockNode(parent, lock=True)

        try:
            separated_objects: list[str] = cmds.polySeparate(
                node, constructionHistory=False
            )
        except RuntimeError:
            if parent:
                cmds.lockNode(parent, lock=False)
            _logger.error('Failed to combine.')
            return False

        # Unparent separate group.
        for i, _node in enumerate(separated_objects):
            if parent:
                separated_objects[i] = cmds.parent(_node, parent)[0]
            else:
                separated_objects[i] = cmds.parent(_node, world=True)[0]

        # Delete separate group.
        cmds.delete(node)

        # Cleanup separated nodes.
        for _node in separated_objects:
            if keep_smooth:
                for attr, value in zip(SMOOTH_MESH_ATTRS, smooth_mesh_values):
                    cmds.setAttr(f'{_node}.{attr}', value)

            surface_shaders = utility.surface_shader(_node)
            if surface_shaders and len(surface_shaders) == 1:
                cmds.sets(_node, edit=True, forceElement=surface_shaders[0])

            try:
                _node = cmds.rename(_node, original_name)

            except RuntimeError:
                pass

            result.append(_node)

        if parent:
            cmds.lockNode(parent, lock=False)

    if result:
        cmds.select(*result)

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygons to separate.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(selection, settings.keep_smooth.value())
    if result:
        _logger.info('Done.')
