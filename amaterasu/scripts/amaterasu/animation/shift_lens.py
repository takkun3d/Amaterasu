# ==============================================================================
#
# Shift Lens
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import math
from functools import partial

try:
    from PySide2.QtCore import Qt, Signal, Slot
    from PySide2.QtWidgets import QWidget, QGridLayout, QSlider, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, Slot
        from PySide6.QtWidgets import QWidget, QGridLayout, QSlider, QPushButton
from maya import cmds
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Shift Lens'
__version__: str = '1.20'
__doc__ = 'Provides vertical lens shift for perspective correction.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class Slider(QSlider):
    '''Brween Slider widget.'''

    drag_start = Signal()
    drag_move = Signal(int)
    drag_end = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setOrientation(Qt.Horizontal)
        self.setRange(-101, 101)  # Bug?
        self.setValue(0)
        self.sliderPressed.connect(self.__drag_start)
        self.sliderMoved.connect(self.__drag_move)
        self.sliderReleased.connect(self.__drag_end)

    @Slot()
    def __drag_start(self) -> None:
        '''Drag start event.'''
        self.drag_start.emit()

    @Slot()
    def __drag_move(self) -> None:
        '''Drag move event.'''
        self.drag_move.emit(self.value())

    @Slot()
    def __drag_end(self) -> None:
        '''Drag end event.'''
        self.setValue(0)
        self.drag_end.emit()


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
        self.__current_rotate_x: float = 0.0

        option_widget: QWidget = self.option_widget()
        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        picker_layout: widgets.FormLayout = widgets.FormLayout(self)
        main_layout.addLayout(picker_layout, 0, 0, 1, 7)

        self.__camera: widgets.NodePicker = widgets.NodePicker(1, self)
        picker_layout.addRow(widgets.FormLabel('Camera'), self.__camera)

        line: widgets.HorizontalLine = widgets.HorizontalLine(self)
        main_layout.addWidget(line, 1, 0, 1, 7)

        slider = Slider(self)
        slider.drag_start.connect(self.drag_start)
        slider.drag_move.connect(self.drag_move)
        slider.drag_end.connect(self.drag_end)
        main_layout.addWidget(slider, 2, 0, 1, 7)

        line: widgets.HorizontalLine = widgets.HorizontalLine(self)
        main_layout.addWidget(line, 3, 0, 1, 7)

        button: QPushButton = QPushButton('<<<', self)
        button.clicked.connect(partial(self.apply_offset, 5))
        main_layout.addWidget(button, 4, 0)

        button: QPushButton = QPushButton('<<', self)
        button.clicked.connect(partial(self.apply_offset, 1))
        main_layout.addWidget(button, 4, 1)

        button: QPushButton = QPushButton('<', self)
        button.clicked.connect(partial(self.apply_offset, 0.1))
        main_layout.addWidget(button, 4, 2)

        button: QPushButton = QPushButton('Auto', self)
        button.clicked.connect(self.apply_auto)
        main_layout.addWidget(button, 4, 3)

        button: QPushButton = QPushButton('>', self)
        button.clicked.connect(partial(self.apply_offset, -0.1))
        main_layout.addWidget(button, 4, 4)

        button: QPushButton = QPushButton('>>', self)
        button.clicked.connect(partial(self.apply_offset, -1))
        main_layout.addWidget(button, 4, 5)

        button: QPushButton = QPushButton('>>>', self)
        button.clicked.connect(partial(self.apply_offset, -5))
        main_layout.addWidget(button, 4, 6)

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

    def set_camera(self, camera: str) -> None:
        '''Set camera to widget.'''
        self.__camera.set_text(camera)

    @Slot()
    def drag_start(self) -> None:
        '''Start slider drag.'''
        camera = self.__camera.text()
        if not camera:
            _logger.error('Camera is required to apply Dolly Zoom.')
            return

        camera_shapes: list[str] = (
            cmds.listRelatives(camera, type='camera') or []
        )
        if not camera_shapes:
            return

        rotate = cmds.xform(camera, query=True, rotation=True, worldSpace=True)
        self.__current_rotate_x = rotate[0]
        cmds.undoInfo(openChunk=True)

    @Slot()
    def drag_move(self, value: int) -> None:
        '''Move slider.'''
        camera = self.__camera.text()
        if not camera:
            return

        rotate_x: float = self.__current_rotate_x * (1.0 - (value / 100.0))
        apply(camera, rotate_x)

    @Slot()
    def drag_end(self) -> None:
        '''End slider drag.'''
        cmds.undoInfo(closeChunk=True)

    @widgets.undo
    def apply_offset(self, offset_value: float) -> None:
        '''Apply'''
        self.save_settings()
        camera = self.__camera.text()
        if not camera:
            _logger.error('Camera is required to apply Dolly Zoom.')
            return

        apply(camera, 0, offset_value)

    @widgets.undo
    def apply_auto(self) -> None:
        '''Apply zero to rotate X'''
        self.save_settings()
        camera = self.__camera.text()
        if not camera:
            _logger.error('Camera is required to apply Dolly Zoom.')
            return

        apply(camera, 0)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(camera: str, rotate_x: float, offset: float | None = None) -> bool:
    '''Dot it'''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return False

    rotate: list[float] = cmds.xform(
        camera, query=True, rotation=True, worldSpace=True
    )
    focal_length: float = cmds.getAttr(f'{camera_shapes[0]}.focalLength')
    current_offset_v = cmds.getAttr(f"{camera_shapes[0]}.verticalFilmOffset")
    if offset is not None:
        rotate_x = rotate[0] + offset

    # Check Aim Camera.(Maya defult)
    aim_target: str = ''
    look_at_nodes: list[str] = (
        cmds.listConnections(
            camera, type='lookAt', source=True, destination=False
        )
        or []
    )
    if look_at_nodes:
        target_nodes: list[str] = (
            cmds.listConnections(
                f'{look_at_nodes[0]}.target[0].targetParentMatrix',
                type='transform',
                source=True,
                destination=False,
            )
            or []
        )
        if target_nodes:
            aim_target = target_nodes[0]

    # Calculate film offset x amout.
    # 25.4 is mm to inch
    offset_amount = (focal_length / 25.4) * (
        math.tan(math.radians(rotate[0])) - math.tan(math.radians(rotate_x))
    )

    # Apply(Camera)
    if not aim_target:
        cmds.xform(
            camera, rotation=(rotate_x, rotate[1], rotate[2]), worldSpace=True
        )

    # Apply(Aim Camera)
    else:
        # Get World Positions
        camera_position: list[float] = cmds.xform(
            camera, query=True, worldSpace=True, translation=True
        )
        target_position: list[float] = cmds.xform(
            aim_target, query=True, worldSpace=True, translation=True
        )

        # Calculate Horizontal Distance (XZ plane only)
        dx: float = target_position[0] - camera_position[0]
        dz: float = target_position[2] - camera_position[2]
        horizontal_distance: float = math.sqrt(dx * dx + dz * dz)

        # Calculate New Height Difference
        height_difference = horizontal_distance * math.tan(
            math.radians(rotate_x)
        )

        # Calculate translate Y
        translate_y = camera_position[1] + height_difference

        # Apply
        cmds.xform(
            aim_target,
            translation=(target_position[0], translate_y, target_position[2]),
            worldSpace=True,
        )

    cmds.setAttr(
        f'{camera_shapes[0]}.verticalFilmOffset',
        current_offset_v + offset_amount,
    )
    return True


def main(unique_id: str = '', camera: str | None = None) -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    if camera is not None:
        window.set_camera(camera)
    window.show()
