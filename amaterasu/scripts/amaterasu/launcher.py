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
"""Amaterasu Launcher module.

This module provides the main portal UI for Amaterasu, allowing users to
check for updates, download new releases, and access quick links to
documentation and social media.
"""

from __future__ import annotations
from typing import Any
import pathlib
import json
import urllib.request
import webbrowser
import os
import re
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils
from . import env

__product__: str = "Amaterasu Launcher"
_logger: utils.Logger = utils.get_logger(__product__)

BG_IMAGE_PATH: str = dcc.get_icon_path("launcher/background.png")
NOTION_ICON_PATH: str = dcc.get_icon_path("launcher/notion.png")
GITHUB_ICON_PATH: str = dcc.get_icon_path("launcher/github.png")
X_ICON_PATH: str = dcc.get_icon_path("launcher/x.png")
ABOUT_ICON_PATH: str = dcc.get_icon_path("launcher/about.png")
CLOSE_ICON_PATH: str = dcc.get_icon_path("launcher/close.png")
_BG_IMAGE_URL: str = BG_IMAGE_PATH.replace("\\", "/")

LAUNCHER_CSS: str = f"""
    #AmaterasuLauncher {{
        background-color: #1a1a1a;
        border-radius: 15px;
        border-image: url("{_BG_IMAGE_URL}") 0 0 0 0 stretch stretch;
    }}
    #LeftPanel {{
        background-color: rgba(15, 15, 25, 150);
        border-top-left-radius: 15px;
        border-bottom-left-radius: 15px;
        border-right: 2px solid rgba(0, 210, 255, 100);
        margin: 0;
        padding: 20px;
    }}
    #RightPanel {{
        margin: 0;
        padding: 20px;
    }}
    #TitleLabel {{
        color: #ffffff;
        font-size: 36px;
        font-weight: 900;
        letter-spacing: 2px;
    }}
    #VersionLabel {{
        color: #00d2ff;
        font-size: 16px;
        font-weight: bold;
    }}
    #InfoText {{
        background-color: transparent;
        color: #ddd;
        font-size: 14px;
        line-height: 1.6;
        border: none;
    }}
    #LinkBtn {{
        background-color: transparent;
        border: none;
        border-radius: 10px;
    }}
    #LinkBtn:hover {{
        background-color: rgba(255, 255, 255, 30);
    }}
    #UpdateBtn {{
        background-color: #ffde00;
        color: #000;
        font-size: 18px;
        font-weight: 900;
        border-radius: 30px;
    }}
    #UpdateBtn:hover {{
        background-color: #ffeb3a;
        border: 2px solid #fff;
    }}
    #UpdateBtn:disabled {{
        background-color: rgba(255, 255, 255, 30);
        color: rgba(255, 255, 255, 100);
    }}
    QProgressBar {{
        background-color: rgba(0, 0, 0, 150);
        border-radius: 4px;
    }}
    QProgressBar::chunk {{
        background-color: #ffde00;
        border-radius: 4px;
    }}
    QScrollBar:vertical {{
        border: none;
        background: rgba(0, 0, 0, 50);
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: #00d2ff;
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
"""


class UpdateCheckerThread(QtCore.QThread):
    """A background thread to check for the latest Amaterasu release on GitHub.

    This thread silently fetches the latest release information from the
    GitHub API without blocking the main UI thread.
    """

    update_required = QtCore.Signal(dict)
    error_occurred = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtCore.QObject | None = None,
        force_emit: bool = False,
    ) -> None:
        """Initializes the update checker thread.

        Args:
            parent (QtCore.QObject | None, optional): The parent object.
                Defaults to None.
            force_emit (bool, optional): If True, forces the emission of
                the update signal even if the local version is already up-to-date.
                Defaults to False.
        """
        if parent is None:
            parent = parent = dcc.get_maya_window()

        super().__init__(parent)
        self.__force_emit: bool = force_emit

    def run(self) -> None:
        """Executes the version check operation.

        Fetches the latest tag from GitHub, compares it with the local version,
        and emits the `update_required` signal with release data if needed.
        """
        try:
            req = urllib.request.Request(env.GITHUB_LATEST_URL, method="HEAD")
            req.add_header("User-Agent", "Amaterasu-Updater")

            with urllib.request.urlopen(req, timeout=5) as response:
                tag_name = response.url.split("/")[-1]

            digits: str = re.sub(r"\D", "", tag_name)
            github_version: int = int(digits) if digits else 0
            local_version: int = env.__version__

            if github_version <= local_version and not self.__force_emit:
                return

            cache_dir: pathlib.Path = env.USER_DATA_DIR
            if not cache_dir.exists():
                os.makedirs(cache_dir)

            json_path: pathlib.Path = cache_dir / f"{tag_name}.json"
            release_data: dict[str, Any] = {}
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    release_data = json.load(f)

            else:
                api_req = urllib.request.Request(env.GITHUB_API_LATEST_URL)
                api_req.add_header("User-Agent", "Amaterasu-Updater")
                with urllib.request.urlopen(api_req, timeout=5) as api_res:
                    if api_res.status == 200:
                        release_data = json.loads(
                            api_res.read().decode("utf-8")
                        )
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(
                                release_data, f, ensure_ascii=False, indent=4
                            )

            self.update_required.emit(release_data)

        except TimeoutError as e:
            self.error_occurred.emit(f"Check failed: {str(e)}")

        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Check failed: {str(e)}")


class DownloadThread(QtCore.QThread):
    """A background thread for downloading the Amaterasu release ZIP file.

    Emits progress updates to keep the UI responsive during the download.
    """

    progress_changed = QtCore.Signal(int)
    download_finished = QtCore.Signal(bool, str)

    def __init__(
        self,
        url: str,
        save_path: str,
        parent: QtCore.QObject | None = None,
    ) -> None:
        """Initializes the download thread.

        Args:
            url (str): The URL of the ZIP file to download.
            save_path (str): The local file path where the ZIP will be saved.
            parent (QtCore.QObject | None, optional): The parent object.
                Defaults to None.
        """
        super().__init__(parent)
        self.__url: str = url
        self.__save_path: str = save_path

    def run(self) -> None:
        """Executes the download operation.

        Downloads the file in chunks, calculates the progress percentage,
        and emits the `progress_changed` and `download_finished` signals.
        """
        req: urllib.request.Request = urllib.request.Request(self.__url)
        req.add_header("User-Agent", "Amaterasu-Updater")

        try:
            with urllib.request.urlopen(req) as response:
                total_size: int = int(response.info().get("Content-Length", 0))
                bytes_so_far: int = 0
                chunk_size: int = 8192

                with open(self.__save_path, "wb") as f:
                    while True:
                        total_size = int(
                            response.info().get("Content-Length", 0)
                        )
                        chunk: bytes = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        bytes_so_far += len(chunk)

                        if total_size > 0:
                            self.progress_changed.emit(
                                int(bytes_so_far * 100 / total_size)
                            )

            self.download_finished.emit(True, self.__save_path)

        except urllib.error.URLError as e:
            self.download_finished.emit(False, str(e))


class Launcher(QtWidgets.QWidget):
    """The main portal UI for Amaterasu, providing update checks and quick links.

    Features a custom frameless window design with a background image.
    """

    def __init__(
        self,
        release_data: dict[str, Any],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the launcher UI.

        Args:
            release_data (dict | None, optional): Pre-fetched release data.
                If None, the launcher will fetch the data dynamically upon opening.
                Defaults to None.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        if parent is None:
            parent = dcc.get_maya_window()

        super().__init__(parent)
        self.setWindowTitle("Amaterasu Launcher")
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1280, 720)

        self.__version: QtWidgets.QLabel
        self.__info: QtWidgets.QTextEdit

        self.__release_data: dict[str, Any] = release_data
        self.__download_url: str = ""
        self.__download_thread: DownloadThread | None = None
        self.__drag_position: QtCore.QPoint = QtCore.QPoint()

        self.setup_ui()
        self.apply_release_data()
        self.center_window()

    def setup_ui(self) -> None:
        """Builds the frameless, game-launcher-style user interface."""

        bg: QtWidgets.QLabel = QtWidgets.QLabel(self)
        bg.setGeometry(0, 0, 1280, 720)
        bg.setObjectName("AmaterasuLauncher")

        main_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Panel
        left_panel: QtWidgets.QFrame = QtWidgets.QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setFixedWidth(500)
        main_layout.addWidget(left_panel)

        left_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(left_panel)

        title: QtWidgets.QLabel = QtWidgets.QLabel("AMATERASU")
        title.setObjectName("TitleLabel")
        left_layout.addWidget(title)

        self.__version = QtWidgets.QLabel("Checking...")
        self.__version.setObjectName("VersionLabel")
        left_layout.addWidget(self.__version)

        left_layout.addSpacing(10)

        self.__info = QtWidgets.QTextEdit()
        self.__info.setObjectName("InfoText")
        self.__info.setReadOnly(True)
        left_layout.addWidget(self.__info)

        left_layout.addSpacing(10)

        links_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        left_layout.addLayout(links_layout)

        notion: QtWidgets.QPushButton = QtWidgets.QPushButton(self)
        notion.setObjectName("LinkBtn")
        notion.setFixedSize(40, 40)
        notion.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        notion.setIcon(QtGui.QIcon(NOTION_ICON_PATH))
        notion.setIconSize(QtCore.QSize(24, 24))
        notion.clicked.connect(lambda: webbrowser.open(env.NOTION_URL))
        links_layout.addWidget(notion)

        github: QtWidgets.QPushButton = QtWidgets.QPushButton(self)
        github.setObjectName("LinkBtn")
        github.setFixedSize(40, 40)
        github.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        github.setIcon(QtGui.QIcon(GITHUB_ICON_PATH))
        github.setIconSize(QtCore.QSize(24, 24))
        github.clicked.connect(lambda: webbrowser.open(env.GITHUB_URL))
        links_layout.addWidget(github)

        twitter: QtWidgets.QPushButton = QtWidgets.QPushButton(self)
        twitter.setObjectName("LinkBtn")
        twitter.setFixedSize(40, 40)
        twitter.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        twitter.setIcon(QtGui.QIcon(X_ICON_PATH))
        twitter.setIconSize(QtCore.QSize(24, 24))
        twitter.clicked.connect(lambda: webbrowser.open(env.X_URL))
        links_layout.addWidget(twitter)

        links_layout.addStretch()

        # Right Panel
        right_panel: QtWidgets.QFrame = QtWidgets.QFrame()
        right_panel.setObjectName("RightPanel")
        main_layout.addWidget(right_panel)

        right_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(right_panel)

        top_right_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        right_layout.addLayout(top_right_layout)

        top_right_layout.addStretch()

        about: QtWidgets.QPushButton = QtWidgets.QPushButton(self)
        about.setObjectName("LinkBtn")
        about.setFixedSize(40, 40)
        about.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        about.setIcon(QtGui.QIcon(ABOUT_ICON_PATH))
        about.setIconSize(QtCore.QSize(24, 24))
        about.clicked.connect(self.show_about)
        top_right_layout.addWidget(about)

        close: QtWidgets.QPushButton = QtWidgets.QPushButton(self)
        close.setObjectName("LinkBtn")
        close.setFixedSize(40, 40)
        close.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        close.setIcon(QtGui.QIcon(CLOSE_ICON_PATH))
        close.setIconSize(QtCore.QSize(24, 24))
        close.clicked.connect(self.close)
        top_right_layout.addWidget(close)

        right_layout.addStretch()

        self.__progress_bar: QtWidgets.QProgressBar = QtWidgets.QProgressBar()
        self.__progress_bar.setVisible(False)
        self.__progress_bar.setFixedHeight(8)
        self.__progress_bar.setTextVisible(False)
        right_layout.addWidget(self.__progress_bar)

        bottom_right_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        right_layout.addLayout(bottom_right_layout)

        bottom_right_layout.addStretch()

        self.__update_btn: QtWidgets.QPushButton = QtWidgets.QPushButton("...")
        self.__update_btn.setObjectName("UpdateBtn")
        self.__update_btn.setEnabled(False)
        self.__update_btn.setFixedSize(280, 60)
        self.__update_btn.clicked.connect(self.download)
        bottom_right_layout.addWidget(self.__update_btn)

        self.setStyleSheet(LAUNCHER_CSS)

    def apply_release_data(self) -> None:
        """Parses the stored release data and updates the launcher UI.

        Extracts the version information and release notes to display.
        Constructs the download URL and enables the download button.
        If the local version is already up-to-date with the GitHub version,
        the download button is disabled.
        """
        tag_name: str = self.__release_data.get("tag_name", "Unknown")
        digits: str = re.sub(r'\D', '', tag_name)
        github_version: int = int(digits) if digits else 0
        body: str = self.__release_data.get("body", "No release notes.")

        self.__version.setText(f"LATEST VERSION: {github_version}")
        self.__info.setMarkdown(body)
        if tag_name != "Unknown":
            self.__download_url = (
                f"{env.GITHUB_URL}/archive/refs/tags/{tag_name}.zip"
            )
            self.__update_btn.setEnabled(True)
            self.__update_btn.setText("DOWNLOAD ZIP")

        local_version: int = env.__version__
        if github_version <= local_version:
            self.__update_btn.setEnabled(False)

    def center_window(self) -> None:
        """Centers the launcher window on the screen."""
        window_geometry: QtCore.QRect = self.frameGeometry()
        screen: QtGui.QScreen = QtGui.QGuiApplication.primaryScreen()
        if screen:
            screen_geometry: QtCore.QRect = screen.availableGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            self.move(window_geometry.topLeft())

    def download(self) -> None:
        """Opens a file dialog for the user and starts the download thread."""
        version_str: str = (
            self.__version.text().replace("LATEST VERSION: ", "").strip()
        )
        default_filename: str = (
            f"Amaterasu_{version_str}.zip"
            if version_str
            else "Amaterasu_latest.zip"
        )
        desktop_path: pathlib.Path = pathlib.Path.home() / "Desktop"
        initial_path: pathlib.Path = desktop_path / default_filename

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Amaterasu ZIP File",
            str(initial_path),
            "ZIP Files (*.zip);;All Files (*)",
        )

        if not save_path:
            return

        self.__update_btn.setEnabled(False)
        self.__update_btn.setText("DOWNLOADING...")
        self.__progress_bar.setValue(0)
        self.__progress_bar.setRange(0, 0)
        self.__progress_bar.setVisible(True)

        self.__download_thread = DownloadThread(
            self.__download_url, save_path, self
        )
        self.__download_thread.progress_changed.connect(
            self.__progress_bar.setValue
        )
        self.__download_thread.download_finished.connect(self.finished_download)
        self.__download_thread.start()

    def finished_download(self, success: bool, message: str) -> None:
        """Handles the completion of the download process.

        Args:
            success (bool): True if the download was successful, False otherwise.
            message (str): The saved file path or the error message.
        """
        self.__progress_bar.setVisible(False)
        self.__update_btn.setEnabled(True)
        self.__update_btn.setText("DOWNLOAD ZIP")

        if success:
            _logger.info("Downloaded latest Amaterasu: %s", message)

        else:
            _logger.error("Faield to download amaterasu: %s", message)

    def show_about(self) -> None:
        """Displays the About dialog using the common widget."""
        framework.AboutDialog.info(
            dcc.get_maya_window(),
            env.__product__,
            str(env.__version__),
            env.DEFAULT_LICENSE,
            "",
        )

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles the mouse press event to enable dragging the frameless window.
        Records the initial click position relative to the window's top-left corner.

        Args:
            event (QtGui.QMouseEvent): The mouse event containing position data.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            global_pos: QtCore.QPoint = (
                event.globalPosition().toPoint()
                if hasattr(event, "globalPosition")
                else event.globalPos()
            )
            self.__drag_position = global_pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles the mouse move event to update the window position during a drag.
        Calculates the new global position and moves the window accordingly.

        Args:
            event (QtGui.QMouseEvent): The mouse event containing position data.
        """
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            global_pos: QtCore.QPoint = (
                event.globalPosition().toPoint()
                if hasattr(event, "globalPosition")
                else event.globalPos()
            )
            self.move(global_pos - self.__drag_position)
            event.accept()


def show_launcher(release_data: dict[str, Any]) -> None:
    """Instantiates and shows the launcher using pre-fetched data.
    Typically called silently during startup if an update is detected.

    Args:
        release_data (dict): The release information.
    """
    launcher = Launcher(release_data)
    launcher.show()


def main(force_emit: bool = True) -> None:
    """Manually opens the Amaterasu Launcher and checks for updates dynamically.
    Typically called from the Amaterasu DCC menu.

    Args:
        force_emit (bool, optional): If True, forces the launcher to show the update UI
            even if the current version is up-to-date. Defaults to True.
    """
    thread = UpdateCheckerThread(force_emit=force_emit)
    thread.update_required.connect(show_launcher)
    thread.start()
