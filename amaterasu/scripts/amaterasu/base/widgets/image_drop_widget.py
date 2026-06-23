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
"""Generic graphical user interface widgets for Amaterasu.

This module provides reusable UI components designed to be used across
various Amaterasu tools. Widgets defined here, such as `DropImage`,
are intended to be pure UI elements. They rely on Qt signals to communicate
user interactions and strictly avoid containing Maya-specific business logic,
ensuring maximum reusability and a clean MVC architecture.
"""

from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc

DROP_ICON: str = dcc.get_icon_path("a_download.png")


class ImageDropImage(QtWidgets.QLabel):
    """A custom QLabel widget that accepts image file drag and drop.

    This widget displays a placeholder icon initially. When a user drops an
    image file onto it, it updates its pixmap to display the dropped image
    and emits a signal with the file path.

    Attributes:
        image_dropped (QtCore.Signal): Signal emitted when an image is successfully
            dropped. Emits the string path of the dropped image file.
    """

    image_dropped = QtCore.Signal(str)

    def __init__(
        self,
        width: int = 128,
        height: int = 128,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the DropImage widget.

        Args:
            width (int, optional): The fixed width of the widget. Defaults to 128.
            height (int, optional): The fixed height of the widget. Defaults to 128.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resize(width, height)
        self.setAcceptDrops(True)

        self.__file_path: str = ""

        pixmap: QtGui.QPixmap = QtGui.QPixmap(DROP_ICON)
        pixmap = pixmap.scaled(
            self.width(),
            self.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(pixmap)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Handles the drag enter event to accept URLs.

        Args:
            event (QtGui.QDragEnterEvent): The drag enter event containing
                mime data.
        """
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handles the drop event to load and display the dropped image.

        Extracts the file path from the dropped URL, loads it into a QPixmap,
        scales it to fit the widget, and emits the `image_dropped` signal.
        Only processes the first valid image URL.

        Args:
            event (QtGui.QDropEvent): The drop event containing the dragged URLs.
        """
        urls: list[QtCore.QUrl] = event.mimeData().urls()
        for url in urls:
            file_path: str = url.toLocalFile()
            pixmap: QtGui.QPixmap = QtGui.QPixmap(file_path)
            if pixmap.isNull():
                continue

            pixmap = pixmap.scaled(
                self.width(),
                self.height(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pixmap)
            self.__file_path = file_path

            self.image_dropped.emit(self.__file_path)
            break

    def file_path(self) -> str:
        """Gets the file path of the currently loaded image.

        Returns:
            str: The absolute file path of the dropped image, or an empty string
                if no image has been dropped yet.
        """
        return self.__file_path
