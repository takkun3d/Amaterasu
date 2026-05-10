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
"""Toast notification widget for Amaterasu.

This module provides the `ToastWidget`, a transient, auto-fading overlay
used to display alerts and information to the user in a non-intrusive way.
"""
from __future__ import annotations
from maya import mel
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc


class ToastWidget(QtWidgets.QWidget):
    """A custom widget that displays a transient toast notification.

    The widget appears at the bottom right of the main Maya window,
    fades in, stays for a specified duration, and fades out. Clicking
    the toast opens the Maya Script Editor.
    """

    label_color: dict[str, str] = {
        "INFO": "#5CB85C",
        "WARNING": "#E6A23C",
        "ERROR": "#F56C6C",
        "DEBUG": "#409EFF",
    }
    text_color: dict[str, str] = {
        "INFO": "#AAAAAA",
        "WARNING": "#AAAAAA",
        "ERROR": "#AAAAAA",
        "DEBUG": "#AAAAAA",
    }
    label_style: str = """
        QLabel {{
            background-color: #2B2B2B;
            border-left: 15px solid {label_color};
            padding: 5px 15px 5px 15px;
            border-radius: 0px;
            font-family: 'Segoe UI', sans-serif;
            font-weight: bold;
            color: {text_color};
        }}
        """
    label_text: str = """
        <style>
            .header{{
                font-size: 10px;
            }}
            .body{{
                font-size: 12px;
            }}
        </style>
        <div class="header">{title} : {level}</div>
        <div class="body">{message}</div>
        """
    display_time: int = 3000
    opacity: float = 0.9
    spacing: int = 3

    def __init__(
        self,
        title: str,
        level: str,
        message: str,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize the ToastWidget.

        Args:
            title (str): The title of the toast (usually the logger name).
            level (str): The log level (e.g., 'INFO', 'WARNING').
            message (str): The main content of the log message.
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None, which attaches it to Maya's main window.
        """
        if parent is None:
            parent = dcc.get_maya_window()

        super().__init__(parent)

        label_color: str = self.label_color.get(level, self.label_color["INFO"])
        text_color: str = self.text_color.get(level, self.text_color["INFO"])

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__label: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.__label.setText(
            self.label_text.format(
                label_color=label_color,
                text_color=text_color,
                title=title,
                level=level,
                message=message,
            )
        )
        self.__label.setStyleSheet(
            self.label_style.format(
                label_color=label_color,
                text_color=text_color,
                title=title,
                level=level,
                message=message,
            )
        )
        self.__label.setFixedWidth(300)
        self.__label.setWordWrap(True)
        layout.addWidget(self.__label)
        self.adjustSize()

        if parent is None:
            return

        geom: QtCore.QRect = parent.geometry()
        x: int = geom.x() + geom.width() - self.width() - 5
        y: int = geom.y() + 5
        self.move(x, y)
        self.setWindowOpacity(0.0)

        self.__fade_in_anim: QtCore.QPropertyAnimation = (
            QtCore.QPropertyAnimation(self, QtCore.QByteArray(b"windowOpacity"))
        )
        self.__fade_in_anim.setDuration(300)
        self.__fade_in_anim.setStartValue(0.0)
        self.__fade_in_anim.setEndValue(self.opacity)
        self.__fade_in_anim.start()

        self.__fade_out_anim: QtCore.QPropertyAnimation = (
            QtCore.QPropertyAnimation(self, QtCore.QByteArray(b"windowOpacity"))
        )
        self.__fade_out_anim.setDuration(400)
        self.__fade_out_anim.setStartValue(self.opacity)
        self.__fade_out_anim.setEndValue(0.0)
        self.__fade_out_anim.finished.connect(self.close)

        self.__target_y: int | None = None
        self.__anim_move: QtCore.QPropertyAnimation = QtCore.QPropertyAnimation(
            self, QtCore.QByteArray(b"pos")
        )
        self.__anim_move.setDuration(300)
        self.__anim_move.setEasingCurve(QtCore.QEasingCurve.Type.OutExpo)

        QtCore.QTimer.singleShot(self.display_time, self.__fade_out_anim.start)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse clicks on the toast notification.

        If the left mouse button is clicked, it opens the Maya Script Editor
        and immediately starts the fade-out animation to dismiss the toast.

        Args:
            event (QtGui.QMouseEvent): The mouse event parameters.
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            mel.eval("ScriptEditor;")
            self.__fade_out_anim.start()

        super().mousePressEvent(event)

    def offset(self, shift_amount: int) -> None:
        """Shift the toast widget vertically to make room for new toasts.

        Args:
            shift_amount (int): The amount of pixels to shift down.
        """
        if self.__target_y is None:
            self.__target_y = self.y()

        self.__target_y += shift_amount + self.spacing
        if self.__anim_move.state() == QtCore.QPropertyAnimation.State.Running:
            self.__anim_move.stop()

        self.__anim_move.setStartValue(self.pos())
        self.__anim_move.setEndValue(QtCore.QPoint(self.x(), self.__target_y))
        self.__anim_move.start()


class ToastSignalEmitter(QtCore.QObject):
    """Signal emitter for toast logging.

    Attributes:
        log_received (QtCore.Signal): Emits (title, level, message) when
            a new log record needs to be displayed.
    """

    log_received: QtCore.Signal = QtCore.Signal(str, str, str)
