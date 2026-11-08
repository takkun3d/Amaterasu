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
"""Sets up a time warp for the animation of the selected nodes.

This module creates a time warp controller to scale or offset the animation
timing of the provided nodes globally using Maya's objectSet and time attributes.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Time Warp"
__version__: str = "1.21"
_logger: utils.Logger = utils.get_logger(__product__)

ATTR_NAME: str = "frame"


def apply(nodes: list[str]) -> utils.DataResult[str]:
    """Sets up a time warp for the animation of the provided nodes.

    Args:
        nodes (list[str]): A list of Maya node names to apply the time
            warp to.

    Returns:
        utils.DataResult[str]: A DataResult containing the name of the
            created time warp controller objectSet.
    """
    result: utils.DataResult[str] = utils.DataResult("")
    if not nodes:
        result.add_failure("None", "No nodes provided for time warp.")
        return result

    controller: str = cmds.sets(nodes, name="time_warp#")  # type: ignore
    cmds.addAttr(controller, longName=ATTR_NAME, attributeType="time")

    plug: str = f"{controller}.{ATTR_NAME}"
    cmds.setAttr(plug, edit=True, keyable=True)

    start_frame: float = cmds.playbackOptions(
        query=True, animationStartTime=True
    )  # type: ignore

    end_frame: float = cmds.playbackOptions(
        query=True, animationEndTime=True
    )  # type: ignore

    cmds.setKeyframe(
        plug,
        time=start_frame,  # type: ignore
        value=start_frame,
        inTangentType="linear",
        outTangentType="linear",
    )

    cmds.setKeyframe(
        plug,
        time=end_frame,  # type: ignore
        value=end_frame,
        inTangentType="linear",
        outTangentType="linear",
    )

    for node in nodes:
        attrs: list[str] = cmds.listAttr(node, keyable=True)
        if not attrs:
            continue

        for attr in attrs:
            connection: str = dcc.animation.get_anim_curve(node, attr)
            if not connection:
                continue

            cmds.connectAttr(plug, f"{connection}.input", force=True)

    result.set_value(controller)
    return result


def main() -> None:
    """Executes the time warp setup for currently selected objects.

    Checks the active Maya selection and generates a time warp controller.
    Displays an error if no valid objects are selected.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select node(s) to set up time warp.")
        return

    result: utils.DataResult[str] = apply(selection)
    if result.value():
        cmds.select(result.value(), noExpand=True)

    result.log(_logger)
