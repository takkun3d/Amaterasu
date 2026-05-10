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
"""Selects hard edge shells."""

from __future__ import annotations
from maya import cmds, mel
from amaterasu.base import dcc, utils

__product__: str = "Select Hard Edges Shell"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Executes the select hard edges shell operation."""
    selection: list[str] = cmds.ls(selection=True) or []
    if not selection:
        _logger.error("Select nodes or components to find hard edge shells.")
        return

    faces: list[str] = dcc.mesh.to_face(selection)
    if not faces:
        _logger.error(
            "Select polygon vertices, edges, or faces to find hard edge shells."
        )
        return

    shell_faces: list[str] = dcc.mesh.get_hard_edge_shells(faces)
    if not shell_faces:
        _logger.info("There were no hard edge shells in this selection.")
        return

    mel.eval("SelectFacetMask")
    cmds.select(*shell_faces, replace=True)
    _logger.info("Done.")
