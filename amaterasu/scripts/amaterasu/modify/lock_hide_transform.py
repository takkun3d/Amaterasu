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
"""Locks and hides transform attributes for selected nodes.

This tool safely locks and hides (or unlocks and shows) the translate,
rotate, scale, and visibility attributes of the currently selected
transform nodes in the Maya scene. It utilizes the centralized
`dcc.attribute` API to comprehensively manage lock, keyable, and
channel box visibility states.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Lock & Hide Transform"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main(is_lock: bool = True) -> None:
    """Locks and hides, or unlocks and shows transform attributes of selected nodes.

    Args:
        is_lock (bool, optional): True to lock/hide, False to unlock/show.
            Defaults to True.
    """
    selection: list[str] = cmds.ls(selection=True, type="transform")
    if not selection:
        if is_lock:
            _logger.error("Select node(s) to lock and hide attributes.")

        else:
            _logger.error("Select node(s) to unlock and show attributes.")
        return

    if is_lock:
        dcc.attribute.lock_and_hide(
            selection, translate=True, rotate=True, scale=True, visibility=True
        )

    else:
        dcc.attribute.unlock_and_show(
            selection, translate=True, rotate=True, scale=True, visibility=True
        )

    _logger.info("Done.")
