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
"""Provides utilities to manage the history visibility of Maya nodes.

This module contains functions to toggle the `isHistoricallyInteresting`
attribute for the history nodes of given Maya objects, which is useful
for keeping the Channel Box and other editors clean.
"""

from __future__ import annotations
from maya import cmds


def __show_and_hide(nodes: list[str], visibility: bool) -> None:
    """Toggles the historical interest attribute of the given nodes' history.

    This is an internal helper function that iterates through the history
    of the specified nodes and updates their visibility state.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        visibility (bool): True to make the history interesting (visible),
            False to make it uninteresting (hidden).
    """
    for node in nodes:
        histories: list[str] = cmds.listHistory(node, leaf=False) or []  # type: ignore
        for history in histories:
            cmds.setAttr(f'{history}.isHistoricallyInteresting', visibility)


def show_history(nodes: list[str]) -> None:
    """Makes the history of the specified nodes visible in Maya editors.

    Sets the `isHistoricallyInteresting` attribute to True (1) for all
    history nodes associated with the given target nodes.

    Args:
        nodes (list[str]): A list of Maya node names whose history should
            be shown.
    """
    __show_and_hide(nodes, True)


def hide_history(nodes: list[str]) -> None:
    """Hides the history of the specified nodes from Maya editors.

    Sets the `isHistoricallyInteresting` attribute to False (0) for all
    history nodes associated with the given target nodes. This is highly
    recommended for rig controls or guide objects to prevent users from
    accidentally modifying construction history in the Channel Box.

    Args:
        nodes (list[str]): A list of Maya node names whose history should
            be hidden.
    """
    __show_and_hide(nodes, False)


def delete_history(nodes: list[str]) -> None:
    """Deletes construction history for the given nodes."""
    for node in nodes:
        cmds.delete(node, constructionHistory=True)


def remove_intermediate_objects(nodes: list[str]) -> None:
    """Removes intermediate objects from the given nodes."""
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        for shape in shapes:
            if cmds.getAttr(f"{shape}.io"):
                cmds.delete(shape)
