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
from logging import Logger  # for type hint

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

from . import widgets, parser


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
    label_text: str = '''
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
        '''
    display_time: int = 3000
    opacity: float = 0.9
    spacing: int = 3

    def __init__(
        self,
        title: str,
        level: str,
        message: str,
        parent: QWidget | None = None,
    ) -> None:
        '''Initialize Widget'''
        if parent is None:
            parent = widgets.maya_window_to_qt()

        super().__init__(parent)

        label_color: str = self.label_color.get(level, self.label_color['INFO'])
        text_color: str = self.text_color.get(level, self.text_color['INFO'])

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

        self.__label: QLabel = QLabel(self)
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

        self.__target_y: int | None = None
        self.__anim_move = QPropertyAnimation(self, QByteArray(b'pos'))
        self.__anim_move.setDuration(300)
        self.__anim_move.setEasingCurve(QEasingCurve.OutExpo)

        QTimer.singleShot(self.display_time, self.__fade_out_anim.start)

    def offset(self, shift_amount: int) -> None:
        '''Offset Toast Widget'''
        if self.__target_y is None:
            self.__target_y = self.y()

        self.__target_y += shift_amount + self.spacing
        if self.__anim_move.state() == QPropertyAnimation.Running:
            self.__anim_move.stop()

        self.__anim_move.setStartValue(self.pos())
        self.__anim_move.setEndValue(QPoint(self.x(), self.__target_y))
        self.__anim_move.start()


class ToastSignalEmitter(QObject):
    '''Toast Signal Emitter'''

    log_recieved: Signal = Signal(str, str, str)


class ToastLogHandler(parser.Singleton, logging.Handler):
    '''Toast Log Handler'''

    def __init__(self) -> None:
        '''Initialize'''
        super().__init__()
        self.__emitter: ToastSignalEmitter = ToastSignalEmitter()
        self.__emitter.log_recieved.connect(self.show_toast)
        self.__toasts: list[ToastWidget] = []

    def emit(self, record: logging.LogRecord) -> None:
        '''Emit signal (override)'''
        message: str = self.format(record)
        self.__emitter.log_recieved.emit(
            record.name,
            record.levelname,
            message,
        )

    def show_toast(self, title: str, level: str, message: str) -> None:
        '''Show toast widget'''
        toast: ToastWidget = ToastWidget(title, level, message)
        toast.destroyed.connect(
            lambda *args, t=toast: (
                self.__toasts.remove(t) if t in self.__toasts else None
            )
        )
        toast.show()

        for t in self.__toasts:
            t.offset(toast.height())

        self.__toasts.append(toast)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def get_logger(name: str, level: int = logging.INFO) -> Logger:
    '''Returns toast logger'''
    logger: Logger = logging.getLogger(name)
    logger.setLevel(level)

    has_toast: bool = any(
        type(h).__name__ == ToastLogHandler.__name__ for h in logger.handlers
    )
    if not has_toast:
        toast_handler: ToastLogHandler = ToastLogHandler()
        logger.addHandler(toast_handler)

    return logger
