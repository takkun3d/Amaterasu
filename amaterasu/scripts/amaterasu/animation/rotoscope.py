# ==============================================================================
#
# Rotoscope
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import os
from functools import partial

try:
    from PySide2.QtCore import Qt, Signal, QTimer, QSize
    from PySide2.QtGui import (
        QPixmap,
        QCloseEvent,
        QDragEnterEvent,
        QDragMoveEvent,
        QDropEvent,
        QWheelEvent,
        QMouseEvent,
        QKeySequence,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QMessageBox,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QSlider,
        QLineEdit,
        QFileDialog,
        QShortcut,
    )

    PYSIDE_VERSION: int = 2

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QTimer, QSize
        from PySide6.QtGui import (
            QPixmap,
            QCloseEvent,
            QDragEnterEvent,
            QDragMoveEvent,
            QDropEvent,
            QWheelEvent,
            QMouseEvent,
            QKeySequence,
            QShortcut,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QPushButton,
            QMessageBox,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QSlider,
            QLineEdit,
            QFileDialog,
        )

        PYSIDE_VERSION = 6

from maya import OpenMayaUI, cmds, mel
from ..lib import logger, parser, widgets
from . import shift_lens, dolly_zoom, camera_rig

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Rotoscope'
__version__: str = '1.61'
__doc__ = 'This tool is usefull operation for the layout and the animation.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

DEFAULT_MAIN_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 80, 100),
    (2, 20, 100),
]
DEFAULT_LEFT_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 100, 99),
    (2, 100, 1),
]
DEFAULT_RIGHT_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 100, 1),
    (2, 100, 29),
    (3, 100, 70),
]


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    main_panel: parser.Variant[list[tuple[int, int, int]]] = parser.Variant(
        DEFAULT_MAIN_PANEL_SIZE
    )
    left_panel: parser.Variant[list[tuple[int, int, int]]] = parser.Variant(
        DEFAULT_LEFT_PANEL_SIZE
    )
    right_panel: parser.Variant[list[tuple[int, int, int]]] = parser.Variant(
        DEFAULT_RIGHT_PANEL_SIZE
    )

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
    displayTextures: parser.Variant[bool] = parser.Variant(True)
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
    # rendererName: parser.Variant[str] = parser.Variant('vp2Renderer')
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

    controllers: parser.Variant[bool] = parser.Variant(False)
    nurbsCurves: parser.Variant[bool] = parser.Variant(True)
    nurbsSurfaces: parser.Variant[bool] = parser.Variant(False)
    controlVertices: parser.Variant[bool] = parser.Variant(False)
    hulls: parser.Variant[bool] = parser.Variant(False)
    polymeshes: parser.Variant[bool] = parser.Variant(True)
    subdivSurfaces: parser.Variant[bool] = parser.Variant(True)
    planes: parser.Variant[bool] = parser.Variant(False)
    lights: parser.Variant[bool] = parser.Variant(False)
    cameras: parser.Variant[bool] = parser.Variant(False)
    imagePlane: parser.Variant[bool] = parser.Variant(True)
    joints: parser.Variant[bool] = parser.Variant(False)
    ikHandles: parser.Variant[bool] = parser.Variant(False)
    deformers: parser.Variant[bool] = parser.Variant(False)
    dynamics: parser.Variant[bool] = parser.Variant(True)
    particleInstancers: parser.Variant[bool] = parser.Variant(True)
    fluids: parser.Variant[bool] = parser.Variant(False)
    hairSystems: parser.Variant[bool] = parser.Variant(False)
    follicles: parser.Variant[bool] = parser.Variant(False)
    nCloths: parser.Variant[bool] = parser.Variant(False)
    nParticles: parser.Variant[bool] = parser.Variant(True)
    nRigids: parser.Variant[bool] = parser.Variant(False)
    dynamicConstraints: parser.Variant[bool] = parser.Variant(False)
    locators: parser.Variant[bool] = parser.Variant(False)
    dimensions: parser.Variant[bool] = parser.Variant(False)
    pivots: parser.Variant[bool] = parser.Variant(False)
    handles: parser.Variant[bool] = parser.Variant(False)
    textures: parser.Variant[bool] = parser.Variant(False)
    strokes: parser.Variant[bool] = parser.Variant(True)
    motionTrails: parser.Variant[bool] = parser.Variant(True)
    pluginShapes: parser.Variant[bool] = parser.Variant(True)
    clipGhosts: parser.Variant[bool] = parser.Variant(True)
    greasePencils: parser.Variant[bool] = parser.Variant(True)
    manipulators: parser.Variant[bool] = parser.Variant(True)
    headsUpDisplay: parser.Variant[bool] = parser.Variant(True)
    grid: parser.Variant[bool] = parser.Variant(False)
    selectionHiliteDisplay: parser.Variant[bool] = parser.Variant(True)

    def read_from_model_panel(self, model_panel: str) -> None:
        '''Write flag value from model panel.'''
        self.read_from_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)  # type: ignore
        )

    def read_from_model_editor(self, model_editor: str) -> None:
        '''Write flag value from model editor.'''
        for element in self:
            try:
                if element.name() in [
                    'window_geo',
                    'main_panel',
                    'left_panel',
                    'right_panel',
                ]:
                    continue

                kwargs: dict[str, Any] = {
                    'query': True,
                    element.name(): True,
                }
                element.set_value(cmds.modelEditor(model_editor, **kwargs))

            except RuntimeError:
                _logger.warning('Unsupport flag : %s', element.name())

    def write_from_model_panel(self, model_panel: str) -> None:
        '''Write flag value to model panel.'''
        self.write_from_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)  # type: ignore
        )

    def write_from_model_editor(self, model_editor: str) -> None:
        '''Write flag value to model editor.'''
        for element in self:
            try:
                if element.name() in [
                    'window_geo',
                    'main_panel',
                    'left_panel',
                    'right_panel',
                ]:
                    continue

                if element.name() == 'camera':
                    if not cmds.objExists(element.value()):
                        element.set_value('persp')

                kwargs: dict[str, Any] = {
                    'edit': True,
                    element.name(): element.value(),
                }
                cmds.modelEditor(model_editor, **kwargs)

            except RuntimeError:
                _logger.warning('Unsupport flag : %s', element.name())


class BaseCameraDraggerContext:
    '''Base Camera Dragger Context'''

    def __init__(
        self,
        tool_name: str,
        cursor: str = 'crossHair',
        tool_image: str = '',
        help_string: str = '',
        camera: str = '',
    ) -> None:
        '''Initialize'''
        self.__tool_name: str = tool_name
        self.__cursor: str = cursor
        self.__tool_image: str = tool_image
        self.__help: str = help_string
        self.__camera: str = camera
        self.__start_x: float = 0.0
        self.__start_y: float = 0.0
        self.__start_z: float = 0.0

    def cursor(self) -> str:
        '''Return cursor'''
        return self.__cursor

    def set_cursor(self, cursor: str) -> None:
        '''Set cursor'''
        self.__cursor = cursor

    def camera(self) -> str:
        '''Returns camera'''
        return self.__camera

    def set_camera(self, camera: str) -> None:
        '''Set Camera'''
        self.__camera = camera

    def press_event(self) -> None:
        '''Press Event'''
        x: float
        y: float
        z: float
        x, y, z = cmds.draggerContext(
            self.__tool_name, query=True, anchorPoint=True
        )  # type: ignore
        self.__start_x = x
        self.__start_y = y
        self.__start_z = z

        self.__camera = self.camera()
        self.setup_drag()

    def drag_event(self) -> None:
        '''Drag Event'''
        pos: tuple[float, float, float] = cmds.draggerContext(
            self.__tool_name, query=True, dragPoint=True
        )  # type: ignore
        mods: int = cmds.getModifiers()
        self.execute_drag(
            (self.__start_x, self.__start_y, self.__start_z),
            pos,
            (mods & 1) > 0,
            (mods & 4) > 0,
        )
        cmds.refresh()

    def setup_drag(self) -> None:
        '''Setup Drag'''

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        '''Execute Drag'''

    def set_tool(self) -> None:
        '''Execute Tool'''
        if cmds.draggerContext(self.__tool_name, exists=True):
            cmds.deleteUI(self.__tool_name)

        cmds.draggerContext(
            self.__tool_name,
            pressCommand=self.press_event,
            dragCommand=self.drag_event,
            cursor=self.__cursor,
            undoMode='step',
            image1=self.__tool_image,
            helpString=self.__help,
        )
        cmds.setToolTo(self.__tool_name)


class FilmOffsetContext(BaseCameraDraggerContext):
    '''Film Offset Context'''

    def __init__(self, camera: str = '') -> None:
        super().__init__(
            'FilmOffsetTool',
            'track',
            'a_move.png',
            'Film Offset Tool: Drag in the viewport to adjust. (Shift: Lock Axis)',
            camera,
        )
        self.__start_offset_x: float = 0.0
        self.__start_offset_y: float = 0.0
        self.__horizontal_plug: str = ''
        self.__vertical_plug: str = ''
        self.__lock_axis: str = ''

    def setup_drag(self) -> None:
        '''Setup Drag (override)'''
        self.__horizontal_plug = find_target_plug(
            self.camera(),
            'horizontalFilmOffset',
            'filmOffsetSlider_C_ctrl',
            'translateX',
        )
        self.__start_offset_x = cmds.getAttr(self.__horizontal_plug)

        self.__vertical_plug = find_target_plug(
            self.camera(),
            'verticalFilmOffset',
            'filmOffsetSlider_C_ctrl',
            'translateY',
        )
        self.__start_offset_y = cmds.getAttr(self.__vertical_plug)

        self.__lock_axis = ''

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        '''Execute Drag (override)'''
        sensitivity: float = -0.002
        delta_x: float = (pos[0] - start_pos[0]) * sensitivity
        delta_y: float = (pos[1] - start_pos[1]) * sensitivity
        if is_shift:
            abs_x: float = abs(pos[0] - start_pos[0])
            abs_y: float = abs(pos[1] - start_pos[1])
            if not self.__lock_axis and (abs_x > 5 or abs_y > 5):
                if abs_x > abs_y:
                    self.__lock_axis = 'x'

                else:
                    self.__lock_axis = 'y'

            if self.__lock_axis == 'x':
                delta_y = 0.0

            elif self.__lock_axis == 'y':
                delta_x = 0.0

        else:
            self.__lock_axis = ''

        cmds.setAttr(self.__horizontal_plug, self.__start_offset_x + delta_x)
        cmds.setAttr(self.__vertical_plug, self.__start_offset_y + delta_y)


class PostScaleContext(BaseCameraDraggerContext):
    '''Post Scale Context'''

    def __init__(self, camera: str = '') -> None:
        '''Initialize'''
        super().__init__(
            'PostScaleTool',
            'dolly',
            'a_zoom.png',
            'Post Scale Tool: Drag in the viewport to adjust.',
            camera,
        )
        self.__start_post_scale: float = 1.0
        self.__scale_plug: str = ''

    def setup_drag(self) -> None:
        '''Setup Drag (override)'''
        self.__scale_plug = find_target_plug(
            self.camera(),
            'postScale',
            'camera_C_ctrl',
            'postScale',
        )
        self.__start_post_scale = cmds.getAttr(self.__scale_plug)

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        '''Execute Drag (override)'''
        sensitivity: float = 0.002
        delta: float = (
            (pos[0] - start_pos[0]) + (pos[1] - start_pos[1])
        ) * sensitivity
        new_scale: float = max(0.001, self.__start_post_scale + delta)
        cmds.setAttr(self.__scale_plug, new_scale)


class LayerItemWidget(QWidget):
    '''Layer Item Widget'''

    visibility_toggled: Signal = Signal(str, bool)
    name_changed = Signal(str, str)
    update_requested: Signal = Signal()
    request_attribute_editor = Signal(str)

    def __init__(self, node: str, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.__node: str = node

        self.__main_layout = QHBoxLayout(self)
        self.__main_layout.setContentsMargins(4, 4, 4, 4)

        self.__visible: widgets.IconButton = widgets.IconButton(self)
        self.update_visible_state()
        self.__visible.clicked.connect(self.on_visible_clicked)
        self.__main_layout.addWidget(self.__visible)

        self.__thumbnail: QLabel = QLabel()
        self.__thumbnail.setFixedSize(30, 30)
        self.__thumbnail.setAlignment(Qt.AlignCenter)
        self.update_thumbnail()
        self.__main_layout.addWidget(self.__thumbnail)

        self.__name = QLineEdit(self.__node)
        self.__name.setFrame(False)
        self.__name.setReadOnly(True)
        self.__name.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.__name.setStyleSheet('background: transparent;')
        self.__name.editingFinished.connect(self.rename_node)
        self.__main_layout.addWidget(self.__name)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        '''mouseDoubleClickEvent (override)'''
        if self.__name.geometry().contains(event.pos()):
            self.start_editing()
            event.accept()

        else:
            self.request_attribute_editor.emit(self.__node)
            event.accept()

    def on_visible_clicked(self) -> None:
        '''Clicked visible button'''
        if not cmds.objExists(self.__node):
            _logger.error('Does not exists image plane: %s', self.__node)
            self.update_requested.emit()
            return None

        visible: bool = cmds.getAttr(f'{self.__node}.visibility')
        if cmds.getAttr(f'{self.__node}.displayMode') != 3:
            visible = False

        self.visibility_toggled.emit(self.__node, not visible)

    def update_visible_state(self) -> None:
        '''Update visible state'''
        visible: bool = cmds.getAttr(f'{self.__node}.visibility')
        if cmds.getAttr(f'{self.__node}.displayMode') != 3:
            visible = False

        icon: str = 'view/a_show.png' if visible else 'view/a_hide.png'
        self.__visible.set_icon(icon)

    def update_thumbnail(self) -> None:
        '''Update thumbnail'''
        filepath: str = cmds.getAttr(f'{self.__node}.imageName')
        pixmap: QPixmap = QPixmap(filepath)
        if not pixmap.isNull():
            self.__thumbnail.setPixmap(
                pixmap.scaled(
                    self.__thumbnail.width(),
                    self.__thumbnail.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def start_editing(self) -> None:
        '''Start edit mode'''
        self.__name.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.__name.setReadOnly(False)
        self.__name.setFrame(True)
        self.__name.setStyleSheet('')
        self.__name.setFocus()
        self.__name.selectAll()

    def rename_node(self) -> None:
        '''Rename image plane name'''
        self.__name.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.__name.setReadOnly(True)
        self.__name.setFrame(False)
        self.__name.setStyleSheet('background: transparent;')

        new_name: str = self.__name.text()
        if new_name and new_name != self.__node:
            try:
                old_name: str = self.__node
                self.__node = cmds.rename(self.__node, new_name)
                self.__node = self.__node.split('->')[-1]
                self.__name.setText(self.__node)
                self.name_changed.emit(old_name, new_name)

            except RuntimeError:
                self.__name.setText(self.__node)

        else:
            self.__name.setText(self.__node)


class ImagePlaneListWidget(QListWidget):
    '''Image Plane List Widget'''

    order_changed: Signal = Signal()
    files_dropped: Signal = Signal(list)
    wheel_scrolled: Signal = Signal(int)

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        '''dragEnterEvent [override]'''
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        '''dragMoveEvent [override]'''
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        '''dropEvent [override]'''
        if event.mimeData().hasUrls():
            filepaths: list[str] = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            if filepaths:
                self.files_dropped.emit(filepaths)

            event.acceptProposedAction()

        else:
            super().dropEvent(event)
            QTimer.singleShot(0, self.order_changed.emit)

    def wheelEvent(self, event: QWheelEvent) -> None:
        '''wheelEvent [override]'''
        delta: int = event.angleDelta().y()
        step: int = 5 if delta > 0 else -5
        self.wheel_scrolled.emit(step)
        event.accept()
        # super().wheelEvent(event)


class UndoableSlider(QSlider):
    '''Undoable Slider'''

    def __init__(
        self,
        orientation: Qt.Orientation,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(orientation, parent)
        self.sliderPressed.connect(self.begin_undo_chunk)
        self.sliderReleased.connect(self.end_undo_chunk)

    def begin_undo_chunk(self) -> None:
        '''Begin undo chunk'''
        cmds.undoInfo(openChunk=True, chunkName='UndoableSlider')

    def end_undo_chunk(self) -> None:
        '''End undo chunk'''
        cmds.undoInfo(closeChunk=True)


class SubToolManager(QWidget):
    '''Sub Tool Manager'''

    update_requested: Signal = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setWindowFlags(flags)
        self.setObjectName(f'SubToolManager{str(id(self))}')

        self.__camera: str = ''

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(layout)

        button = widgets.IconButton(self)
        button.set_icon('a_move.png')
        button.setToolTip('Film Offset Tool')
        button.clicked.connect(self.film_offset_context)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_zoom.png')
        button.setToolTip('Post Scale Tool')
        button.clicked.connect(self.post_scale_context)
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        button = widgets.IconButton(self)
        button.set_icon('a_shift_lens.png')
        button.setToolTip('Show Shift Lens')
        button.clicked.connect(self.show_shift_lens)
        layout.addWidget(button)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_zoom_out.png')
        button.setToolTip('Show Dolly Zoom')
        button.clicked.connect(self.show_dolly_zoom)
        layout.addWidget(button)

        layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_update.png')
        button.setToolTip('Update window')
        button.clicked.connect(self.update_ui)
        layout.addWidget(button)

        main_layout.addStretch(True)

    def set_camera(self, camera: str) -> None:
        '''Set camera'''
        self.__camera = camera

    def camera(self) -> str:
        '''Returns current camera'''
        return self.__camera

    def show_shift_lens(self) -> None:
        '''Show Dolly Zoom'''
        shift_lens.main(camera=self.camera())

    def show_dolly_zoom(self) -> None:
        '''Show Dolly Zoom'''
        dolly_zoom.main(camera=self.camera())

    def update_ui(self) -> None:
        '''Update UI'''
        self.update_requested.emit()

    def film_offset_context(self) -> None:
        '''Film offset context'''
        context: FilmOffsetContext = FilmOffsetContext(self.camera())
        context.set_tool()

    def post_scale_context(self) -> None:
        '''Post scale context'''
        context: PostScaleContext = PostScaleContext(self.camera())
        context.set_tool()


class CameraInfoManager(QWidget):
    '''Camera Info Manager'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setWindowFlags(flags)
        self.setObjectName(f'CameraInfoManager{str(id(self))}')

        self.__camera: str = ''
        self.__model_editor: str = ''
        current_parent: str = cmds.setParent(query=True)  # type: ignore

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setObjectName(f'Layout{str(id(self))}')
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        layout: QHBoxLayout = QHBoxLayout()
        layout.setObjectName(f'Layout{str(id(layout))}')
        main_layout.addLayout(layout)

        self.__dummy_window: str = cmds.window()  # type:ignore
        self.__dummy_layout: str = cmds.columnLayout()  # type:ignore

        self.__focal_length: str = cmds.attrFieldSliderGrp(
            label='Lens',
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        focal_length_qt: QWidget = widgets.maya_control_to_qt(
            self.__focal_length
        )
        focal_length_qt.setMaximumWidth(100)
        self.__focal_length = focal_length_qt.objectName()
        layout.addWidget(focal_length_qt, True)

        button = widgets.IconButton(self)
        button.set_icon('a_reset.png')
        button.clicked.connect(
            partial(self.reset_value, self.__focal_length, 35)
        )
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        self.__offset_x: str = cmds.attrFieldSliderGrp(
            label='Film X',
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        offset_x_qt: QWidget = widgets.maya_control_to_qt(self.__offset_x)
        offset_x_qt.setMaximumWidth(100)
        self.__offset_x = offset_x_qt.objectName()
        layout.addWidget(offset_x_qt, True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_reset.png')
        button.clicked.connect(partial(self.reset_value, self.__offset_x, 0.0))
        layout.addWidget(button)

        self.__offset_y: str = cmds.attrFieldSliderGrp(
            label='Film Y',
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        offset_y_qt: QWidget = widgets.maya_control_to_qt(self.__offset_y)
        offset_y_qt.setMaximumWidth(100)
        self.__offset_y = offset_y_qt.objectName()
        layout.addWidget(offset_y_qt, True)

        button = widgets.IconButton(self)
        button.set_icon('a_reset.png')
        button.clicked.connect(partial(self.reset_value, self.__offset_y, 0.0))
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        self.__post_scale: str = cmds.attrFieldSliderGrp(
            label='Scale',
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        post_scale_qt: QWidget = widgets.maya_control_to_qt(self.__post_scale)
        post_scale_qt.setMaximumWidth(100)
        self.__post_scale = post_scale_qt.objectName()
        layout.addWidget(post_scale_qt, True)

        button = widgets.IconButton(self)
        button.set_icon('a_reset.png')
        button.clicked.connect(
            partial(self.reset_value, self.__post_scale, 1.0)
        )
        layout.addWidget(button)

        layout.addStretch(True)

        self.__curve: widgets.IconButton = widgets.IconButton(self)
        self.__curve.set_icon('a_curve.png')
        self.__curve.setCheckable(True)
        self.__curve.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__curve)

        self.__polygon: widgets.IconButton = widgets.IconButton(self)
        self.__polygon.set_icon('a_polygon.png')
        self.__polygon.setCheckable(True)
        self.__polygon.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__polygon)

        self.__image_plane: widgets.IconButton = widgets.IconButton(self)
        self.__image_plane.set_icon('a_image_plane.png')
        self.__image_plane.setCheckable(True)
        self.__image_plane.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__image_plane)

        cmds.setParent(current_parent)

    def set_camera(self, camera: str) -> None:
        '''Set camera'''
        self.__camera = camera
        self.update_controllers()

    def camera(self) -> str:
        '''Returns current camera'''
        return self.__camera

    def set_model_editor(self, model_editor: str) -> None:
        '''Set model editor name'''
        self.__model_editor = model_editor
        self.__curve.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, nurbsCurves=True)  # type: ignore
        )
        self.__polygon.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, polymeshes=True)  # type: ignore
        )
        self.__image_plane.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, imagePlane=True)  # type: ignore
        )

    def set_displayed_filter(self) -> None:
        '''Set displayed filter'''
        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            nurbsCurves=self.__curve.isChecked(),
            polymeshes=self.__polygon.isChecked(),
            imagePlane=self.__image_plane.isChecked(),
        )

    def reset_value(self, widget: str, value: float) -> None:
        '''Reset widget value'''
        plug: str = cmds.attrFieldSliderGrp(widget, query=True, attribute=True)  # type: ignore
        if plug:
            cmds.setAttr(plug, value)

    def update_controllers(self) -> None:
        '''Update controllers'''
        plug: str = find_target_plug(
            self.camera(),
            'focalLength',
            'camera_C_ctrl',
            'focalLength',
        )
        cmds.attrFieldSliderGrp(self.__focal_length, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            'horizontalFilmOffset',
            'filmOffsetSlider_C_ctrl',
            'translateX',
        )
        cmds.attrFieldSliderGrp(self.__offset_x, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            'verticalFilmOffset',
            'filmOffsetSlider_C_ctrl',
            'translateY',
        )
        cmds.attrFieldSliderGrp(self.__offset_y, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            'postScale',
            'camera_C_ctrl',
            'postScale',
        )
        cmds.attrFieldSliderGrp(self.__post_scale, edit=True, attribute=plug)

    def cleanup(self) -> None:
        '''Cleanup widgets'''
        cmds.deleteUI(self.__focal_length)
        cmds.deleteUI(self.__offset_x)
        cmds.deleteUI(self.__offset_y)
        cmds.deleteUI(self.__post_scale)
        cmds.deleteUI(self.__dummy_layout)
        cmds.deleteUI(self.__dummy_window)


class CameraManager(QWidget):
    '''Camera Manager'''

    camera_changed: Signal = Signal(str)
    update_requested: Signal = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setWindowFlags(flags)
        self.setObjectName(f'CameraManager{str(id(self))}')

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(header_layout)

        label: QLabel = QLabel('Camera')
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_add.png')
        button.setToolTip('Create Camera')
        button.clicked.connect(self.create_camera)
        header_layout.addWidget(button)

        # button: widgets.IconButton = widgets.IconButton(self)
        # button.set_icon('a_attribute.png')
        # button.setToolTip('Show Attribute Editor')
        # button.clicked.connect(self.show_attribute_editor)
        # header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_trash.png')
        button.setToolTip('Delete Camera')
        button.clicked.connect(self.delete_camera)
        header_layout.addWidget(button)

        self.__camera_list: QListWidget = QListWidget(self)
        self.__camera_list.setSelectionMode(QListWidget.SingleSelection)
        self.__camera_list.itemSelectionChanged.connect(self.switched_camera)
        self.__camera_list.itemDoubleClicked.connect(self.show_attribute_editor)
        main_layout.addWidget(self.__camera_list)

        self.update_cameras()

    def set_camera(self, camera: str) -> None:
        '''Set camera'''
        items: list[QListWidgetItem] = self.__camera_list.findItems(
            camera, Qt.MatchExactly
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)

        self.switched_camera()

    def current_camera(self) -> str:
        '''Returns current camera'''
        items: list[QListWidgetItem] = self.__camera_list.selectedItems()
        if items:
            return items[0].text()

        return ''

    def switched_camera(self) -> None:
        '''Switched camera on list view.'''
        current_camera: str = self.current_camera()
        if current_camera:
            if not cmds.objExists(current_camera):
                _logger.error('Does not exists camera: %s', current_camera)
                self.update_requested.emit()
                return

            self.camera_changed.emit(current_camera)

    def update_cameras(self, current_camera: str = '') -> None:
        '''Update camera list.'''

        def sort_camera(camera: str) -> tuple[int, str]:
            '''Sort camera list'''
            default_order: dict[str, str] = {
                'persp': '1',
                'top': '2',
                'front': '3',
                'side': '4',
            }
            if camera in default_order:
                return (1, default_order[camera])

            return (0, camera)

        self.__camera_list.blockSignals(True)

        if not current_camera:
            current_camera = self.current_camera()

        self.__camera_list.clear()

        cameras: list[str] = []
        camera_shapes: list[str] = cmds.ls(type='camera')
        for camera_shape in camera_shapes:
            parent: str = cmds.listRelatives(
                camera_shape, parent=True, fullPath=True
            )[0]
            parent = cmds.ls(parent)[0]
            cameras.append(parent)

        cameras.sort(key=sort_camera)
        for camera in cameras:
            item: QListWidgetItem = QListWidgetItem(camera)
            self.__camera_list.addItem(item)

        self.__camera_list.blockSignals(False)

        items: list[QListWidgetItem] = self.__camera_list.findItems(
            current_camera, Qt.MatchExactly
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)

    def show_attribute_editor(
        self,
        item: QListWidgetItem | None = None,
    ) -> None:
        '''Show Attribute Editor'''
        camera: str = self.current_camera()
        if item:
            camera = item.text()

        cmds.select(camera)
        mel.eval('ShowAttributeEditorOrChannelBox;')

    @widgets.undo
    def create_camera(self) -> None:
        '''Create Camera'''
        camera: str = 'render_cam'
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Create Camera')
        msg_box.setText('Which type of camera would you like to create?')
        msg_box.setIcon(QMessageBox.Question)

        amaterasu_camera_rig: QPushButton = msg_box.addButton(
            'Camera Rig',
            QMessageBox.ActionRole,
        )
        default_camera: QPushButton = msg_box.addButton(
            'Default Camera',
            QMessageBox.ActionRole,
        )
        msg_box.addButton('Cancel', QMessageBox.RejectRole)

        if PYSIDE_VERSION == 2:
            msg_box.exec_()
        else:
            msg_box.exec()

        if msg_box.clickedButton() == amaterasu_camera_rig:
            if cmds.objExists('render_cam'):
                QMessageBox.critical(
                    self,
                    'Duplicate Camera Rig',
                    'An Amaterasu camera rig already exists in the scene.',
                )
                return

            camera = camera_rig.main()
            camera = cmds.ls(camera)[0]

        elif msg_box.clickedButton() == default_camera:
            created_camera: str = cmds.camera(
                name=camera,
                centerOfInterest=5,
                focalLength=35,
                lensSqueezeRatio=1,
                cameraScale=1,
                horizontalFilmAperture=1.41732,
                horizontalFilmOffset=0,
                verticalFilmAperture=0.94488,
                verticalFilmOffset=0,
                filmFit='horizontal',
                overscan=1.3,
                motionBlur=False,
                shutterAngle=144,
                nearClipPlane=0.1,
                farClipPlane=10000,
                orthographic=False,
                orthographicWidth=30,
                panZoomEnabled=False,
                horizontalPan=0,
                verticalPan=0,
                zoom=1,
                displayResolution=True,
            )  # type: ignore
            camera = cmds.rename(created_camera[0], camera)
            cmds.setAttr(f'{camera}.displayGateMaskOpacity', 0.9)
            cmds.setAttr(
                f'{camera}.displayGateMaskColor', 0, 0, 0, type='double3'
            )
            cmds.setAttr(f'{camera}.locatorScale', 10)

        else:
            return

        cmds.select(clear=True)
        item: QListWidgetItem = QListWidgetItem(camera)
        self.__camera_list.addItem(item)
        self.__camera_list.setCurrentItem(item)
        self.update_cameras()

    @widgets.undo
    def delete_camera(self) -> None:
        '''Delete camera'''
        camera: str = self.current_camera()
        if camera in ['persp', 'top', 'front', 'side']:
            return

        full_path: str = cmds.ls(camera, long=True)[0]
        parts: list[str] = full_path.split('|')
        if len(parts) > 2:
            cmds.delete(parts[1])

        else:
            cmds.delete(camera)

        self.update_cameras()
        items: list[QListWidgetItem] = self.__camera_list.findItems(
            'persp', Qt.MatchExactly
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)


class ImagePlaneManager(QWidget):
    '''Image Plane Manager'''

    update_requested: Signal = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setWindowFlags(flags)
        self.setObjectName(f'CameraManager{str(id(self))}')

        self.__camera: str = ''

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(header_layout)

        label: QLabel = QLabel('Image Plane')
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon('a_add.png')
        button.setToolTip('Create Image Plane')
        button.clicked.connect(self.import_images)
        header_layout.addWidget(button)

        # button: widgets.IconButton = widgets.IconButton(self)
        # button.set_icon('a_attribute.png')
        # button.setToolTip('Show Attribute Editor')
        # button.clicked.connect(self.show_attribute_editor)
        # header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_trash.png')
        button.setToolTip('Delete Image Plane')
        button.clicked.connect(self.delete_image_planes)
        header_layout.addWidget(button)

        slider_layout: QHBoxLayout = QHBoxLayout()
        slider_layout.setContentsMargins(30, 2, 2, 2)
        main_layout.addLayout(slider_layout)

        label = QLabel('Opacity :', self)
        slider_layout.addWidget(label)

        self.__slider: UndoableSlider = UndoableSlider(Qt.Horizontal, self)
        self.__slider.setRange(0, 100)
        self.__slider.setValue(100)
        self.__slider.setEnabled(False)
        self.__slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.__slider)

        self.__image_list: ImagePlaneListWidget = ImagePlaneListWidget(self)
        self.__image_list.itemSelectionChanged.connect(
            self.on_selection_changed
        )
        self.__image_list.order_changed.connect(self.rebuild_after_drop)
        self.__image_list.files_dropped.connect(self.create_image_planes)
        # self.__image_list.itemDoubleClicked.connect(self.show_attribute_editor)
        self.__image_list.wheel_scrolled.connect(self.on_wheel_scrolled)
        main_layout.addWidget(self.__image_list)

        shortcut: QShortcut = QShortcut(
            QKeySequence('Delete'), self.__image_list
        )
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(self.delete_image_planes)

        shortcut = QShortcut(QKeySequence('Ctrl+A'), self.__image_list)
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(self.show_attribute_editor)

    def set_camera(self, camera: str) -> None:
        '''Set camera'''
        self.__camera = camera
        self.update_image_planes()

    def camera(self) -> str:
        '''Returns current camera'''
        return self.__camera

    def current_items(self) -> list[str]:
        '''Returns current items'''
        items: list[QListWidgetItem] = self.__image_list.selectedItems()
        return [item.data(Qt.UserRole) for item in items]

    @widgets.undo
    def on_slider_changed(self, value: int) -> None:
        '''Change opacity slider'''
        nodes: list[str] = self.current_items()
        for node in nodes:
            if not cmds.objExists(node):
                _logger.error('Does not exists image plane: %s', node)
                self.update_image_planes()
                return

            cmds.setAttr(f'{node}.alphaGain', value / 100.0)

    def on_selection_changed(self) -> None:
        '''Change image plane'''
        items: list[QListWidgetItem] = self.__image_list.selectedItems()
        if items:
            node: str = items[0].data(Qt.UserRole)
            if not cmds.objExists(node):
                _logger.error('Does not exists image plane: %s', node)
                self.update_image_planes()
                return

            alpha: float = cmds.getAttr(f'{node}.alphaGain')
            self.__slider.setEnabled(True)
            self.__slider.blockSignals(True)
            self.__slider.setValue(int(alpha * 100))
            self.__slider.blockSignals(False)

        else:
            self.__slider.setEnabled(False)

    @widgets.undo
    def on_wheel_scrolled(self, step: int) -> None:
        '''Change opacity from mouse wheel'''
        if self.__slider.isEnabled():
            new_value: int = max(0, min(100, self.__slider.value() + step))
            self.__slider.setValue(new_value)

    @widgets.undo
    def rebuild_after_drop(self) -> None:
        '''Rebuild depth value'''
        nodes: list[str] = []
        for i in range(self.__image_list.count()):
            item: QListWidgetItem = self.__image_list.item(i)
            nodes.append(item.data(Qt.UserRole))

        if not cmds.objExists(self.camera()):
            self.update_image_planes()
            return

        base_depth: float = cmds.getAttr(f'{self.camera()}.nearClipPlane')
        for i, node in enumerate(nodes):
            if not cmds.objExists(node):
                _logger.error('Does not exists image plane: %s', node)
                self.update_image_planes()
                return

            cmds.setAttr(
                f'{node}.depth',
                base_depth + (i + 1) * base_depth / 10.0,
            )

        # self.update_image_planes()

    @widgets.undo
    def on_visibility_toggled(self, trigger_node: str, new_vis: bool) -> None:
        '''Change image plane visibility'''
        selected_items: list[QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        selected_nodes: list[str] = [
            item.data(Qt.UserRole) for item in selected_items
        ]
        selected_nodes.append(trigger_node)
        for node in selected_nodes:
            cmds.setAttr(f'{node}.visibility', new_vis)
            cmds.setAttr(f'{node}.displayMode', 3 if new_vis else 0)

        for i in range(self.__image_list.count()):
            widget: LayerItemWidget = self.__image_list.itemWidget(
                self.__image_list.item(i)
            )
            widget.update_visible_state()

    def on_layer_name_changed(self, old_name: str, new_name: str) -> None:
        '''Change image plane name'''
        for i in range(self.__image_list.count()):
            item: QListWidgetItem = self.__image_list.item(i)
            if item.data(Qt.UserRole) == old_name:
                item.setData(Qt.UserRole, new_name)
                break

    def update_image_planes(self) -> None:
        '''Update image plane view'''
        selected_nodes: list[str] = [
            item.data(Qt.UserRole) for item in self.__image_list.selectedItems()
        ]
        self.__image_list.clear()

        target_cam: str = self.camera()
        image_planes: list[str] = []

        if target_cam:
            if not cmds.objExists(self.camera()):
                _logger.error('Does not exists camera: %s', self.camera())
                self.update_requested.emit()
                return

            cam_shapes: list[str] = (
                cmds.listRelatives(target_cam, shapes=True, type='camera') or []
            )
            if cam_shapes:
                image_planes = (
                    cmds.listConnections(
                        f'{cam_shapes[0]}.imagePlane', type='imagePlane'
                    )
                    or []
                )

        image_planes.sort(key=lambda node: cmds.getAttr(f'{node}.depth'))
        for image_plane in image_planes:
            node: str = image_plane.split('->')[-1]

            item = QListWidgetItem(self.__image_list)
            item.setSizeHint(QSize(0, 35))
            item.setData(Qt.UserRole, node)

            row_widget = LayerItemWidget(node)
            row_widget.visibility_toggled.connect(self.on_visibility_toggled)
            row_widget.name_changed.connect(self.on_layer_name_changed)
            row_widget.update_requested.connect(self.update_image_planes)
            row_widget.request_attribute_editor.connect(
                self.show_attribute_editor
            )
            self.__image_list.setItemWidget(item, row_widget)

            if image_plane in selected_nodes:
                item.setSelected(True)

    @widgets.undo
    def create_image_plane(self, filepath: str) -> None:
        '''Create image plane from file'''
        camera: str = self.camera()
        width: float = cmds.optionVar(query='freeImageWidth')  # type: ignore
        height: float = cmds.optionVar(query='freeImageHeight')  # type: ignore
        maintain_ratio: bool = cmds.optionVar(query='freeImageMR')  # type: ignore

        if not cmds.objExists(self.camera()):
            self.update_image_planes()
            return

        image_plane: list[str] = cmds.imagePlane(
            camera=camera,
            width=width,
            height=height,
            maintainRatio=maintain_ratio,
        )  # type: ignore
        cmds.imagePlane(image_plane[1], edit=True, lookThrough=camera)
        cmds.setAttr(f'{image_plane[1]}.displayOnlyIfCurrent', 1)
        cmds.setAttr(f'{image_plane[1]}.type', 0)
        cmds.setAttr(f'{image_plane[1]}.imageName', filepath, type='string')

        pixmap_size: list[int] = cmds.imagePlane(
            image_plane[1],
            query=True,
            imageSize=True,
        )  # type: ignore
        cmds.imagePlane(image_plane[1], edit=True, width=pixmap_size[0] / 100.0)
        cmds.imagePlane(
            image_plane[1],
            edit=True,
            height=pixmap_size[1] / 100.0,
        )
        cmds.connectAttr(f'{camera}.filmOffset', f'{image_plane[1]}.offset')

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

            cmds.setAttr('defaultResolution.width', pixmap_size[0])
            cmds.setAttr('defaultResolution.height', pixmap_size[1])
            cmds.setAttr('defaultResolution.deviceAspectRatio', device_aspect)
            cmds.setAttr('defaultResolution.pixelAspect', 1.00)

        camera_x: float = cmds.getAttr(f'{camera}.horizontalFilmAperture')
        camera_y: float = cmds.getAttr(f'{camera}.verticalFilmAperture')
        fit_type: int = cmds.getAttr(f'{camera}.filmFit')
        camera_aspect: float = camera_x / camera_y

        if fit_type == 0:  # FILL
            if device_aspect < camera_aspect:
                cmds.setAttr(
                    f'{image_plane[1]}.sizeX',
                    camera_y * device_aspect,
                )
                cmds.setAttr(f'{image_plane[1]}.sizeY', camera_y)
            else:
                cmds.setAttr(f'{image_plane[1]}.sizeX', camera_x)
                cmds.setAttr(
                    f'{image_plane[1]}.sizeY',
                    camera_x * device_aspect,
                )

        elif fit_type == 1:  # Horizontal
            cmds.setAttr(f'{image_plane[1]}.sizeX', camera_x)
            cmds.setAttr(f'{image_plane[1]}.sizeY', camera_x / device_aspect)

        elif fit_type == 2:  # Vertical
            cmds.setAttr(f'{image_plane[1]}.sizeX', camera_y)
            cmds.setAttr(f'{image_plane[1]}.sizeY', camera_y * device_aspect)

        elif fit_type == 3:  # Overscan
            if device_aspect < camera_aspect:
                cmds.setAttr(f'{image_plane[1]}.sizeX', camera_x)
                cmds.setAttr(
                    f'{image_plane[1]}.sizeY',
                    camera_x / device_aspect,
                )
            else:
                cmds.setAttr(
                    f'{image_plane[1]}.sizeX',
                    camera_y * device_aspect,
                )
                cmds.setAttr(f'{image_plane[1]}.sizeY', camera_y)

        self.update_image_planes()
        self.rebuild_after_drop()

    @widgets.undo
    def create_image_planes(self, filepaths: list[str]) -> None:
        '''Create image planes from files'''
        for filepath in filepaths:
            self.create_image_plane(filepath)

    @widgets.undo
    def import_images(self) -> None:
        '''Import images'''
        workspace: str = cmds.workspace(query=True, fullName=True)  # type: ignore
        start_dir: str = os.path.join(workspace, 'sourceImages')
        if not os.path.exists(start_dir):
            start_dir = workspace

        filepaths: list[str] = []
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            'Import images',
            start_dir,
            'Images (*.png *.jpg *.jpeg *.tif *.tiff *.tga *.bmp)',
        )
        if filepaths:
            self.create_image_planes(filepaths)

    @widgets.undo
    def delete_image_planes(self) -> None:
        '''Delete image plane from selected item in view'''
        items: list[QListWidgetItem] = self.__image_list.selectedItems()
        if not items:
            return

        delete_nodes: list[str] = [item.data(Qt.UserRole) for item in items]
        cmds.delete(*delete_nodes)
        self.update_image_planes()

    def show_attribute_editor(self, node: str = '') -> None:
        '''Show Attribute Editor'''
        nodes: list[str] = [node]
        if node == '':
            items: list[QListWidgetItem] = self.__image_list.selectedItems()
            if not items:
                return

            nodes = [item.data(Qt.UserRole) for item in items]

        cmds.select(*nodes)
        mel.eval('ShowAttributeEditorOrChannelBox;')


class MainWindow(widgets.BaseToolWidget):
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
        self.resize(1280, 720)

        self.__main_panel: str = ''
        self.__left_panel: str = ''
        self.__right_panel: str = ''
        self.__model_panel_name: str = ''
        self.__model_editor_name: str = ''

        self.__subtool_mgr: SubToolManager = SubToolManager(self)
        self.__camera_info_mgr: CameraInfoManager = CameraInfoManager(self)
        self.__camera_mgr: CameraManager = CameraManager(self)
        self.__image_plane_mgr: ImagePlaneManager = ImagePlaneManager(self)

        # Bind the shortcut to a visible child widget instead of 'self'.
        # The MainWindow loses focus after being docked into Maya's UI.
        self.__toggle_shortcut: QShortcut = QShortcut(
            QKeySequence('Ctrl+Space'),
            self.__subtool_mgr,
        )
        self.__toggle_shortcut.setContext(Qt.WindowShortcut)
        self.__main_panel_size: list[tuple[int, int, int]] = []
        self.__left_panel_size: list[tuple[int, int, int]] = []
        self.__is_toggle: bool = False

    # Override
    def show(self) -> None:
        '''Show'''
        self.initialize_workspace()
        parent_path: str | None = self.workspace_window()
        if not parent_path:
            _logger.error('Failed to get workspace window.')
            return

        # Maya's Panel Layout --------------------------------------------------
        self.__main_panel = cmds.paneLayout(
            configuration='vertical2',
            parent=parent_path,
        )  # type: ignore

        self.__left_panel = cmds.paneLayout(
            configuration='horizontal2',
            parent=self.__main_panel,
        )  # type: ignore

        self.__right_panel = cmds.paneLayout(
            configuration='horizontal3',
            parent=self.__main_panel,
        )  # type: ignore

        # ----------------------------------------------------------------------
        # Model Panel
        self.__model_panel_name = cmds.modelPanel(
            unParent=True,
            menuBarVisible=True,
        )  # type: ignore
        cmds.modelPanel(
            self.__model_panel_name,
            edit=True,
            parent=self.__left_panel,
        )
        self.__model_editor_name = cmds.modelPanel(
            self.__model_panel_name,
            query=True,
            modelEditor=True,
        )  # type: ignore

        # ----------------------------------------------------------------------
        # Event
        self.__camera_mgr.camera_changed.connect(self.__subtool_mgr.set_camera)
        self.__camera_mgr.camera_changed.connect(
            self.__camera_info_mgr.set_camera
        )
        self.__camera_mgr.camera_changed.connect(
            self.__image_plane_mgr.set_camera
        )
        self.__camera_mgr.camera_changed.connect(self.set_camera)
        self.__camera_mgr.update_requested.connect(self.update_ui)
        self.__subtool_mgr.update_requested.connect(self.update_ui)
        self.__image_plane_mgr.update_requested.connect(self.update_ui)
        self.__toggle_shortcut.activated.connect(self.toggle_ui_visibility)

        # ----------------------------------------------------------------------
        # Move PySide Widget to Maya's UI
        add_widget_to_maya(self.__camera_info_mgr, self.__left_panel)
        add_widget_to_maya(self.__subtool_mgr, self.__right_panel)
        add_widget_to_maya(self.__camera_mgr, self.__right_panel)
        add_widget_to_maya(self.__image_plane_mgr, self.__right_panel)

        # ----------------------------------------------------------------------
        self.load_settings()
        self.update_ui()

    # Override
    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.save_settings()
        self.__camera_info_mgr.cleanup()
        super().closeEvent(event)

    # Override
    def load_settings(self) -> None:
        '''Load ui settings from file.'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        cmds.paneLayout(
            self.__main_panel, edit=True, paneSize=settings.main_panel.value()
        )
        cmds.paneLayout(
            self.__left_panel, edit=True, paneSize=settings.left_panel.value()
        )
        cmds.paneLayout(
            self.__right_panel, edit=True, paneSize=settings.right_panel.value()
        )
        settings.write_from_model_panel(self.__model_panel_name)

    # Override
    def save_settings(self) -> None:
        '''Save ui settings to file.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.main_panel.set_value(
            self.convert_panel_size(self.__main_panel)
        )
        settings.left_panel.set_value(
            self.convert_panel_size(self.__left_panel)
        )
        settings.right_panel.set_value(
            self.convert_panel_size(self.__right_panel)
        )
        settings.read_from_model_panel(self.__model_panel_name)
        settings.write()

    def convert_panel_size(self, panel: str) -> list[tuple[int, int, int]]:
        '''Convert panel size'''
        data: list[int] = cmds.paneLayout(panel, query=True, paneSize=True)  # type: ignore
        return [
            (index, data[i], data[i + 1])
            for index, i in enumerate(range(0, len(data), 2), 1)
        ]

    def set_camera(self, camera: str) -> None:
        '''Switched camera'''
        cmds.modelPanel(
            self.__model_panel_name,
            edit=True,
            camera=camera,
        )

    def current_camera(self) -> str:
        '''Returns current camera'''
        camera: str = cmds.modelPanel(
            self.__model_panel_name, query=True, camera=True
        )  # type: ignore
        return camera

    def toggle_ui_visibility(self) -> None:
        '''Toggle UI Visibility'''
        if not self.__is_toggle:
            self.__main_panel_size = self.convert_panel_size(self.__main_panel)
            self.__left_panel_size = self.convert_panel_size(self.__left_panel)
            cmds.paneLayout(
                self.__main_panel,
                edit=True,
                paneSize=[(1, 100, 100), (2, 0, 100)],
            )

            cmds.paneLayout(
                self.__left_panel,
                edit=True,
                paneSize=[(1, 100, 100), (2, 100, 0)],
            )

        else:
            # Prevent saving width as 0 when the UI is collapsed.
            if not self.__main_panel_size or self.__main_panel_size[1][1] == 0:
                self.__main_panel_size = DEFAULT_MAIN_PANEL_SIZE

            if not self.__left_panel_size or self.__left_panel_size[1][2] == 0:
                self.__left_panel_size = DEFAULT_LEFT_PANEL_SIZE

            cmds.paneLayout(
                self.__main_panel, edit=True, paneSize=self.__main_panel_size
            )

            cmds.paneLayout(
                self.__left_panel, edit=True, paneSize=self.__left_panel_size
            )

        self.__is_toggle = not self.__is_toggle

    def update_ui(self) -> None:
        '''Update ui'''
        self.__camera_mgr.update_cameras(self.current_camera())
        self.__camera_info_mgr.set_model_editor(self.__model_editor_name)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def add_widget_to_maya(widget: QWidget, parent_name: str) -> None:
    '''Move PySide Widget to Maya's UI'''
    ptr: int = int(OpenMayaUI.MQtUtil.findControl(widget.objectName()))
    parent_ptr: int = int(OpenMayaUI.MQtUtil.findLayout(parent_name))
    OpenMayaUI.MQtUtil.addWidgetToMayaLayout(ptr, parent_ptr)


def find_target_plug(
    start_node: str,
    attr_name: str,
    target_name: str,
    target_attr: str,
) -> str:
    '''Find target plug'''
    start_plug: str = f'{start_node}.{attr_name}'
    connections: list[str] = (
        cmds.listConnections(
            start_plug, source=True, destination=False, plugs=True
        )
        or []
    )
    if not connections:
        return start_plug

    plugs_to_check: list[str] = list(connections)
    visited_plugs: set[str] = set()
    while plugs_to_check:
        current_plug: str = plugs_to_check.pop(0)
        if current_plug in visited_plugs:
            continue

        visited_plugs.add(current_plug)

        node_name: str = current_plug.split('.')[0]
        if target_name in node_name:
            return f'{node_name}.{target_attr}'

        upstreams: list[str] = (
            cmds.listConnections(
                node_name, source=True, destination=False, plugs=True
            )
            or []
        )
        plugs_to_check.extend(upstreams)

    return start_plug


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
