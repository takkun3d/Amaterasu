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
"""Base utility module for Amaterasu.

This module provides general-purpose helper functions and utilities used
across the Amaterasu application. It serves as a central hub for accessing
data conversion, serialization, and other core utility operations.
"""

from amaterasu.base.utils.qt_convert import qt_to_ascii, ascii_to_qt
from amaterasu.base.utils.logger import Logger, get_logger
from amaterasu.base.utils.singleton import SingletonMeta, Singleton
from amaterasu.base.utils.multiton import MultitonMeta, Multiton

__all__: list[str] = [
    "qt_to_ascii",
    "ascii_to_qt",
    "Logger",
    "get_logger",
    "SingletonMeta",
    "Singleton",
    "MultitonMeta",
    "Multiton",
]
