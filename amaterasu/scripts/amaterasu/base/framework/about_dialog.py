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
"""Standard 'About' dialog module for Amaterasu tools.

This module provides the `AboutDialog` class, which is used to display
consistent product information, versioning, and copyright details across
all Amaterasu tool windows. It automatically handles Maya main window
parenting to ensure the dialog stays on top of the application.
"""
from __future__ import annotations
from maya import OpenMayaUI
from amaterasu.base.qt import QtCore, QtGui, QtWidgets, wrap_instance
from amaterasu.base import dcc

LOGO: str = "a_logo.png"
HEADER: str = "a_about_header.png"


class AboutDialog(QtWidgets.QDialog):
    """A standardized 'About' dialog for displaying tool information.

    This dialog automatically parents itself to Maya's main window if no
    parent is provided. It displays a header image, formatted HTML text
    for tool details, and a standard 'OK' button to close.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Dialog,
    ) -> None:
        """Initializes the AboutDialog.

        If no parent is provided, it dynamically finds Maya's main window
        and sets it as the parent to prevent the dialog from being hidden.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Dialog.
        """
        if parent is None:
            ptr: int = int(OpenMayaUI.MQtUtil.mainWindow())
            parent = wrap_instance(ptr, QtWidgets.QWidget)

        super().__init__(parent, flag)
        self.setWindowIcon(QtGui.QIcon(dcc.get_icon_path(LOGO)))
        self.resize(320, 340)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)

        header_image: QtWidgets.QLabel = QtWidgets.QLabel(self)
        header_image.setPixmap(QtGui.QPixmap(dcc.get_icon_path(HEADER)))
        header_image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_image)

        self.__text_area: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.__text_area.setReadOnly(True)
        main_layout.addWidget(self.__text_area)

        ok_button: QtWidgets.QPushButton = QtWidgets.QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)
        main_layout.addWidget(ok_button)

    def set_text(self, text: str) -> None:
        """Sets the rich text content of the dialog.

        Args:
            text (str): The HTML formatted string to display in the text area.
        """
        self.__text_area.setText(text)

    @classmethod
    def info(
        cls,
        parent: QtWidgets.QWidget | None = None,
        product: str = "",
        version: str = "",
        copyright_: str = "",
        document: str = "",
    ) -> AboutDialog:
        """A convenience factory method to create and show the About dialog.

        This method generates the standard HTML layout using the provided
        tool information, instantiates the dialog, and displays it.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            product (str, optional): The name of the tool/product.
                Defaults to "".
            version (str, optional): The version string. Defaults to "".
            copyright_ (str, optional): The copyright notice.
                Defaults to "".
            document (str, optional): A brief description of the tool.
                Defaults to "".

        Returns:
            Self: The created AboutDialog instance.
        """
        text: str = f"""
<h1>{product}</h1>
<p>Version: {version}</p>
<hr />
<p>{document}</p>
<hr />
<p>{copyright_}</p>
"""
        dialog: AboutDialog = cls(parent)
        dialog.setWindowTitle(f"About {product}")
        dialog.set_text(text)
        dialog.show()
        return dialog
