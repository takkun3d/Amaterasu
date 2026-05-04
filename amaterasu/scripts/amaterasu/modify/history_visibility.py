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
"""Toggles the visibility of history in the Channel Box.

This tool modifies the `isHistoricallyInteresting` attribute of the
history nodes for the selected objects and forces a selection update
to refresh the Channel Box display.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "History Visibility"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main(is_show: bool = True) -> None:
    """Shows or hides the history in the Channel Box for selected nodes.

    Args:
        is_show (bool, optional): True to show history, False to hide.
            Defaults to True.
    """
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        if is_show:
            _logger.error("Select node(s) to show the history in Channel Box.")

        else:
            _logger.error("Select node(s) to hide the history in Channel Box.")
        return

    shapes: list[str] = cmds.listRelatives(*selection, shapes=True) or []
    target_nodes: list[str] = list(set(selection + shapes))
    if is_show:
        dcc.node.show_history(target_nodes)

    else:
        dcc.node.hide_history(target_nodes)

    cmds.select(*selection, replace=True)
    _logger.info("Done.")
