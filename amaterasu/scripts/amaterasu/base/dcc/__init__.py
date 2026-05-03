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
"""Base DCC module for Amaterasu.

This module provides common utilities and decorators for integrating
Amaterasu tools with Digital Content Creation (DCC) applications like Maya.
It serves as a central hub for accessing DCC-specific functions, such as
path resolution and undo stack management.
"""

from __future__ import annotations
from amaterasu.base.dcc.paths import get_icon_path
from amaterasu.base.dcc.decorators import undo
from amaterasu.base.dcc.ui import get_maya_window

from amaterasu.base.dcc import project
from amaterasu.base.dcc import scene
from amaterasu.base.dcc import reference
from amaterasu.base.dcc import plugin
from amaterasu.base.dcc import node
from amaterasu.base.dcc import shape
from amaterasu.base.dcc import attribute
from amaterasu.base.dcc import selection
from amaterasu.base.dcc import viewport

__all__: list[str] = [
    "get_icon_path",
    "undo",
    "get_maya_window",
    #
    "project",
    "scene",
    "reference",
    "plugin",
    "node",
    "shape",
    "attribute",
    "selection",
    "viewport",
]
