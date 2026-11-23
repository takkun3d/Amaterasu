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
"""Creates a CV curve that follows the specified transform nodes."""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc, utils

__product__: str = "Curve Linker"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig or dcc.node).
def extract_base_name(node: str) -> str:
    """Extracts the short base name from a DAG path or namespaced node.

    Args:
        node (str): The full or partial node name.

    Returns:
        str: The extracted base name prefix.
    """
    short_name: str = node.split("|")[-1].split(":")[-1]
    return short_name.split("_")[0]


# TODO: Consider moving to amaterasu.base (e.g., dcc.rig).
def connect_mult_matrix(
    base_name: str,
    source_plugs: list[str],
    target_plug: str,
) -> str:
    """Creates a multMatrix node and connects the specified matrix plugs.

    Args:
        base_name (str): The naming prefix for the multMatrix node.
        source_plugs (list[str]): Ordered list of source matrix plugs.
        target_plug (str): The destination plug to connect the matrix sum to.

    Returns:
        str: The name of the created multMatrix node.
    """
    mult_matrix: str = cmds.createNode(
        "multMatrix", name=f"{base_name}_multMtx"
    )
    for i, plug in enumerate(source_plugs):
        cmds.connectAttr(plug, f"{mult_matrix}.matrixIn[{i}]")

    cmds.connectAttr(f"{mult_matrix}.matrixSum", target_plug)
    return mult_matrix


def apply(nodes: list[str]) -> str:
    """Creates a degree-1 CV curve driven by the specified transform nodes.

    Args:
        nodes (list[str]): Transform nodes to link with the curve's CVs.

    Returns:
        str: The name of the created curve transform node.
    """

    start_name: str = extract_base_name(nodes[0])
    end_name: str = extract_base_name(nodes[-1])

    point_count: int = len(nodes)
    points: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * point_count
    knots: list[int] = list(range(point_count))
    curve: str = cmds.curve(
        degree=1,
        point=points,
        knot=knots,  # type: ignore
        name=f"{start_name}To{end_name.title()}_crv",
    )
    temp_shape: str = cmds.listRelatives(curve, shapes=True, path=True)[0]
    curve_shape: str = cmds.rename(temp_shape, f"{curve.split('|')[-1]}Shape")

    for i, node in enumerate(nodes):
        node_name: str = extract_base_name(node)

        decompose_mtx: str = cmds.createNode(
            "decomposeMatrix", name=f"{node_name}_decomposeMtx"
        )
        connect_mult_matrix(
            node_name,
            [f"{node}.worldMatrix[0]", f"{curve}.worldInverseMatrix[0]"],
            f"{decompose_mtx}.inputMatrix",
        )
        cmds.connectAttr(
            f"{decompose_mtx}.outputTranslate",
            f"{curve_shape}.controlPoints[{i}]",
        )

    dcc.node.hide_history([curve, curve_shape])
    return curve


def main() -> None:
    """Validates the current selection and creates a linked curve."""
    selection: list[str] = cmds.ls(selection=True, transforms=True)
    if not selection or len(selection) < 2:
        _logger.error("Select two or more transforms to create a curve.")
        return

    apply(selection)
    _logger.info("Done.")
