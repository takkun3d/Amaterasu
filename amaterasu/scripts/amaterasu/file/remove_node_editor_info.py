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
"""Removes Node Editor Info nodes from the open scene.

This tool finds and deletes all 'nodeGraphEditorInfo' nodes, which
often accumulate in scenes, bloat file sizes, and cause unnecessary
warnings.
"""

from __future__ import annotations
from amaterasu.base import dcc, utils

__product__: str = "Remove Node Editor Info"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Executes the removal of nodeGraphEditorInfo nodes.

    Delegates the safe disconnection and deletion of these nodes to
    the base DCC scene utilities, then logs the resulting status.
    """
    result: utils.Result = dcc.scene.remove_node_editor_info()
    result.log(_logger)
