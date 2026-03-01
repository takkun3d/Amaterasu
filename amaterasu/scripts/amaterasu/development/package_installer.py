# ==============================================================================
#
# Amaterasu Package Installer
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import sys
import os
import subprocess

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QTextEdit,
        QLabel,
        QCheckBox,
        QLineEdit,
        QApplication,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QPushButton,
            QTextEdit,
            QLabel,
            QCheckBox,
            QLineEdit,
            QApplication,
            QMessageBox,
        )

from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Package Installer'
__version__: str = '1.10'
__doc__ = (
    'GUI tool to install/uninstall python packages via pip for current Maya.'
)
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

PACKAGE_MAP: dict[str, str] = {
    'numpy': 'numpy',
    'scipy': 'scipy',
    'Pillow': 'PIL',
    'opencv-python': 'cv2',
    'requests': 'requests',
}


# ==============================================================================
#
# Colors
#
# ==============================================================================
class LogColor:
    '''Color constants for log output.'''

    DEFAULT: str = '#EEEEEE'
    GREEN: str = '#44FF44'
    YELLOW: str = '#FFFF44'
    CYAN: str = '#44FFFF'
    RED: str = '#FF5555'
    GRAY: str = '#888888'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    use_user_flag: parser.Variant[bool] = parser.Variant(True)


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
        self.resize(700, 600)

        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        mayapy_path: str = get_mayapy_path()
        main_layout.addWidget(QLabel(f'<strong>Target:</strong> {mayapy_path}'))

        self.__user_flag: QCheckBox = QCheckBox(
            'Install to User Directory (Does not require Administrator)', self
        )
        main_layout.addWidget(self.__user_flag)

        #
        util_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(util_layout)

        button: QPushButton = QPushButton('Show Install Dirs', self)
        button.clicked.connect(self.check_directories)
        util_layout.addWidget(button)

        button = QPushButton('Show Installed Packages', self)
        button.clicked.connect(self.show_packages)
        util_layout.addWidget(button)

        button = QPushButton('Upgrade pip', self)
        button.clicked.connect(self.upgrade_pip)
        util_layout.addWidget(button)

        main_layout.addWidget(widgets.HorizontalLine(self))

        #
        main_layout.addWidget(QLabel('<strong>Install Package</strong>', self))

        install_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(install_layout)
        install_layout.setSpacing(2)

        button = QPushButton('NumPy', self)
        button.clicked.connect(lambda: self.install_package('numpy'))
        install_layout.addWidget(button)

        button = QPushButton('SciPy', self)
        button.clicked.connect(lambda: self.install_package('scipy'))
        install_layout.addWidget(button)

        button = QPushButton('Pillow', self)
        button.clicked.connect(lambda: self.install_package('Pillow'))
        install_layout.addWidget(button)

        button = QPushButton('OpenCV', self)
        button.clicked.connect(lambda: self.install_package('opencv-python'))
        install_layout.addWidget(button)

        button = QPushButton('Requests', self)
        button.clicked.connect(lambda: self.install_package('requests'))
        install_layout.addWidget(button)

        #
        manual_install_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(manual_install_layout)

        self.__install_input: QLineEdit = QLineEdit(self)
        self.__install_input.setPlaceholderText('Package Name...')
        manual_install_layout.addWidget(self.__install_input)

        button = QPushButton('Install', self)
        button.setMinimumWidth(70)
        button.clicked.connect(self.install_package)
        manual_install_layout.addWidget(button)

        main_layout.addWidget(widgets.HorizontalLine(self))

        #
        main_layout.addWidget(
            QLabel('<strong>Uninstall Package</strong>', self)
        )

        uninstall_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(uninstall_layout)
        uninstall_layout.setSpacing(2)

        button = QPushButton('NumPy', self)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(lambda: self.uninstall_package('numpy'))
        uninstall_layout.addWidget(button)

        button = QPushButton('SciPy', self)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(lambda: self.uninstall_package('scipy'))
        uninstall_layout.addWidget(button)

        button = QPushButton('Pillow', self)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(lambda: self.uninstall_package('Pillow'))
        uninstall_layout.addWidget(button)

        button = QPushButton('OpenCV', self)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(lambda: self.uninstall_package('opencv-python'))
        uninstall_layout.addWidget(button)

        button = QPushButton('Requests', self)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(lambda: self.uninstall_package('requests'))
        uninstall_layout.addWidget(button)

        manual_uninstall_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(manual_uninstall_layout)

        self.__uninstall_input: QLineEdit = QLineEdit(self)
        self.__uninstall_input.setPlaceholderText('Package Name')
        manual_uninstall_layout.addWidget(self.__uninstall_input)

        button = QPushButton('Uninstall', self)
        button.setMinimumWidth(70)
        button.setStyleSheet('background-color: #552222;')
        button.clicked.connect(self.uninstall_package)
        manual_uninstall_layout.addWidget(button)

        main_layout.addWidget(widgets.HorizontalLine(self))

        #
        log_header_layout: QHBoxLayout = QHBoxLayout()
        main_layout.addLayout(log_header_layout)

        log_header_layout.addWidget(QLabel('Log Output:', self))
        log_header_layout.addStretch()

        self.__log_area: QTextEdit = QTextEdit(self)
        self.__log_area.setReadOnly(True)
        self.__log_area.setStyleSheet(
            'background-color: #222222; '
            'color: #EEEEEE; '
            'font-family: "Consolas", "Courier New", "Menlo", monospace;'
        )
        main_layout.addWidget(self.__log_area)

        button = QPushButton('Clear Log', self)
        button.clicked.connect(self.__log_area.clear)
        log_header_layout.addWidget(button)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__user_flag.setChecked(settings.use_user_flag.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.use_user_flag.set_value(self.__user_flag.isChecked())
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

    def log(self, message: str, color: str = LogColor.DEFAULT) -> None:
        '''Append text to log area with specified color.'''
        formatted_message = f'<span style="color:{color};">{message}</span>'
        self.__log_area.append(formatted_message)
        scroll_bar = self.__log_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        QApplication.processEvents()

    def show_restart_dialog(self) -> None:
        '''Show a dialog prompting the user to restart Maya.'''
        QMessageBox.information(
            self,
            'Restart Required',
            'Process completed.\nPlease restart Maya to apply changes.',
            QMessageBox.Ok,
        )

    def run_process(self, cmd_list: list[str]) -> bool:
        '''Helper to run subprocess commands with real-time logging.'''
        cmd_str: str = ' '.join(cmd_list)
        self.log(f'>> Running: {cmd_str}', LogColor.GREEN)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        result: bool = False
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo,
                universal_newlines=True,
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    self.log(line.rstrip(), LogColor.DEFAULT)

            if process.returncode == 0:
                self.log('>> SUCCESS (Code: 0)', LogColor.CYAN)
                result = True

            else:
                self.log(
                    f'>> FAILED (Code: {process.returncode}).', LogColor.RED
                )

        except Exception as e:
            self.log(f'>> EXCEPTION: {e}', LogColor.RED)

        finally:
            QApplication.restoreOverrideCursor()

        self.log('\n')
        return result

    def run_pip(self, args: list[str]) -> bool:
        '''Run pip command via subprocess.'''
        mayapy: str = get_mayapy_path()
        if not os.path.exists(mayapy):
            self.log(f'Error: mayapy not found at {mayapy}', LogColor.RED)
            return False

        cmd: list[str] = [mayapy, '-m', 'pip'] + args

        if self.__user_flag.isChecked() and 'pip' not in args[-1]:
            if 'install' in args and '--user' not in args:
                cmd.append('--user')

        return self.run_process(cmd)

    def check_directories(self) -> None:
        '''Show site packages directories.'''
        mayapy: str = get_mayapy_path()

        if self.__user_flag.isChecked():
            self.log('-' * 80, LogColor.YELLOW)
            self.log('User Install Locations', LogColor.YELLOW)
            self.log('-' * 80, LogColor.YELLOW)

            self.log('[User Base]', LogColor.DEFAULT)
            self.run_process([mayapy, '-m', 'site', '--user-base'])

            self.log('\n', LogColor.DEFAULT)
            self.log('[User Site-Packages]', LogColor.DEFAULT)
            self.run_process([mayapy, '-m', 'site', '--user-site'])

        else:
            self.log('-' * 80, LogColor.YELLOW)
            self.log('System Paths', LogColor.YELLOW)
            self.log('-' * 80, LogColor.YELLOW)
            self.run_process([mayapy, '-m', 'site'])

    def show_packages(self) -> None:
        '''Show installed packages.'''
        mayapy: str = get_mayapy_path()

        if self.__user_flag.isChecked():
            self.log('-' * 80, LogColor.YELLOW)
            self.log('User Installed Packages', LogColor.YELLOW)
            self.log('-' * 80, LogColor.YELLOW)
            self.run_process([mayapy, '-m', 'pip', 'list', '--user'])
        else:
            self.log('-' * 80, LogColor.YELLOW)
            self.log('All Installed Packages', LogColor.YELLOW)
            self.log('-' * 80, LogColor.YELLOW)
            self.run_process([mayapy, '-m', 'pip', 'list'])

    def upgrade_pip(self) -> None:
        '''Upgrade pip.'''
        self.log('-' * 80, LogColor.YELLOW)
        self.log('Upgrade pip', LogColor.YELLOW)
        self.log('-' * 80, LogColor.YELLOW)
        self.run_pip(['install', '--upgrade', 'pip'])

    def install_package(self, package_name: str | None = None) -> None:
        '''Install specific package. If None, read from text input.'''

        if not package_name:
            package_name = self.__install_input.text().strip()

        if not package_name:
            self.log(
                'Error: Please enter a package name or use preset buttons.',
                LogColor.RED,
            )
            return

        # Check sys.modules
        module_name: str = PACKAGE_MAP.get(package_name, package_name)
        if module_name in sys.modules:
            QMessageBox.warning(
                self,
                'Restart Required',
                f'{package_name} is currently loaded and locked.\n'
                f'Please restart Maya (without loading {package_name}) and try again.',
            )
            return

        self.log('-' * 80, LogColor.YELLOW)
        self.log(f'Install Package : {package_name}', LogColor.YELLOW)
        self.log('-' * 80, LogColor.YELLOW)
        if self.run_pip(['install', package_name]):
            self.show_restart_dialog()

    def uninstall_package(self, package_name: str | None = None) -> None:
        '''Uninstall package. If None, read from text input.'''

        if not package_name:
            package_name = self.__uninstall_input.text().strip()

        if not package_name:
            self.log(
                'Error: Please enter a package name or use preset buttons.',
                LogColor.RED,
            )
            return

        # Check sys.modules
        module_name: str = PACKAGE_MAP.get(package_name, package_name)
        if module_name in sys.modules:
            QMessageBox.warning(
                self,
                'Restart Required',
                f'{package_name} is currently loaded and locked.\n'
                f'Please restart Maya (without loading {package_name}) and try again.',
            )
            return

        self.log('-' * 80, LogColor.YELLOW)
        self.log(f'Uninstall Package : {package_name}', LogColor.YELLOW)
        self.log('-' * 80, LogColor.YELLOW)
        if self.run_pip(['uninstall', package_name, '-y']):
            self.show_restart_dialog()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def get_mayapy_path() -> str:
    '''Get the path to mayapy executable for the current Maya.'''
    bin_dir: str = os.path.dirname(sys.executable)
    if os.name == 'nt':
        return os.path.join(bin_dir, 'mayapy.exe')
    else:
        return os.path.join(bin_dir, 'mayapy')


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
