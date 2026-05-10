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
"""Custom TabWidget with add, rename, and close capabilities."""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc
from amaterasu.base.widgets.icon_button import IconButton

TAB_ADD: str = "a_add.png"
TAB_ADD_HOVER: str = "a_add_hover.png"
TAB_ADD_PRESSED: str = "a_add_pressed.png"
TAB_CLOSE: str = "a_close.png"
TAB_CLOSE_HOVER: str = "a_close_hover.png"
TAB_CLOSE_PRESSED: str = "a_close_pressed.png"
TAB_ICON_SIZE: QtCore.QSize = QtCore.QSize(24, 24)


class TabBarPlus(QtWidgets.QTabBar):
    """Custom QTabBar with an interactive 'Plus' button for adding tabs."""

    plus_clicked = QtCore.Signal()
    double_clicked = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the TabBarPlus widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)

        self.__plus: IconButton = IconButton(self)
        self.__plus.set_icon(TAB_ADD)
        self.__plus.set_hover_icon(TAB_ADD_HOVER)
        self.__plus.set_pressed_icon(TAB_ADD_PRESSED)
        self.__plus.setIconSize(TAB_ICON_SIZE)
        self.__plus.clicked.connect(self.plus_clicked.emit)

        close_icon: str = dcc.get_icon_path(TAB_CLOSE)
        close_hover: str = dcc.get_icon_path(TAB_CLOSE_HOVER)
        close_pressed: str = dcc.get_icon_path(TAB_CLOSE_PRESSED)
        self.setStyleSheet(f"""
            QTabBar::close-button {{ image: url({close_icon}); }}
            QTabBar::close-button:hover {{ image: url({close_hover}); }}
            QTabBar::close-button:pressed {{ image: url({close_pressed}); }}
            """)
        self.move_plus_button()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Overrides mousePressEvent to emit double_clicked on the tab.

        Args:
            event (QtGui.QMouseEvent): The mouse press event.
        """
        if event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
            if self.tabRect(self.currentIndex()).contains(event.pos()):
                self.double_clicked.emit()
        else:
            super().mousePressEvent(event)

    def sizeHint(self) -> QtCore.QSize:
        """Overrides sizeHint to make room for the plus button.

        Returns:
            QtCore.QSize: The adjusted size hint.
        """
        size_hint: QtCore.QSize = super().sizeHint()
        return QtCore.QSize(size_hint.width() + 25, TAB_ICON_SIZE.height())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Overrides resizeEvent to adjust the plus button position.

        Args:
            event (QtGui.QResizeEvent): The resize event.
        """
        super().resizeEvent(event)
        self.move_plus_button()

    def tabLayoutChange(self) -> None:
        """Overrides tabLayoutChange to adjust the plus button position."""
        super().tabLayoutChange()
        self.move_plus_button()

    def move_plus_button(self) -> None:
        """Moves the plus button to the right end of the tabs."""
        size: int = sum(self.tabRect(i).width() for i in range(self.count()))
        w: int = self.width()
        h: int = self.geometry().top()

        if size > w:
            self.__plus.move(w - 54, h)

        else:
            self.__plus.move(size, h)


class TabWidget(QtWidgets.QTabWidget):
    """A generic TabWidget that notifies the parent when actions are requested."""

    add_requested = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        default_tab_name: str = "No Name",
        title: str = "Information",
    ) -> None:
        """Initializes the TabWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            default_tab_name (str, optional): The default name for newly created tabs.
                Defaults to "No Name".
            title (str, optional): The title used for input dialogs.
                Defaults to "Information".
        """
        super().__init__(parent)

        self.__default_tab_name: str = default_tab_name
        self.__title: str = title

        tab_bar = TabBarPlus(self)
        tab_bar.plus_clicked.connect(self.add_tab_callback)
        tab_bar.double_clicked.connect(self.rename_tab_callback)

        self.setTabBar(tab_bar)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.remove_tab)

    @QtCore.Slot()
    def add_tab_callback(self) -> None:
        """Prompts for a name and emits the signal."""
        text: str
        ok: bool
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            self.__title,
            "New Tab Name",
            QtWidgets.QLineEdit.EchoMode.Normal,
            self.__default_tab_name,
        )
        if ok:
            self.add_requested.emit(text)

    @QtCore.Slot()
    def rename_tab_callback(self) -> None:
        """Prompts to rename the current tab."""
        text: str
        ok: bool
        text, ok = QtWidgets.QInputDialog.getText(
            self,
            self.__title,
            "Rename Tab Name",
            QtWidgets.QLineEdit.EchoMode.Normal,
            self.tabText(self.currentIndex()),
        )
        if ok:
            self.setTabText(self.currentIndex(), text)

    @QtCore.Slot(int)
    def remove_tab(self, index: int) -> None:
        """Removes the tab at the specified index if more than one exists.

        Args:
            index (int): The index of the tab to be removed.
        """
        if self.count() >= 2:
            self.removeTab(index)

    def add_custom_tab(self, widget: QtWidgets.QWidget, label: str) -> None:
        """Adds a custom widget as a new tab and switches to it.

        Args:
            widget (QtWidgets.QWidget): The custom widget to display in the new tab.
            label (str): The text label for the new tab.
        """
        self.addTab(widget, label)
        self.setCurrentIndex(self.count() - 1)
