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
"""Provides bounding box spatial utilities for Maya nodes."""

from __future__ import annotations
import itertools
from maya import cmds


def get_stacked_nodes(nodes: list[str], seek: int = 0) -> list[str]:
    """Finds nodes that occupy the exact same bounding box space.

    Calculates the world-space bounding box for each node (rounded to 15
    decimal places) and groups nodes with identical bounding boxes.

    Args:
        nodes (list[str]): A list of Maya node names to evaluate. Only nodes
            with shape children will be processed.
        seek (int, optional): The starting index for slicing the grouped list
            of stacked nodes.
            - `0`: Returns ALL stacked nodes in the group.
            - `1`: Returns all stacked nodes EXCEPT the first one (useful
              for keeping one and deleting the rest as duplicates).
            Defaults to 0.

    Returns:
        list[str]: A flat list of node names that are stacked on top of
            each other, filtered by the `seek` parameter.
    """
    data_list: list[tuple[str, list[float]]] = [
        (
            x,
            [
                round(y, 15)  # type: ignore
                for y in cmds.xform(
                    x, query=True, boundingBox=True, worldSpace=True
                )  # type: ignore
            ],
        )
        for x in nodes
        if cmds.listRelatives(x, shapes=True, path=True)
    ]

    # Group geometries by their matrix
    # [[(geometry, matrix), ...], ...]
    geometries_by_matrix: list[list[tuple[str, list[float]]]] = [
        y
        for y in [
            list(g)
            for k, g in itertools.groupby(
                sorted(data_list, key=lambda x: x[1]), lambda x: x[1]
            )
        ]
        if len(y) > 1
    ]

    # Extract selected nodes from the specified position.
    # [geometry, ...]
    result: list[str] = [y[0] for x in geometries_by_matrix for y in x[seek:]]

    return result
