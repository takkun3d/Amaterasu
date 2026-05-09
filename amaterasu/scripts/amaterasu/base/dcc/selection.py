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
from itertools import product
from maya import cmds, mel
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


def get_selected_channel_box_plugs() -> list[str]:
    """Gets a list of selected plugs (node.attribute) from the Channel Box.

    Returns:
        list[str]: A list of combined plug strings
            (e.g., ['pCube1.tx', 'pCube1.ty']).
    """
    cb_name: str = mel.eval("$gChannelBoxName=$gChannelBoxName;")
    if not cb_name:
        return []

    def _get_plugs(
        nodes: list[str] | None,
        attrs: list[str] | None,
    ) -> list[str]:
        """Creates a list of full plug names from nodes and attributes.

        Args:
            nodes (list[str] | None): A list of node names.
            attrs (list[str] | None): A list of attribute names.

        Returns:
            list[str]: A list of combined plug strings (e.g., ['node.attr']).
        """
        return [f"{n}.{a}" for n, a in product(nodes or [], attrs or [])]

    plugs: list[str] = []
    plugs.extend(
        _get_plugs(
            cmds.channelBox(cb_name, query=True, mainObjectList=True),  # type: ignore
            cmds.channelBox(cb_name, query=True, selectedMainAttributes=True),  # type: ignore
        )
    )

    plugs.extend(
        _get_plugs(
            cmds.channelBox(cb_name, query=True, shapeObjectList=True),  # type: ignore
            cmds.channelBox(cb_name, query=True, selectedShapeAttributes=True),  # type: ignore
        )
    )

    plugs.extend(
        _get_plugs(
            cmds.channelBox(cb_name, query=True, historyObjectList=True),  # type: ignore
            cmds.channelBox(
                cb_name, query=True, selectedHistoryAttributes=True
            ),  # type: ignore
        )
    )

    plugs.extend(
        _get_plugs(
            cmds.channelBox(cb_name, query=True, outputObjectList=True),  # type: ignore
            cmds.channelBox(
                cb_name, query=True, selectedOutputAttributes=True
            ),  # type: ignore
        )
    )

    return plugs
