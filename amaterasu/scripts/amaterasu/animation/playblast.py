# ==============================================================================
#
# Playblash
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import os

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QLabel,
        QLineEdit,
        QCheckBox,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QSizePolicy,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QLabel,
            QLineEdit,
            QCheckBox,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox,
            QSizePolicy,
        )
from maya import cmds, mel
from maya.app.renderSetup.model import renderSetup
from maya.app.renderSetup.model import renderLayer
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Playblast'
__version__: str = '1.30'
__doc__ = 'Quick playblast from the rendering setup.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

DEFAULT_FILE_NAME_PREFIX: str = '<Scene>/<RenderLayer>/<RenderLayer>'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    sub_folder: parser.Variant[str] = parser.Variant('playblast')
    format: parser.Variant[str] = parser.Variant('image')
    encoding: parser.Variant[str] = parser.Variant('png')
    quality: parser.Variant[int] = parser.Variant(100)
    frame_padding: parser.Variant[int] = parser.Variant(4)
    scale: parser.Variant[float] = parser.Variant(1.0)

    use_default_material: parser.Variant[bool] = parser.Variant(False)
    wireframe_on_shaded: parser.Variant[bool] = parser.Variant(False)
    display_texture: parser.Variant[bool] = parser.Variant(True)
    display_lights: parser.Variant[bool] = parser.Variant(False)  # New
    ssao: parser.Variant[bool] = parser.Variant(False)  # New
    mb: parser.Variant[bool] = parser.Variant(False)  # New
    msaa: parser.Variant[bool] = parser.Variant(False)  # New

    show_ornaments: parser.Variant[bool] = parser.Variant(False)
    show_polygon: parser.Variant[bool] = parser.Variant(True)
    show_cv_curve: parser.Variant[bool] = parser.Variant(False)
    show_nurbs: parser.Variant[bool] = parser.Variant(False)
    show_fluids: parser.Variant[bool] = parser.Variant(False)
    show_particle: parser.Variant[bool] = parser.Variant(False)
    show_paint_effects: parser.Variant[bool] = parser.Variant(True)
    show_plugin_shapes: parser.Variant[bool] = parser.Variant(False)
    show_gpu_cache: parser.Variant[bool] = parser.Variant(True)


class PlayblastOption:
    '''Playblast Option'''

    def __init__(self) -> None:
        '''Initialize.'''
        self.__sub_folder: str = ''
        self.__format: str = ''
        self.__encoding: str = ''
        self.__quality: int = 100
        self.__frame_padding: int = 4
        self.__scale: float = 1.0
        self.__use_default_material: bool = False
        self.__wireframe_on_shaded: bool = False
        self.__display_texture: bool = True
        self.__display_lights: bool = False
        self.__ssao: bool = False
        self.__mb: bool = False
        self.__msaa: bool = False
        self.__show_ornaments: bool = False
        self.__show_polygon: bool = True
        self.__show_cv_curve: bool = False
        self.__show_nurbs: bool = False
        self.__show_fluids: bool = False
        self.__show_particle: bool = False
        self.__show_paint_effects: bool = True
        self.__show_plugin_shapes: bool = False
        self.__show_gpu_cache: bool = False

        self.__width: int = cmds.getAttr('defaultResolution.width')
        self.__height: int = cmds.getAttr('defaultResolution.height')
        self.__camera: str = 'persp'
        for camera in cmds.ls(type='camera'):
            if not cmds.getAttr(f'{camera}.renderable'):
                continue

            parent: list[str] = (
                cmds.listRelatives(camera, parent=True, path=True) or []
            )
            if not parent:
                continue

            self.__camera = parent[0]
            break

    def sub_folder(self) -> str:
        '''Return sub folder name.'''
        return self.__sub_folder

    def format(self) -> str:
        '''Return format.'''
        return self.__format

    def encoding(self) -> str:
        '''Return encoding.'''
        return self.__encoding

    def quality(self) -> int:
        '''Return quality.'''
        return self.__quality

    def frame_padding(self) -> int:
        '''Return frame padding.'''
        return self.__frame_padding

    def scale(self) -> float:
        '''Return scale.'''
        return self.__scale

    def use_default_material(self) -> bool:
        '''Return use default material.'''
        return self.__use_default_material

    def wireframe_on_shaded(self) -> bool:
        '''Return wireframe on shaded.'''
        return self.__wireframe_on_shaded

    def display_texture(self) -> bool:
        '''Return display texture'''
        return self.__display_texture

    def display_lights(self) -> str:
        '''Return display lights.'''
        return 'all' if self.__display_lights else 'default'

    def ssao(self) -> bool:
        '''Return ssao.'''
        return self.__ssao

    def mb(self) -> bool:
        '''Return motion blur.'''
        return self.__mb

    def msaa(self) -> bool:
        '''Return msaa.'''
        return self.__msaa

    def show_ornaments(self) -> bool:
        '''Return show ornaments'''
        return self.__show_ornaments

    def show_polygon(self) -> bool:
        '''Return show polygon.'''
        return self.__show_polygon

    def show_cv_curve(self) -> bool:
        '''Return show cv curve.'''
        return self.__show_cv_curve

    def show_nurbs(self) -> bool:
        '''Return shor nubs.'''
        return self.__show_nurbs

    def show_fluids(self) -> bool:
        '''Return show fluids.'''
        return self.__show_fluids

    def show_particle(self) -> bool:
        '''Return show particle.'''
        return self.__show_particle

    def show_paint_effects(self) -> bool:
        '''Return show paint effects.'''
        return self.__show_paint_effects

    def show_plugin_shapes(self) -> bool:
        '''Return show plugin shapes.'''
        return self.__show_plugin_shapes

    def show_gpu_cache(self) -> bool:
        '''Return show gpu cache.'''
        return self.__show_gpu_cache

    def width(self) -> int:
        '''Return width.'''
        return self.__width

    def height(self) -> int:
        '''Return height.'''
        return self.__height

    def camera(self) -> str:
        '''Return camera.'''
        return self.__camera

    def filename(self, layer_name: str = '') -> str:
        '''Return filename.'''
        filename: str = os.path.join(
            cmds.workspace(query=True, rootDirectory=True),
            cmds.workspace(fileRuleEntry='images'),
            self.sub_folder(),
            cmds.getAttr('defaultRenderGlobals.imageFilePrefix')
            or DEFAULT_FILE_NAME_PREFIX,
        )

        scene_name: str = cmds.file(query=True, sceneName=True, shortName=True)
        scene_name = scene_name if scene_name else 'untitled'
        scene_base_name, _ = os.path.splitext(scene_name)
        version: str = (
            cmds.getAttr('defaultRenderGlobals.renderVersion')
            if cmds.getAttr('defaultRenderGlobals.renderVersion')
            else 'v01'
        )

        filename = filename.replace('<Scene>', scene_base_name)
        filename = filename.replace('<RenderLayer>', layer_name)
        filename = filename.replace('<Camera>', self.__camera)
        filename = filename.replace('<RenderPassFileGroup>', '')
        filename = filename.replace('<RenderPass>', '')
        filename = filename.replace('<RenderPassType>', '')
        filename = filename.replace('<Extension>', self.__encoding)
        filename = filename.replace('<Version>', version)
        filename = filename.replace('<', '_')
        filename = filename.replace('>', '_')
        filename = os.path.normpath(filename)
        return filename

    def from_settings(self, settings: Settings) -> None:
        '''Set value from settings.'''
        self.__sub_folder = settings.sub_folder.value()
        self.__format = settings.format.value()
        self.__encoding = settings.encoding.value()
        self.__quality = settings.quality.value()
        self.__frame_padding = settings.frame_padding.value()
        self.__scale = settings.scale.value()

        self.__use_default_material = settings.use_default_material.value()
        self.__wireframe_on_shaded = settings.wireframe_on_shaded.value()
        self.__display_texture = settings.display_texture.value()
        self.__display_lights = settings.display_lights.value()
        self.__ssao = settings.ssao.value()
        self.__mb = settings.mb.value()
        self.__msaa = settings.msaa.value()

        self.__show_ornaments = settings.show_ornaments.value()
        self.__show_polygon = settings.show_polygon.value()
        self.__show_cv_curve = settings.show_cv_curve.value()
        self.__show_nurbs = settings.show_nurbs.value()
        self.__show_fluids = settings.show_fluids.value()
        self.__show_particle = settings.show_particle.value()
        self.__show_paint_effects = settings.show_paint_effects.value()
        self.__show_plugin_shapes = settings.show_plugin_shapes.value()
        self.__show_gpu_cache = settings.show_gpu_cache.value()


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

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())

        # Output Settings
        output_frame = widgets.FrameWidget('Output Settings', False, True, self)
        main_layout.addWidget(output_frame)

        output_layout = widgets.FormLayout(self)
        output_frame.setLayout(output_layout)

        output_layout.addRow(
            widgets.FormLabel('Output'),
            QLabel(
                'From Render Settings.\n'
                f'If empty, the output will be {DEFAULT_FILE_NAME_PREFIX}.',
                self,
            ),
        )

        self.__sub_folder = QLineEdit(self)
        output_layout.addRow(widgets.FormLabel('Sub Folder'), self.__sub_folder)

        # File Format Settings
        file_format_frame = widgets.FrameWidget(
            'File Format Settings', False, True, self
        )
        main_layout.addWidget(file_format_frame)

        self.__file_format_layout = widgets.FormLayout(self)
        file_format_frame.setLayout(self.__file_format_layout)

        self.__format = QComboBox(self)
        self.__format.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        for item in cmds.playblast(query=True, format=True):
            self.__format.addItem(item)
        self.__file_format_layout.addRow(
            widgets.FormLabel('Format'), self.__format
        )

        self.__encoding = QComboBox(self)
        self.__encoding.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self.__file_format_layout.addRow(
            widgets.FormLabel('Encoding'), self.__encoding
        )

        self.__quality = QSpinBox(self)
        self.__quality.setRange(0, 100)
        self.__quality.setButtonSymbols(QSpinBox.NoButtons)
        self.__quality.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__file_format_layout.addRow(
            widgets.FormLabel('Quality'), self.__quality
        )

        self.__frame_padding = QSpinBox(self)
        self.__frame_padding.setRange(0, 100)
        self.__frame_padding.setButtonSymbols(QSpinBox.NoButtons)
        self.__frame_padding.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        self.__file_format_layout.addRow(
            widgets.FormLabel('Frame Padding'), self.__frame_padding
        )
        self.__frame_padding_index: int = self.__file_format_layout.row_id()

        # Frame Range
        range_frame = widgets.FrameWidget('Frame Range', False, True, self)
        main_layout.addWidget(range_frame)

        range_layout = widgets.FormLayout(self)
        range_frame.setLayout(range_layout)

        range_layout.addRow(
            widgets.FormLabel('Frame Range'),
            QLabel('From Render Settings.'),
        )

        # Camera Settings
        camera_frame = widgets.FrameWidget('Camera Settings', False, True, self)
        main_layout.addWidget(camera_frame)

        camera_layout = widgets.FormLayout(self)
        camera_frame.setLayout(camera_layout)

        camera_layout.addRow(
            widgets.FormLabel('Camera'),
            QLabel('From Render Settings. (Only the first.)'),
        )
        camera_layout.addRow(
            widgets.FormLabel('Resolution'),
            QLabel('From Render Settings.'),
        )

        self.__scale = QDoubleSpinBox(self)
        self.__scale.setRange(0.0, 100.0)
        self.__scale.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__scale.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        camera_layout.addRow(widgets.FormLabel('Scale'), self.__scale)

        # Shading Settings
        shading_frame = widgets.FrameWidget(
            'Shading Settings', False, True, self
        )
        main_layout.addWidget(shading_frame)

        shading_layout = widgets.FormLayout(self)
        shading_frame.setLayout(shading_layout)

        self.__use_default_material = QCheckBox('Use Default Material', self)
        shading_layout.addRow(
            widgets.FormLabel(''), self.__use_default_material
        )

        self.__wireframe_on_shaded = QCheckBox('Wireframe on Shaded', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__wireframe_on_shaded)

        self.__display_texture = QCheckBox('Display Texture', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__display_texture)

        self.__display_lights = QCheckBox('Lighting', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__display_lights)

        self.__ssao = QCheckBox('Screen-spacce Ambient Occlusion', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__ssao)

        self.__mb = QCheckBox('Motion Blur', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__mb)

        self.__msaa = QCheckBox('Multisampling Anti-aliasing', self)
        shading_layout.addRow(widgets.FormLabel(''), self.__msaa)

        # Display Settings
        display_frame = widgets.FrameWidget(
            'Display Settings', False, True, self
        )
        main_layout.addWidget(display_frame)

        display_layout = widgets.FormLayout(self)
        display_frame.setLayout(display_layout)

        self.__show_ornaments = QCheckBox('Show Ornaments', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_ornaments)

        self.__show_polygon = QCheckBox('Show Polygon', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_polygon)

        self.__show_cv_curve = QCheckBox('Show CV Curve', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_cv_curve)

        self.__show_nurbs = QCheckBox('Show NURBS', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_nurbs)

        self.__show_fluids = QCheckBox('Show Fluids', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_fluids)

        self.__show_particle = QCheckBox('Show Particle', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_particle)

        self.__show_paint_effects = QCheckBox('Show Paint Effects', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_paint_effects)

        self.__show_plugin_shapes = QCheckBox('Show Plugin Shapes', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_plugin_shapes)

        self.__show_gpu_cache = QCheckBox('Show GPU Cache', self)
        display_layout.addRow(widgets.FormLabel(''), self.__show_gpu_cache)

        main_layout.addStretch(True)

        # Event
        self.__format.currentIndexChanged.connect(self.set_valid_options)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

        self.__sub_folder.setText(settings.sub_folder.value())
        index: int = self.__format.findText(settings.format.value())
        if index >= 0:
            self.__format.setCurrentIndex(index)

        index = self.__encoding.findText(settings.encoding.value())
        if index >= 0:
            self.__encoding.setCurrentIndex(index)

        self.__quality.setValue(settings.quality.value())
        self.__frame_padding.setValue(settings.frame_padding.value())
        self.__scale.setValue(settings.scale.value())

        self.__use_default_material.setChecked(
            settings.use_default_material.value()
        )
        self.__wireframe_on_shaded.setChecked(
            settings.wireframe_on_shaded.value()
        )
        self.__display_texture.setChecked(settings.display_texture.value())
        self.__display_lights.setChecked(settings.display_lights.value())
        self.__ssao.setChecked(settings.ssao.value())
        self.__mb.setChecked(settings.mb.value())
        self.__msaa.setChecked(settings.msaa.value())

        self.__show_ornaments.setChecked(settings.show_ornaments.value())
        self.__show_polygon.setChecked(settings.show_polygon.value())
        self.__show_cv_curve.setChecked(settings.show_cv_curve.value())
        self.__show_nurbs.setChecked(settings.show_nurbs.value())
        self.__show_fluids.setChecked(settings.show_fluids.value())
        self.__show_particle.setChecked(settings.show_particle.value())
        self.__show_paint_effects.setChecked(
            settings.show_paint_effects.value()
        )
        self.__show_plugin_shapes.setChecked(
            settings.show_plugin_shapes.value()
        )
        self.__show_gpu_cache.setChecked(settings.show_gpu_cache.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))

        settings.sub_folder.set_value(self.__sub_folder.text())
        settings.format.set_value(self.__format.currentText())
        settings.encoding.set_value(self.__encoding.currentText())
        settings.quality.set_value(self.__quality.value())
        settings.frame_padding.set_value(self.__frame_padding.value())
        settings.scale.set_value(self.__scale.value())

        settings.use_default_material.set_value(
            self.__use_default_material.isChecked()
        )
        settings.wireframe_on_shaded.set_value(
            self.__wireframe_on_shaded.isChecked()
        )
        settings.display_texture.set_value(self.__display_texture.isChecked())
        settings.display_lights.set_value(self.__display_lights.isChecked())
        settings.ssao.set_value(self.__ssao.isChecked())
        settings.mb.set_value(self.__mb.isChecked())
        settings.msaa.set_value(self.__msaa.isChecked())

        settings.show_ornaments.set_value(self.__show_ornaments.isChecked())
        settings.show_polygon.set_value(self.__show_polygon.isChecked())
        settings.show_cv_curve.set_value(self.__show_cv_curve.isChecked())
        settings.show_nurbs.set_value(self.__show_nurbs.isChecked())
        settings.show_fluids.set_value(self.__show_fluids.isChecked())
        settings.show_particle.set_value(self.__show_particle.isChecked())
        settings.show_paint_effects.set_value(
            self.__show_paint_effects.isChecked()
        )
        settings.show_plugin_shapes.set_value(
            self.__show_plugin_shapes.isChecked()
        )
        settings.show_gpu_cache.set_value(self.__show_gpu_cache.isChecked())

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

    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        self.__encoding.clear()
        output_format: str = self.__format.currentText()
        state: bool = cmds.commandEcho(query=True, state=True)

        cmds.commandEcho(state=False)
        encodings: list[str] = mel.eval(
            f'$am_playblastFormat = `playblast -format {output_format} -query -compression`;'
        )
        for encoding in encodings:
            self.__encoding.addItem(encoding)

        cmds.commandEcho(state=state)
        self.__file_format_layout.set_row_enabled(
            self.__frame_padding_index, bool(output_format == 'image')
        )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        apply()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def create_playblast_window(option: PlayblastOption) -> tuple[str, str, str]:
    '''Create window for playblast.'''
    window: str = cmds.window()
    layout: str = cmds.formLayout()
    panel: str = cmds.modelPanel()
    editor: str = cmds.modelPanel(panel, query=True, modelEditor=True)
    cmds.modelEditor(
        editor,
        edit=True,
        camera=option.camera(),
        displayAppearance='smoothShaded',
        useDefaultMaterial=option.use_default_material(),
        wireframeOnShaded=option.wireframe_on_shaded(),
        displayTextures=option.display_texture(),
        displayLights=option.display_lights(),
        nurbsCurves=option.show_cv_curve(),
        nurbsSurfaces=option.show_nurbs(),
        controlVertices=False,
        hulls=False,
        polymeshes=option.show_polygon(),
        subdivSurfaces=False,
        planes=False,
        lights=False,
        cameras=False,
        imagePlane=False,
        joints=False,
        ikHandles=False,
        deformers=False,
        dynamics=False,
        particleInstancers=option.show_particle(),
        fluids=option.show_fluids(),
        hairSystems=False,
        follicles=False,
        nCloths=False,
        nParticles=option.show_particle(),
        nRigids=False,
        dynamicConstraints=False,
        locators=False,
        dimensions=False,
        pivots=False,
        handles=False,
        textures=False,
        strokes=option.show_paint_effects(),
        motionTrails=False,
        pluginShapes=option.show_plugin_shapes(),
        clipGhosts=False,
        greasePencils=False,
        pluginObjects=('gpuCacheDisplayFilter', option.show_gpu_cache()),
        manipulators=False,
        grid=False,
        headsUpDisplay=False,
        holdOuts=False,
        selectionHiliteDisplay=False,
    )
    cmds.formLayout(
        layout,
        edit=True,
        attachForm=[
            (panel, 'top', 0),
            (panel, 'left', 0),
            (panel, 'bottom', 0),
            (panel, 'right', 0),
        ],
    )
    return (window, panel, editor)


def playblast(layer_name: str, option: PlayblastOption) -> None:
    '''Playblast from specific layer.'''
    window, panel, _ = create_playblast_window(option)
    ssao: bool = cmds.getAttr('hardwareRenderingGlobals.ssaoEnable')
    mb: bool = cmds.getAttr('hardwareRenderingGlobals.motionBlurEnable')
    msaa: bool = cmds.getAttr('hardwareRenderingGlobals.multiSampleEnable')
    start_frame: float = cmds.getAttr('defaultRenderGlobals.startFrame')
    end_frame: float = cmds.getAttr('defaultRenderGlobals.endFrame')

    cmds.setAttr('hardwareRenderingGlobals.ssaoEnable', option.ssao())
    cmds.setAttr('hardwareRenderingGlobals.motionBlurEnable', option.mb())
    cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable', option.msaa())

    cmds.setFocus(panel)
    cmds.playblast(
        format=option.format(),
        filename=option.filename(layer_name),
        forceOverwrite=True,
        sequenceTime=False,
        clearCache=True,
        viewer=False,
        showOrnaments=option.show_ornaments(),
        offScreen=True,
        framePadding=option.frame_padding(),
        percent=int(option.scale() * 100),
        compression=option.encoding(),
        quality=option.quality(),
        widthHeight=(option.width(), option.height()),
        startTime=int(start_frame),
        endTime=int(end_frame),
    )

    cmds.setAttr('hardwareRenderingGlobals.ssaoEnable', ssao)
    cmds.setAttr('hardwareRenderingGlobals.motionBlurEnable', mb)
    cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable', msaa)
    cmds.deleteUI(window)


def apply() -> bool:
    '''Playblast from Render Setup Layers.'''
    render_setup: renderSetup.RenderSetup = renderSetup.instance()
    default_layer: renderLayer.RenderLayer = (
        render_setup.getDefaultRenderLayer()
    )
    layers: list[renderLayer.RenderLayer] = render_setup.getRenderLayers()
    if default_layer.isRenderable():
        layers.insert(0, default_layer)

    option = PlayblastOption()
    option.from_settings(Settings.instance(__name__, True))

    for layer in layers:
        if not layer.isRenderable():
            continue

        render_setup.switchToLayer(layer)
        playblast(layer.name(), option)

    render_setup.switchToLayer(default_layer)
    _logger.info('Done.')
    return True


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
