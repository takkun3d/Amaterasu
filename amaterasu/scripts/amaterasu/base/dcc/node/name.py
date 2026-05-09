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
"""Utilities for managing and normalizing Maya node names."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def normalize_shape_name(node: str) -> utils.Result:
    """Normalizes the names of shapes under a specified transform node.

    Renames the shape nodes to match the transform node's name with a 'Shape'
    suffix. If there are multiple shapes, a numeric index is added (e.g.,
    'node0Shape', 'node1Shape').

    Args:
        node (str): The name of the transform node whose shapes will be renamed.

    Returns:
        utils.Result: The result of the operation, containing any failures.
    """
    result: utils.Result = utils.Result()
    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        return result

    is_solo: bool = len(shapes) == 1
    for i, shape in enumerate(shapes):
        try:
            short_name: str = node.split("|")[-1]
            new_name: str = (
                f"{short_name}Shape" if is_solo else f"{short_name}{i}Shape"
            )

            if shape.split("|")[-1] != new_name:
                cmds.rename(shape, new_name)

        except RuntimeError:
            result.add_failure(shape, "Failed to rename shape.")

    return result


def normalize_shading_engine_name(material: str) -> utils.Result:
    """Normalizes the name of the shading engine connected to a material.

    Renames the connected shading engine to match the material's name with
    an 'SG' suffix. Default Maya materials (e.g., 'lambert1', 'shaderGlow1')
    are ignored.

    Args:
        material (str): The name of the material node.

    Returns:
        utils.Result: The result of the operation, containing any failures.
    """
    result: utils.Result = utils.Result()
    if material in (
        "lambert1",
        "particleCloud1",
        "shaderGlow1",
        "standardSurface1",
    ):
        return result

    shading_engines: list[str] = (
        cmds.listConnections(
            material, source=False, destination=True, type="shadingEngine"
        )
        or []
    )
    if not shading_engines:
        return result

    try:
        new_name: str = f"{material}SG"
        if shading_engines[0] != new_name:
            cmds.rename(shading_engines[0], new_name)

    except RuntimeError:
        result.add_failure(material, "Failed to rename shading engine.")

    return result


def remove_pasted_prefixes(nodes: list[str] | None = None) -> utils.Result:
    """Removes the 'pasted__' prefix from specified nodes.

    If no nodes are provided, it searches the entire scene for nodes with
    the 'pasted__' prefix and renames them. Nodes are processed in descending
    order of path length to safely rename deep hierarchies without breaking
    child paths.

    Args:
        nodes (list[str] | None, optional): A list of full node paths to process.
            If None, all nodes in the scene with the prefix will be processed.
            Defaults to None.

    Returns:
        utils.Result: The result of the operation, containing any failures.
    """
    result: utils.Result = utils.Result()
    if nodes is None:
        nodes = cmds.ls("pasted__*", long=True)
        if not nodes:
            return result

    for node in sorted(nodes, key=len, reverse=True):
        short_name: str = node.split("|")[-1]
        new_name: str = short_name.replace("pasted__", "")
        try:
            cmds.rename(node, new_name)

        except RuntimeError:
            result.add_failure(node, "Failed to remove prefix")

    return result
