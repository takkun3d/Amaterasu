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
"""Base framework module for Amaterasu.

This module provides the core architectural components for building Amaterasu tools.
It includes base window classes, Maya workspace control integration, and standard
dialogs, ensuring a consistent lifecycle and UI structure across all tools.
"""

from amaterasu.base.framework.workspace_control import WorkspaceControlWindow
from amaterasu.base.framework.tool_window import ToolWindow
from amaterasu.base.framework.standard_tool_window import StandardToolWindow
from amaterasu.base.framework.about_dialog import AboutDialog
from amaterasu.base.framework.settings import ToolSettings, Variant

__all__: list[str] = [
    "WorkspaceControlWindow",
    "ToolWindow",
    "StandardToolWindow",
    "AboutDialog",
    "ToolSettings",
    "Variant",
]
