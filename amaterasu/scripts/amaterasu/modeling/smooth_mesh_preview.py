# ==============================================================================
#
# Smooth Mesh Preview
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import dataclasses

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import QWidget, QComboBox, QCheckBox, QSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import QWidget, QComboBox, QCheckBox, QSpinBox
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Smooth Mesh Preview'
__version__: str = '1.00'
__doc__ = 'Set parameter of smooth mesh preview to selected it.'
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
    display_smooth_mesh: parser.Variant[int] = parser.Variant(2)  # 0, 1, 2
    use_global_smooth_draw_type: parser.Variant[bool] = parser.Variant(False)
    smooth_draw_type: parser.Variant[int] = parser.Variant(0)  # 0, 2, 3

    # Subdivition Levels
    display_subd_comps: parser.Variant[bool] = parser.Variant(False)
    smooth_level: parser.Variant[int] = parser.Variant(2)
    use_smooth_preview_for_render: parser.Variant[bool] = parser.Variant(True)
    render_smooth_level: parser.Variant[int] = parser.Variant(2)

    # OpenSubdiv Controls
    # TODO: more param

    # Maya Catmull-Clark Controls
    smooth_uvs: parser.Variant[bool] = parser.Variant(True)
    propagate_edge_hardness: parser.Variant[bool] = parser.Variant(False)
    # TODO: more param


@dataclasses.dataclass
class SmoothMeshPreviewParam:
    '''Smooth mesh preview parameter.'''

    display_smooth_mesh: int = 2
    use_global_smooth_draw_type: bool = False
    smooth_draw_type: int = 0
    display_subd_comps: bool = False
    smooth_level: int = 2
    use_smooth_preview_for_render: bool = True
    render_smooth_level: int = 2
    smooth_uvs: bool = True
    propagate_edge_hardness: bool = False

    def from_settings(self, settings: Settings) -> None:
        '''Set value from settings.'''
        self.display_smooth_mesh = settings.display_smooth_mesh.value()
        self.use_global_smooth_draw_type = (
            settings.use_global_smooth_draw_type.value()
        )
        self.smooth_draw_type = settings.smooth_draw_type.value()
        self.display_subd_comps = settings.display_subd_comps.value()
        self.smooth_level = settings.smooth_level.value()
        self.use_smooth_preview_for_render = (
            settings.use_smooth_preview_for_render.value()
        )
        self.render_smooth_level = settings.render_smooth_level.value()
        self.smooth_uvs = settings.smooth_uvs.value()
        self.propagate_edge_hardness = settings.propagate_edge_hardness.value()


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

        main_layout.addRow(
            widgets.FrameWidget(
                'Smooth Mesh Preview Options', False, False, self
            )
        )

        self.__display_smooth_mesh: QComboBox = QComboBox(self)
        self.__display_smooth_mesh.addItem('OFF')
        self.__display_smooth_mesh.addItem('Cage + Smooth Mesh')
        self.__display_smooth_mesh.addItem('Smooth Mesh')
        main_layout.addRow(
            widgets.FormLabel('Smooth Mesh Preview'), self.__display_smooth_mesh
        )

        self.__use_global_smooth_draw_type: QCheckBox = QCheckBox(
            'Use global subdivision method', self
        )
        main_layout.addRow('', self.__use_global_smooth_draw_type)

        self.__smooth_draw_type: QComboBox = QComboBox(self)
        self.__smooth_draw_type.addItem('Maya Catmull-Clark', 0)
        self.__smooth_draw_type.addItem('OpenSubdiv Catmull-Clark', 2)
        self.__smooth_draw_type.addItem('OpenSubdiv Catmull-Clark Adaptive', 3)
        main_layout.addRow(
            widgets.FormLabel('Subdivision Method'), self.__smooth_draw_type
        )

        main_layout.addRow(
            widgets.FrameWidget('Smooth Options', False, False, self)
        )

        self.__display_subd_comps: QCheckBox = QCheckBox(
            'Display Subdivisions', self
        )
        main_layout.addRow('', self.__display_subd_comps)

        self.__smooth_level: QSpinBox = QSpinBox(self)
        self.__smooth_level.setRange(0, 10)
        self.__smooth_level.setMinimumWidth(70)
        self.__smooth_level.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addRow(
            widgets.FormLabel('Preview Division Levels'), self.__smooth_level
        )

        self.__use_smooth_preview_for_render: QCheckBox = QCheckBox(
            'Use Preview Level for Rendering', self
        )
        main_layout.addRow('', self.__use_smooth_preview_for_render)

        self.__render_smooth_level: QSpinBox = QSpinBox(self)
        self.__render_smooth_level.setRange(0, 10)
        self.__render_smooth_level.setMinimumWidth(70)
        self.__render_smooth_level.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addRow(
            widgets.FormLabel('Render Division Levels'),
            self.__render_smooth_level,
        )

        main_layout.addRow(
            widgets.FrameWidget(
                'Maya Catmull-Clark Options', False, False, self
            )
        )

        self.__smooth_uvs: QCheckBox = QCheckBox('Smooth UVs', self)
        main_layout.addRow('', self.__smooth_uvs)

        self.__propagate_edge_hardness: QCheckBox = QCheckBox(
            'Propagate Edge Hardness', self
        )
        main_layout.addRow('', self.__propagate_edge_hardness)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__display_smooth_mesh.setCurrentIndex(
            settings.display_smooth_mesh.value()
        )
        self.__use_global_smooth_draw_type.setChecked(
            settings.use_global_smooth_draw_type.value()
        )
        self.__smooth_draw_type.setCurrentIndex(
            settings.smooth_draw_type.value()
        )
        self.__display_subd_comps.setChecked(
            settings.display_subd_comps.value()
        )
        self.__smooth_level.setValue(settings.smooth_level.value())
        self.__use_smooth_preview_for_render.setChecked(
            settings.use_smooth_preview_for_render.value()
        )
        self.__render_smooth_level.setValue(
            settings.render_smooth_level.value()
        )
        self.__smooth_uvs.setChecked(settings.smooth_uvs.value())
        self.__propagate_edge_hardness.setChecked(
            settings.propagate_edge_hardness.value()
        )
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.display_smooth_mesh.set_value(
            self.__display_smooth_mesh.currentIndex()
        )
        settings.use_global_smooth_draw_type.set_value(
            self.__use_global_smooth_draw_type.isChecked()
        )
        settings.smooth_draw_type.set_value(
            self.__smooth_draw_type.currentIndex()
        )
        settings.display_subd_comps.set_value(
            self.__display_subd_comps.isChecked()
        )
        settings.smooth_level.set_value(self.__smooth_level.value())
        settings.use_smooth_preview_for_render.set_value(
            self.__use_smooth_preview_for_render.isChecked()
        )
        settings.render_smooth_level.set_value(
            self.__render_smooth_level.value()
        )
        settings.smooth_uvs.set_value(self.__smooth_uvs.isChecked())
        settings.propagate_edge_hardness.set_value(
            self.__propagate_edge_hardness.isChecked()
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

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''

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
def apply(nodes: list[str], param: SmoothMeshPreviewParam) -> bool:
    '''Set parameter of smooth mesh preview.'''
    param.smooth_draw_type = [0, 2, 3][param.smooth_draw_type]
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != 'mesh':
            continue

        try:
            cmds.setAttr(
                f'{shape}.displaySmoothMesh', param.display_smooth_mesh
            )
            cmds.setAttr(
                f'{shape}.displaySmoothMesh', param.display_smooth_mesh
            )
            cmds.setAttr(
                f'{shape}.useGlobalSmoothDrawType',
                param.use_global_smooth_draw_type,
            )
            cmds.setAttr(f'{shape}.smoothDrawType', param.smooth_draw_type)
            cmds.setAttr(f'{shape}.displaySubdComps', param.display_subd_comps)
            cmds.setAttr(f'{shape}.smoothLevel', param.smooth_level)
            cmds.setAttr(
                f'{shape}.useSmoothPreviewForRender',
                param.use_smooth_preview_for_render,
            )
            cmds.setAttr(
                f'{shape}.renderSmoothLevel', param.render_smooth_level
            )
            cmds.setAttr(f'{shape}.smoothUVs', param.smooth_uvs)
            cmds.setAttr(
                f'{shape}.propagateEdgeHardness', param.propagate_edge_hardness
            )

        except RuntimeError:
            pass

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygon node to set Smooth Mesh Preview.')
        return

    param: SmoothMeshPreviewParam = SmoothMeshPreviewParam()
    param.from_settings(Settings.instance(__name__, True))
    result: bool = apply(selection, param)
    if result:
        _logger.info('Done.')
