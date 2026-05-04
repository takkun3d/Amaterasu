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
"""Selects crease edges from selected nodes or components."""

from __future__ import annotations
from maya import cmds, mel
from amaterasu.base import dcc, utils

__product__: str = "Select Crease Edges"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Executes the select crease edges operation."""
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select nodes or components to find crease edges.")
        return

    result: list[str] = []
    for node in selection:
        edges: list[str] = dcc.mesh.to_edge(node)
        if not edges:
            continue

        crease_edges: list[str] = dcc.mesh.get_crease_edges(edges)
        if crease_edges:
            result.extend(crease_edges)

    if not result:
        _logger.info("There were no crease edges in this selection.")
        return

    mel.eval("SelectEdgeMask")
    cmds.select(*result, replace=True)
    _logger.info("Done.")
