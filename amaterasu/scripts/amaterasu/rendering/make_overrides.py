# ==============================================================================
#
# Make Overrides
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt, Signal, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QTabWidget,
        QLabel,
        QComboBox,
        QDoubleSpinBox,
        QSpinBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QTabWidget,
            QLabel,
            QComboBox,
            QDoubleSpinBox,
            QSpinBox,
        )
from maya import cmds
from maya.app.renderSetup.model import utils
from maya.app.renderSetup.views import viewCmds
from maya.app.renderSetup.model.expandedState import setExpandedStateValue
from maya.app.renderSetup.model.renderLayer import RenderLayer
from maya.app.renderSetup.model import group
from maya.app.renderSetup.model.group import Group
from maya.app.renderSetup.model import collection
from maya.app.renderSetup.model.collection import (
    Collection,
    RenderSettingsCollection,
)
from maya.app.renderSetup.model import selector
from maya.app.renderSetup.model.selector import SimpleSelector
from maya.app.renderSetup.model import override
from maya.app.renderSetup.model.override import AbsUniqueOverride
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Make Overrides'
__version__: str = '1.10'
__doc__ = 'Create overrides on the selected layers.'
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
    renderer: parser.Variant[int] = parser.Variant(0)
    start_frame: parser.Variant[float] = parser.Variant(1.0)
    end_frame: parser.Variant[float] = parser.Variant(120.0)
    width: parser.Variant[int] = parser.Variant(1920)
    height: parser.Variant[int] = parser.Variant(1080)
    image_format_sw: parser.Variant[int] = parser.Variant(10)
    image_format_arnold: parser.Variant[int] = parser.Variant(4)
    filter_type_arnold: parser.Variant[int] = parser.Variant(6)
    filter_width_arnold: parser.Variant[float] = parser.Variant(2.0)


class ContainerWidget(QWidget):
    '''Container Widget'''

    apply_clicked = Signal()
    remove_clicked = Signal()

    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

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

        self.__remove_btn: widgets.IconButton = widgets.IconButton(self)
        self.__remove_btn.set_icon('a_trash.png')
        self.__remove_btn.setFixedSize(QSize(24, 24))
        self.__remove_btn.clicked.connect(self.remove_callback)
        main_layout.addWidget(self.__remove_btn, False)

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

    def remove_callback(self) -> None:
        '''Emit signal of remove.'''
        self.remove_clicked.emit()


class DoubleContainerWidget(QWidget):
    '''Double Container Widget'''

    apply_clicked = Signal(float)
    remove_clicked = Signal()

    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_label: widgets.FormLabel = widgets.FormLabel(label, self)
        main_layout.addWidget(self.__form_label, False)

        self.__value: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__value.setRange(-1000000, 1000000)
        self.__value.setButtonSymbols(QDoubleSpinBox.NoButtons)
        main_layout.addWidget(self.__value, True)

        self.__apply_btn: widgets.IconButton = widgets.IconButton(self)
        self.__apply_btn.set_icon('a_apply.png')
        self.__apply_btn.setFixedSize(QSize(24, 24))
        self.__apply_btn.clicked.connect(self.apply_callback)
        main_layout.addWidget(self.__apply_btn, False)

        self.__remove_btn: widgets.IconButton = widgets.IconButton(self)
        self.__remove_btn.set_icon('a_trash.png')
        self.__remove_btn.setFixedSize(QSize(24, 24))
        self.__remove_btn.clicked.connect(self.remove_callback)
        main_layout.addWidget(self.__remove_btn, False)

    def label(self) -> str:
        '''Return label text.'''
        return self.__form_label.text()

    def set_label(self, label: str) -> None:
        '''Set label text.'''
        self.__form_label.setText(label)

    def label_widget(self) -> widgets.FormLabel:
        '''Return label widget.'''
        return self.__form_label

    def value(self) -> float:
        '''Return value'''
        return self.__value.value()

    def set_value(self, value: float) -> None:
        '''Set value.'''
        self.__value.setValue(value)

    def value_widget(self) -> QDoubleSpinBox:
        '''Retirm value widget.'''
        return self.__value

    def apply_button(self) -> widgets.IconButton:
        '''Return apply button.'''
        return self.__apply_btn

    def remove_button(self) -> widgets.IconButton:
        '''Return remove button.'''
        return self.__remove_btn

    def apply_callback(self) -> None:
        '''Emit signal of apply.'''
        self.apply_clicked.emit(self.value())

    def remove_callback(self) -> None:
        '''Emit signal of remove.'''
        self.remove_clicked.emit()


class IntContainerWidget(QWidget):
    '''Int Container Widget'''

    apply_clicked = Signal(int)
    remove_clicked = Signal()

    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_label: widgets.FormLabel = widgets.FormLabel(label, self)
        main_layout.addWidget(self.__form_label, False)

        self.__value: QSpinBox = QSpinBox(self)
        self.__value.setRange(-1000000, 1000000)
        self.__value.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addWidget(self.__value, True)

        self.__apply_btn: widgets.IconButton = widgets.IconButton(self)
        self.__apply_btn.set_icon('a_apply.png')
        self.__apply_btn.setFixedSize(QSize(24, 24))
        self.__apply_btn.clicked.connect(self.apply_callback)
        main_layout.addWidget(self.__apply_btn, False)

        self.__remove_btn: widgets.IconButton = widgets.IconButton(self)
        self.__remove_btn.set_icon('a_trash.png')
        self.__remove_btn.setFixedSize(QSize(24, 24))
        self.__remove_btn.clicked.connect(self.remove_callback)
        main_layout.addWidget(self.__remove_btn, False)

    def label(self) -> str:
        '''Return label text.'''
        return self.__form_label.text()

    def set_label(self, label: str) -> None:
        '''Set label text.'''
        self.__form_label.setText(label)

    def label_widget(self) -> widgets.FormLabel:
        '''Return label widget.'''
        return self.__form_label

    def value(self) -> int:
        '''Return value'''
        return self.__value.value()

    def set_value(self, value: int) -> None:
        '''Set value.'''
        self.__value.setValue(value)

    def value_widget(self) -> QDoubleSpinBox:
        '''Retirm value widget.'''
        return self.__value

    def apply_button(self) -> widgets.IconButton:
        '''Return apply button.'''
        return self.__apply_btn

    def remove_button(self) -> widgets.IconButton:
        '''Return remove button.'''
        return self.__remove_btn

    def apply_callback(self) -> None:
        '''Emit signal of apply.'''
        self.apply_clicked.emit(self.value())

    def remove_callback(self) -> None:
        '''Emit signal of remove.'''
        self.remove_clicked.emit()


class EnumContainerWidget(QWidget):
    '''Enum Container Widget'''

    apply_clicked = Signal(object)
    remove_clicked = Signal()

    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__form_label: widgets.FormLabel = widgets.FormLabel(label, self)
        main_layout.addWidget(self.__form_label, False)

        self.__value: QComboBox = QComboBox(self)
        main_layout.addWidget(self.__value, True)

        self.__apply_btn: widgets.IconButton = widgets.IconButton(self)
        self.__apply_btn.set_icon('a_apply.png')
        self.__apply_btn.setFixedSize(QSize(24, 24))
        self.__apply_btn.clicked.connect(self.apply_callback)
        main_layout.addWidget(self.__apply_btn, False)

        self.__remove_btn: widgets.IconButton = widgets.IconButton(self)
        self.__remove_btn.set_icon('a_trash.png')
        self.__remove_btn.setFixedSize(QSize(24, 24))
        self.__remove_btn.clicked.connect(self.remove_callback)
        main_layout.addWidget(self.__remove_btn, False)

    def label(self) -> str:
        '''Return label text.'''
        return self.__form_label.text()

    def set_label(self, label: str) -> None:
        '''Set label text.'''
        self.__form_label.setText(label)

    def label_widget(self) -> widgets.FormLabel:
        '''Return label widget.'''
        return self.__form_label

    def current_index(self) -> int:
        '''Return value'''
        return self.__value.currentIndex()

    def set_current_index(self, value: int) -> None:
        '''Set value.'''
        self.__value.setCurrentIndex(value)

    def add_item(self, label_datas: list[tuple[str, Any]]) -> None:
        '''Add item to QComboBox.'''
        for label, data in label_datas:
            self.__value.addItem(label, data)

    def item_data(self, index: int) -> Any:
        '''Return data of current item.'''
        return self.__value.itemData(index)

    def value_widget(self) -> QDoubleSpinBox:
        '''Retirm value widget.'''
        return self.__value

    def apply_button(self) -> widgets.IconButton:
        '''Return apply button.'''
        return self.__apply_btn

    def remove_button(self) -> widgets.IconButton:
        '''Return remove button.'''
        return self.__remove_btn

    def apply_callback(self) -> None:
        '''Emit signal of apply.'''
        self.apply_clicked.emit(self.item_data(self.current_index()))

    def remove_callback(self) -> None:
        '''Emit signal of remove.'''
        self.remove_clicked.emit()


class GeneralOption(QWidget):
    '''General option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        self.__renderer = EnumContainerWidget('Renderer', self)
        self.__renderer.add_item(
            [
                ('Maya Software', 'mayaSoftware'),
                ('Maya Hardware 2.0', 'mayaHardware2'),
                ('Pencil+ 4 Line', 'pencil4line'),
                ('Arnold Renderer', 'arnold'),
            ]
        )
        self.__renderer.apply_clicked.connect(self.override_renderer_callback)
        self.__renderer.remove_clicked.connect(
            self.remove_override_renderer_callback
        )
        main_layout.addWidget(self.__renderer)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__start_frame = DoubleContainerWidget('Start Frame', self)
        self.__start_frame.apply_clicked.connect(
            self.override_start_frame_callback
        )
        self.__start_frame.remove_clicked.connect(
            self.remove_override_start_frame_callback
        )
        main_layout.addWidget(self.__start_frame)

        self.__end_frame = DoubleContainerWidget('End Frame', self)
        self.__end_frame.apply_clicked.connect(self.override_end_frame_callback)
        self.__end_frame.remove_clicked.connect(
            self.remove_override_end_frame_callback
        )
        main_layout.addWidget(self.__end_frame)

        main_layout.addWidget(widgets.HorizontalLine(self))

        camera: list[tuple[str, str]] = [(x, x) for x in cmds.ls(type='camera')]
        self.__camera = EnumContainerWidget('Camera', self)
        self.__camera.add_item(camera)
        self.__camera.apply_clicked.connect(
            self.override_renderable_camera_callback
        )
        self.__camera.remove_clicked.connect(
            self.remove_override_renderable_camera_callback
        )
        main_layout.addWidget(self.__camera)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__width = IntContainerWidget('Width', self)
        self.__width.apply_clicked.connect(self.override_width_callback)
        self.__width.remove_clicked.connect(self.remove_override_width_callback)
        main_layout.addWidget(self.__width)

        self.__height = IntContainerWidget('Hidth', self)
        self.__height.apply_clicked.connect(self.override_height_callback)
        self.__height.remove_clicked.connect(
            self.remove_override_height_callback
        )
        main_layout.addWidget(self.__height)
        main_layout.addStretch(True)

    @widgets.undo
    def override_renderer_callback(self, renderer: str) -> None:
        '''Override renderer callback'''
        override_renderer(renderer)

    @widgets.undo
    def remove_override_renderer_callback(self) -> None:
        '''Remove override renderer callback'''
        remove_override_renderer()

    @widgets.undo
    def override_start_frame_callback(self, frame: float) -> None:
        '''Override start frame callback'''
        override_start_frame(frame)

    @widgets.undo
    def remove_override_start_frame_callback(self) -> None:
        '''Remove override start frame callback'''
        remove_override_start_frame()

    @widgets.undo
    def override_end_frame_callback(self, frame: float) -> None:
        '''Override end frame callback'''
        override_end_frame(frame)

    @widgets.undo
    def remove_override_end_frame_callback(self) -> None:
        '''Remove override end frame callback'''
        remove_override_end_frame()

    @widgets.undo
    def override_renderable_camera_callback(self, camera: str) -> None:
        '''Override renderable camera callback'''
        override_renderable_camera([camera])

    @widgets.undo
    def remove_override_renderable_camera_callback(self) -> None:
        '''Remove override renderable camera callback'''
        remove_override_renderable_camera()

    @widgets.undo
    def override_width_callback(self, width: int) -> None:
        '''Override width callback'''
        override_width(width)

    @widgets.undo
    def remove_override_width_callback(self) -> None:
        '''Remove override width callback'''
        remove_override_width()

    @widgets.undo
    def override_height_callback(self, height: int) -> None:
        '''Override height callback'''
        override_height(height)

    @widgets.undo
    def remove_override_height_callback(self) -> None:
        '''Remove override height callback'''
        remove_override_height()

    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__renderer.set_current_index(settings.renderer.value())
        self.__start_frame.set_value(settings.start_frame.value())
        self.__end_frame.set_value(settings.end_frame.value())
        self.__width.set_value(settings.width.value())
        self.__height.set_value(settings.height.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.renderer.set_value(self.__renderer.current_index())
        settings.start_frame.set_value(self.__start_frame.value())
        settings.end_frame.set_value(self.__end_frame.value())
        settings.width.set_value(self.__width.value())
        settings.height.set_value(self.__height.value())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()


class MayaSoftwareOption(QWidget):
    '''Maya Software option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        self.__image_format = EnumContainerWidget('Format', self)
        self.__image_format.add_item(
            [
                ('Alias PIX(als)', 6),
                ('AVI (avi)', 23),
                ('DDS (dds)', 35),
                ('EPS (eps)', 9),
                ('GIF (gif)', 0),
                ('JPEG (jpg)', 8),
                ('Maya IFF (iff)', 7),
                ('Maya 16 IFF (iff)', 10),
                ('PSD (psd)', 31),
                ('PSD Layered (psd)', 36),
                ('PNG (png)', 32),
                ('Quantel (yuv)', 12),
                ('Quicktime Movie (mov)', 22),
                ('PLA (rla)', 2),
                ('SGI (sgi)', 5),
                ('SGI 16 (sgi)', 13),
                ('SoftImage (pic)', 1),
                ('Targa (tga)', 19),
                ('Tiff (tif)', 3),
                ('Windows Bitmap (bmp)', 20),
                ('Sony Playstation (tim)', 63),
                ('XPM (xpm)', 63),
            ]
        )
        self.__image_format.apply_clicked.connect(
            self.override_image_format_callback
        )
        self.__image_format.remove_clicked.connect(
            self.remove_override_image_format_callback
        )
        main_layout.addWidget(self.__image_format)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__disable_anti = ContainerWidget('Disable Anti', self)
        self.__disable_anti.apply_clicked.connect(
            self.override_disable_anti_callback
        )
        self.__disable_anti.remove_clicked.connect(
            self.remove_override_disable_anti_callback
        )
        main_layout.addWidget(self.__disable_anti)
        main_layout.addWidget(
            QLabel('Warning: The exported data may contain errors.', self)
        )
        main_layout.addStretch(True)

    @widgets.undo
    def override_image_format_callback(self, format: int) -> None:
        '''Override image format callback'''
        override_image_format_sw(format)

    @widgets.undo
    def remove_override_image_format_callback(self) -> None:
        '''Remove override image format callback'''
        remove_override_image_format_sw()

    @widgets.undo
    def override_disable_anti_callback(self) -> None:
        '''Override disable anti callback'''
        override_disable_anti_sw()

    @widgets.undo
    def remove_override_disable_anti_callback(self) -> None:
        '''Remove override disable anti callback'''
        remove_override_disable_anti_sw()

    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__image_format.set_current_index(settings.image_format_sw.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.image_format_sw.set_value(self.__image_format.current_index())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()


class Pencil4LineOption(QWidget):
    '''Pencil+ 4 Line option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        self.__disable_anti = ContainerWidget('Disable Line', self)
        self.__disable_anti.apply_clicked.connect(
            self.override_disable_line_callback
        )
        self.__disable_anti.remove_clicked.connect(
            self.remove_override_disable_line_callback
        )
        main_layout.addWidget(self.__disable_anti)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__disable_anti = ContainerWidget('Disable Anti', self)
        self.__disable_anti.apply_clicked.connect(
            self.override_disable_anti_callback
        )
        self.__disable_anti.remove_clicked.connect(
            self.remove_override_disable_anti_callback
        )
        main_layout.addWidget(self.__disable_anti)
        main_layout.addStretch(True)

    @widgets.undo
    def override_disable_line_callback(self) -> None:
        '''Override disable line callback'''
        override_disable_pencil_line()

    @widgets.undo
    def remove_override_disable_line_callback(self) -> None:
        '''Remove override disable line callback'''
        remove_override_disable_pencil_line()

    @widgets.undo
    def override_disable_anti_callback(self) -> None:
        '''Override disable anti callback'''
        override_disable_anti_pencil_line()

    @widgets.undo
    def remove_override_disable_anti_callback(self) -> None:
        '''Remove override disable anti callback'''
        remove_override_disable_anti_pencil_line()

    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        # settings: Settings = Settings.instance(__name__, True)

    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        # settings: Settings = Settings.instance(__name__, True)
        # settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        # settings: Settings = Settings.instance(__name__, True)
        # settings.reset()
        # self.load_settings()


class ArnoldOption(QWidget):
    '''Arnold option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flag)

        main_layout: QVBoxLayout = QVBoxLayout(self)

        self.__image_format = EnumContainerWidget('Format', self)
        self.__image_format.add_item(
            [
                ('JPEG', 'jpeg'),
                ('PNG', 'png'),
                ('Deep EXR', 'deepexr'),
                ('TIFF', 'tif'),
                ('EXR', 'exr'),
                ('Maya', 'maya'),
            ]
        )
        self.__image_format.apply_clicked.connect(
            self.override_image_format_callback
        )
        self.__image_format.remove_clicked.connect(
            self.remove_override_image_format_callback
        )
        main_layout.addWidget(self.__image_format)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__disable_anti = ContainerWidget('Disable Anti', self)
        self.__disable_anti.apply_clicked.connect(
            self.override_disable_anti_callback
        )
        self.__disable_anti.remove_clicked.connect(
            self.remove_override_disable_anti_callback
        )
        main_layout.addWidget(self.__disable_anti)

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__filter_type = EnumContainerWidget('Filter Type', self)
        self.__filter_type.add_item(
            [
                ('box', 'box'),
                ('sinc', 'sinc'),
                ('blackman_harris', 'blackman_harris'),
                ('triangle', 'triangle'),
                ('catrom', 'catrom'),
                ('mitnet', 'mitnet'),
                ('gaussian', 'gaussian'),
                ('closest', 'closest'),
                ('farhest', 'farhest'),
                ('variance', 'variance'),
                ('heatmap', 'heatmap'),
                ('contour', 'contour'),
                ('<built-in>', '<built-in>'),
            ]
        )
        self.__filter_type.apply_clicked.connect(
            self.override_filter_type_callback
        )
        self.__filter_type.remove_clicked.connect(
            self.remove_override_filter_type_callback
        )
        main_layout.addWidget(self.__filter_type)

        self.__filter_width = DoubleContainerWidget('Filter Width', self)
        self.__filter_width.apply_clicked.connect(
            self.override_filter_width_callback
        )
        self.__filter_width.remove_clicked.connect(
            self.remove_override_filter_width_callback
        )
        main_layout.addWidget(self.__filter_width)

        main_layout.addStretch(True)

    @widgets.undo
    def override_image_format_callback(self, format: str) -> None:
        '''Override image format callback'''
        override_image_format_arnold(format)

    @widgets.undo
    def remove_override_image_format_callback(self) -> None:
        '''Remove override image format callback'''
        remove_override_image_format_arnold()

    @widgets.undo
    def override_disable_anti_callback(self) -> None:
        '''Override disable anti callback'''
        override_disable_anti_arnold()

    @widgets.undo
    def remove_override_disable_anti_callback(self) -> None:
        '''Remove override disable anti callback'''
        remove_override_disable_anti_arnold()

    @widgets.undo
    def override_filter_type_callback(self, format: str) -> None:
        '''Override filter type callback'''
        override_filter_type_arnold(format)

    @widgets.undo
    def remove_override_filter_type_callback(self) -> None:
        '''Remove override filter type callback'''
        remove_override_filter_type_arnold()

    @widgets.undo
    def override_filter_width_callback(self, width: float) -> None:
        '''Override filter width callback'''
        override_filter_width_arnold(width)

    @widgets.undo
    def remove_override_filter_width_callback(self) -> None:
        '''Remove override filter width callback'''
        remove_override_filter_width_arnold()

    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__image_format.set_current_index(
            settings.image_format_arnold.value()
        )
        self.__filter_type.set_current_index(
            settings.filter_type_arnold.value()
        )
        self.__filter_width.set_value(settings.filter_width_arnold.value())

    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.image_format_arnold.set_value(
            self.__image_format.current_index()
        )
        settings.filter_type_arnold.set_value(
            self.__filter_type.current_index()
        )
        settings.filter_width_arnold.set_value(self.__filter_width.value())
        settings.write()

    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()


class MainWindow(widgets.ToolWidget):
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

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__general_option = GeneralOption(self)
        self.__mayasoftware_option = MayaSoftwareOption(self)
        self.__pencil4line_option = Pencil4LineOption(self)
        self.__arnold_option = ArnoldOption(self)

        self.__tab = QTabWidget(self)
        self.__tab.setDocumentMode(True)
        self.__tab.addTab(self.__general_option, 'General')
        self.__tab.addTab(self.__mayasoftware_option, 'Maya Software')
        self.__tab.addTab(self.__pencil4line_option, 'Pencil+ 4 Line')
        self.__tab.addTab(self.__arnold_option, 'Arnold')
        main_layout.addWidget(self.__tab)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__general_option.load_settings()
        self.__mayasoftware_option.load_settings()
        self.__pencil4line_option.load_settings()
        self.__arnold_option.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        self.__general_option.save_settings()
        self.__mayasoftware_option.save_settings()
        self.__pencil4line_option.save_settings()
        self.__arnold_option.save_settings()
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


# ==============================================================================
#
# Functions
#
# ==============================================================================
# Utility
def selected_render_layer() -> list[RenderLayer]:
    '''Return list of layers selected on window.'''
    selected_layers: list[str] = viewCmds.getSelection(
        True, False, False, False
    )
    if not selected_layers:
        return []

    return [utils.nameToUserNode(x) for x in selected_layers]


def override_render_settings(
    node: str, attr: str, value: Any, name: str = ''
) -> bool:
    '''Create override of render settings.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        return False

    for layer in layers:
        renderSettings: RenderSettingsCollection = (
            layer.renderSettingsCollectionInstance()
        )
        setExpandedStateValue(renderSettings, False)

        overrides: list[AbsUniqueOverride] = renderSettings.getOverrides()
        for override_ in overrides:
            if (
                override_.targetNodeName() == node
                and override_.attributeName() == attr
            ):
                override_.setAttrValue(value)
                return True

        override_: AbsUniqueOverride = renderSettings.createAbsoluteOverride(
            node, attr
        )
        override_.setAttrValue(value)
        if name:
            override_.setName(name)

    return True


def remove_render_settings(node: str, attr: str) -> bool:
    '''Remove override of render settings.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        return False

    for layer in layers:
        if not layer.hasRenderSettingsCollectionInstance():
            continue

        renderSettings: RenderSettingsCollection = (
            layer.renderSettingsCollectionInstance()
        )

        overrides: list[AbsUniqueOverride] = renderSettings.getOverrides()
        for override_ in overrides:
            if (
                override_.targetNodeName() == node
                and override_.attributeName() == attr
            ):
                override.delete(override_)

        overrides = renderSettings.getOverrides()
        if not overrides:
            collection.delete(renderSettings)

    return True


# ------------------------------------------------------------------------------
# Geneal override
def override_renderer(renderer: str) -> bool:
    '''Create override renderer for selected render layers.'''
    result: bool = override_render_settings(
        'defaultRenderGlobals', 'currentRenderer', renderer
    )
    if not result:
        _logger.error('Select Render Layers to create override of renderer.')
    else:
        _logger.info('Done')
    return result


def remove_override_renderer() -> bool:
    '''Remove override renderer for selected render layers.'''
    result: bool = remove_render_settings(
        'defaultRenderGlobals', 'currentRenderer'
    )
    if not result:
        _logger.error('Select Render Layers to remove override of renderer.')

    else:
        _logger.info('Done')
    return result


def override_start_frame(frame: float) -> bool:
    '''Create override start frame for selected render layers.'''
    result: bool = override_render_settings(
        'defaultRenderGlobals', 'startFrame', frame * 250
    )
    if not result:
        _logger.error('Select Render Layers to create override of start frame.')
    else:
        _logger.info('Done')
    return result


def remove_override_start_frame() -> bool:
    '''Remove override start frame for selected render layers.'''
    result: bool = remove_render_settings('defaultRenderGlobals', 'startFrame')
    if not result:
        _logger.error('Select Render Layers to remove override of start frame.')

    else:
        _logger.info('Done')
    return result


def override_end_frame(frame: float) -> bool:
    '''Create override end frame for selected render layers.'''
    result: bool = override_render_settings(
        'defaultRenderGlobals', 'endFrame', frame * 250
    )
    if not result:
        _logger.error('Select Render Layers to create override of end frame.')
    else:
        _logger.info('Done')
    return result


def remove_override_end_frame() -> bool:
    '''Remove override end frame for selected render layers.'''
    result: bool = remove_render_settings('defaultRenderGlobals', 'endFrame')
    if not result:
        _logger.error('Select Render Layers to remove override of end frame.')

    else:
        _logger.info('Done')
    return result


def override_width(size: int) -> bool:
    '''Create override width for selected render layers.'''
    result: bool = override_render_settings('defaultResolution', 'width', size)
    if not result:
        _logger.error('Select Render Layers to create override of width.')
    else:
        _logger.info('Done')
    return result


def remove_override_width() -> bool:
    '''Remove override width for selected render layers.'''
    result: bool = remove_render_settings('defaultResolution', 'width')
    if not result:
        _logger.error('Select Render Layers to remove override of width.')

    else:
        _logger.info('Done')
    return result


def override_height(size: int) -> bool:
    '''Create override height for selected render layers.'''
    result: bool = override_render_settings('defaultResolution', 'height', size)
    if not result:
        _logger.error('Select Render Layers to create override of height.')
    else:
        _logger.info('Done')
    return result


def remove_override_height() -> bool:
    '''Remove override height for selected render layers.'''
    result: bool = remove_render_settings('defaultResolution', 'height')
    if not result:
        _logger.error('Select Render Layers to remove override of height.')

    else:
        _logger.info('Done')
    return result


def override_renderable_camera(cameras: list[str]) -> bool:
    '''Create override renderable camera for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to create override renderable camera.'
        )
        return False

    if not cameras:
        return False

    for layer in layers:
        # ----------------------------------------------------------------------
        # Group
        # ----------------------------------------------------------------------
        for g in layer.getGroups():
            if g.getNotes() == 'AMATERASU_RENDERABLE_CAMERA_GROUP':
                group.delete(g)

        camera_group: Group = layer.createGroup('Renderable_Camera')
        camera_group.setNotes('AMATERASU_RENDERABLE_CAMERA_GROUP')
        setExpandedStateValue(camera_group, False)

        # ----------------------------------------------------------------------
        # Disable renderable camera.
        # ----------------------------------------------------------------------
        disable_camera: Collection = camera_group.createCollection(
            'Disable_Renderble_Camera'
        )
        disable_camera.setNotes(
            'AMATERASU_DISABLE_RENDERABLE_CAMERA_COLLECTION'
        )
        setExpandedStateValue(disable_camera, False)
        disable_camera_selector: SimpleSelector = disable_camera.getSelector()
        disable_camera_selector.setFilterType(selector.Filters.kCustom)
        disable_camera_selector.setCustomFilterValue('camera')
        disable_camera_selector.setPattern('*')
        disable_camera_override: AbsUniqueOverride = (
            disable_camera.createAbsoluteOverride('perspShape', 'renderable')
        )
        disable_camera_override.setAttrValue(False)

        # ----------------------------------------------------------------------
        # Enable renderable camera.
        # ----------------------------------------------------------------------
        enable_camera: Collection = camera_group.createCollection(
            'Enable_Render_Camera'
        )
        enable_camera.setNotes('AMATERASU_ENABLE_RENDERABLE_CAMERA_COLLECTION')
        setExpandedStateValue(enable_camera, False)
        enable_camera_selector: SimpleSelector = enable_camera.getSelector()
        enable_camera_selector.setFilterType(selector.Filters.kCustom)
        enable_camera_selector.setCustomFilterValue('camera')
        enable_camera_selector.staticSelection.set(cameras)
        enable_camera_override: AbsUniqueOverride = (
            enable_camera.createAbsoluteOverride('perspShape', 'renderable')
        )
        enable_camera_override.setAttrValue(True)

    _logger.info('Done')
    return True


def remove_override_renderable_camera() -> bool:
    '''Remove override renderable camera for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to remove override of renderable camera.'
        )
        return False

    for layer in layers:
        groups: list[Group] = layer.getGroups()
        for group_ in groups:
            if group_.getNotes() == 'AMATERASU_RENDERABLE_CAMERA_GROUP':
                group.delete(group_)

    _logger.info('Done')
    return True


# ------------------------------------------------------------------------------
# Maya Software override
def override_image_format_sw(image_format: int) -> bool:
    '''Create override mayaSoftware image format for selected render layers.'''
    result: bool = override_render_settings(
        'defaultRenderGlobals',
        'imageFormat',
        image_format,
        'mayaSoftware_image_format',
    )
    if not result:
        _logger.error(
            'Select Render Layers to create override of image format.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_image_format_sw() -> bool:
    '''Remove override mayaSoftware image format for selected render layers.'''
    result: bool = remove_render_settings('defaultRenderGlobals', 'imageFormat')
    if not result:
        _logger.error(
            'Select Render Layers to remove override of image format.'
        )

    else:
        _logger.info('Done')
    return result


def override_disable_anti_sw() -> bool:
    '''Create override disable anti aliasing for selected render layers.'''
    if not cmds.attributeQuery(
        'useZBuffer', node='defaultRenderGlobals', exists=True
    ):
        cmds.addAttr(
            'defaultRenderGlobals',
            cachedInternally=True,
            longName='useZBuffer',
            defaultValue=1,
            minValue=0,
            maxValue=1,
            attributeType='bool',
        )

    result: bool = override_render_settings(
        'defaultRenderGlobals', 'currentRenderer', 'mayaSoftware'
    )
    result = override_render_settings('defaultRenderGlobals', 'useZBuffer', 1)
    result = override_render_settings(
        'defaultRenderGlobals', 'jitterFinalColor', 0
    )
    result = override_render_settings(
        'defaultRenderQuality', 'edgeAntiAliasing', 0
    )
    result = override_render_settings(
        'defaultRenderQuality', 'shadingSamples', 2
    )
    result = override_render_settings(
        'defaultRenderQuality', 'maxShadingSamples', 8
    )
    result = override_render_settings(
        'defaultRenderQuality', 'useMultiPixelFilter', 0
    )
    result = override_render_settings(
        'defaultRenderQuality', 'enableRaytracing', 0
    )
    result = override_render_settings('defaultRenderQuality', 'reflections', 10)
    result = override_render_settings('defaultRenderQuality', 'refractions', 10)
    result = override_render_settings('defaultRenderQuality', 'shadows', 0)
    if not result:
        _logger.error(
            'Select Render Layers to create override of disable anti aliasing.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_disable_anti_sw() -> bool:
    '''Remove override disable anti aliasing for selected render layers.'''
    result: bool = remove_render_settings(
        'defaultRenderGlobals', 'currentRenderer'
    )
    result = remove_render_settings('defaultRenderGlobals', 'useZBuffer')
    result = remove_render_settings('defaultRenderGlobals', 'jitterFinalColor')
    result = remove_render_settings('defaultRenderQuality', 'edgeAntiAliasing')
    result = remove_render_settings('defaultRenderQuality', 'shadingSamples')
    result = remove_render_settings('defaultRenderQuality', 'maxShadingSamples')
    result = remove_render_settings(
        'defaultRenderQuality', 'useMultiPixelFilter'
    )
    result = remove_render_settings('defaultRenderQuality', 'enableRaytracing')
    result = remove_render_settings('defaultRenderQuality', 'reflections')
    result = remove_render_settings('defaultRenderQuality', 'refractions')
    result = remove_render_settings('defaultRenderQuality', 'shadows')
    if not result:
        _logger.error(
            'Select Render Layers to remove override of disable anti aliasing.'
        )
    else:
        _logger.info('Done')
    return result


# ------------------------------------------------------------------------------
# Arnold override
def override_image_format_arnold(image_format: str) -> bool:
    '''Create override arnold image format for selected render layers.'''
    result: bool = override_render_settings(
        'defaultArnoldDriver',
        'aiTranslator',
        image_format,
        'arnold_image_format',
    )
    if not result:
        _logger.error(
            'Select Render Layers to create override of image format.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_image_format_arnold() -> bool:
    '''Remove override arnold image format for selected render layers.'''
    result: bool = remove_render_settings('defaultArnoldDriver', 'aiTranslator')
    if not result:
        _logger.error(
            'Select Render Layers to remove override of image format.'
        )
    else:
        _logger.info('Done')
    return result


def override_filter_type_arnold(filter_type: str) -> bool:
    '''Create override arnold filter type for selected render layers.'''
    result: bool = override_render_settings(
        'defaultArnoldFilter',
        'aiTranslator',
        filter_type,
        'arnold_filter_type',
    )
    if not result:
        _logger.error(
            'Select Render Layers to create override of arnold filter type.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_filter_type_arnold() -> bool:
    '''Remove override arnold filter type for selected render layers.'''
    result: bool = remove_render_settings('defaultArnoldFilter', 'aiTranslator')
    if not result:
        _logger.error(
            'Select Render Layers to remove override of arnold filter type.'
        )
    else:
        _logger.info('Done')
    return result


def override_filter_width_arnold(width: float) -> bool:
    '''Create override arnold filter width for selected render layers.'''
    result: bool = override_render_settings(
        'defaultArnoldFilter',
        'width',
        width,
        'arnold_filter_width',
    )
    if not result:
        _logger.error(
            'Select Render Layers to create override of arnold filter width.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_filter_width_arnold() -> bool:
    '''Remove override arnold filter width for selected render layers.'''
    result: bool = remove_render_settings('defaultArnoldFilter', 'width')
    if not result:
        _logger.error(
            'Select Render Layers to remove override of arnold filter width.'
        )
    else:
        _logger.info('Done')
    return result


def override_disable_anti_arnold() -> bool:
    '''Create override disable anti aliasing for selected render layers.'''
    result: bool = override_render_settings(
        'defaultRenderGlobals', 'currentRenderer', 'arnold'
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'AASamples', 0
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'GIDiffuseSamples', 0
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'GISpecularSamples', 0
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'GITransmissionSamples', 0
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'GISssSamples', 0
    )
    result = override_render_settings(
        'defaultArnoldRenderOptions', 'GIVolumeSamples', 0
    )
    if not result:
        _logger.error(
            'Select Render Layers to create override of disable anti aliasing.'
        )
    else:
        _logger.info('Done')
    return result


def remove_override_disable_anti_arnold() -> bool:
    '''Remove override disable anti aliasing for selected render layers.'''
    result: bool = remove_render_settings(
        'defaultRenderGlobals', 'currentRenderer'
    )
    result = remove_render_settings('defaultArnoldRenderOptions', 'AASamples')
    result = remove_render_settings(
        'defaultArnoldRenderOptions', 'GIDiffuseSamples'
    )
    result = remove_render_settings(
        'defaultArnoldRenderOptions', 'GISpecularSamples'
    )
    result = remove_render_settings(
        'defaultArnoldRenderOptions', 'GITransmissionSamples'
    )
    result = remove_render_settings(
        'defaultArnoldRenderOptions', 'GISssSamples'
    )
    result = remove_render_settings(
        'defaultArnoldRenderOptions', 'GIVolumeSamples'
    )
    if not result:
        _logger.error(
            'Select Render Layers to remove override of disable anti aliasing.'
        )
    else:
        _logger.info('Done')
    return result


# ------------------------------------------------------------------------------
# Pencil + 4 Line override
def override_disable_pencil_line() -> bool:
    '''Create override disable pencil+4 line for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to create override disable pencil+ 4 line.'
        )
        return False

    pencil_lines: list[str] = cmds.ls(type='PencilLine')
    if not pencil_lines:
        _logger.error('Pencil+ 4 line does not exist and cannot be processed.')
        return False

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == 'AMATERASU_DISABLE_PENCIL+4_LINE':
                collection.delete(c)

        pencil_collection: Collection = layer.createCollection(
            'Disable_Pencil_4_Line'
        )
        pencil_collection.setNotes('AMATERASU_DISABLE_PENCIL+4_LINE')
        setExpandedStateValue(pencil_collection, False)
        pencil_collection_selector: SimpleSelector = (
            pencil_collection.getSelector()
        )
        pencil_collection_selector.setFilterType(selector.Filters.kCustom)
        pencil_collection_selector.setCustomFilterValue('PencilLine')
        pencil_collection_selector.setPattern('*')
        disable_camera_override: AbsUniqueOverride = (
            pencil_collection.createAbsoluteOverride(pencil_lines[0], 'active')
        )
        disable_camera_override.setAttrValue(False)

    _logger.info('Done')
    return True


def remove_override_disable_pencil_line() -> bool:
    '''Remove override disable pencil+4 line for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to remove override of disable pencil+4 line.'
        )
        return False

    for layer in layers:
        collections: list[Collection] = layer.getCollections()
        for collect in collections:
            if collect.getNotes() == 'AMATERASU_DISABLE_PENCIL+4_LINE':
                collection.delete(collect)

    _logger.info('Done')
    return True


def override_disable_anti_pencil_line() -> bool:
    '''Create override disable anti pencil+4 line for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to create override disable anti for pencil+4 line.'
        )
        return False

    pencil_lines: list[str] = cmds.ls(type='PencilLine')
    if not pencil_lines:
        _logger.error('Pencil+ 4 line does not exist and cannot be processed.')
        return False

    for layer in layers:
        for c in layer.getCollections():
            if c.getNotes() == 'AMATERASU_DISABLE_ANTI_PENCIL+4_LINE':
                collection.delete(c)

        pencil_collection: Collection = layer.createCollection(
            'Disable_Anti_Pencil_4_Line'
        )
        pencil_collection.setNotes('AMATERASU_DISABLE_ANTI_PENCIL+4_LINE')
        setExpandedStateValue(pencil_collection, False)
        pencil_collection_selector: SimpleSelector = (
            pencil_collection.getSelector()
        )
        pencil_collection_selector.setFilterType(selector.Filters.kCustom)
        pencil_collection_selector.setCustomFilterValue('PencilLine')
        pencil_collection_selector.setPattern('*')
        sampling_override: AbsUniqueOverride = (
            pencil_collection.createAbsoluteOverride(
                pencil_lines[0], 'overSampling'
            )
        )
        sampling_override.setAttrValue(1)

        antialiasing_override: AbsUniqueOverride = (
            pencil_collection.createAbsoluteOverride(
                pencil_lines[0], 'antialiasing'
            )
        )
        antialiasing_override.setAttrValue(0)

    _logger.info('Done')
    return True


def remove_override_disable_anti_pencil_line() -> bool:
    '''Remove override disable pencil+4 line for selected render layers.'''
    layers: list[RenderLayer] = selected_render_layer()
    if not layers:
        _logger.error(
            'Select Render Layers to remove override of disable anti for pencil+4 line.'
        )
        return False

    for layer in layers:
        collections: list[Collection] = layer.getCollections()
        for collect in collections:
            if collect.getNotes() == 'AMATERASU_DISABLE_ANTI_PENCIL+4_LINE':
                collection.delete(collect)

    _logger.info('Done')
    return True


# ------------------------------------------------------------------------------
def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
