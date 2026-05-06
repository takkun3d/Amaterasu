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
"""Custom Node Picker widget based on BrowseWidget."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base.widgets.browse_widget import BrowseWidget


class NodePicker(BrowseWidget):
    """A widget to load selected Maya nodes, inheriting the standard BrowseWidget UI."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        multi_select: bool = False,
        icon_name: str = "a_import.png",
    ) -> None:
        """Initializes the NodePicker.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            multi_select (bool, optional): Allow multiple nodes separated by commas.
                Defaults to False.
            icon_name (str, optional): The icon to display on the button.
                Defaults to "a_import.png".
        """
        super().__init__(parent, flag, icon_name)
        self.__multi_select: bool = multi_select
        self.clicked.connect(self._load_selection)

    def _load_selection(self) -> None:
        """Loads Maya selection into the text field."""
        selection: list[str] = cmds.ls(selection=True) or []
        if not selection:
            return

        if not self.__multi_select:
            self.set_text(selection[0])

        else:
            self.set_text(", ".join(selection))

    def text_as_list(self) -> list[str]:
        """Returns the text split by commas as a list of strings.

        Returns:
            list[str]: A list of node names without whitespace.
        """
        raw_text: str = self.text().strip()
        if not raw_text:
            return []

        return [s.strip() for s in raw_text.split(",") if s.strip()]
