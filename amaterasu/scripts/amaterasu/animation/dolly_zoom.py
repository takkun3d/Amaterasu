# ==============================================================================
#
# Dolly Zoom
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
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
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Dolly Zoom'
__version__: str = '1.10'
__doc__ = 'Applies a Dolly Zoom by adjusting camera distance relative to focal length.'
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
        self.__current_focal_length: float = 35

        option_widget: QWidget = self.option_widget()
        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        picker_layout: widgets.FormLayout = widgets.FormLayout(self)
        main_layout.addLayout(picker_layout, 0, 0, 1, 7)

        self.__camera: widgets.NodePicker = widgets.NodePicker(1, self)
        picker_layout.addRow(widgets.FormLabel('Camera'), self.__camera)

        self.__target: widgets.NodePicker = widgets.NodePicker(1, self)
        picker_layout.addRow(widgets.FormLabel('Target'), self.__target)

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
        button.clicked.connect(partial(self.apply_offset, -5))
        main_layout.addWidget(button, 4, 0)

        button: QPushButton = QPushButton('<<', self)
        button.clicked.connect(partial(self.apply_offset, -1))
        main_layout.addWidget(button, 4, 1)

        button: QPushButton = QPushButton('<', self)
        button.clicked.connect(partial(self.apply_offset, -0.1))
        main_layout.addWidget(button, 4, 2)

        button: QPushButton = QPushButton('>', self)
        button.clicked.connect(partial(self.apply_offset, 0.1))
        main_layout.addWidget(button, 4, 4)

        button: QPushButton = QPushButton('>>', self)
        button.clicked.connect(partial(self.apply_offset, 1))
        main_layout.addWidget(button, 4, 5)

        button: QPushButton = QPushButton('>>>', self)
        button.clicked.connect(partial(self.apply_offset, 5))
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

        target = self.__target.text()
        if not target:
            _logger.error('Target transform is required to apply Dolly Zoom.')
            return

        camera_shapes: list[str] = (
            cmds.listRelatives(camera, type='camera') or []
        )
        if not camera_shapes:
            return

        self.__current_focal_length = cmds.getAttr(
            f'{camera_shapes[0]}.focalLength'
        )
        cmds.undoInfo(openChunk=True)

    @Slot()
    def drag_move(self, value: int) -> None:
        '''Move slider.'''
        camera = self.__camera.text()
        if not camera:
            return

        target = self.__target.text()
        if not target:
            return

        focal_length: float = self.__current_focal_length + (value / 20.0)
        apply(camera, target, focal_length)

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

        target = self.__target.text()
        if not target:
            _logger.error('Target transform is required to apply Dolly Zoom.')
            return

        apply(camera, target, 0, offset_value)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    camera: str, target: str, focal_length: float, offset: float | None = None
) -> bool:
    '''Dot it'''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return False

    current_focal_length: float = cmds.getAttr(
        f'{camera_shapes[0]}.focalLength'
    )

    if offset is not None:
        focal_length = current_focal_length + offset

    if focal_length <= 1:
        return False

    # Distance
    p1: list[float] = cmds.xform(
        camera, query=True, worldSpace=True, translation=True
    )
    p2: list[float] = cmds.xform(
        target, query=True, worldSpace=True, translation=True
    )
    current_distance: float = math.sqrt(
        sum([(a - b) ** 2 for a, b in zip(p1, p2)])
    )
    if current_distance == 0:
        return False

    # New Distance
    # Doubling the focal length doubles the distance.
    distance: float = current_distance * (focal_length / current_focal_length)

    # Calculate vector to move camera to new distance along target vector.
    # Vector = Normalize(CameraPosotion - TargetPosition) * New Distance
    target_vector: list[float] = [(a - b) for a, b in zip(p1, p2)]
    target_vector_length = math.sqrt(sum([x**2 for x in target_vector]))
    target_normalize_vector = [x / target_vector_length for x in target_vector]
    position: list[float] = [
        b + (v * distance) for b, v in zip(p2, target_normalize_vector)
    ]

    # Apply
    cmds.xform(camera, worldSpace=True, translation=position)
    cmds.setAttr(f"{camera_shapes[0]}.focalLength", focal_length)
    return True


def main(unique_id: str = '', camera: str | None = None) -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    if camera is not None:
        window.set_camera(camera)
    window.show()
