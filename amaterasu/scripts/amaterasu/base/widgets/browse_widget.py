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
"""rovides a generic combined widget with a text field and an action button.

This highly versatile widget is commonly used for browsing file paths,
capturing selected Maya nodes, or triggering custom input dialogs.
"""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base.widgets.icon_button import IconButton


class BrowseWidget(QtWidgets.QWidget):
    """A combined widget containing a line edit and a browse button.

    This widget is commonly used to accept file paths or node names,
    providing a convenient button to trigger a file dialog or selection.

    Attributes:
        clicked (QtCore.Signal): Emitted when the browse button is clicked.
    """

    clicked: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        icon_name: str = "a_folder.png",
    ) -> None:
        """Initializes the BrowseWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            icon_name (str, optional): The icon to display on the button.
                Defaults to "a_folder.png".
        """
        super().__init__(parent, flag)

        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.__line_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        layout.addWidget(self.__line_edit)

        self.__button: IconButton = IconButton(self)
        self.__button.set_icon(icon_name)
        self.__button.clicked.connect(self.clicked)
        layout.addWidget(self.__button)

    def text(self) -> str:
        """Gets the current text of the line edit.

        Returns:
            str: The text currently displayed in the line edit.
        """
        return self.__line_edit.text()

    def set_text(self, text: str) -> None:
        """Sets the text of the line edit.

        Args:
            text (str): The text to display in the line edit.
        """
        self.__line_edit.setText(text)

    def set_icon(self, icon_name: str) -> None:
        """Set the default icon for the button from a file name.

        Args:
            icon (str): The file name of the default icon (e.g., "icon.png").
        """
        self.__button.set_icon(icon_name)
