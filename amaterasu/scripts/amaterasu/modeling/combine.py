# ==============================================================================
#
# Combine
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import QWidget, QCheckBox, QDoubleSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import QWidget, QCheckBox, QDoubleSpinBox
from maya import cmds
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Combine'
__version__: str = '1.30'
__doc__ = 'Combine polygons from selected it.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
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
    merge: parser.Variant[bool] = parser.Variant(False)
    threshold: parser.Variant[float] = parser.Variant(0.01)


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

        self.__keep_smooth: QCheckBox = QCheckBox(
            'Keep Smooth Mesh Preview Options', self
        )
        main_layout.addRow('', self.__keep_smooth)

        self.__merge: QCheckBox = QCheckBox('Merge', self)
        self.__merge.clicked.connect(self.set_valid_options)
        main_layout.addRow('', self.__merge)

        self.__threshold: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__threshold.setDecimals(4)
        self.__threshold.setRange(0.0000, 9999.9999)
        self.__threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__threshold.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel('Threshold'), self.__threshold)
        self.__threshold_index: int = main_layout.row_id()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__keep_smooth.setChecked(settings.keep_smooth.value())
        self.__merge.setChecked(settings.merge.value())
        self.__threshold.setValue(settings.threshold.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.keep_smooth.set_value(self.__keep_smooth.isChecked())
        settings.merge.set_value(self.__merge.isChecked())
        settings.threshold.set_value(self.__threshold.value())
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
        layout: widgets.FormLayout = self.option_widget().layout()
        layout.set_row_enabled(self.__threshold_index, self.__merge.isChecked())

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
def search_polygons(
    nodes: list[str], result: list[str] | None = None
) -> list[str]:
    '''Search for polygons in a hierarchy.'''
    if not result:
        result = []

    for node in nodes:
        if cmds.objectType(node) != 'transform':
            continue

        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            children: list[str] = (
                cmds.listRelatives(node, children=True, path=True) or []
            )
            if children:
                result = search_polygons(children, result)

        else:
            shape: str = shapes[0]
            if cmds.objectType(shape) == 'mesh':
                result.append(node)

    return result


def apply(
    nodes: list[str],
    keep_smooth: bool = True,
    merge: bool = False,
    threshold: float = 0.01,
) -> bool:
    '''Combine polygons'''
    combine_nodes: list[str] = search_polygons(nodes)
    if len(combine_nodes) <= 1:
        _logger.error('Combine needs at least 2 polygonal objects.')
        return False

    smooth_mesh_values: list[Any] = []
    if keep_smooth:
        for attr in SMOOTH_MESH_ATTRS:
            smooth_mesh_values.append(
                cmds.getAttr(f'{combine_nodes[0]}.{attr}')
            )

    original_name: str = nodes[0].split('|')[-1]
    temp: list[str] = cmds.listRelatives(nodes[0], parent=True, path=True) or []
    parent: str = ''
    if temp:
        parent = temp[0]

    if parent:
        cmds.lockNode(parent, lock=True)

    try:
        temp = cmds.polyUnite(combine_nodes, constructionHistory=False)
        combined_node: str = temp[0]

        if merge:
            cmds.polyMergeVertex(
                combined_node, distance=threshold, constructionHistory=False
            )
            cmds.select(combined_node)

    except RuntimeError:
        if parent:
            cmds.lockNode(parent, lock=False)
        _logger.error('Failed to combine.')
        return False

    surface_shaders: list[str] = utility.surface_shader(combined_node)
    if surface_shaders and len(surface_shaders) == 1:
        cmds.sets(combined_node, edit=True, forceElement=surface_shaders[0])

    for node in combine_nodes:
        if cmds.objExists(node):
            cmds.delete(node)

    if keep_smooth:
        for attr, value in zip(SMOOTH_MESH_ATTRS, smooth_mesh_values):
            cmds.setAttr(f'{combined_node}.{attr}', value)

    try:
        combined_node = cmds.rename(combined_node, original_name)
    except RuntimeError:
        pass

    if parent:
        cmds.lockNode(parent, lock=False)
        cmds.parent(combined_node, parent)

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygons to combine.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        selection,
        settings.keep_smooth.value(),
        settings.merge.value(),
        settings.threshold.value(),
    )
    if result:
        _logger.info('Done.')
