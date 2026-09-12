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
"""Generates a speed meter rig for selected Maya objects.

This module creates a curve-based digital speed meter that calculates and
displays the speed of an object in km/h using Maya expressions. It visually
updates colors based on speed thresholds.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Speed Meter"
__version__: str = "1.00"
_logger: utils.Logger = utils.get_logger(__product__)

PTS_0: list[tuple[float, float, float]] = [
    (0, 2, 0),
    (1, 2, 0),
    (1, 0, 0),
    (0, 0, 0),
    (0, 2, 0),
]
PTS_1: list[tuple[float, float, float]] = [(1, 2, 0), (1, 0, 0)]
PTS_2: list[tuple[float, float, float]] = [
    (0, 2, 0),
    (1, 2, 0),
    (1, 1, 0),
    (0, 1, 0),
    (0, 0, 0),
    (1, 0, 0),
]
PTS_3: list[tuple[float, float, float]] = [
    (0, 2, 0),
    (1, 2, 0),
    (1, 1, 0),
    (0, 1, 0),
    (1, 1, 0),
    (1, 0, 0),
    (0, 0, 0),
]
PTS_4: list[tuple[float, float, float]] = [
    (0, 2, 0),
    (0, 1, 0),
    (1, 1, 0),
    (1, 2, 0),
    (1, 1, 0),
    (1, 0, 0),
]
PTS_5: list[tuple[float, float, float]] = [
    (1, 2, 0),
    (0, 2, 0),
    (0, 1, 0),
    (1, 1, 0),
    (1, 0, 0),
    (0, 0, 0),
]
PTS_6: list[tuple[float, float, float]] = [
    (1, 2, 0),
    (0, 2, 0),
    (0, 0, 0),
    (1, 0, 0),
    (1, 1, 0),
    (0, 1, 0),
]
PTS_7: list[tuple[float, float, float]] = [(0, 2, 0), (1, 2, 0), (1, 0, 0)]
PTS_8: list[tuple[float, float, float]] = [
    (0, 1, 0),
    (0, 2, 0),
    (1, 2, 0),
    (1, 0, 0),
    (0, 0, 0),
    (0, 1, 0),
    (1, 1, 0),
]
PTS_9: list[tuple[float, float, float]] = [
    (1, 1, 0),
    (0, 1, 0),
    (0, 2, 0),
    (1, 2, 0),
    (1, 0, 0),
]
PTS_LIST: list[list[tuple[float, float, float]]] = [
    PTS_0,
    PTS_1,
    PTS_2,
    PTS_3,
    PTS_4,
    PTS_5,
    PTS_6,
    PTS_7,
    PTS_8,
    PTS_9,
]

PTS_K: list[tuple[float, float, float]] = [
    (1, 2, 0),
    (0, 1, 0),
    (0, 2, 0),
    (0, 0, 0),
    (0, 1, 0),
    (1, 0, 0),
]
PTS_M: list[tuple[float, float, float]] = [
    (0, 0, 0),
    (0, 1, 0),
    (0.5, 1, 0),
    (0.5, 0, 0),
    (0.5, 1, 0),
    (1, 1, 0),
    (1, 0, 0),
]
PTS_SLASH: list[tuple[float, float, float]] = [(0, 0, 0), (1, 2, 0)]
PTS_H: list[tuple[float, float, float]] = [
    (0, 2, 0),
    (0, 0, 0),
    (0, 1, 0),
    (1, 1, 0),
    (1, 0, 0),
]

COLOR_NAMES: list[str] = [
    "Default",
    "Black",
    "Dark Gray",
    "Light Gray",
    "Crimson",
    "Navy Blue",
    "Blue",
    "Dark Green",
    "Dark Purple",
    "Magenta",
    "Brown",
    "Dark Brown",
    "Rust",
    "Red",
    "Green",
    "Bright Blue",
    "White",
    "Yellow",
    "Light Blue",
    "Light Green",
    "Pink",
    "Orange",
    "Light Yellow",
    "Solid Green",
    "Light Brown",
    "Mustard",
    "Bright Yellow Green",
    "Cyan",
    "Bright Cyan",
    "Pale Blue",
    "Purple",
    "Light Magenta",
]
COLOR_ENUM_STR: str = ":".join(COLOR_NAMES)


def create_digit(
    pts_list: list[list[tuple[float, float, float]]],
    digit_name: str,
    pos_x: float,
    parent_grp: str,
) -> list[str]:
    """Creates curve shapes for a single numerical digit.

    Args:
        pts_list (list[list[tuple[float, float, float]]]):
            A list containing lists of point coordinates for each number (0-9).
        digit_name (str): The base name for the generated curve shapes.
        pos_x (float): The X-axis offset for positioning the digit.
        parent_grp (str): The name of the parent group to which the shapes will be parented.

    Returns:
        list[str]: A list of the created curve shape names.
    """
    result: list[str] = []
    for i, pts in enumerate(pts_list):
        offset_pts: list[tuple[float, float, float]] = [
            (p[0] + pos_x, p[1], p[2]) for p in pts
        ]
        crv: str = cmds.curve(degree=1, point=offset_pts)
        shape: str = cmds.listRelatives(crv, shapes=True)[0]
        shape = cmds.rename(shape, f"{digit_name}_{i}_crvShape")
        cmds.setAttr(f"{shape}.visibility", False)
        cmds.setAttr(f"{shape}.isHistoricallyInteresting", 0)
        cmds.connectAttr(f"{parent_grp}.lineWidth", f"{shape}.lineWidth")

        cmds.parent(shape, parent_grp, shape=True, relative=True)
        cmds.delete(crv)

        result.append(shape)

    return result


def make_letter(
    pts: list[tuple[float, float, float]],
    name: str,
    base_x: float,
    tx: float,
    scale: float,
    parent_grp: str,
) -> None:
    """Creates a curve shape for a specific letter or symbol (e.g., 'k', 'm', '/').

    Args:
        pts (list[tuple[float, float, float]]): The list of point coordinates for the letter.
        name (str): The base name for the generated curve shape.
        base_x (float): The base X-axis offset.
        tx (float): The translation X offset for spacing letters.
        scale (float): The uniform scale factor applied to the points.
        parent_grp (str): The name of the parent group to which the shape will be parented.
    """
    offset_pts: list[tuple[float, float, float]] = [
        (p[0] * scale + base_x + (tx * scale), p[1] * scale, p[2] * scale)
        for p in pts
    ]
    crv: str = cmds.curve(degree=1, point=offset_pts)
    shape: str = cmds.listRelatives(crv, shapes=True)[0]
    shape = cmds.rename(shape, f"{name}_crvShape")
    cmds.setAttr(f"{shape}.isHistoricallyInteresting", 0)
    cmds.connectAttr(f"{parent_grp}.lineWidth", f"{shape}.lineWidth")

    cmds.parent(shape, parent_grp, shape=True, relative=True)
    cmds.delete(crv)


def create_speedmeter(obj: str) -> str | None:
    """Creates a speed meter rig for the specified object.

    This function builds a hierarchical rig containing digital number curves
    and a 'km/h' label. It also creates a Maya expression node to calculate
    the object's speed based on its world matrix over time, dynamically changing
    colors based on predefined speed levels.

    Args:
        obj (str): The name of the Maya node to attach the speed meter to.

    Returns:
        str | None: The name of the main display curve group if successful, or None.
    """
    base_name: str = obj.replace(":", "_")
    exp_name: str = f"speedmeter_{base_name}_expr"
    root_grp: str = f"speedmeter_{base_name}_null"
    display_crv: str = f"speedmeter_{base_name}_crv"

    if cmds.objExists(root_grp):
        cmds.delete(root_grp)

    if cmds.objExists(exp_name):
        cmds.delete(exp_name)

    root_grp = cmds.group(empty=True, name=root_grp)
    display_crv: str = cmds.group(empty=True, name=display_crv, parent=root_grp)
    cmds.setAttr(f"{display_crv}.overrideEnabled", 1)
    cmds.setAttr(f"{display_crv}.overrideColor", 14)

    dcc.attribute.add_separator(display_crv, "System", keyable=True)
    dcc.attribute.add_float(
        display_crv, "modelScale", 0.01, 100, 1, keyable=True
    )

    dcc.attribute.add_separator(display_crv, "Style", keyable=True)
    dcc.attribute.add_float(
        display_crv, "lineWidth", None, None, 2.0, keyable=True
    )
    dcc.attribute.add_enum(
        display_crv, "baseColor", COLOR_ENUM_STR, 14, keyable=True
    )

    dcc.attribute.add_separator(display_crv, "Level", keyable=True)
    for name, speed_val, col_val in [
        ("Level1", 40, 26),
        ("Level2", 60, 17),
        ("Level3", 80, 21),
        ("Level4", 100, 13),
    ]:
        dcc.attribute.add_float(
            display_crv, f"speed{name}", None, None, speed_val, keyable=True
        )
        dcc.attribute.add_enum(
            display_crv, f"color{name}", COLOR_ENUM_STR, col_val, keyable=True
        )

    digit_100: list[str] = create_digit(
        PTS_LIST, f"{base_name}_digit100", -3.0, display_crv
    )
    digit_10: list[str] = create_digit(
        PTS_LIST, f"{base_name}_digit10", -1.5, display_crv
    )
    digit_1: list[str] = create_digit(
        PTS_LIST, f"{base_name}_digit1", 0.0, display_crv
    )

    make_letter(PTS_K, f"{base_name}_k", 1.5, 0.0, 0.7, display_crv)
    make_letter(PTS_M, f"{base_name}_m", 1.5, 1.2, 0.7, display_crv)
    make_letter(PTS_SLASH, f"{base_name}_slash", 1.5, 2.4, 0.7, display_crv)
    make_letter(PTS_H, f"{base_name}_h", 1.5, 3.6, 0.7, display_crv)

    exp_str: str = f"""
float $fps = `currentTimeUnitToFPS`;
float $cTime = frame;
float $cMat[] = `getAttr -t $cTime "{obj}.worldMatrix[0]"`;
float $pMat[] = `getAttr -t ($cTime - 1) "{obj}.worldMatrix[0]"`;
float $dx = $cMat[12] - $pMat[12];
float $dy = $cMat[13] - $pMat[13];
float $dz = $cMat[14] - $pMat[14];
float $dist = sqrt($dx*$dx + $dy*$dy + $dz*$dz);
float $scale = {display_crv}.modelScale;
float $speed = ($dist / $scale) * $fps * 0.036;
if($speed >= {display_crv}.speedLevel4){{
    {display_crv}.overrideColor = {display_crv}.colorLevel4;
}}else if($speed >= {display_crv}.speedLevel3){{
    {display_crv}.overrideColor = {display_crv}.colorLevel3;
}}else if($speed >= {display_crv}.speedLevel2){{
    {display_crv}.overrideColor = {display_crv}.colorLevel2;
}}else if($speed >= {display_crv}.speedLevel1){{
    {display_crv}.overrideColor = {display_crv}.colorLevel1;
}}else{{
    {display_crv}.overrideColor = {display_crv}.baseColor;
}}

int $digit100 = (trunc($speed / 100)) % 10;
int $digit10 = (trunc($speed / 10)) % 10;
int $digit1 = (trunc($speed)) % 10;
""".replace("\n", "")

    for i in range(len(PTS_LIST)):
        exp_str += f"{digit_100[i]}.visibility = ($digit100 == {i});"
        exp_str += f"{digit_10[i]}.visibility = ($digit10 == {i});"
        exp_str += f"{digit_1[i]}.visibility = ($digit1 == {i});"

    exp_name = cmds.expression(
        name=exp_name, string=exp_str, alwaysEvaluate=True
    )

    dcc.node.hide_history([display_crv])

    # TODO Matrix
    cmds.pointConstraint(obj, root_grp, maintainOffset=False)
    dcc.attribute.lock([root_grp], True, True, True, False)

    cmds.select(display_crv)
    return display_crv


def main() -> None:
    """Executes the speed meter creation for all currently selected objects.

    Checks the active Maya selection and generates a speed meter rig for each
    selected node. Displays a warning if no valid objects are selected.
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.warning("Select node(s) to create speed meter(s).")
        return

    results: list[str] = []
    for node in selection:
        result: str | None = create_speedmeter(node)
        if result:
            results.append(result)

    if results:
        _logger.info(
            "Successfully created speed meters for %s nodes.", len(results)
        )
        cmds.select(*results)
