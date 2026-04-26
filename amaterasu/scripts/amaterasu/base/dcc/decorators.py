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
"""Decorators for DCC application commands.

This module provides useful decorators for Maya, such as grouping
multiple commands into a single undo chunk.
"""
from __future__ import annotations
from typing import Any, Callable
import functools
from maya import cmds


def undo(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to group Maya commands into a single undo chunk.

    This ensures that all operations performed within the decorated
    function can be undone with a single 'Ctrl+Z' operation in Maya.

    Args:
        func (Callable): The function to wrap.

    Returns:
        Callable: The wrapped function executing within an undo chunk.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)

        finally:
            cmds.undoInfo(closeChunk=True)

    return wrapper
