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
"""Path and environment utilities for Amaterasu.

This module provides utility functions to resolve file paths and load
resources from various environments, including the host DCC application.
"""

import os
from amaterasu.base.qt import QtGui


def get_icon_path(file_name: str) -> str:
    """Find and return the full path or resource string for an icon file.

    This function searches for the given icon file name in the following order:
    1. Current working directory or straightforward path.
    2. Qt internal resource path (:/file_name).
    3. Directories specified in the 'XBMLANGPATH' environment variable.

    Args:
        file_name (str): The name of the icon file (e.g., "a_trash.png").

    Returns:
        str: The resolved full path to the icon file, or the Qt resource string.

    Raises:
        ValueError: If the icon file cannot be found in any of the search paths.
    """
    icon: QtGui.QIcon = QtGui.QIcon(file_name)
    if len(icon.availableSizes()) > 0:
        return file_name

    icon = QtGui.QIcon(':/' + file_name)
    if len(icon.availableSizes()) > 0:
        return file_name

    icon_path: str | None = os.getenv('XBMLANGPATH')
    if not icon_path:
        raise ValueError(f'Not found file: {file_name}')

    for path in icon_path.split(';'):
        fullpath: str = os.path.join(path, file_name)
        if os.path.isfile(fullpath):
            fullpath = fullpath.replace("\\", "/")
            return fullpath

    raise ValueError(f'Not found file: {file_name}')
