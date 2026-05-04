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
"""Provides utilities for locking and hiding Maya node attributes.

This module contains functions to safely lock and hide, or unlock and show,
specific transform and visibility attributes of Maya nodes.
"""

from __future__ import annotations
from maya import cmds


def __set_lock(
    nodes: list[str],
    state: bool,
    translate: bool,
    rotate: bool,
    scale: bool,
    visibility: bool,
) -> None:
    """Internal helper to set the lock state of attributes.

    Args:
        nodes (list[str]): A list of Maya node names.
        state (bool): True to lock, False to unlock.
        translate (bool): Apply to translate attributes.
        rotate (bool): Apply to rotate attributes.
        scale (bool): Apply to scale attributes.
        visibility (bool): Apply to the visibility attribute.
    """
    for node in nodes:
        for attr, flag in zip(["t", "r", "s"], [translate, rotate, scale]):
            if not flag:
                continue
            for axis in ["x", "y", "z"]:
                cmds.setAttr(f"{node}.{attr}{axis}", lock=state)

        if visibility:
            cmds.setAttr(f"{node}.v", lock=state)


def __set_lock_and_hide(
    nodes: list[str],
    state: bool,
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Internal helper to set the lock and visibility state of attributes.

    This function coordinates the `lock`, `keyable`, and `channelBox` states.
    When `state` is True, attributes are locked and hidden. When False, they
    are unlocked and made visible.

    Args:
        nodes (list[str]): A list of Maya node names.
        state (bool): True to lock and hide, False to unlock and show.
        translate (bool, optional): Apply to translate attributes.
            Defaults to False.
        rotate (bool, optional): Apply to rotate attributes.
            Defaults to False.
        scale (bool, optional): Apply to scale attributes.
            Defaults to False.
        visibility (bool, optional): Apply to the visibility attribute.
            Defaults to False.
    """
    for node in nodes:
        for attr, flag in zip(["t", "r", "s"], [translate, rotate, scale]):
            if not flag:
                continue
            for axis in ["x", "y", "z"]:
                cmds.setAttr(
                    f"{node}.{attr}{axis}",
                    lock=state,
                    keyable=not state,
                    # channelBox=not state,
                )

        if visibility:
            cmds.setAttr(
                f"{node}.v",
                lock=state,
                keyable=not state,
                # channelBox=not state,
            )


def lock(
    nodes: list[str],
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Locks specified attributes for the given Maya nodes without hiding them.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        translate (bool, optional): If True, locks translate attributes.
            Defaults to False.
        rotate (bool, optional): If True, locks rotate attributes.
            Defaults to False.
        scale (bool, optional): If True, locks scale attributes.
            Defaults to False.
        visibility (bool, optional): If True, locks the visibility attribute.
            Defaults to False.
    """
    __set_lock(nodes, True, translate, rotate, scale, visibility)


def unlock(
    nodes: list[str],
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Unlocks specified attributes for the given Maya nodes.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        translate (bool, optional): If True, unlocks translate attributes.
            Defaults to False.
        rotate (bool, optional): If True, unlocks rotate attributes.
            Defaults to False.
        scale (bool, optional): If True, unlocks scale attributes.
            Defaults to False.
        visibility (bool, optional): If True, unlocks the visibility attribute.
            Defaults to False.
    """
    __set_lock(nodes, False, translate, rotate, scale, visibility)


def lock_and_hide(
    nodes: list[str],
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Locks and hides specified attributes for the given Maya nodes.

    Locked attributes are also made non-keyable and hidden from the Channel Box.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        translate (bool, optional): If True, locks and hides translate attributes.
            Defaults to False.
        rotate (bool, optional): If True, locks and hides rotate attributes.
            Defaults to False.
        scale (bool, optional): If True, locks and hides scale attributes.
            Defaults to False.
        visibility (bool, optional): If True, locks and hides the visibility attribute.
            Defaults to False.
    """
    __set_lock_and_hide(nodes, True, translate, rotate, scale, visibility)


def unlock_and_show(
    nodes: list[str],
    translate: bool = False,
    rotate: bool = False,
    scale: bool = False,
    visibility: bool = False,
) -> None:
    """Unlocks and shows specified attributes for the given Maya nodes.

    Unlocked attributes are made keyable, returning them to the Channel Box.

    Args:
        nodes (list[str]): A list of Maya node names to process.
        translate (bool, optional): If True, unlocks and shows translate attributes.
            Defaults to False.
        rotate (bool, optional): If True, unlocks and shows rotate attributes.
            Defaults to False.
        scale (bool, optional): If True, unlocks and shows scale attributes.
            Defaults to False.
        visibility (bool, optional): If True, unlocks and shows the visibility attribute.
            Defaults to False.
    """
    __set_lock_and_hide(nodes, False, translate, rotate, scale, visibility)
