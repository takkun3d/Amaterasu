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
"""Provides utilities for managing Maya projects and workspaces."""

from __future__ import annotations
import pathlib
from maya import mel, cmds
from amaterasu.base import utils


def find_workspace(file_path: str | pathlib.Path) -> str:
    """Finds the Maya project directory containing the workspace.mel file.

    It searches the directory of the given file and traverses upwards
    until a 'workspace.mel' is found.

    Args:
        file_path (str | pathlib.Path): The starting file or directory path.

    Returns:
        str: The path to the project directory, or an empty string if not found.
    """
    path: pathlib.Path = pathlib.Path(file_path)
    if path.is_file():
        path = path.parent

    # Check current dir and all parent directories iteratively
    for parent in [path, *path.parents]:
        if (parent / "workspace.mel").is_file():
            return str(parent)

    return ""


def get_workspace() -> str:
    """Gets the current Maya project root directory.

    Returns:
        str: The root directory path of the current project.
    """
    return cmds.workspace(query=True, rootDirectory=True)  # type: ignore


def set_project(project_path: str) -> utils.Result:
    """Sets the current Maya project to the specified path.

    Args:
        project_path (str): The path to the project directory.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    if not project_path:
        result.set_error("Project path is empty.")
        return result

    try:
        escaped_path: str = project_path.replace("\\", "\\\\")
        mel.eval(f'setProject "{escaped_path}"')

    except RuntimeError as e:
        result.set_error(str(e))

    return result
