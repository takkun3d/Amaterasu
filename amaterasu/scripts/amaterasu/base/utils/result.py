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
"""Provides a structured result object for batch operations.

This module defines the `Result` class and `ResultStatus` enum, which are used
to track, merge, and log the outcomes of operations performed on multiple items.
It allows tools to gracefully handle partial failures and generate appropriate
log messages or UI feedback.
"""

from __future__ import annotations
from typing import Generic, TypeVar, cast
import enum
from amaterasu.base.utils import logger

T = TypeVar("T")


class ResultStatus(enum.Enum):
    """Enumeration of possible result statuses.

    Attributes:
        SUCCESS: Operation completed without any errors or failures.
        WARNING: Operation completed but some items failed.
        ERROR: Operation failed completely due to a global error.
    """

    SUCCESS = 0
    WARNING = 1
    ERROR = 2


class Result:
    """Stores and relays the results of batch operations.

    This class manages global errors and individual item failures, providing
    methods to merge results, determine the overall status, and output formatted
    log messages.
    """

    def __init__(self) -> None:
        """Initializes an empty Result object."""
        self.__infos: dict[str, str] = {}
        self.__failures: dict[str, str] = {}
        self.__error: str = ""

    def add_info(self, item: str, reason: str) -> None:
        """Records an informational message for a specific item.

        Args:
            item (str): The name or identifier of the item.
            reason (str): The informational message to record.
        """
        self.__infos[item] = reason

    def infos(self) -> dict[str, str]:
        """Gets the dictionary of items and their informational messages.

        Returns:
            dict[str, str]: A dictionary mapping item names to info messages.
        """
        return self.__infos

    def set_error(self, message: str) -> None:
        """Sets a global error message.

        Setting a global error indicates a critical failure that prevents
        the operation from proceeding, resulting in an ERROR status.

        Args:
            message (str): The error message.
        """
        self.__error = message

    def add_failure(self, item: str, reason: str) -> None:
        """Records a failure for a specific item.

        Args:
            item (str): The name or identifier of the failed item.
            reason (str): The reason for the failure.
        """
        self.__failures[item] = reason

    def failures(self) -> dict[str, str]:
        """Gets the dictionary of failed items and their reasons.

        Returns:
            dict[str, str]: A dictionary mapping item names to error messages.
        """
        return self.__failures

    def error(self) -> str:
        """Gets the global error message.

        Returns:
            str: The global error message, or an empty string if none is set.
        """
        return self.__error

    def merge(self, other: Result) -> None:
        """Merges another Result object into this one.
        This method absorbs the infos, failures, and global error of the other result.

        Args:
            other (Result): Another Result object to merge.
        """
        self.__infos.update(other.infos())
        self.__failures.update(other.failures())
        if other.error():
            self.set_error(other.error())

    def status(self) -> ResultStatus:
        """Determines the overall status of the result.

        Returns:
            ResultStatus: ERROR if a global error is set, WARNING if there are
                individual item failures, and SUCCESS otherwise.
        """
        if self.__error:
            return ResultStatus.ERROR

        if self.__failures:
            return ResultStatus.WARNING

        return ResultStatus.SUCCESS

    def message(self, success_msg: str = "Done.") -> str:
        """Generates a formatted message based on the current status.

        Args:
            success_msg (str, optional): The message to return if the status
                is SUCCESS. Defaults to "Done.".

        Returns:
            str: The generated message containing success, error,
                or warning details.
        """
        current_status: ResultStatus = self.status()
        lines: list[str] = []

        if current_status == ResultStatus.SUCCESS:
            lines.append(success_msg)
            for item, info in self.__infos.items():
                lines.append(f"- {item}: {info}")

        elif current_status == ResultStatus.ERROR:
            lines.append(self.__error)

        else:
            lines.append("Completed with some errors:")
            for item, error in self.__failures.items():
                lines.append(f"- {item}: {error}")

        return "\n".join(lines)

    def log(self, _logger: logger.Logger, success_msg: str = "Done.") -> None:
        """Outputs the result message to a logger with the appropriate level.

        This method automatically selects `info`, `warning`, or `error` based
        on the current status of the result.

        Args:
            _logger (logger.Logger): The logger instance to use for output.
            success_msg (str, optional): The message to log upon success.
                Defaults to "Done.".
        """
        current_status: ResultStatus = self.status()
        msg: str = self.message(success_msg)

        if current_status == ResultStatus.SUCCESS:
            _logger.info(msg)

        elif current_status == ResultStatus.ERROR:
            _logger.error(msg)

        else:
            _logger.warning(msg)


class DataResult(Result, Generic[T]):
    """Extends Result to support generic types for batch operations.

    This class inherits from the standard Result class but adds strict
    type hinting for the return value payload.
    """

    def __init__(self, value: T) -> None:
        """Initializes a DataResult object with a strictly typed value.

        Args:
            value (T): The initial value to store.
        """
        super().__init__()
        self.__value: T = value

    def value(self) -> T:
        """Gets the stored value.

        Returns:
            T: The stored value.
        """
        return self.__value

    def set_value(self, value: T) -> None:
        """Sets the return value for this result.

        Args:
            value (T): The value to store.
        """
        self.__value = value

    def merge(self, other: DataResult[T]) -> None:  # type: ignore[override]
        """Merges another Result object into this one.

        This method absorbs the infos, failures, and global error of the
        other result. If both results hold collections (list, dict, or set)
        as their values, they are combined. Otherwise, the current value is
        kept unless it is None.

        Args:
            other (DataResult[T]): Another Result object to merge.
        """
        super().merge(other)
        value: T = other.value()
        if value is not None:
            if self.__value is None:
                self.__value = value
            elif isinstance(self.__value, list) and isinstance(value, list):
                self.__value.extend(value)

            elif isinstance(self.__value, dict) and isinstance(value, dict):
                self.__value.update(value)

            elif isinstance(self.__value, set) and isinstance(value, set):
                self.__value.update(value)

            elif isinstance(self.__value, int) and isinstance(value, int):
                self.__value = cast(T, self.__value + value)

            elif isinstance(self.__value, float) and isinstance(value, float):
                self.__value = cast(T, self.__value + value)

            elif isinstance(self.__value, str) and isinstance(value, str):
                self.__value = cast(T, self.__value + value)
