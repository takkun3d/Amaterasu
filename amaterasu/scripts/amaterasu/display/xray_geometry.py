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
"""Enables or disables X-ray mode for selected geometry.

This module provides headless commands to control the X-ray display state
in the Maya viewport, designed to be executed directly from menus or
custom shelves.
"""

from __future__ import annotations
from amaterasu.base import dcc, utils

__product__: str = "Xray Geometry"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


def enable() -> None:
    """Enables X-ray mode for the currently selected nodes."""
    result: utils.Result = dcc.node.set_xray(True)
    result.log(_logger)


def disable() -> None:
    """Disables X-ray mode for the currently selected nodes."""
    result: utils.Result = dcc.node.set_xray(False)
    result.log(_logger)
