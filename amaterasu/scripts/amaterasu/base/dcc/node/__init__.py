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
"""General node manipulation and management utilities for Maya.

This sub-package provides a collection of functions to handle general Maya
nodes safely and efficiently. It acts as a centralized facade, aggregating
various node-level operations (such as drawing color overrides, history
visibility, and future additions like hierarchy management or naming
conventions) to keep tool logic clean and decoupled from direct DCC API calls.
"""

from __future__ import annotations
from amaterasu.base.dcc.node.display import set_xray, set_display_local_axis
from amaterasu.base.dcc.node.drawing import (
    set_drawing_index_color,
    set_drawing_rgb_color,
    clear_drawing_color,
)
from amaterasu.base.dcc.node.hide_history import show_history, hide_history
from amaterasu.base.dcc.node.outliner import (
    set_outliner_color,
    clear_outliner_color,
)

__all__: list[str] = [
    "set_xray",
    "set_display_local_axis",
    "set_drawing_index_color",
    "set_drawing_rgb_color",
    "clear_drawing_color",
    "show_history",
    "hide_history",
    "set_outliner_color",
    "clear_outliner_color",
]
