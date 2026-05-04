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
"""Locks or unlocks the selected nodes.

This tool safely changes the lock state of the currently selected
nodes in the Maya scene, preventing or allowing modifications
such as deletion or renaming. It utilizes the centralized
`dcc.node` API for execution.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils

__product__: str = "Lock Node"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main(is_lock: bool = True) -> None:
    """Locks or unlocks the selected nodes.

    Args:
        is_lock (bool, optional): True to lock, False to unlock.
            Defaults to True.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        if is_lock:
            _logger.error("Select node(s) to lock state.")

        else:
            _logger.error("Select node(s) to unlock state.")
        return

    cmds.lockNode(*selection, lock=is_lock)
    _logger.info("Done.")
