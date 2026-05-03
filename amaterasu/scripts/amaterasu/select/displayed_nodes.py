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
"""Selects nodes that are displayed within the active camera view."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Select Displayed Nodes"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Executes the select displayed nodes operation."""
    nodes: list[str] = dcc.viewport.displayed_nodes()
    if not nodes:
        cmds.select(clear=True)
        _logger.error("No nodes were visible to select.")
        return

    cmds.select(*nodes, replace=True)
    _logger.info("Done.")
