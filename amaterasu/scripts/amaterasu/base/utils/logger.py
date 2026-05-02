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
"""Toast logger utility for Amaterasu tools.

This module provides a custom logging system that displays non-intrusive,
auto-fading toast notifications directly within the Maya viewport.
It allows developers to easily dispatch log messages that are immediately
visible to the user without requiring the Script Editor.
"""
from __future__ import annotations
import logging
from logging import Logger
from amaterasu.base import widgets
from amaterasu.base.utils.singleton import Singleton


class ToastLogHandler(Singleton, logging.Handler):
    """A custom logging handler that routes log records to ToastWidgets.

    It acts as a singleton to ensure all messages are queued and displayed
    properly without spawning duplicate handlers.
    """

    def __init__(self) -> None:
        """Initialize the ToastLogHandler and its internal signal emitter."""
        super().__init__()
        self.__emitter: widgets.ToastSignalEmitter = (
            widgets.ToastSignalEmitter()
        )
        self.__emitter.log_received.connect(self.show_toast)
        self.__toasts: list[widgets.ToastWidget] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record and emit a signal to display the toast.

        Args:
            record (logging.LogRecord): The log record to process.
        """
        message: str = self.format(record)
        self.__emitter.log_received.emit(
            record.name,
            record.levelname,
            message,
        )

    def show_toast(self, title: str, level: str, message: str) -> None:
        """Create and display a new ToastWidget.

        Args:
            title (str): The logger name.
            level (str): The severity level of the log.
            message (str): The formatted log message.
        """
        toast: widgets.ToastWidget = widgets.ToastWidget(title, level, message)
        toast.destroyed.connect(
            lambda *args, t=toast: (
                self.__toasts.remove(t) if t in self.__toasts else None
            )
        )
        toast.show()

        for t in self.__toasts:
            t.offset(toast.height())

        self.__toasts.append(toast)


def get_logger(name: str, level: int = logging.INFO) -> Logger:
    """Get a Python logger configured with the ToastLogHandler.

    Args:
        name (str): The name of the logger (typically __name__ of the caller).
        level (int, optional): The minimum logging level.
            Defaults to logging.INFO.

    Returns:
        Logger: The configured logging instance.
    """
    logger: Logger = logging.getLogger(name)
    logger.setLevel(level)

    has_toast: bool = any(
        type(h).__name__ == ToastLogHandler.__name__ for h in logger.handlers
    )
    if not has_toast:
        toast_handler: ToastLogHandler = ToastLogHandler()
        logger.addHandler(toast_handler)

    return logger
