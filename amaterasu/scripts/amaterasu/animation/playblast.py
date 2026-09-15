# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Quick playblast from the rendering setup."""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from maya import cmds, mel
from maya.app.renderSetup.model import renderSetup
from maya.app.renderSetup.model import renderLayer
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Playblast"
__version__: str = "1.31"
_logger: utils.Logger = utils.get_logger(__product__)

DEFAULT_FILE_NAME_PREFIX: str = "<Scene>/<RenderLayer>/<RenderLayer>"


class Settings(framework.ToolSettings):
    """Settings for the Playblast tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved geometry of the window.
        sub_folder (framework.Variant[str]): Subfolder name for output.
        format (framework.Variant[str]): Output format (e.g., image, movie).
        encoding (framework.Variant[str]): Compression encoding (e.g., png).
        quality (framework.Variant[int]): Output quality percentage.
        frame_padding (framework.Variant[int]): Padding length for image sequences.
        scale (framework.Variant[float]): Playblast resolution scale.
        use_default_material (framework.Variant[bool]): Use default material.
        wireframe_on_shaded (framework.Variant[bool]): Wireframe on shaded.
        display_texture (framework.Variant[bool]): Display textures.
        display_lights (framework.Variant[bool]): Enable lighting display.
        ssao (framework.Variant[bool]): Enable Screen-space Ambient Occlusion.
        mb (framework.Variant[bool]): Enable motion blur.
        msaa (framework.Variant[bool]): Enable Multisampling Anti-aliasing.
        show_ornaments (framework.Variant[bool]): Show ornaments.
        show_polygon (framework.Variant[bool]): Show polygons.
        show_cv_curve (framework.Variant[bool]): Show CV curves.
        show_nurbs (framework.Variant[bool]): Show NURBS surfaces.
        show_fluids (framework.Variant[bool]): Show fluids.
        show_particle (framework.Variant[bool]): Show particles.
        show_paint_effects (framework.Variant[bool]): Show paint effects.
        show_plugin_shapes (framework.Variant[bool]): Show plugin shapes.
        show_gpu_cache (framework.Variant[bool]): Show GPU caches.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    sub_folder: framework.Variant[str] = framework.Variant("playblast")
    format: framework.Variant[str] = framework.Variant("image")
    encoding: framework.Variant[str] = framework.Variant("png")
    quality: framework.Variant[int] = framework.Variant(100)
    frame_padding: framework.Variant[int] = framework.Variant(4)
    scale: framework.Variant[float] = framework.Variant(1.0)

    use_default_material: framework.Variant[bool] = framework.Variant(False)
    wireframe_on_shaded: framework.Variant[bool] = framework.Variant(False)
    display_texture: framework.Variant[bool] = framework.Variant(True)
    display_lights: framework.Variant[bool] = framework.Variant(False)
    ssao: framework.Variant[bool] = framework.Variant(False)
    mb: framework.Variant[bool] = framework.Variant(False)
    msaa: framework.Variant[bool] = framework.Variant(False)

    show_ornaments: framework.Variant[bool] = framework.Variant(False)
    show_polygon: framework.Variant[bool] = framework.Variant(True)
    show_cv_curve: framework.Variant[bool] = framework.Variant(False)
    show_nurbs: framework.Variant[bool] = framework.Variant(False)
    show_fluids: framework.Variant[bool] = framework.Variant(False)
    show_particle: framework.Variant[bool] = framework.Variant(False)
    show_paint_effects: framework.Variant[bool] = framework.Variant(True)
    show_plugin_shapes: framework.Variant[bool] = framework.Variant(False)
    show_gpu_cache: framework.Variant[bool] = framework.Variant(True)


@dataclass
class PlayblastOption:
    """Struct-like data class for Playblast Options."""

    sub_folder: str = ""
    format: str = ""
    encoding: str = ""
    quality: int = 100
    frame_padding: int = 4
    scale: float = 1.0
    use_default_material: bool = False
    wireframe_on_shaded: bool = False
    display_texture: bool = True
    display_lights: bool = False
    ssao: bool = False
    mb: bool = False
    msaa: bool = False
    show_ornaments: bool = False
    show_polygon: bool = True
    show_cv_curve: bool = False
    show_nurbs: bool = False
    show_fluids: bool = False
    show_particle: bool = False
    show_paint_effects: bool = True
    show_plugin_shapes: bool = False
    show_gpu_cache: bool = False

    width: int = field(init=False)
    height: int = field(init=False)
    camera: str = field(init=False)

    def __post_init__(self) -> None:
        """Initialize dynamic attributes like resolution and camera."""
        self.width: int = cmds.getAttr("defaultResolution.width")
        self.height: int = cmds.getAttr("defaultResolution.height")
        self.camera: str = "persp"
        for camera in cmds.ls(type="camera"):
            if not cmds.getAttr(f"{camera}.renderable"):
                continue

            parent: list[str] = (
                cmds.listRelatives(camera, parent=True, path=True) or []
            )
            if not parent:
                continue

            self.camera = parent[0]
            break

    def filename(self, layer_name: str = "") -> str:
        """Generates the absolute output filename for the playblast.

        Args:
            layer_name (str, optional): The name of the render layer.
                Defaults to "".

        Returns:
            str: The formatted absolute file path.
        """
        file_prefix: str = (
            cmds.getAttr("defaultRenderGlobals.imageFilePrefix")
            or DEFAULT_FILE_NAME_PREFIX
        )
        workspace_root: str = cmds.workspace(query=True, rootDirectory=True)  # type: ignore
        images_dir: str = cmds.workspace(fileRuleEntry="images")  # type: ignore

        filename: str = os.path.join(
            workspace_root, images_dir, self.sub_folder, file_prefix
        )

        scene_name: str = cmds.file(query=True, sceneName=True, shortName=True)  # type: ignore
        scene_base_name, _ = os.path.splitext(
            scene_name if scene_name else "untitled"
        )
        version: str = (
            cmds.getAttr("defaultRenderGlobals.renderVersion") or "v01"
        )

        filename = filename.replace("<Scene>", scene_base_name)
        filename = filename.replace("<RenderLayer>", layer_name)
        filename = filename.replace("<Camera>", self.camera)
        filename = filename.replace("<RenderPassFileGroup>", "")
        filename = filename.replace("<RenderPass>", "")
        filename = filename.replace("<RenderPassType>", "")
        filename = filename.replace("<Extension>", self.encoding)
        filename = filename.replace("<Version>", version)
        filename = filename.replace("<", "_")
        filename = filename.replace(">", "_")
        filename = os.path.normpath(filename)
        return filename

    def from_settings(self, settings: Settings) -> None:
        """Set option values from the tool settings.

        Args:
            settings (Settings): The current tool settings instance.
        """
        self.sub_folder = settings.sub_folder.value()
        self.format = settings.format.value()
        self.encoding = settings.encoding.value()
        self.quality = settings.quality.value()
        self.frame_padding = settings.frame_padding.value()
        self.scale = settings.scale.value()

        self.use_default_material = settings.use_default_material.value()
        self.wireframe_on_shaded = settings.wireframe_on_shaded.value()
        self.display_texture = settings.display_texture.value()
        self.display_lights = settings.display_lights.value()
        self.ssao = settings.ssao.value()
        self.mb = settings.mb.value()
        self.msaa = settings.msaa.value()

        self.show_ornaments = settings.show_ornaments.value()
        self.show_polygon = settings.show_polygon.value()
        self.show_cv_curve = settings.show_cv_curve.value()
        self.show_nurbs = settings.show_nurbs.value()
        self.show_fluids = settings.show_fluids.value()
        self.show_particle = settings.show_particle.value()
        self.show_paint_effects = settings.show_paint_effects.value()
        self.show_plugin_shapes = settings.show_plugin_shapes.value()
        self.show_gpu_cache = settings.show_gpu_cache.value()


class MainWindow(framework.StandardToolWindow[Settings]):
    """Main window for the Playblast tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): A unique ID for restoring window
                states. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 600)
        self.__file_format_layout: widgets.FormLayout
        self.__frame_padding_index: int
        self.__format: QtWidgets.QComboBox
        self.__encoding: QtWidgets.QComboBox

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)

        # Output Settings
        output_frame = widgets.FrameWidget(
            "Output Settings", False, True, parent
        )
        main_layout.addWidget(output_frame)
        output_layout = widgets.FormLayout()
        output_frame.setLayout(output_layout)

        output_layout.addRow(
            widgets.FormLabel("Output"),
            QtWidgets.QLabel(
                "From Render Settings.\n"
                f"If empty, output will be {DEFAULT_FILE_NAME_PREFIX}."
            ),
        )

        sub_folder = QtWidgets.QLineEdit(self)
        output_layout.addRow(widgets.FormLabel("Sub Folder"), sub_folder)

        # File Format Settings
        file_format_frame = widgets.FrameWidget(
            "File Format Settings", False, True, parent
        )
        main_layout.addWidget(file_format_frame)
        self.__file_format_layout = widgets.FormLayout()
        file_format_frame.setLayout(self.__file_format_layout)

        self.__format = QtWidgets.QComboBox(self)
        self.__format.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.__format.addItems(cmds.playblast(query=True, format=True))  # type: ignore
        self.__file_format_layout.addRow(
            widgets.FormLabel("Format"), self.__format
        )

        self.__encoding = QtWidgets.QComboBox(self)
        self.__encoding.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.__file_format_layout.addRow(
            widgets.FormLabel("Encoding"), self.__encoding
        )

        quality = QtWidgets.QSpinBox(self)
        quality.setRange(0, 100)
        quality.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.__file_format_layout.addRow(widgets.FormLabel("Quality"), quality)

        frame_padding = QtWidgets.QSpinBox(self)
        frame_padding.setRange(0, 100)
        frame_padding.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        self.__file_format_layout.addRow(
            widgets.FormLabel("Frame Padding"), frame_padding
        )
        self.__frame_padding_index = self.__file_format_layout.row_id()

        # Frame Range
        range_frame = widgets.FrameWidget("Frame Range", False, True, parent)
        main_layout.addWidget(range_frame)

        range_layout = widgets.FormLayout()
        range_frame.setLayout(range_layout)
        range_layout.addRow(
            widgets.FormLabel("Frame Range"),
            QtWidgets.QLabel("From Render Settings."),
        )

        # Camera Settings
        camera_frame = widgets.FrameWidget(
            "Camera Settings", False, True, parent
        )
        main_layout.addWidget(camera_frame)
        camera_layout = widgets.FormLayout()
        camera_frame.setLayout(camera_layout)

        camera_layout.addRow(
            widgets.FormLabel("Camera"),
            QtWidgets.QLabel("From Render Settings. (Only the first.)"),
        )
        camera_layout.addRow(
            widgets.FormLabel("Resolution"),
            QtWidgets.QLabel("From Render Settings."),
        )

        scale = QtWidgets.QDoubleSpinBox(self)
        scale.setRange(0.0, 100.0)
        scale.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum,
        )
        scale.setSingleStep(0.1)
        camera_layout.addRow(widgets.FormLabel("Scale"), scale)

        # Shading Settings
        shading_frame = widgets.FrameWidget(
            "Shading Settings", False, True, parent
        )
        main_layout.addWidget(shading_frame)
        shading_layout = widgets.FormLayout()
        shading_frame.setLayout(shading_layout)

        use_default_mat = QtWidgets.QCheckBox("Use Default Material", self)
        shading_layout.addRow(widgets.FormLabel(""), use_default_mat)

        wireframe = QtWidgets.QCheckBox("Wireframe on Shaded", self)
        shading_layout.addRow(widgets.FormLabel(""), wireframe)

        display_tex = QtWidgets.QCheckBox("Display Texture", self)
        shading_layout.addRow(widgets.FormLabel(""), display_tex)

        display_lights = QtWidgets.QCheckBox("Lighting", self)
        shading_layout.addRow(widgets.FormLabel(""), display_lights)

        ssao = QtWidgets.QCheckBox("Screen-space Ambient Occlusion", self)
        shading_layout.addRow(widgets.FormLabel(""), ssao)

        mb = QtWidgets.QCheckBox("Motion Blur", self)
        shading_layout.addRow(widgets.FormLabel(""), mb)

        msaa = QtWidgets.QCheckBox("Multisampling Anti-aliasing", self)
        shading_layout.addRow(widgets.FormLabel(""), msaa)

        # Display Settings
        display_frame = widgets.FrameWidget(
            "Display Settings", False, True, parent
        )
        main_layout.addWidget(display_frame)
        display_layout = widgets.FormLayout()
        display_frame.setLayout(display_layout)

        show_ornaments = QtWidgets.QCheckBox("Show Ornaments", self)
        display_layout.addRow(widgets.FormLabel(""), show_ornaments)

        show_polygon = QtWidgets.QCheckBox("Show Polygon", self)
        display_layout.addRow(widgets.FormLabel(""), show_polygon)

        show_cv_curve = QtWidgets.QCheckBox("Show CV Curve", self)
        display_layout.addRow(widgets.FormLabel(""), show_cv_curve)

        show_nurbs = QtWidgets.QCheckBox("Show NURBS", self)
        display_layout.addRow(widgets.FormLabel(""), show_nurbs)

        show_fluids = QtWidgets.QCheckBox("Show Fluids", self)
        display_layout.addRow(widgets.FormLabel(""), show_fluids)

        show_particle = QtWidgets.QCheckBox("Show Particle", self)
        display_layout.addRow(widgets.FormLabel(""), show_particle)

        show_paint_fx = QtWidgets.QCheckBox("Show Paint Effects", self)
        display_layout.addRow(widgets.FormLabel(""), show_paint_fx)

        show_plugin_sh = QtWidgets.QCheckBox("Show Plugin Shapes", self)
        display_layout.addRow(widgets.FormLabel(""), show_plugin_sh)

        show_gpu_cache = QtWidgets.QCheckBox("Show GPU Cache", self)
        display_layout.addRow(widgets.FormLabel(""), show_gpu_cache)

        main_layout.addStretch(1)

        # Settings Binding
        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.sub_folder.bind(
            setter=sub_folder.setText,
            getter=sub_folder.text,
        )
        settings.format.bind(
            setter=self.__format.setCurrentText,
            getter=self.__format.currentText,
        )
        settings.encoding.bind(
            setter=self.__encoding.setCurrentText,
            getter=self.__encoding.currentText,
        )
        settings.quality.bind(
            setter=quality.setValue,
            getter=quality.value,
        )
        settings.frame_padding.bind(
            setter=frame_padding.setValue,
            getter=frame_padding.value,
        )
        settings.scale.bind(
            setter=scale.setValue,
            getter=scale.value,
        )
        settings.use_default_material.bind(
            setter=use_default_mat.setChecked,
            getter=use_default_mat.isChecked,
        )
        settings.wireframe_on_shaded.bind(
            setter=wireframe.setChecked,
            getter=wireframe.isChecked,
        )
        settings.display_texture.bind(
            setter=display_tex.setChecked,
            getter=display_tex.isChecked,
        )
        settings.display_lights.bind(
            setter=display_lights.setChecked,
            getter=display_lights.isChecked,
        )
        settings.ssao.bind(
            setter=ssao.setChecked,
            getter=ssao.isChecked,
        )
        settings.mb.bind(
            setter=mb.setChecked,
            getter=mb.isChecked,
        )
        settings.msaa.bind(
            setter=msaa.setChecked,
            getter=msaa.isChecked,
        )
        settings.show_ornaments.bind(
            setter=show_ornaments.setChecked,
            getter=show_ornaments.isChecked,
        )
        settings.show_polygon.bind(
            setter=show_polygon.setChecked,
            getter=show_polygon.isChecked,
        )
        settings.show_cv_curve.bind(
            setter=show_cv_curve.setChecked,
            getter=show_cv_curve.isChecked,
        )
        settings.show_nurbs.bind(
            setter=show_nurbs.setChecked,
            getter=show_nurbs.isChecked,
        )
        settings.show_fluids.bind(
            setter=show_fluids.setChecked,
            getter=show_fluids.isChecked,
        )
        settings.show_particle.bind(
            setter=show_particle.setChecked,
            getter=show_particle.isChecked,
        )
        settings.show_paint_effects.bind(
            setter=show_paint_fx.setChecked,
            getter=show_paint_fx.isChecked,
        )
        settings.show_plugin_shapes.bind(
            setter=show_plugin_sh.setChecked,
            getter=show_plugin_sh.isChecked,
        )
        settings.show_gpu_cache.bind(
            setter=show_gpu_cache.setChecked,
            getter=show_gpu_cache.isChecked,
        )

        # Events
        self.__format.currentTextChanged.connect(self.set_valid_options)
        self.set_valid_options(self.__format.currentText())

    def set_valid_options(self, output_format: str) -> None:
        """Synchronizes encoding options with the selected format.

        Args:
            output_format (str): The currently selected output format.
        """
        self.__encoding.clear()
        state: bool = cmds.commandEcho(query=True, state=True)  # type: ignore

        cmds.commandEcho(state=False)
        encodings: list[str] = mel.eval(
            f"$am_playblastFormat = `playblast -format {output_format} -query -compression`;"
        )
        if encodings:
            self.__encoding.addItems(encodings)

        cmds.commandEcho(state=state)
        self.__file_format_layout.set_row_enabled(
            self.__frame_padding_index, bool(output_format == "image")
        )

    @dcc.undo
    def apply(self) -> None:
        """Applies the settings and executes the playblast."""
        self.save_settings()
        apply(self.tool_settings())


def create_playblast_window(option: PlayblastOption) -> tuple[str, str, str]:
    """Creates a temporary model panel window for playblasting.

    Args:
        option (PlayblastOption): The current playblast options data class.

    Returns:
        tuple[str, str, str]: A tuple containing the window, panel, and
            editor names.
    """
    window: str = cmds.window()  # type: ignore
    layout: str = cmds.formLayout()  # type: ignore
    panel: str = cmds.modelPanel()  # type: ignore
    editor: str = cmds.modelPanel(panel, query=True, modelEditor=True)  # type: ignore
    cmds.modelEditor(
        editor,
        edit=True,
        camera=option.camera,
        displayAppearance="smoothShaded",
        useDefaultMaterial=option.use_default_material,
        wireframeOnShaded=option.wireframe_on_shaded,
        displayTextures=option.display_texture,
        displayLights="all" if option.display_lights else "default",
        nurbsCurves=option.show_cv_curve,
        nurbsSurfaces=option.show_nurbs,
        controlVertices=False,
        hulls=False,
        polymeshes=option.show_polygon,
        subdivSurfaces=False,
        planes=False,
        lights=False,
        cameras=False,
        imagePlane=False,
        joints=False,
        ikHandles=False,
        deformers=False,
        dynamics=False,
        particleInstancers=option.show_particle,
        fluids=option.show_fluids,
        hairSystems=False,
        follicles=False,
        nCloths=False,
        nParticles=option.show_particle,
        nRigids=False,
        dynamicConstraints=False,
        locators=False,
        dimensions=False,
        pivots=False,
        handles=False,
        textures=False,
        strokes=option.show_paint_effects,
        motionTrails=False,
        pluginShapes=option.show_plugin_shapes,
        clipGhosts=False,
        greasePencils=False,
        pluginObjects=("gpuCacheDisplayFilter", option.show_gpu_cache),
        manipulators=False,
        grid=False,
        headsUpDisplay=False,
        holdOuts=False,
        selectionHiliteDisplay=False,
    )  # type: ignore
    cmds.formLayout(
        layout,
        edit=True,
        attachForm=[
            (panel, "top", 0),
            (panel, "left", 0),
            (panel, "bottom", 0),
            (panel, "right", 0),
        ],
    )
    return (window, panel, editor)


def playblast(layer_name: str, option: PlayblastOption) -> None:
    """Executes the playblast for a specific render layer.

    Args:
        layer_name (str): The name of the render layer.
        option (PlayblastOption): The current playblast options data class.
    """
    window, panel, _ = create_playblast_window(option)
    ssao: bool = cmds.getAttr("hardwareRenderingGlobals.ssaoEnable")
    mb: bool = cmds.getAttr("hardwareRenderingGlobals.motionBlurEnable")
    msaa: bool = cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable")
    start_frame: float = cmds.getAttr("defaultRenderGlobals.startFrame")
    end_frame: float = cmds.getAttr("defaultRenderGlobals.endFrame")

    cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", option.ssao)
    cmds.setAttr("hardwareRenderingGlobals.motionBlurEnable", option.mb)
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", option.msaa)

    cmds.setFocus(panel)
    cmds.playblast(
        format=option.format,
        filename=option.filename(layer_name),
        forceOverwrite=True,
        sequenceTime=False,
        clearCache=True,
        viewer=False,
        showOrnaments=option.show_ornaments,
        offScreen=True,
        framePadding=option.frame_padding,
        percent=int(option.scale * 100),
        compression=option.encoding,
        quality=option.quality,
        widthHeight=(option.width, option.height),
        startTime=int(start_frame),
        endTime=int(end_frame),
    )

    cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", ssao)
    cmds.setAttr("hardwareRenderingGlobals.motionBlurEnable", mb)
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", msaa)
    cmds.deleteUI(window)


def apply(settings: Settings | None = None) -> bool:
    """Executes the playblast process based on tool settings.

    Args:
        settings (Settings | None, optional): The tool settings instance to
            use. If None, it initializes settings from the module.
            Defaults to None.
    """
    if settings is None:
        settings = Settings.instance(__name__, True)
        settings.read()

    render_setup: renderSetup.RenderSetup = renderSetup.instance()
    default_layer: renderLayer.RenderLayer = (
        render_setup.getDefaultRenderLayer()
    )
    layers: list[renderLayer.RenderLayer] = render_setup.getRenderLayers()
    if default_layer.isRenderable():
        layers.insert(0, default_layer)

    option = PlayblastOption()
    option.from_settings(settings)

    for layer in layers:
        if not layer.isRenderable():
            continue

        render_setup.switchToLayer(layer)
        playblast(layer.name(), option)

    render_setup.switchToLayer(default_layer)
    _logger.info("Done.")
    return True


def main(unique_id: str = "") -> None:
    """Shows the tool's main window.

    Args:
        unique_id (str, optional): A unique identifier for the window
            instance. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
