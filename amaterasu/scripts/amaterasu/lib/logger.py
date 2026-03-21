# ==============================================================================
#
# Logger
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import (
        QObject,
        Qt,
        Signal,
        QRect,
        QPoint,
        QPropertyAnimation,
        QByteArray,
        QEasingCurve,
        QTimer,
    )
    from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            QObject,
            Qt,
            Signal,
            QRect,
            QPoint,
            QPropertyAnimation,
            QByteArray,
            QEasingCurve,
            QTimer,
        )
        from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from . import widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================


# ==============================================================================
#
# Classes
#
# ==============================================================================
class ToastWidget(QWidget):
    '''Toast Widget'''

    label_color: dict[str, str] = {
        'INFO': '#5CB85C',
        'WARNING': '#E6A23C',
        'ERROR': '#F56C6C',
        'DEBUG': '#409EFF',
    }
    text_color: dict[str, str] = {
        'INFO': '#AAAAAA',
        'WARNING': '#AAAAAA',
        'ERROR': '#AAAAAA',
        'DEBUG': '#AAAAAA',
    }
    label_style: str = '''
        QLabel {{
            background-color: #2B2B2B;
            border-left: 15px solid {label_color};
            padding: 5px 15px 5px 15px;
            border-radius: 0px;
            font-family: 'Segoe UI', sans-serif;
            font-weight: bold;
            color: {text_color};
        }}
        '''
    display_time: int = 3000
    opacity: float = 0.9
    spacing: int = 3

    def __init__(
        self,
        message: str,
        level: str,
        title: str,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize Widget'''
        if parent is None:
            parent = widgets.maya_window_to_qt()

        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label_color: str = self.label_color.get(level, self.label_color['INFO'])
        text_color: str = self.text_color.get(level, self.text_color['INFO'])

        self.label: QLabel = QLabel(f'{title} : {level}\n{message}')
        self.label.setFixedWidth(300)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            self.label_style.format(
                label_color=label_color, text_color=text_color
            )
        )
        layout.addWidget(self.label)
        self.adjustSize()

        geom: QRect = parent.geometry()
        x: int = geom.x() + geom.width() - self.width() - 5
        y: int = geom.y() + 5
        self.move(x, y)
        self.setWindowOpacity(0.0)

        self.__fade_in_anim: QPropertyAnimation = QPropertyAnimation(
            self, QByteArray(b'windowOpacity')
        )
        self.__fade_in_anim.setDuration(300)
        self.__fade_in_anim.setStartValue(0.0)
        self.__fade_in_anim.setEndValue(self.opacity)
        self.__fade_in_anim.start()

        self.__fade_out_anim: QPropertyAnimation = QPropertyAnimation(
            self, QByteArray(b'windowOpacity')
        )
        self.__fade_out_anim.setDuration(400)
        self.__fade_out_anim.setStartValue(self.opacity)
        self.__fade_out_anim.setEndValue(0.0)
        self.__fade_out_anim.finished.connect(self.close)

        self.__anim_move = QPropertyAnimation(self, QByteArray(b'pos'))
        self.__anim_move.setDuration(300)

        QTimer.singleShot(self.display_time, self.__fade_out_anim.start)

    def offset(self) -> None:
        '''Offset Toast Widget'''
        offset: int = self.height() + self.spacing
        current_pos: QPoint = self.pos()
        target_pos: QPoint = QPoint(current_pos.x(), current_pos.y() + offset)

        self.__anim_move.setStartValue(current_pos)
        self.__anim_move.setEndValue(target_pos)
        self.__anim_move.setEasingCurve(QEasingCurve.OutExpo)
        self.__anim_move.start()


class ToastSignalEmitter(QObject):
    '''Toast Signal Emitter'''

    log_recieved: Signal = Signal(str, str, str)


class ToastLogHandler(logging.Handler):
    '''Toast Log Handler'''

    def __init__(self) -> None:
        '''Initialize'''
        super().__init__()
        self.__emitter: ToastSignalEmitter = ToastSignalEmitter()
        self.__emitter.log_recieved.connect(self.show_toast)
        self.__toasts: list[ToastWidget] = []

    def emit(self, record: logging.LogRecord) -> None:
        '''Emit signal (override)'''
        msg: str = self.format(record)
        self.__emitter.log_recieved.emit(
            record.levelname,
            record.name,
            msg,
        )

    def show_toast(self, level: str, title: str, msg: str) -> None:
        '''Show toast widget'''
        toast: ToastWidget = ToastWidget(msg, level, title)
        toast.destroyed.connect(
            lambda *args, t=toast: (
                self.__toasts.remove(t) if t in self.__toasts else None
            )
        )
        toast.show()

        for t in self.__toasts:
            t.offset()

        self.__toasts.append(toast)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    '''Returns toast logger'''
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(level)

    has_toast: bool = any(
        type(h).__name__ == ToastLogHandler.__name__ for h in logger.handlers
    )
    if not has_toast:
        toast_handler: ToastLogHandler = ToastLogHandler()
        logger.addHandler(toast_handler)

    return logger
