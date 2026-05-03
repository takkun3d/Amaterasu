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
"""The project is automatically set when scene is opened in Maya.

This tool ensures that Maya's current project workspace is updated
to match the location of the scene file being opened, preventing
missing texture links and relative path issues.
"""

from __future__ import annotations
from amaterasu.base import dcc, utils

__product__: str = "Auto Set Project"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main(file_path: str = "", force: bool = False) -> None:
    """Executes the Auto Set Project routine.

    Args:
        file_path (str, optional): The explicit path of the scene to open.
            Defaults to "".
        force (bool, optional): If True, bypasses save prompts and dialogs.
            Requires `file_path` to be provided. Defaults to False.
    """
    if not force:
        if not dcc.scene.prompt_save_changes():
            return

        file_path = dcc.scene.prompt_select_file()
        if not file_path:
            return

    else:
        if not file_path:
            _logger.error("A file path must be provided when force is True.")
            return

    project_path: str = dcc.project.find_workspace(file_path)
    if not project_path:
        _logger.error(
            "The file defining the project (workspace.mel) does not exist."
        )
        return

    dcc.project.set_project(project_path)
    result: utils.Result = dcc.scene.open_file(file_path)
    result.log(_logger, success_msg=f"Done : {project_path}")
