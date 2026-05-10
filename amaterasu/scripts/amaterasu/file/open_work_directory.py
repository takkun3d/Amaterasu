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
"""Opens the current project directory in the OS file explorer.

This tool retrieves the root directory of the currently active Maya
project and opens it using the default system file manager (e.g.,
Windows Explorer, macOS Finder).
"""

from __future__ import annotations
from amaterasu.base import dcc, system, utils

__product__: str = "Open Work Directory"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Opens the project in Explorer."""
    project_path: str = dcc.project.get_workspace()
    if not project_path:
        _logger.error("Project path is not set.")
        return

    result: utils.Result = system.open_directory(project_path)
    if result.status() != utils.ResultStatus.SUCCESS:
        result.log(_logger)
