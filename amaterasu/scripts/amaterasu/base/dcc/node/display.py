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
"""Provides utilities for managing Maya viewport display states.

This module contains functions to toggle viewport-specific display
attributes, such as local axes and X-ray mode, for Maya nodes.
It handles attribute modifications and safely catches runtime errors.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def set_display_local_axis(
    state: bool,
    nodes: list[str] | None = None,
) -> utils.Result:
    """Sets the display state of the local axis for the specified nodes.

    Args:
        state (bool): True to show the local axis, False to hide it.
        nodes (list[str] | None, optional): A list of Maya node names to
            process. Defaults to None, which uses the current selection.

    Returns:
        utils.Result: An object containing the success or failure states
            of the operation.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        result.set_error("Select nodes to set Display Local Axis.")
        return result

    for node in nodes:
        try:
            cmds.setAttr(f"{node}.displayLocalAxis", state)

        except RuntimeError as e:
            reason: str = str(e).split(":", maxsplit=1)[-1].strip()
            result.add_failure(node, reason)

    return result


def set_xray(
    state: bool,
    nodes: list[str] | None = None,
) -> utils.Result:
    """Sets the X-ray display mode for the specified geometry nodes.

    Args:
        state (bool): True to enable X-ray mode, False to disable it.
        nodes (list[str] | None, optional): A list of Maya node names to
            process. Defaults to None, which uses the current selection.

    Returns:
        utils.Result: An object containing the success or failure states
            of the operation.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        result.set_error("Select nodes to set Xray Geometry.")
        return result

    for node in nodes:
        try:
            cmds.displaySurface(node, xRay=state)

        except RuntimeError as e:
            reason: str = str(e).split(":", maxsplit=1)[-1].strip()
            result.add_failure(node, reason)

    return result
