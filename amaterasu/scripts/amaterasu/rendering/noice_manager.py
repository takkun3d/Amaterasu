# ==============================================================================
#
# Noice Manager
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import os
import tempfile
import subprocess

try:
    from PySide2.QtCore import Qt, QPoint, QPointF, QRectF
    from PySide2.QtGui import (
        QColor,
        QPainter,
        QPixmap,
        QPen,
        QFont,
        QDragEnterEvent,
        QMouseEvent,
        QWheelEvent,
        QResizeEvent,
        QPaintEvent,
    )
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QDoubleSpinBox,
        QSpinBox,
        QCheckBox,
        QLabel,
        QListWidget,
        QComboBox,
        QGraphicsScene,
        QGraphicsView,
        QGraphicsItem,
        QStyleOptionGraphicsItem,
        QPushButton,
        QFileDialog,
        QMessageBox,
        QApplication,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
        from PySide6.QtGui import (
            QColor,
            QPainter,
            QPixmap,
            QPen,
            QFont,
            QDragEnterEvent,
            QMouseEvent,
            QWheelEvent,
            QResizeEvent,
            QPaintEvent,
        )
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QDoubleSpinBox,
            QSpinBox,
            QCheckBox,
            QLabel,
            QListWidget,
            QComboBox,
            QGraphicsScene,
            QGraphicsView,
            QGraphicsItem,
            QStyleOptionGraphicsItem,
            QPushButton,
            QFileDialog,
            QMessageBox,
            QApplication,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Noice Manager'
__version__: str = '1.10'
__doc__ = 'Easy tool to control Arnold Noice. Check images and export batch.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

PLUGIN_NAME: str = 'mtoa'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    variance: parser.Variant[float] = parser.Variant(0.5)
    search_radius: parser.Variant[int] = parser.Variant(9)
    patch_radius: parser.Variant[int] = parser.Variant(3)
    extra_frames: parser.Variant[int] = parser.Variant(2)
    auto_frames: parser.Variant[bool] = parser.Variant(True)
    override_frames: parser.Variant[int] = parser.Variant(1)


class DragDropListWidget(QListWidget):
    '''Drag and Drop list widget.'''

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initialize widget.'''
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        '''override'''
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        '''override'''
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDragEnterEvent) -> None:
        '''override'''
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        event.setDropAction(Qt.CopyAction)
        event.accept()
        for url in event.mimeData().urls():
            path: str = url.toLocalFile()
            if not os.path.isdir(path):
                continue

            if path not in [self.item(i).text() for i in range(self.count())]:
                self.addItem(path)

    def paintEvent(self, event: QPaintEvent) -> None:
        '''Override'''
        super().paintEvent(event)

        if self.count() == 0:
            painter: QPainter = QPainter(self.viewport())
            painter.save()
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                self.viewport().rect(),
                Qt.AlignCenter,
                'Drag & Drop Folders Here',
            )
            painter.restore()

    def add_folder(self) -> None:
        '''Show file dialog.'''
        path: str = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if path:
            self.addItem(path)

    def remove_selected(self) -> None:
        '''Remove selected items.'''
        for i in self.selectedItems():
            self.takeItem(self.row(i))

    def as_list(self) -> list[str]:
        '''Return list[str] from my data.'''
        return [self.item(i).text() for i in range(self.count())]


class CompareImageItem(QGraphicsItem):
    '''Compare Image Item'''

    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        '''Initialize item'''
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.__before_image: QPixmap = QPixmap()
        self.__after_image: QPixmap = QPixmap()
        self.__split_x: float = 0.0

    def boundingRect(self) -> QRectF:
        '''Override'''
        if self.__before_image.isNull():
            return QRectF()

        return QRectF(self.__before_image.rect())

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        '''Override'''
        if self.__before_image.isNull():
            return

        painter.drawPixmap(0, 0, self.__before_image)

        if self.__after_image.isNull():
            return

        w: int = self.__before_image.width()
        h: int = self.__before_image.height()
        clip_x: float = max(0, min(self.__split_x, w))
        if clip_x < w:
            painter.save()
            painter.setClipRect(QRectF(clip_x, 0, w - clip_x, h))
            painter.drawPixmap(0, 0, self.__after_image)
            painter.restore()

    def set_images(self, before_path: str, after_path: str) -> tuple[int, int]:
        '''Load images.'''
        self.__before_image = QPixmap(before_path)
        self.__after_image = QPixmap(after_path)
        self.update()
        return (self.__before_image.width(), self.__before_image.height())

    def set_split_x(self, x: float) -> None:
        '''Set split potision X.'''
        self.__split_x = x
        self.update()


class ImageCompareView(QGraphicsView):
    '''Image Compare View'''

    def __init__(
        self,
        scene: QGraphicsScene,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize widget.'''
        super().__init__(scene, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setMouseTracking(True)

        self.__is_zooming: bool = False
        self.__is_panning: bool = False
        self.__is_sliding: bool = False
        self.__last_pos: QPoint = QPoint()
        self.__slider_pos: float = 0.5
        self.__compare_image: CompareImageItem = CompareImageItem()
        self.__is_first: bool = True
        self.scene().addItem(self.__compare_image)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        '''Override'''
        painter.save()
        painter.resetTransform()

        # No preview loaded
        if self.__compare_image.boundingRect().isEmpty():
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                self.viewport().rect(), Qt.AlignCenter, 'No Preview Loaded'
            )
            painter.restore()
            return

        # Split line
        view_w: int = self.width()
        view_h: int = self.height()
        split_x = int(view_w * self.__slider_pos)
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        painter.drawLine(split_x, 0, split_x, view_h)

        # Background label
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.NoPen)
        painter.drawRect(split_x - 80, view_h - 35, 160, 30)

        # Text
        painter.setPen(QColor(255, 255, 255))
        font: QFont = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(split_x - 60, view_h - 15, 'Original')
        painter.drawText(split_x + 15, view_h - 15, 'Denoised')

        painter.restore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if event.modifiers() == Qt.AltModifier:
            if (
                event.button() == Qt.MiddleButton
                or event.button() == Qt.LeftButton
            ):
                self.__is_panning = True
                self.__last_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                return

            if event.button() == Qt.RightButton:
                self.__is_zooming = True
                self.__last_pos = event.pos()
                self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
                self.setCursor(Qt.SizeVerCursor)
                event.accept()
                return

        else:
            if event.button() == Qt.LeftButton:
                self.__is_sliding = True
                self.update_slider_pos(event.pos().x())
                self.setCursor(Qt.SplitHCursor)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        delta: QPoint = event.pos() - self.__last_pos
        if self.__is_zooming:
            zoom_input: int = delta.x() - delta.y()
            zoom_factor: float = 1.0 + (zoom_input * 0.003)
            if zoom_factor > 0:
                self.scale(zoom_factor, zoom_factor)
                self.__last_pos = event.pos()
            return

        if self.__is_panning:
            self.__last_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.update_split_line()
            event.accept()
            return

        if self.__is_sliding:
            self.update_slider_pos(event.pos().x())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        '''Override'''
        if self.__is_panning or self.__is_zooming or self.__is_sliding:
            self.__is_zooming = False
            self.__is_panning = False
            self.__is_sliding = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        '''Override'''
        factor = 1.1
        if event.delta() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1.0 / factor, 1.0 / factor)

    def resizeEvent(self, event: QResizeEvent) -> None:
        '''Override'''
        super().resizeEvent(event)
        self.update_split_line()

    def set_images(self, before_image: str, after_image: str) -> None:
        '''Set image compare item.'''
        width, height = self.__compare_image.set_images(
            before_image, after_image
        )

        margin: int = 100000
        rect: QRectF = QRectF(
            -margin,
            -margin,
            width + margin * 2,
            height + margin * 2,
        )
        self.scene().setSceneRect(rect)
        if self.__is_first:
            self.fit_to_window()
            self.__is_first = False

    def fit_to_window(self) -> None:
        '''Fit image to window.'''
        if self.__compare_image.boundingRect().isEmpty():
            return

        self.fitInView(self.__compare_image, Qt.KeepAspectRatio)
        self.update_split_line()

    def update_slider_pos(self, x: float) -> None:
        '''Update slider position.'''
        self.__slider_pos = max(0.0, min(1.0, float(x) / self.width()))
        self.update_split_line()
        self.viewport().update()

    def update_split_line(self) -> None:
        '''Update split line'''
        screen_x: float = self.width() * self.__slider_pos
        scene_pt: QPointF = self.mapToScene(QPoint(int(screen_x), 0))
        item_pt: QPointF = self.__compare_image.mapFromScene(scene_pt)
        self.__compare_image.set_split_x(item_pt.x())
        self.scene().update()


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
        self.resize(1200, 700)

        option_widget: QWidget = self.option_widget()
        main_layout: QHBoxLayout = QHBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left
        left_panel: QWidget = QWidget(self)
        left_panel.setFixedWidth(400)
        main_layout.addWidget(left_panel)

        left_layout: QVBoxLayout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(left_layout)

        # Folder
        label: QLabel = QLabel('Directories :', self)
        left_layout.addWidget(label)

        self.__folder_list: DragDropListWidget = DragDropListWidget(self)
        left_layout.addWidget(self.__folder_list)

        folder_layout: QHBoxLayout = QHBoxLayout(self)
        left_layout.addLayout(folder_layout)

        button: QPushButton = QPushButton('Add Folder', self)
        button.clicked.connect(self.__folder_list.add_folder)
        folder_layout.addWidget(button)

        button = QPushButton('Remove Selected', self)
        button.clicked.connect(self.__folder_list.remove_selected)
        folder_layout.addWidget(button)

        button = QPushButton('Clear', self)
        button.clicked.connect(self.__folder_list.clear)
        folder_layout.addWidget(button)

        left_layout.addWidget(widgets.HorizontalLine(self))

        # Settings
        settings_layout: widgets.FormLayout = widgets.FormLayout(self)
        left_layout.addLayout(settings_layout)

        self.__variance: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__variance.setRange(0.0, 1.0)
        self.__variance.setSingleStep(0.1)
        self.__variance.setMinimumWidth(70)
        settings_layout.addRow(widgets.FormLabel('Variance'), self.__variance)

        self.__search_radius: QSpinBox = QSpinBox(self)
        self.__search_radius.setMinimumWidth(70)
        settings_layout.addRow(
            widgets.FormLabel('Search Radius'), self.__search_radius
        )

        self.__patch_radius: QSpinBox = QSpinBox(self)
        self.__patch_radius.setMinimumWidth(70)
        settings_layout.addRow(
            widgets.FormLabel('Patch Radius'), self.__patch_radius
        )

        self.__extra_frames: QSpinBox = QSpinBox(self)
        self.__extra_frames.setMinimumWidth(70)
        settings_layout.addRow(
            widgets.FormLabel('Extra Frames'), self.__extra_frames
        )

        self.__auto_frames: QCheckBox = QCheckBox('Complete Sequence', self)
        self.__auto_frames.toggled.connect(
            lambda c: self.__override_frames.setEnabled(not c)
        )
        settings_layout.addRow('', self.__auto_frames)

        self.__override_frames: QSpinBox = QSpinBox(self)
        self.__override_frames.setRange(1, 99999)
        self.__override_frames.setMinimumWidth(70)
        settings_layout.addRow(
            widgets.FormLabel('Frame'), self.__override_frames
        )

        left_layout.addWidget(widgets.HorizontalLine(self))

        # Actions
        button_layout: QHBoxLayout = QHBoxLayout(self)
        left_layout.addLayout(button_layout)

        button = QPushButton('Preview', self)
        button.clicked.connect(self.preview)
        button_layout.addWidget(button)

        button = QPushButton('Run in Consle', self)
        button.clicked.connect(self.run_console)
        button_layout.addWidget(button)

        button = QPushButton('Save Batch', self)
        button.clicked.connect(self.save_batch_file)
        button_layout.addWidget(button)

        # Right
        right_layout: QVBoxLayout = QVBoxLayout(self)
        right_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(right_layout)

        tool_layout: QHBoxLayout = QHBoxLayout(self)
        tool_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addLayout(tool_layout)

        # AOV
        self.__current_raw_exr: str = ''
        self.__current_denoised_exr: str = ''
        self.__aov: QComboBox = QComboBox(self)
        self.__aov.currentIndexChanged.connect(self.update_preview_image)
        tool_layout.addWidget(self.__aov)

        label: QLabel = QLabel(
            '<strong>* Preview is converted from linear to sRGB.</strong>',
            self,
        )
        tool_layout.addWidget(label)

        # Preview
        self.__scene: QGraphicsScene = QGraphicsScene()
        self.__preview: ImageCompareView = ImageCompareView(self.__scene, self)
        right_layout.addWidget(self.__preview)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__variance.setValue(settings.variance.value())
        self.__search_radius.setValue(settings.search_radius.value())
        self.__patch_radius.setValue(settings.patch_radius.value())
        self.__extra_frames.setValue(settings.extra_frames.value())
        self.__auto_frames.setChecked(settings.auto_frames.value())
        self.__override_frames.setValue(settings.override_frames.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.variance.set_value(self.__variance.value())
        settings.search_radius.set_value(self.__search_radius.value())
        settings.patch_radius.set_value(self.__patch_radius.value())
        settings.extra_frames.set_value(self.__extra_frames.value())
        settings.auto_frames.set_value(self.__auto_frames.isChecked())
        settings.override_frames.set_value(self.__override_frames.value())
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

    def __batch_contents(self) -> str:
        '''Retrun batch contents from UI.'''
        folder_paths: list[str] = self.__folder_list.as_list()
        if not folder_paths:
            QMessageBox.critical(
                self, 'Error', 'Add a folder to denoise the image.'
            )
            return ''

        contents: str = generate_batch_content(
            folder_paths,
            self.__variance.value(),
            self.__search_radius.value(),
            self.__patch_radius.value(),
            self.__extra_frames.value(),
            self.__auto_frames.isChecked(),
            self.__override_frames.value(),
        )
        if not contents:
            QMessageBox.critical(
                self, 'Error', 'Failed to generate batch commands.'
            )
            return ''

        return contents

    def run_console(self) -> None:
        '''Run'''
        self.save_settings()
        contents: str = self.__batch_contents()
        if not contents:
            return

        bat: str = os.path.join(
            tempfile.gettempdir(), 'amaterasu_noice_manager.bat'
        )
        try:
            with open(bat, 'w', encoding='cp932', errors='ignore') as f:
                f.write(contents)

        except IOError as e:
            QMessageBox.critical(
                self, 'Error', f'Failed to save file.\n{str(e)}'
            )
            return

        subprocess.Popen([bat], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def save_batch_file(self) -> None:
        '''Save batch file.'''
        self.save_settings()
        contents: str = self.__batch_contents()
        if not contents:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Batch', '', 'Batch Files (*.bat)'
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='cp932', errors='ignore') as f:
                f.write(contents)

        except IOError as e:
            QMessageBox.critical(
                self, 'Error', f'Failed to save file.\n{str(e)}'
            )
            return

    def preview(self) -> None:
        '''Preview'''
        self.save_settings()
        folder_paths: list[str] = self.__folder_list.as_list()
        if not folder_paths:
            QMessageBox.critical(
                self, 'Error', 'Add a folder to preview denoised image.'
            )
            return

        exr_files: list[str] = exr_list(folder_paths[0])
        if not exr_files:
            QMessageBox.critical(
                self, 'Error', f'Not found EXR files.\n{folder_paths[0]}'
            )
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        denoised_exr: str = denoise_image(
            exr_files[0],
            self.__variance.value(),
            self.__search_radius.value(),
            self.__patch_radius.value(),
            self.__extra_frames.value(),
        )
        if not denoised_exr:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, 'Error', 'Failed to denoise EXR.')
            return

        self.__current_raw_exr = exr_files[0]
        self.__current_denoised_exr = denoised_exr
        aovs: list[str] = get_denoise_aovs(exr_files[0])

        self.__aov.blockSignals(True)
        self.__aov.clear()
        self.__aov.addItem('Beauty')
        if aovs:
            self.__aov.addItems(aovs)
        self.__aov.blockSignals(False)

        self.update_preview_image()
        QApplication.restoreOverrideCursor()

    def update_preview_image(self, is_cursor: bool = True) -> None:
        '''Update preview image.'''
        if not self.__current_raw_exr or not self.__current_denoised_exr:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        selected_aov: str = self.__aov.currentText()
        temp_dir: str = tempfile.gettempdir()
        before_image: str = os.path.join(temp_dir, 'amaterasu_before.png')
        after_image: str = os.path.join(temp_dir, 'amaterasu_after.png')

        before_image = convert_to_png(
            self.__current_raw_exr, before_image, selected_aov
        )
        after_image = convert_to_png(
            self.__current_denoised_exr, after_image, selected_aov
        )
        if not before_image or not after_image:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                self, 'Error', 'Failed to generate preview image.'
            )
            return

        self.__preview.set_images(before_image, after_image)
        QApplication.restoreOverrideCursor()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def arnold_path() -> str:
    '''Returns arnold path.'''
    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)
        if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
            return ''

    plugin_path: str = cmds.pluginInfo(PLUGIN_NAME, query=True, path=True)
    root_path: str = os.path.dirname(os.path.dirname(plugin_path))
    return os.path.normpath(root_path)


def noice_path() -> str:
    '''Returns noice path.'''
    arnold_root: str = arnold_path()
    if not arnold_root:
        return ''

    ext: str = '.exe' if os.name == 'nt' else ''
    path: str = os.path.join(arnold_root, 'bin', f'noice{ext}')
    return os.path.normpath(path)


def oiiotool_path() -> str:
    '''Returns oiiotool path.'''
    arnold_root: str = arnold_path()
    if not arnold_root:
        return ''

    ext: str = '.exe' if os.name == 'nt' else ''
    path: str = os.path.join(arnold_root, 'bin', f'oiiotool{ext}')
    return os.path.normpath(path)


def exr_list(folder_path: str) -> list[str]:
    '''Returns EXR file list'''
    files: list[str] = sorted(
        [
            os.path.normpath(os.path.join(folder_path, f))
            for f in os.listdir(folder_path)
            if f.endswith('.exr')
        ]
    )
    if not files:
        return []

    return files


def build_command(
    folder_path: str,
    variance: float,
    search_radius: int,
    patch_radius: int,
    extra_frames: int,
    auto_frame: bool,
    override_frame: int,
) -> tuple[str, str]:
    '''Build command.'''
    noice: str = noice_path()
    if not noice:
        _logger.error('Not found noice.')
        return ('', '')

    folder_path = os.path.normpath(folder_path)
    exr_files: list[str] = exr_list(folder_path)
    if not exr_files:
        _logger.error('Not found EXR files. %s', folder_path)
        return ('', '')

    start_file: str = exr_files[0]
    file_count: int = len(exr_files)

    out_dir: str = os.path.join(
        os.path.dirname(folder_path),
        f'{os.path.basename(folder_path)}_denoised',
    )
    out_file: str = os.path.join(out_dir, os.path.basename(start_file))
    frames: str = str(file_count) if auto_frame else str(override_frame)

    batch_args: list[str] = []
    batch_args.append(f'-i "{start_file}"')
    batch_args.append(f'-o "{out_file}"')
    batch_args.append(f'-f {frames}')
    batch_args.append(f'-v {variance}')
    batch_args.append(f'-sr {search_radius}')
    batch_args.append(f'-pr {patch_radius}')
    if extra_frames > 0:
        batch_args.append(f'-ef {extra_frames}')

    for aov in get_denoise_aovs(start_file):
        batch_args.extend(['-l', aov])

    args: str = ' '.join(batch_args)
    command: str = f'"{noice}" {args}'
    return (command, out_dir)


def generate_batch_content(
    folder_paths: list[str],
    variance: float,
    search_radius: int,
    patch_radius: int,
    extra_frames: int,
    auto_frame: bool,
    override_frame: int,
) -> str:
    '''Generate batch content.'''
    count: int = len(folder_paths)
    if count == 0:
        return ''

    lines: list[str] = []
    lines.append('@echo off')
    lines.append('echo \033[31m')
    lines.append('echo ' + ('=' * 80))
    lines.append('echo Arnold Noice')
    lines.append('echo Build command by Amaterasu.')
    lines.append('echo ' + ('=' * 80))

    valid_count: int = 0
    for folder_path in folder_paths:
        command, output_path = build_command(
            folder_path,
            variance,
            search_radius,
            patch_radius,
            extra_frames,
            auto_frame,
            override_frame,
        )
        if not command:
            continue

        valid_count += 1
        lines.append('echo \033[33m')
        lines.append(
            f'echo Job {valid_count} / {count}: {os.path.basename(folder_path)}'
        )
        lines.append(f'if not exist "{output_path}" mkdir "{output_path}"')
        lines.append('echo \033[37m')
        lines.append(command)
        lines.append('')

    if valid_count == 0:
        return ''

    lines.append('echo \033[36m')
    lines.append('echo.')
    lines.append('echo ' + ('=' * 80))
    lines.append('echo All denoising tasks completed.')
    lines.append('echo ' + ('=' * 80))
    lines.append('pause')
    return '\n'.join(lines)


def denoise_image(
    filename: str,
    variance: float,
    search_radius: int,
    patch_radius: int,
    extra_frames: int,
    output: str = 'amaterasu_noice_manager_denoise.exr',
) -> str:
    '''Denoise image.'''
    noice: str = noice_path()
    if not noice:
        _logger.error('Not found noice.')
        return ''

    temp_dir: str = tempfile.gettempdir()
    output = os.path.join(temp_dir, output)

    command: list[str] = [
        noice,
        '-i',
        filename,
        '-o',
        output,
        '-v',
        str(variance),
        '-sr',
        str(search_radius),
        '-pr',
        str(patch_radius),
        '-ef',
        str(extra_frames),
    ]
    for aov in get_denoise_aovs(filename):
        command.extend(['-l', aov])

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command, startupinfo=startupinfo, check=True)

    except subprocess.CalledProcessError as e:
        _logger.error('Failed to denoise image : %s', e)
        return ''

    return output


def get_denoise_aovs(filename: str) -> list[str]:
    '''Returns denoise aovs from EXR file.'''
    oiiotool: str = oiiotool_path()
    if not oiiotool:
        _logger.error('Not found oiiotool.')
        return []

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        command: list[str] = [oiiotool, '--info', '-v', filename]
        result: subprocess.CompletedProcess[str] = subprocess.run(
            command,
            startupinfo=startupinfo,
            capture_output=True,
            text=True,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        _logger.error('Error running oiiotool: %s', e)
        return []

    aovs: set[str] = set()
    for line in result.stdout.splitlines():
        if 'channel list:' in line:
            channels: str = line.split('channel list:')[1]
            raw_channels: list[str] = channels.split(',')
            for raw_ch in raw_channels:
                channel: str = raw_ch.strip().split(' ')[-1]
                if '.' in channel:
                    aov_name: str = channel.split('.')[0]
                    aovs.add(aov_name)

                else:
                    aovs.add(channel)

    valid_aovs: list[str] = []
    for aov in aovs:
        if aov.endswith('_1'):
            continue

        if f'{aov}_1' in aovs:
            valid_aovs.append(aov)

    return valid_aovs


def convert_to_png(
    filename: str,
    output: str = 'amaterasu_noice_manager_preview.png',
    aov: str = 'Beauty',
) -> str:
    '''Convert EXR image to PNG.'''
    oiiotool: str = oiiotool_path()
    if not oiiotool:
        _logger.error('Not found oiiotool.')
        return ''

    temp_dir: str = tempfile.gettempdir()
    output: str = os.path.join(temp_dir, output)

    command: list[str] = [oiiotool, filename]
    if aov and aov != 'Beauty':
        command.extend(['--ch', f'R={aov}.R,G={aov}.G,B={aov}.B'])
    else:
        command.extend(['--ch', 'R,G,B'])

    command.extend(['--colorconvert', 'linear', 'sRGB'])
    command.extend(['-o', output])

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command, startupinfo=startupinfo, check=True)

    except subprocess.CalledProcessError as e:
        _logger.error('Failed to convert EXR to PNG: %s', e)
        return ''

    return output


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
