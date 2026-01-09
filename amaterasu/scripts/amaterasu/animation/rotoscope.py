# ==============================================================================
#
# Rotoscope
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from functools import partial

try:
    from PySide2.QtCore import Qt, Slot, Signal
    from PySide2.QtGui import QCloseEvent
    from PySide2.QtWidgets import (
        QWidget,
        QMainWindow,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QToolButton,
        QMessageBox,
        QMenu,
        QActionGroup,
        QAction,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot, Signal
        from PySide6.QtGui import QCloseEvent, QActionGroup, QAction
        from PySide6.QtWidgets import (
            QWidget,
            QMainWindow,
            QVBoxLayout,
            QHBoxLayout,
            QPushButton,
            QToolButton,
            QMessageBox,
            QMenu,
        )
from maya import cmds, mel
from . import shift_lens, dolly_zoom, camera_rig
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Rotoscope'
__version__: str = '1.40'
__doc__ = 'This tool is usefull operation for the layout and the animation.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant = parser.Variant('')

    camera: parser.Variant[str] = parser.Variant('persp')
    displayLights: parser.Variant[str] = parser.Variant('default')
    bufferMode: parser.Variant[str] = parser.Variant('double')
    activeOnly: parser.Variant[bool] = parser.Variant(False)
    twoSidedLighting: parser.Variant[bool] = parser.Variant(False)
    displayAppearance: parser.Variant[str] = parser.Variant('smoothShaded')
    wireframeOnShaded: parser.Variant[bool] = parser.Variant(False)
    useDefaultMaterial: parser.Variant[bool] = parser.Variant(False)
    wireframeBackingStore: parser.Variant[bool] = parser.Variant(False)
    backfaceCulling: parser.Variant[bool] = parser.Variant(True)
    xray: parser.Variant[bool] = parser.Variant(False)
    jointXray: parser.Variant[bool] = parser.Variant(False)
    activeComponentsXray: parser.Variant[bool] = parser.Variant(False)
    maxConstantTransparency: parser.Variant[float] = parser.Variant(1.0)
    displayTextures: parser.Variant[bool] = parser.Variant(False)
    smoothWireframe: parser.Variant[bool] = parser.Variant(False)
    lineWidth: parser.Variant[float] = parser.Variant(1.0)
    textureAnisotropic: parser.Variant[bool] = parser.Variant(False)
    textureSampling: parser.Variant[int] = parser.Variant(2)
    textureDisplay: parser.Variant[str] = parser.Variant('modulate')
    textureHilight: parser.Variant[bool] = parser.Variant(True)
    fogging: parser.Variant[bool] = parser.Variant(False)
    fogSource: parser.Variant[str] = parser.Variant('fragment')
    fogMode: parser.Variant[str] = parser.Variant('linear')
    fogDensity: parser.Variant[float] = parser.Variant(0.1)
    fogEnd: parser.Variant[float] = parser.Variant(100.0)
    fogStart: parser.Variant[float] = parser.Variant(0.0)
    fogColor: parser.Variant[list[float]] = parser.Variant([0.5, 0.5, 0.5, 1])
    shadows: parser.Variant[bool] = parser.Variant(False)
    rendererName: parser.Variant[str] = parser.Variant('vp2Renderer')
    colorResolution: parser.Variant[list[int]] = parser.Variant([256, 156])
    bumpResolution: parser.Variant[list[int]] = parser.Variant([512, 512])
    transparencyAlgorithm: parser.Variant[str] = parser.Variant(
        'frontAndBackCull'
    )
    transpInShadows: parser.Variant[bool] = parser.Variant(False)
    cullingOverride: parser.Variant[str] = parser.Variant('none')
    lowQualityLighting: parser.Variant[bool] = parser.Variant(False)
    occlusionCulling: parser.Variant[bool] = parser.Variant(False)
    useBaseRenderer: parser.Variant[bool] = parser.Variant(False)
    useInteractiveMode: parser.Variant[bool] = parser.Variant(False)
    sortTransparent: parser.Variant[bool] = parser.Variant(True)
    viewSelected: parser.Variant[bool] = parser.Variant(False)

    controllers: parser.Variant[bool] = parser.Variant(True)
    nurbsCurves: parser.Variant[bool] = parser.Variant(True)
    nurbsSurfaces: parser.Variant[bool] = parser.Variant(True)
    controlVertices: parser.Variant[bool] = parser.Variant(True)
    hulls: parser.Variant[bool] = parser.Variant(True)
    polymeshes: parser.Variant[bool] = parser.Variant(True)
    subdivSurfaces: parser.Variant[bool] = parser.Variant(True)
    planes: parser.Variant[bool] = parser.Variant(True)
    lights: parser.Variant[bool] = parser.Variant(True)
    cameras: parser.Variant[bool] = parser.Variant(True)
    imagePlane: parser.Variant[bool] = parser.Variant(True)
    joints: parser.Variant[bool] = parser.Variant(True)
    ikHandles: parser.Variant[bool] = parser.Variant(True)
    deformers: parser.Variant[bool] = parser.Variant(True)
    dynamics: parser.Variant[bool] = parser.Variant(True)
    particleInstancers: parser.Variant[bool] = parser.Variant(True)
    fluids: parser.Variant[bool] = parser.Variant(True)
    hairSystems: parser.Variant[bool] = parser.Variant(True)
    follicles: parser.Variant[bool] = parser.Variant(True)
    nCloths: parser.Variant[bool] = parser.Variant(True)
    nParticles: parser.Variant[bool] = parser.Variant(True)
    nRigids: parser.Variant[bool] = parser.Variant(True)
    dynamicConstraints: parser.Variant[bool] = parser.Variant(True)
    locators: parser.Variant[bool] = parser.Variant(True)
    dimensions: parser.Variant[bool] = parser.Variant(True)
    pivots: parser.Variant[bool] = parser.Variant(True)
    handles: parser.Variant[bool] = parser.Variant(True)
    textures: parser.Variant[bool] = parser.Variant(True)
    strokes: parser.Variant[bool] = parser.Variant(True)
    motionTrails: parser.Variant[bool] = parser.Variant(True)
    pluginShapes: parser.Variant[bool] = parser.Variant(True)
    clipGhosts: parser.Variant[bool] = parser.Variant(True)
    greasePencils: parser.Variant[bool] = parser.Variant(True)
    manipulators: parser.Variant[bool] = parser.Variant(True)
    headsUpDisplay: parser.Variant[bool] = parser.Variant(True)
    grid: parser.Variant[bool] = parser.Variant(True)
    selectionHiliteDisplay: parser.Variant[bool] = parser.Variant(True)

    def write_from_model_panel(self, model_panel: str) -> None:
        '''Write flag value from model panel.'''
        self.write_from_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)
        )

    def write_from_model_editor(self, model_editor: str) -> None:
        '''Write flag value from model editor.'''
        for element in self:
            try:
                if element.name() == 'window_geo':
                    continue

                kwargs: dict[str, bool] = {'q': True, element.name(): True}
                element.set_value(cmds.modelEditor(model_editor, **kwargs))

            except RuntimeError:
                _logger.warning('Unsupport flag : %s', element.name())

    def write_to_model_panel(self, model_panel: str) -> None:
        '''Write flag value to model panel.'''
        self.write_to_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)
        )

    def write_to_model_editor(self, model_editor: str) -> None:
        '''Write flag value to model editor.'''
        for element in self:
            try:
                if element.name() == 'window_geo':
                    continue

                kwargs: dict[str, bool] = {
                    "e": True,
                    element.name(): element.value(),
                }
                cmds.modelEditor(model_editor, **kwargs)

            except RuntimeError:
                _logger.warning("Unsupport flag : %s", element.name())


class ChooseItemButton(QToolButton):
    '''Click on this to display a menu and select one of the items.'''

    changed_item = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPopupMode(QToolButton.InstantPopup)

        self.__menu: QMenu = QMenu(self)
        self.setMenu(self.__menu)

        self.__action_grp: QActionGroup = QActionGroup(self)
        self.__action_grp.triggered.connect(self.change_item_callback)

    def add_menu_item(self, item: str) -> None:
        '''Add menu item.'''
        if item != '---':
            action: QAction = self.__menu.addAction(item)
            action.setCheckable(True)
            self.__action_grp.addAction(action)
        else:
            self.__menu.addSeparator()

    def set_menu_items(self, items: list[str]) -> None:
        '''Set menu item.'''
        self.__menu.clear()
        for item in items:
            self.add_menu_item(item)

        first_action: QAction = self.__action_grp.actions()[0]
        first_action.setChecked(True)
        self.changed_item.emit(first_action.text())

    def menu(self) -> QMenu:
        '''Return menu.'''
        return self.__menu

    def action_group(self) -> QActionGroup:
        '''Return action group.'''
        return self.__action_grp

    def current_checked_item(self) -> str:
        '''Return currect checked item.'''
        action: QAction = self.__action_grp.checkedAction()
        if not action:
            return ''

        return self.__action_grp.checkedAction().text()

    def change_item_callback(self, action: QAction) -> None:
        '''Change item callback'''
        self.changed_item.emit(action.text())


class CameraItemButton(ChooseItemButton):
    '''Choose camera button'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget'''
        super().__init__(parent)
        self.setIcon(widgets.icon_from_file_name('a_camera.png'))

    def update_menu(self) -> None:
        '''Update menu.'''
        self.menu().clear()
        action: QAction = self.menu().addAction('Create Camera Rig...')
        action.triggered.connect(partial(self.create_camera))

        self.menu().addSeparator()

        default_camera: list[str] = ['persp', 'top', 'front', 'side']
        for camera in cmds.ls(type="camera"):
            parent: list[str] = (
                cmds.listRelatives(camera, parent=True, path=True) or []
            )
            if not parent:
                continue

            if parent[0] in default_camera:
                continue

            self.add_menu_item(parent[0])

        self.add_menu_item('---')

        for camera in default_camera:
            self.add_menu_item(camera)

        action = self.action_group().actions()[0]
        action.setChecked(True)
        self.changed_item.emit(action.text())

    def create_camera(self) -> None:
        '''Create camera.'''
        # camera_root: str = cmds.group(name='cameraRoot_ctrl', empty=True)
        # camera_offset_a: str = cmds.group(
        #     name='cameraOffsetA_ctrl', empty=True, parent=camera_root
        # )
        # camera_offset_b: str = cmds.group(
        #     name='cameraOffsetB_ctrl', empty=True, parent=camera_offset_a
        # )
        # camera, camera_shape = cmds.camera()
        # cmds.setAttr(f'{camera_shape}.focalLength', 50)
        # cmds.setAttr(f'{camera_shape}.bestFitClippingPlanes', False)
        # cmds.setAttr(f'{camera_shape}.nearClipPlane', 1.0)
        # cmds.setAttr(f'{camera_shape}.farClipPlane', 10000.0)
        # cmds.setAttr(f'{camera_shape}.displayResolution', True)
        # cmds.setAttr(f'{camera_shape}.overscan', 1.3)
        # cmds.setAttr(f'{camera_shape}.displayGateMaskOpacity', 1.0)
        # cmds.setAttr(
        #     f'{camera_shape}.displayGateMaskColor', 0, 0, 0, type='double3'
        # )
        # cmds.setAttr(f'{camera_shape}.locatorScale', 10)

        # camera = cmds.parent(camera, camera_offset_b)[0]
        # camera = cmds.rename(camera, 'render_cam')
        # for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
        #     cmds.setAttr(f'{camera}.{attr}', lock=True)

        # persp_guide: str = cmds.group(
        #     name='perspectiveGuide_grp', empty=True, parent=camera_root
        # )
        # persp_guide_offset: str = cmds.group(
        #     name='perspectiveGuideOffset_grp', empty=True, parent=persp_guide
        # )
        # horizontal_curve: str = cmds.circle(
        #     name='horizontalLine_crv',
        #     center=(0, 0, 0),
        #     normal=(0, 1, 0),
        #     sweep=360,
        #     radius=10,
        #     degree=3,
        #     useTolerance=False,
        #     tolerance=0.01,
        #     sections=8,
        #     ch=False,
        # )[0]
        # cmds.setAttr(f'{horizontal_curve}.overrideEnabled', 1)
        # cmds.setAttr(f'{horizontal_curve}.overrideDisplayType', 2)
        # cmds.setAttr(f'{horizontal_curve}.lineWidth', 3)
        # horizontal_curve = cmds.parent(horizontal_curve, persp_guide_offset)[0]

        # vertical_curve: str = cmds.circle(
        #     name='verticalLine_crv',
        #     center=(0, 0, 0),
        #     normal=(1, 0, 0),
        #     sweep=360,
        #     radius=10,
        #     degree=3,
        #     useTolerance=False,
        #     tolerance=0.01,
        #     sections=8,
        #     ch=False,
        # )[0]
        # cmds.setAttr(f'{vertical_curve}.overrideEnabled', 1)
        # cmds.setAttr(f'{vertical_curve}.overrideDisplayType', 2)
        # cmds.setAttr(f'{vertical_curve}.lineWidth', 3)
        # vertical_curve = cmds.parent(vertical_curve, persp_guide_offset)[0]

        # cmds.pointConstraint(camera, persp_guide, maintainOffset=False)
        camera_rig.main()
        cmds.select(clear=True)
        self.update_menu()


class ImagePlaneItemButton(ChooseItemButton):
    '''Choose image plane button'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget'''
        super().__init__(parent)
        self.setIcon(widgets.icon_from_file_name('a_image.png'))

    def update_menu(self, camera: str) -> None:
        '''Update menu.'''
        self.menu().clear()
        action: QAction = self.menu().addAction('Import Image...')
        action.triggered.connect(partial(self.import_image, camera))

        self.menu().addSeparator()

        camera_shapes: list[str] = (
            cmds.listRelatives(camera, shapes=True, path=True) or []
        )
        if not camera_shapes:
            return

        camera_shape: str = camera_shapes[0]
        images: list[str] = cmds.listConnections(
            camera_shape, source=True, destination=False, type='imagePlane'
        )
        if not images:
            return

        for image in images:
            image = image.split('->')[-1]
            self.add_menu_item(image)

        action = self.action_group().actions()[0]
        action.setChecked(True)
        self.changed_item.emit(action.text())

    @Slot(str)
    @widgets.undo
    def import_image(self, camera: str) -> None:
        '''Import image plane.'''
        workspace: str = cmds.workspace(query=True, fullName=True)
        mel.eval(f'setWorkingDirectory "{workspace}" "image" "sourceImages"')

        files = cmds.fileDialog2(
            caption='Open',
            okCaption='Open',
            fileMode=1,
            startingDirectory=workspace,
            returnFilter=True,
            fileFilter='Image Files (*.map *.pix *.als *.ALS *.jpeg *.JPEG *.jpg *.JPG *.pntg *.PNTG *.ps *.PS *.png *.PNG *.psd *.PSD *.pict *.PICT *.tx *.TX *.tex *.TEX *.ptx *.qt *.QT *.qtif *.QTIF *.sgi *.SGI *.tga *.TGA *.tif *.TIF *.bmp *.BMP *.tiff *.TIFF *.iff *.IFF *.rgb *.RGB *.tdi *.TDI *.gif *.GIF *.exr *.EXR *.xpm *.XPM *.hdr *.HDR *.dds *.DDS);;All Files (*)',
            selectFileFilter='Image Files',
        )

        if not files:
            return

        width: float = cmds.optionVar(query='freeImageWidth')
        height: float = cmds.optionVar(query='freeImageHeight')
        maintain_ratio: int = cmds.optionVar(query='freeImageMR')

        image_plane: list[str] = cmds.imagePlane(
            camera=camera,
            width=width,
            height=height,
            maintainRatio=maintain_ratio,
        )
        cmds.setAttr(f'{image_plane[1]}.displayOnlyIfCurrent', 1)
        cmds.imagePlane(image_plane[1], edit=True, lookThrough=camera)
        try:
            cmds.setAttr(f'{image_plane[1]}.viewNameUsed', 1)
            cmds.setAttr(
                f'{image_plane[1]}.viewNameStr',
                'ACES 1.0 SDR-video',
                type='string',
            )
        except RuntimeError:
            pass
        cmds.setAttr(f'{image_plane[1]}.type', 0)
        cmds.setAttr(f'{image_plane[1]}.imageName', files[0], type='string')

        pixmap_size: list[int] = cmds.imagePlane(
            image_plane[1], query=True, imageSize=True
        )
        cmds.imagePlane(image_plane[1], edit=True, width=pixmap_size[0] / 100.0)
        cmds.imagePlane(
            image_plane[1], edit=True, height=pixmap_size[1] / 100.0
        )
        cmds.connectAttr(f'{camera}.filmOffset', f'{image_plane[1]}.offset')
        self.update_menu(camera)

        render_width: int = cmds.getAttr('defaultResolution.width')
        render_height: int = cmds.getAttr('defaultResolution.height')
        device_aspect: float = float(pixmap_size[0]) / float(pixmap_size[1])
        if pixmap_size[0] != render_width or pixmap_size[1] != render_height:
            result = QMessageBox.question(
                self,
                'Question',
                (
                    'Image size and render image size do not match.\n'
                    + 'Do you want to set the render image size?\n\n'
                    + f'{render_width} x {render_height} -> {pixmap_size[0]} x {pixmap_size[1]}'
                ),
                QMessageBox.Yes | QMessageBox.No,
            )

            if result != QMessageBox.Yes:
                return

            cmds.setAttr("defaultResolution.width", pixmap_size[0])
            cmds.setAttr("defaultResolution.height", pixmap_size[1])
            cmds.setAttr("defaultResolution.deviceAspectRatio", device_aspect)
            cmds.setAttr("defaultResolution.pixelAspect", 1.00)

        camera_x: float = cmds.getAttr(f'{camera}.horizontalFilmAperture')
        camera_y: float = cmds.getAttr(f'{camera}.verticalFilmAperture')
        fit_type: int = cmds.getAttr(f'{camera}.filmFit')
        camera_aspect: float = camera_x / camera_y

        if fit_type == 0:  # FILL
            if device_aspect < camera_aspect:
                cmds.setAttr(
                    f"{image_plane[1]}.sizeX",
                    camera_y * device_aspect,
                )
                cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y)
            else:
                cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
                cmds.setAttr(
                    f"{image_plane[1]}.sizeY",
                    camera_x * device_aspect,
                )

        elif fit_type == 1:  # Horizontal
            cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
            cmds.setAttr(f"{image_plane[1]}.sizeY", camera_x / device_aspect)

        elif fit_type == 2:  # Vertical
            cmds.setAttr(f"{image_plane[1]}.sizeX", camera_y)
            cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y * device_aspect)

        elif fit_type == 3:  # Overscan
            if device_aspect < camera_aspect:
                cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
                cmds.setAttr(
                    f"{image_plane[1]}.sizeY",
                    camera_x / device_aspect,
                )
            else:
                cmds.setAttr(
                    f"{image_plane[1]}.sizeX",
                    camera_y * device_aspect,
                )
                cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y)


class OptionWidget(QWidget):
    '''Option Widget'''

    main_layout_name: str = 'AmaterasuRotoScopeMainLayout'

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setObjectName('RotoScope' + str(id(self)))

        # Main Layout
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setObjectName('Layout' + str(id(self)))

        # Viewport
        cmds.setParent(main_layout.objectName())
        self.__pane_layout_name: str = cmds.paneLayout()
        self.__model_panel_name: str = cmds.modelPanel()
        main_layout.addWidget(
            widgets.maya_control_to_qt(self.__pane_layout_name), True
        )

        # Rotoscope Tool(1)
        layout: QHBoxLayout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.setObjectName('Layout' + str(id(layout)))
        main_layout.addLayout(layout)

        self.__camera: CameraItemButton = CameraItemButton(self)
        layout.addWidget(self.__camera)

        self.__image_plane: ImagePlaneItemButton = ImagePlaneItemButton(self)
        self.__image_plane.setIcon(widgets.icon_from_file_name('a_image.png'))
        layout.addWidget(self.__image_plane)

        layout.addWidget(widgets.VerticalLine(self))

        self.__display_mode: str = cmds.attrEnumOptionMenuGrp(
            label='D',
            columnWidth=([1, 10], [2, 50], [3, 1], [4, 1]),
            adjustableColumn=2,
        )
        display_mode_qt = widgets.maya_control_to_qt(self.__display_mode)
        layout.addWidget(display_mode_qt)
        self.__display_mode = display_mode_qt.objectName()

        self.__alpha: str = cmds.attrFieldSliderGrp(
            label='A',
            min=0,
            max=1,
            columnWidth=([1, 10], [2, 60], [4, 1]),
            adjustableColumn=3,
        )
        alpha_qt = widgets.maya_control_to_qt(self.__alpha)
        layout.addWidget(alpha_qt, True)
        self.__alpha = alpha_qt.objectName()

        button: QPushButton = QPushButton('0.0', self)
        button.clicked.connect(partial(self.set_image_plane_alpha, 0))
        layout.addWidget(button)

        button = QPushButton('0.5', self)
        button.clicked.connect(partial(self.set_image_plane_alpha, 0.5))
        layout.addWidget(button)

        button = QPushButton('1.0', self)
        button.clicked.connect(partial(self.set_image_plane_alpha, 1.0))
        layout.addWidget(button)

        self.__depth: str = cmds.attrFieldSliderGrp(
            label='D',
            # minValue=0.01,
            # maxValue=100000,
            sliderMinValue=0.1,
            sliderMaxValue=10000,
            columnWidth=([1, 10], [2, 70], [4, 1]),
            adjustableColumn=3,
        )
        depth_qt = widgets.maya_control_to_qt(self.__depth)
        layout.addWidget(depth_qt, True)
        self.__depth = depth_qt.objectName()

        # Rotoscope Tool(2)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.setObjectName('Layout' + str(id(layout)))
        main_layout.addLayout(layout)

        self.__offset_x: str = cmds.attrFieldSliderGrp(
            label='X',
            minValue=-1,
            maxValue=1,
            sliderMinValue=-1,
            sliderMaxValue=1,
            columnWidth=([1, 10], [2, 60], [4, 1]),
            adjustableColumn=3,
        )
        offset_x_qt = widgets.maya_control_to_qt(self.__offset_x)
        layout.addWidget(offset_x_qt, True)
        self.__offset_x = offset_x_qt.objectName()

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous2.png'))
        button.clicked.connect(partial(self.set_film_offset, 0.01, None))
        button.setToolTip('Set film Offset X to 0.01.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous.png'))
        button.clicked.connect(partial(self.set_film_offset, 0.001, None))
        button.setToolTip('Set film Offset X to 0.001.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_zero.png'))
        button.setToolTip('Set film Offset X to 0.')
        button.clicked.connect(partial(self.set_film_offset, 0.0, None))
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next.png'))
        button.clicked.connect(partial(self.set_film_offset, -0.001, None))
        button.setToolTip('Set film Offset X to -0.001.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next2.png'))
        button.setToolTip('Set film Offset X to -0.01.')
        button.clicked.connect(partial(self.set_film_offset, -0.01, None))
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        self.__offset_y: str = cmds.attrFieldSliderGrp(
            label='Y',
            minValue=-1,
            maxValue=1,
            sliderMinValue=-1,
            sliderMaxValue=1,
            columnWidth=([1, 10], [2, 60], [4, 1]),
            adjustableColumn=3,
        )
        offset_y_qt = widgets.maya_control_to_qt(self.__offset_y)
        layout.addWidget(offset_y_qt, True)
        self.__offset_y = offset_y_qt.objectName()

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous2.png'))
        button.clicked.connect(partial(self.set_film_offset, None, 0.01))
        button.setToolTip('Set film Offset Y to 0.01.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_previous.png'))
        button.clicked.connect(partial(self.set_film_offset, None, 0.001))
        button.setToolTip('Set film Offset Y to 0.001.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_zero.png'))
        button.clicked.connect(partial(self.set_film_offset, None, 0.0))
        button.setToolTip('Set film Offset Y to 0.')
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next.png'))
        button.setToolTip('Set film Offset Y to -0.001.')
        button.clicked.connect(partial(self.set_film_offset, None, -0.001))
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_next2.png'))
        button.setToolTip('Set film Offset Y to -0.01.')
        button.clicked.connect(partial(self.set_film_offset, None, -0.01))
        button.setMaximumSize(24, 24)
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        icon_btn: widgets.IconButton = widgets.IconButton(self)
        icon_btn.set_icon('a_attribute.png')
        icon_btn.setToolTip('Show Attribute Editor')
        icon_btn.clicked.connect(self.show_attribute_editor)
        layout.addWidget(icon_btn)

        model_editor: str = cmds.modelPanel(
            self.__model_panel_name, query=True, modelEditor=True
        )
        image_plane_vis: bool = cmds.modelEditor(
            model_editor, query=True, imagePlane=True
        )
        self.__toggle_image_plane: widgets.IconButton = widgets.IconButton(self)
        self.__toggle_image_plane.set_icon('a_image_plane.png')
        self.__toggle_image_plane.setToolTip('Toggle display image planes.')
        self.__toggle_image_plane.setCheckable(True)
        self.__toggle_image_plane.setChecked(image_plane_vis)
        self.__toggle_image_plane.clicked.connect(self.toggle_image_plane)
        layout.addWidget(self.__toggle_image_plane)

        icon_btn: widgets.IconButton = widgets.IconButton(self)
        icon_btn.set_icon('a_shift_lens.png')
        icon_btn.setToolTip('Show Shift Lens')
        icon_btn.clicked.connect(self.shift_lens_callback)
        layout.addWidget(icon_btn)

        icon_btn: widgets.IconButton = widgets.IconButton(self)
        icon_btn.set_icon('a_zoom_out.png')
        icon_btn.setToolTip('Show Dolly Zoom')
        icon_btn.clicked.connect(self.dolly_zoom_callback)
        layout.addWidget(icon_btn)

        icon_btn = widgets.IconButton(self)
        icon_btn.set_icon('a_update.png')
        icon_btn.setToolTip('Update window.')
        icon_btn.clicked.connect(self.update_ui)
        layout.addWidget(icon_btn)

        # Event
        self.__camera.changed_item[str].connect(self.change_camera_callback)
        self.__image_plane.changed_item[str].connect(
            self.change_image_plane_callback
        )
        self.update_ui()

    def cleanup(self) -> None:
        '''Clean up maya ui.'''
        cmds.deleteUI(self.__display_mode)
        cmds.deleteUI(self.__alpha)
        cmds.deleteUI(self.__depth)
        cmds.deleteUI(self.__offset_x)
        cmds.deleteUI(self.__offset_y)
        cmds.deleteUI(self.__model_panel_name)
        cmds.deleteUI(self.__pane_layout_name)

    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.parent().restoreGeometry(
            widgets.to_qt(settings.window_geo.value())
        )
        settings.write_to_model_panel(self.__model_panel_name)

    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(
            widgets.to_ascii(self.parent().saveGeometry())
        )
        settings.write_from_model_panel(self.__model_panel_name)
        settings.write()

    def show_attribute_editor(self) -> None:
        '''Show attribute editor.'''
        image_plane: str = self.__image_plane.current_checked_item()
        camera: str = self.__camera.current_checked_item()
        if image_plane:
            cmds.select(image_plane)
        else:
            cmds.select(camera)

        mel.eval('ShowAttributeEditorOrChannelBox;')

    def toggle_image_plane(self) -> None:
        '''Toggle display image plane.'''
        model_editor: str = cmds.modelPanel(
            self.__model_panel_name, query=True, modelEditor=True
        )
        cmds.modelEditor(
            model_editor,
            edit=True,
            imagePlane=self.__toggle_image_plane.isChecked(),
        )

    @widgets.undo
    def shift_lens_callback(self) -> None:
        '''Shift lens callback'''
        camera: str = self.__camera.current_checked_item()
        shift_lens.main(camera)

    @widgets.undo
    def dolly_zoom_callback(self) -> None:
        '''Dolly zoom callback'''
        camera: str = self.__camera.current_checked_item()
        dolly_zoom.main(camera)

    @widgets.undo
    def set_film_offset(
        self, value_x: float | None, value_y: float | None
    ) -> None:
        '''Set film offset.'''
        camera: str = self.__camera.current_checked_item()
        offset_x: str = f'{camera}.horizontalFilmOffset'
        offset_y: str = f'{camera}.verticalFilmOffset'
        if value_x is not None:
            if value_x != 0:
                cmds.setAttr(offset_x, cmds.getAttr(offset_x) + value_x)
            else:
                cmds.setAttr(offset_x, 0)

        if value_y is not None:
            if value_y != 0:
                cmds.setAttr(offset_y, cmds.getAttr(offset_y) + value_y)
            else:
                cmds.setAttr(offset_y, 0)

    @widgets.undo
    def set_image_plane_alpha(self, value: float) -> None:
        '''Set image plane alpha.'''
        image_plane: str = self.__image_plane.current_checked_item()
        cmds.setAttr(f'{image_plane}.alphaGain', value)

    def change_camera_callback(self, camera: str) -> None:
        '''Change camera callback.'''
        cmds.modelPanel(self.__model_panel_name, edit=True, camera=camera)
        cmds.attrFieldSliderGrp(
            self.__offset_x,
            edit=True,
            attribute=f'{camera}.horizontalFilmOffset',
        )
        cmds.attrFieldSliderGrp(
            self.__offset_y,
            edit=True,
            attribute=f'{camera}.verticalFilmOffset',
        )
        self.__image_plane.update_menu(camera)

    def change_image_plane_callback(self, image_plane: str) -> None:
        '''Change image plane callback'''
        camera: str = self.__camera.current_checked_item()
        slider_min_value: float = cmds.getAttr(f'{camera}.nearClipPlane')
        slider_max_value: float = cmds.getAttr(f'{camera}.farClipPlane')
        cmds.attrEnumOptionMenuGrp(
            self.__display_mode,
            edit=True,
            attribute=f'{image_plane}.displayMode',
        )
        cmds.attrFieldSliderGrp(
            self.__alpha,
            edit=True,
            attribute=f'{image_plane}.alphaGain',
        )
        cmds.attrFieldSliderGrp(
            self.__depth,
            edit=True,
            attribute=f'{image_plane}.depth',
            sliderMinValue=slider_min_value,
            sliderMaxValue=slider_max_value,
        )

    def update_ui(self) -> None:
        '''Update ui'''
        self.__camera.update_menu()


# QMainWindow is required to convert Maya's UI to QT.
class MainWindow(QMainWindow):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        if not parent:
            parent = widgets.maya_window_to_qt()

        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(720, 640)

        self.__option_widget: OptionWidget = OptionWidget(self)
        self.__option_widget.load_settings()
        self.setCentralWidget(self.__option_widget)

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        # Cleanup so that Maya will not crash.
        self.__option_widget.save_settings()
        self.__option_widget.cleanup()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
