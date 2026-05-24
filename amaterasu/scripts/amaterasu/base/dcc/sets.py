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
"""Operations for managing and manipulating selection sets in Autodesk Maya.

This module provides core functions to create, delete, select, and modify
members of Maya selection sets, as well as managing a custom favorite state.
"""

from __future__ import annotations
from typing import Any
import enum
from maya import cmds
from amaterasu.base import utils

FAVORITE_ATTR_NAME: str = "amaterasu_sets_favorite"


class SelectionMode(enum.IntEnum):
    """Enumeration for Maya selection modes.

    Attributes:
        REPLACE (int): Replaces the current selection.
        ADD (int): Adds to the current selection.
        TOGGLE (int): Toggles the selection state of the items.
        DESELECT (int): Removes items from the current selection.
    """

    REPLACE = 0
    ADD = 1
    TOGGLE = 2
    DESELECT = 3


def select(sets_name: str, mode: SelectionMode = SelectionMode.REPLACE) -> None:
    """Selects the members of the specified selection set based on mode.

    Args:
        sets_name (str): The name of the selection set.
        mode (SelectionMode, optional): The selection mode.
            Defaults to SelectionMode.REPLACE.
    """
    kwargs: dict[str, Any] = {}
    if mode == SelectionMode.TOGGLE:
        kwargs["tgl"] = True

    elif mode == SelectionMode.DESELECT:
        kwargs["d"] = True

    elif mode == SelectionMode.ADD:
        kwargs["add"] = True

    cmds.select(sets_name, **kwargs)


def create(sets_name: str) -> str:
    """Creates a new selection set with the currently selected objects.

    Args:
        sets_name (str): The desired name for the new selection set.

    Returns:
        str: The actual name of the created selection set in Maya.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        return cmds.sets(name=sets_name)  # type: ignore

    return cmds.sets(*selection, name=sets_name)  # type: ignore


def add_member(
    sets_name: str,
    nodes: list[str] | None = None,
) -> utils.Result:
    """Adds specified or currently selected objects to the specified selection set.

    Args:
        sets_name (str): The target selection set name.
        nodes (list[str] | None, optional): Specific nodes to add. If None,
            the current selection is used. Defaults to None.

    Returns:
        utils.Result: An object containing the success status and error logs.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if nodes:
        cmds.sets(*nodes, edit=True, addElement=sets_name)

    return result


def remove_member(
    sets_name: str,
    nodes: list[str] | None = None,
) -> utils.Result:
    """Removes specified or currently selected objects from the specified selection set.

    Args:
        sets_name (str): The target selection set name.
        nodes (list[str] | None, optional): Specific nodes to remove. If None,
            the current selection is used. Defaults to None.

    Returns:
        utils.Result: An object containing the success status and error logs.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if nodes:
        cmds.sets(*nodes, edit=True, remove=sets_name)

    return result


def show_member(sets_name: str) -> utils.Result:
    """Shows all members belonging to the specified selection set.

    Args:
        sets_name (str): The target selection set name.

    Returns:
        utils.Result: An object containing the success status and error logs.
    """
    result: utils.Result = utils.Result()
    cmds.showHidden(sets_name)
    return result


def hide_member(sets_name: str) -> utils.Result:
    """Hides all members belonging to the specified selection set.

    Args:
        sets_name (str): The target selection set name.

    Returns:
        utils.Result: An object containing the success status and error logs.
    """
    result: utils.Result = utils.Result()
    cmds.hide(sets_name)
    return result


def delete(sets_name: str) -> utils.Result:
    """Deletes the specified selection set node from the Maya scene.

    Args:
        sets_name (str): The selection set name to delete.

    Returns:
        utils.Result: An object containing the success status and error logs.
    """
    result: utils.Result = utils.Result()
    try:
        cmds.delete(sets_name)

    except RuntimeError:
        result.add_failure(sets_name, "Can not delete.")

    return result


def get_favorite_state(sets_name: str) -> bool:
    """Retrieves the custom favorite attribute state of the selection set.

    If the attribute does not exist, it will be automatically created.

    Args:
        sets_name (str): The selection set name to query.

    Returns:
        bool: True if the set is marked as favorite, False otherwise.
    """
    if not cmds.attributeQuery(FAVORITE_ATTR_NAME, node=sets_name, exists=True):
        cmds.addAttr(
            sets_name, longName=FAVORITE_ATTR_NAME, attributeType="bool"
        )

    return bool(cmds.getAttr(f"{sets_name}.{FAVORITE_ATTR_NAME}"))


def set_favorite_state(sets_name: str, value: bool) -> None:
    """Saves the favorite state to the selection set's custom attribute.

    If the attribute does not exist, it will be automatically created.

    Args:
        sets_name (str): The selection set name to update.
        value (bool): The favorite state value to apply.
    """
    if not cmds.attributeQuery(FAVORITE_ATTR_NAME, node=sets_name, exists=True):
        cmds.addAttr(
            sets_name, longName=FAVORITE_ATTR_NAME, attributeType="bool"
        )

    cmds.setAttr(f"{sets_name}.{FAVORITE_ATTR_NAME}", value)
