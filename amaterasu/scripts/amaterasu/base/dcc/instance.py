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
"""Operations for managing and manipulating instance nodes in Maya.

This module provides core logic to safely convert instance nodes into independent
objects and delete instances from the scene.
"""

from maya import cmds
from amaterasu.base import utils


def to_object(node: str) -> utils.Result:
    """Converts a given instance node into an independent object.

    If the provided node is a shape, it resolves to its parent transform
    before duplicating. The original instance is deleted and replaced by
    the newly duplicated independent object.

    Args:
        node (str): The full or partial path to the instance node.

    Returns:
        utils.Result: An object containing the success state and any error
            messages if the conversion fails (e.g., missing parent).
    """
    result: utils.Result = utils.Result()
    if cmds.objectType(node, isAType="shape"):
        parent: list[str] = (
            cmds.listRelatives(node, parent=True, path=True) or []
        )
        if not parent:
            result.add_failure(node, "Does not exist parent.")
            return result

        node = parent[0]

    new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
    delete(node)
    cmds.rename(new_node, node.split("|")[-1])
    return result


def delete(node: str) -> utils.Result:
    """Safely deletes an instance node from the Maya scene.

    Removes the instance connection by un-parenting the object or shape.

    Args:
        node (str): The full or partial path to the instance node to delete.

    Returns:
        utils.Result: An object containing the success state and any error
            messages if the deletion process encounters an exception.
    """
    result: utils.Result = utils.Result()
    try:
        if cmds.objectType(node, isAType="shape"):
            cmds.parent(node, removeObject=True, shape=True)

        else:
            cmds.parent(node, removeObject=True)

    except (RuntimeError, ValueError):
        result.add_failure(node, "Can not delete node.")

    return result
