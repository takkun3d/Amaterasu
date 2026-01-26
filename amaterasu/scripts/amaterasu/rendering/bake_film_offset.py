# ==============================================================================
#
# Bake Film Offset
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, QRectF, QPointF
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QSpinBox,
        QPushButton,
        QMessageBox,
    )
    from PySide2.QtGui import (
        QPainter,
        QColor,
        QPen,
        QPaintEvent,
        QPainterPath,
        QBrush,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QRectF, QPointF
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QSpinBox,
            QPushButton,
            QMessageBox,
        )
        from PySide6.QtGui import (
            QPainter,
            QColor,
            QPen,
            QPaintEvent,
            QPainterPath,
            QBrush,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Bake Film Offset'
__version__: str = '1.00'
__doc__ = (
    'Bakes film offset into resolution and post scale with overscan support.'
)
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
    margin: parser.Variant[int] = parser.Variant(100)


class FilmOffsetVisualizer(QWidget):
    '''
    Widget to visualize the camera aperture and offset.
    '''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setMinimumHeight(200)
        self.__base_width: int = 1920
        self.__base_height: int = 1080
        self.__shift_x: float = 0.0
        self.__shift_y: float = 0.0
        self.__new_width: int = 1920
        self.__new_height: int = 1080
        self.__margin: int = 0
        self.__has_data: bool = False

    def update_data(
        self,
        base_width: int,
        base_height: int,
        shift_x: float,
        shift_y: float,
        new_width: int,
        new_height: int,
        margin: int,
    ) -> None:
        '''Update internal data.'''
        self.__base_width = base_width
        self.__base_height = base_height
        self.__shift_x = shift_x
        self.__shift_y = shift_y
        self.__new_width = new_width
        self.__new_height = new_height
        self.__margin = margin
        self.__has_data = True
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        '''Override'''
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Paint area.
        w: int = self.width()
        h: int = self.height()
        center_x: float = w / 2.0
        center_y: float = h / 2.0

        # Widget Area
        border_pen = QPen(QColor(80, 80, 80), 2)
        border_pen.setStyle(Qt.DashLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(5, 5, w - 10, h - 10, 4, 4)
        if not self.__has_data:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(
                QRectF(0, 0, w, h),
                Qt.AlignCenter,
                'Click [Calculate Baked Offset] to Show Preview',
            )
            return

        # Drawing scale.
        scale_x: float = (w * 0.9) / self.__new_width
        scale_y: float = (h * 0.9) / self.__new_height
        scale: float = min(scale_x, scale_y)

        # Calc New Resolution
        rect_new_w: float = self.__new_width * scale
        rect_new_h: float = self.__new_height * scale
        rect_new: QRectF = QRectF(
            center_x - rect_new_w / 2,
            center_y - rect_new_h / 2,
            rect_new_w,
            rect_new_h,
        )

        # Calc Margin
        needed_w_total: float = self.__base_width + 2.0 * (
            abs(self.__shift_x) + self.__margin
        )
        needed_h_total: float = self.__base_height + 2.0 * (
            abs(self.__shift_y) + self.__margin
        )

        needed_w_pure: float = self.__base_width + 2.0 * abs(self.__shift_x)
        needed_h_pure: float = self.__base_height + 2.0 * abs(self.__shift_y)
        ratio_w: float = (
            needed_w_pure / needed_w_total if needed_w_total > 0 else 1.0
        )
        ratio_h: float = (
            needed_h_pure / needed_h_total if needed_h_total > 0 else 1.0
        )

        rect_comp_w: float = rect_new_w * ratio_w
        rect_comp_h: float = rect_new_h * ratio_h
        rect_comp: QRectF = QRectF(
            center_x - rect_comp_w / 2,
            center_y - rect_comp_h / 2,
            rect_comp_w,
            rect_comp_h,
        )

        # Calc Base Resolution
        rect_base_w: float = self.__base_width * scale
        rect_base_h: float = self.__base_height * scale
        rect_base: QRectF = QRectF(
            center_x - rect_base_w / 2,
            center_y - rect_base_h / 2,
            rect_base_w,
            rect_base_h,
        )

        # Calc Film Offset
        offset_x: float = self.__shift_x * scale
        offset_y: float = -1.0 * self.__shift_y * scale
        rect_shift: QRectF = QRectF(
            center_x - rect_base_w / 2 + offset_x,
            center_y - rect_base_h / 2 + offset_y,
            rect_base_w,
            rect_base_h,
        )

        # Draw Margin
        path_new: QPainterPath = QPainterPath()
        path_new.addRect(rect_new)
        path_comp: QPainterPath = QPainterPath()
        path_comp.addRect(rect_comp)

        path_margin: QPainterPath = path_new.subtracted(path_comp)
        painter.fillPath(path_margin, QBrush(QColor(200, 200, 200, 30)))

        # Draw New Resolution
        pen_red: QPen = QPen(QColor(255, 80, 80), 2)
        painter.setPen(pen_red)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect_new)
        painter.drawText(rect_new.topLeft() - QPointF(-5, -13), 'New')

        # Draw Base Resolution
        pen_black: QPen = QPen(QColor(200, 200, 200), 1.5)
        pen_black.setStyle(Qt.DotLine)
        painter.setPen(pen_black)
        painter.drawRect(rect_base)
        painter.drawText(rect_base.topLeft() - QPointF(-5, -13), 'Base')

        # Draw Film Offset
        pen_green: QPen = QPen(QColor(80, 255, 100), 2)
        pen_green.setStyle(Qt.DashLine)
        painter.setPen(pen_green)
        painter.drawRect(rect_shift)
        painter.drawText(rect_shift.topLeft() - QPointF(-5, -13), 'Current')

        # Draw Center Point
        painter.setPen(QPen(QColor(255, 255, 0), 5))
        painter.drawPoint(QPointF(center_x, center_y))


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
        self.resize(300, 100)

        option_widget: QWidget = self.option_widget()
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)
        main_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__margin: QSpinBox = QSpinBox(self)
        self.__margin.setRange(0, 10000)
        main_layout.addRow(widgets.FormLabel('Margin (px)'), self.__margin)

        button_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addRow(button_layout)

        button: QPushButton = QPushButton('Calculate Baked Offset', self)
        button.clicked.connect(self.calc_overscan)
        button_layout.addWidget(button)

        button = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        button_layout.addWidget(button)

        main_layout.addRow(widgets.HorizontalLine(self))

        main_layout.addRow(QLabel('Information', self))
        self.__x: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Shift X (px)'), self.__x)

        self.__y: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Shift Y (px)'), self.__y)

        self.__width: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Width'), self.__width)

        self.__height: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Height'), self.__height)

        self.__post_scale: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('PostScale'), self.__post_scale)

        self.__preview = FilmOffsetVisualizer(self)
        main_layout.addRow(self.__preview)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__margin.setValue(settings.margin.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.margin.set_value(self.__margin.value())
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

    def calc_overscan(self) -> None:
        '''Calculate Shift'''
        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select camera to calculate baked overscan.')
            return

        if len(selection) != 1:
            _logger.error('Select a single camera to calculate baked overscan.')
            return

        result_shift: tuple[float, float] | None = calculate_shift_pixel(
            selection[0]
        )
        if not result_shift:
            _logger.error('Select a camera to calculate baked overscan.')
            return

        result_overscan: tuple[int, int, float] | None = calculate_baked_offset(
            selection[0],
            result_shift[0],
            result_shift[1],
            settings.margin.value(),
        )
        if not result_overscan:
            _logger.error('Select a camera to calculate baked overscan.')
            return

        self.__x.setText(f'{result_shift[0]:.2f}')
        self.__y.setText(f'{result_shift[1]:.2f}')
        self.__width.setText(f'{result_overscan[0]}')
        self.__height.setText(f'{result_overscan[1]}')
        self.__post_scale.setText(f'{result_overscan[2]:.2f}')

        base_w = cmds.getAttr('defaultResolution.width')
        base_h = cmds.getAttr('defaultResolution.height')

        self.__preview.update_data(
            base_w,
            base_h,
            result_shift[0],
            result_shift[1],
            result_overscan[0],
            result_overscan[1],
            settings.margin.value(),
        )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        result: int = QMessageBox.warning(
            self,
            'Warning',
            'This operation modifies the render resolution settings.\n'
            'Undo functionality may not work correctly after execution.\n\n'
            'Do you want to proceed?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.No:
            _logger.info('Cancelled.')

            return

        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select camera to calculate baked overscan.')
            return

        if len(selection) != 1:
            _logger.error('Select a single camera to calculate baked overscan.')
            return

        self.calc_overscan()
        apply(selection[0], settings.margin.value())
        _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def calculate_shift_pixel(camera: str) -> tuple[float, float] | None:
    '''Calculates pixel shift considering Film Fit and Pixel Aspect.'''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return None

    camera_shape: str = camera_shapes[0]
    width: int = cmds.getAttr('defaultResolution.width')
    height: int = cmds.getAttr('defaultResolution.height')
    pixel_aspect: float = cmds.getAttr('defaultResolution.pixelAspect')
    h_aperture: float = cmds.getAttr(f'{camera_shape}.horizontalFilmAperture')
    v_aperture: float = cmds.getAttr(f'{camera_shape}.verticalFilmAperture')
    h_offset: float = cmds.getAttr(f'{camera_shape}.horizontalFilmOffset')
    v_offset: float = cmds.getAttr(f'{camera_shape}.verticalFilmOffset')
    film_fit: int = cmds.getAttr(f'{camera_shape}.filmFit')

    # Calculate aspect ratios
    resolution_aspect: float = width * pixel_aspect / height
    film_aspect: float = h_aperture / v_aperture

    fit_horizontal: bool = True
    if film_fit == 2:  # Vertical
        fit_horizontal = False

    elif film_fit == 0:  # Fill
        # larger Aspect Ratio
        fit_horizontal = film_aspect < resolution_aspect

    elif film_fit == 3:  # Over
        # larger Aspect Ratio
        fit_horizontal = film_aspect > resolution_aspect

    # Calculate Pixels Per Inch (PPI)
    if fit_horizontal:
        # Based on Width (Width pixels = H Aperture)
        ppi_x: float = width / h_aperture
        ppi_y: float = ppi_x * pixel_aspect

    else:
        # Based on Height (Height pixels = V Aperture)
        ppi_y = height / v_aperture
        ppi_x = ppi_y / pixel_aspect

    # Final Calculation (Offset * PPI)
    # Offset is in inches, PPI is px/inch, so just multiply.
    shift_x: float = -1 * h_offset * ppi_x
    shift_y: float = -1 * v_offset * ppi_y
    return (shift_x, shift_y)


def calculate_baked_offset(
    camera: str,
    shift_x: float,
    shift_y: float,
    margin: int = 0,
) -> tuple[int, int, float] | None:
    '''
    Calculates overscan preserving aspect ratio and existing Post Scale.
    '''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return None

    width: int = cmds.getAttr('defaultResolution.width')
    height: int = cmds.getAttr('defaultResolution.height')
    post_scale: float = cmds.getAttr(f'{camera_shapes[0]}.postScale')

    temp_width: float = width + (2.0 * (abs(shift_x) + margin))
    temp_height: float = height + (2.0 * (abs(shift_y) + margin))

    scale_x: float = width / temp_width
    scale_y: float = height / temp_height
    scale: float = min(scale_x, scale_y)

    new_width: int = int(width / scale)
    new_height: int = int(height / scale)
    new_post_scale: float = post_scale * scale
    return (new_width, new_height, new_post_scale)


def apply(camera: str, margin: int) -> None:
    '''Apply'''
    camera_shapes: list[str] = cmds.listRelatives(camera, type='camera') or []
    if not camera_shapes:
        return

    result_shift: tuple[float, float] | None = calculate_shift_pixel(camera)
    if not result_shift:
        return

    result_baked_offset: tuple[int, int, float] | None = calculate_baked_offset(
        camera, result_shift[0], result_shift[1], margin
    )
    if not result_baked_offset:
        return

    width: int = result_baked_offset[0]
    height: int = result_baked_offset[1]
    post_scale: float = result_baked_offset[2]
    device_aspect: float = float(width) / float(height)
    pixel_aspect: float = cmds.getAttr('defaultResolution.pixelAspect')

    cmds.setAttr('defaultResolution.lockDeviceAspectRatio', 0)
    cmds.setAttr('defaultResolution.width', width)
    cmds.setAttr('defaultResolution.height', height)
    cmds.setAttr('defaultResolution.deviceAspectRatio', device_aspect)
    cmds.setAttr('defaultResolution.pixelAspect', pixel_aspect)
    cmds.setAttr(f'{camera_shapes[0]}.postScale', post_scale)
    cmds.setAttr(f'{camera_shapes[0]}.horizontalFilmOffset', 0)
    cmds.setAttr(f'{camera_shapes[0]}.verticalFilmOffset', 0)


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
