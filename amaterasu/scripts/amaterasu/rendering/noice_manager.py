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
    from PySide2.QtCore import Qt
    from PySide2.QtGui import QDragEnterEvent
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QVBoxLayout,
        QDoubleSpinBox,
        QSpinBox,
        QCheckBox,
        QLabel,
        QListWidget,
        QPushButton,
        QFileDialog,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QDragEnterEvent
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QVBoxLayout,
            QDoubleSpinBox,
            QSpinBox,
            QCheckBox,
            QLabel,
            QListWidget,
            QPushButton,
            QFileDialog,
            QMessageBox,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Noice Manager'
__version__: str = '1.00'
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
        button_layout.addWidget(button)

        button = QPushButton('Run in Consle', self)
        button.clicked.connect(self.run_console)
        button_layout.addWidget(button)

        button = QPushButton('Save Batch', self)
        button.clicked.connect(self.save_batch_file)
        button_layout.addWidget(button)

        # Right
        # Preview
        self.__preview: QWidget = QWidget(self)
        main_layout.addWidget(self.__preview)

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
        contents: str = generate_batch_content(
            folder_paths,
            self.__variance.value(),
            self.__search_radius.value(),
            self.__patch_radius.value(),
            self.__extra_frames.value(),
            self.__auto_frames.isChecked(),
            self.__override_frames.value(),
        )
        return contents

    def run_console(self) -> None:
        '''Run'''
        self.save_settings()
        contents: str = self.__batch_contents()
        if not contents:
            QMessageBox.critical(
                self, 'Error', 'Failed to generate batch commands.'
            )
            return

        bat: str = os.path.join(
            tempfile.gettempdir(), 'amaterasu_noice_manager.bat'
        )
        try:
            with open(bat, 'w', encoding='cp932', errors='ignore') as f:
                f.write(contents)

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
            return

        subprocess.Popen([bat], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def save_batch_file(self) -> None:
        '''Save batch file.'''
        self.save_settings()
        contents: str = self.__batch_contents()
        if not contents:
            QMessageBox.critical(
                self, 'Error', 'Failed to generate batch commands.'
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Batch', '', 'Batch Files (*.bat)'
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='cp932', errors='ignore') as f:
                f.write(contents)

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
            return


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
        _logger.error('Not found EXR files.')
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


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
