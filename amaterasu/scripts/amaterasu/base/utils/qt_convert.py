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
"""Qt data conversion utilities for Amaterasu.

This module provides helper functions to serialize and deserialize Qt
data structures, such as QByteArray, into ASCII strings for safe storage
in configuration files.
"""
from __future__ import annotations
from amaterasu.base.qt import QtCore


def qt_to_ascii(byte: QtCore.QByteArray) -> str:
    """Convert a QByteArray to an ASCII hex string.

    This is useful for serializing Qt window geometry or state so it can
    be safely saved in JSON or other text-based configuration files.

    Args:
        byte (QtCore.QByteArray): The Qt byte array to convert.

    Returns:
        str: The hex-encoded ASCII string representation of the byte array.
    """
    return bytes(byte.toHex()).decode('ascii')  # type: ignore


def ascii_to_qt(data: str) -> QtCore.QByteArray:
    """Convert an ASCII hex string back to a QByteArray.

    This is useful for deserializing Qt window geometry or state that was
    previously saved as a text string.

    Args:
        data (str): The hex-encoded ASCII string to convert.

    Returns:
        QtCore.QByteArray: The restored Qt byte array.
    """
    return QtCore.QByteArray.fromHex(bytes(data, 'ascii'))
