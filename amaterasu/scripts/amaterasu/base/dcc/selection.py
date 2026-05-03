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
"""Provides utilities for managing Maya node selections and filtering."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils

ANIMATION_CURVES: list[str] = [
    "animCurveTA",
    "animCurveTL",
    "animCurveTT",
    "animCurveTU",
]


def filter_animated(nodes: list[str] | None = None) -> utils.Result:
    """Selects nodes that are driven by animation curves.

    If a list of nodes is provided, it filters the list to only include
    animated nodes. Otherwise, it selects all animated nodes in the scene.

    Args:
        nodes (list[str] | None, optional): A list of nodes to filter.
            Defaults to None.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    anim_curves: list[str] = cmds.ls(type=ANIMATION_CURVES)

    animated_set: set[str] = set()
    for curve in anim_curves:
        connections: list[str] = cmds.listConnections(curve) or []
        animated_set.update(connections)

    final_nodes: list[str]
    if nodes:
        final_nodes = list(set(nodes) & animated_set)

    else:
        final_nodes = list(animated_set)

    if not final_nodes:
        result.set_error("No animated nodes found.")
        return result

    cmds.select(*final_nodes, replace=True)
    return result
