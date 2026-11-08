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
"""Provides functions for creating NURBS curve nodes in Maya.

This module includes utilities to generate single or multi-shape curves
from `CurveData` presets, as well as specialized spherical guides.
"""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc
from amaterasu.base.dcc.curve.preset import CurveData


def create_curve(
    name: str, parent: str | None, curves_data: list[CurveData]
) -> str:
    """Creates a single transform node containing multiple NURBS curve shapes.

    This function iterates over the provided `CurveData` list, generating a
    NURBS curve for each entry, and then parents all generated shapes under
    a single master transform node.

    Args:
        name (str): The desired name for the main transform node.
        parent (str | None): The name of the parent node. If None, the node
            will be created at the scene root.
        curves_data (list[CurveData]): A list of dictionaries containing
            curve creation parameters (degree, points, knots, periodic).

    Returns:
        str: The name of the created main transform node.
    """
    main_ctrl: str = cmds.createNode("transform", name=name)
    if parent:
        main_ctrl = cmds.parent(main_ctrl, parent)[0]

    for i, data in enumerate(curves_data):
        degree: int = data.get("degree", 1)
        points: list[list[float]] = data.get("points", [])
        knots: list[int] | None = data.get("knots")
        periodic: bool = data.get("periodic", False)

        if periodic:
            if knots is None:
                knots = list(range(-degree + 1, len(points)))

            tmp_crv: str = cmds.curve(
                degree=degree,
                point=points,  # type:ignore
                knot=knots,  # type:ignore
                periodic=True,
            )
        else:
            tmp_crv = cmds.curve(degree=degree, point=points)  # type:ignore

        shapes: list[str] = (
            cmds.listRelatives(tmp_crv, shapes=True, fullPath=True) or []
        )
        for shape in shapes:
            # new_shape = cmds.rename(shape, f"{name}Shape{i + 1:01d}")
            new_shape: str = cmds.rename(shape, f"{name}Shape")
            cmds.parent(new_shape, main_ctrl, shape=True, relative=True)

        cmds.delete(tmp_crv)

    return main_ctrl


def create_spherical_grid(
    base_name: str,
    parent: str,
    axis: int = 0,
    radius: float = 9999,
    division: int = 16,
    line_color: list[float] | None = None,
    line_width: float = 1.0,
) -> str:
    """Creates a spherical vanishing point guide oriented along a specific axis.

    This function generates a series of intersecting circular curves to form
    a spherical grid, representing perspective vanishing lines.

    Args:
        base_name (str): The base prefix for the generated curve nodes.
        parent (str): The name of the parent group node to attach the guide.
        axis (int, optional): The axis index determining the orientation
            (0 for X/Horizontal, 1 for Y/Vertical, 2 for Z/Depth). Defaults to 0.
        radius (float, optional): The radius of the generated guide curves.
            Defaults to 9999.
        division (int, optional): The number of line divisions (circles) to
            generate across the sphere. Defaults to 16.
        line_color (list[float] | None, optional): RGB color array for the
            viewport display. If None, defaults to purple [0.65, 0.2, 1.0].
            Defaults to None.
        line_width (float, optional): The line width for the primary axis curve.
            Defaults to 1.0.

    Returns:
        str: The name of the combined transform node containing all spherical shapes.
    """
    if line_color is None:
        line_color = [0.65, 0.2, 1.0]

    step: float = 180.0 / division
    axis_name: tuple[str, str, str] = ("Horizontal", "Vertical", "Depth")
    curves: list[str] = []
    for i in range(division):
        angle: float = step * i
        normal: tuple[tuple[float, float, float], ...] = (
            (0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        rotate_mask: tuple[tuple[float, float, float], ...] = (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        curve: str = cmds.circle(
            name=f"{base_name}{axis_name[axis]}{i}_C_crv",
            radius=radius,
            normal=normal[axis],
            sections=64,
            degree=3,
            constructionHistory=False,
        )[0]  # type: ignore
        rotate: tuple[float, float, float] = (
            angle * rotate_mask[axis][0],
            angle * rotate_mask[axis][1],
            angle * rotate_mask[axis][2],
        )
        cmds.setAttr(f"{curve}.rotate", *rotate, type="double3")
        dcc.attribute.lock([curve], translate=True, rotate=True, scale=True)

        curve = cmds.parent(curve, parent)[0]
        dcc.attribute.unlock([curve], translate=True, rotate=True, scale=True)
        cmds.makeIdentity(
            curve, apply=True, translate=True, rotate=True, scale=True
        )

        if i == 0:
            cmds.setAttr(f"{curve}.lineWidth", line_width)

        dcc.node.set_drawing_rgb_color(rgb=line_color, nodes=[curve])
        curves.append(curve)

    dcc.shape.combine(curves[0], curves[1:])
    dcc.attribute.lock_and_hide([curves[0]], translate=True, scale=True)
    # dcc.node.hide_history(cmds.listRelatives(curves[0], shapes=True, path=True))

    curves[0] = cmds.rename(curves[0], f"{base_name}{axis_name[axis]}_C_crv")
    return curves[0]
