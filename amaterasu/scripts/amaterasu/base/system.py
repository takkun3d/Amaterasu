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
"""Provides operating system level utilities."""

from __future__ import annotations
import os
import sys
import subprocess
import pathlib
from amaterasu.base import utils


def open_directory(path_str: str) -> utils.Result:
    """Opens a directory in the default OS file explorer.

    Args:
        path_str (str): The path to the directory to open.

    Returns:
        utils.Result: The result of the operation. Failure reasons are
            recorded if the path doesn't exist or the OS is unsupported.
    """
    result: utils.Result = utils.Result()
    path: pathlib.Path = pathlib.Path(path_str)

    if not path.exists():
        result.set_error(f"Does not exist path : {path_str}")
        return result

    try:
        if sys.platform == "win32":
            os.startfile(path)

        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])

        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", str(path)])

        else:
            result.set_error(f"Not supported OS : {sys.platform}")

    except OSError as e:
        result.set_error(f"Failed to open directory (OS Error): {e}")

    except subprocess.SubprocessError as e:
        result.set_error(f"Failed to execute command (Subprocess Error): {e}")

    return result
