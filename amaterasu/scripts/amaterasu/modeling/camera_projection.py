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
"""Projects UVs onto the selected object from the current camera view
using a planar projection.
"""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Camera Projection"
__version__: str = "1.30"
_logger: utils.Logger = utils.get_logger(__product__)


def create_guide_plane(camera: str, z: float = 1.0) -> str:
    """Creates a guide plane that coincides with the camera resolution gate.

    Args:
        camera (str): The name of the camera.
        z (float): The depth offset for the plane. Defaults to 1.0.

    Returns:
        str: The name of the created plane.
    """
    focal_length: float = cmds.getAttr(f"{camera}.focalLength")
    film_offset_h: float = cmds.getAttr(f"{camera}.horizontalFilmOffset")
    film_offset_v: float = cmds.getAttr(f"{camera}.verticalFilmOffset")
    film_aperture_h: float = cmds.getAttr(f"{camera}.horizontalFilmAperture")
    film_aperture_v: float = cmds.getAttr(f"{camera}.verticalFilmAperture")
    aspect_ratio: float = cmds.getAttr("defaultResolution.deviceAspectRatio")

    # 25.4 is mm to inch
    ratio_v: float = film_aperture_h / film_aperture_v / aspect_ratio
    distance_scale_h: float = film_aperture_h * 25.4 / focal_length * z
    distance_scale_v: float = film_aperture_v * 25.4 / focal_length * z

    trans_x: float = distance_scale_h * (film_offset_h / film_aperture_h)
    trans_y: float = distance_scale_v * (film_offset_v / film_aperture_v)
    scale_x: float = distance_scale_h
    scale_y: float = distance_scale_v * ratio_v
    film_fit: int = cmds.getAttr(f"{camera}.filmFit")
    if film_fit == 0:  # Fit
        if aspect_ratio < 1.0:
            scale_x = distance_scale_h / ratio_v
            scale_y = distance_scale_v

    elif film_fit == 2:  # Vertical
        scale_x = distance_scale_h / ratio_v
        scale_y = distance_scale_v

    elif film_fit == 3:  # Overscan
        if aspect_ratio > 1.0:
            scale_x = distance_scale_h / ratio_v
            scale_y = distance_scale_v

    camera_scale: float = cmds.getAttr(f"{camera}.cameraScale")
    pre_scale: float = 1.0 / cmds.getAttr(f"{camera}.preScale")
    post_scale: float = 1.0 / cmds.getAttr(f"{camera}.postScale")
    plane: str = cmds.polyPlane(
        width=1.0 * pre_scale * post_scale * camera_scale,
        height=1.0 * pre_scale * post_scale * camera_scale,
        subdivisionsX=1,
        subdivisionsY=1,
        axis=(0, 0, 1),
        createUVs=2,
        constructionHistory=True,
    )[
        0
    ]  # type: ignore

    plane = cmds.parent(plane, camera)[0]
    cmds.setAttr(f"{plane}.t", trans_x, trans_y, z * -1, type="double3")
    cmds.setAttr(f"{plane}.r", 0, 0, 0, type="double3")
    cmds.setAttr(f"{plane}.s", scale_x, scale_y, 1, type="double3")

    plane = cmds.parent(plane, world=True)[0]
    return plane


def project_uvs(node: str, camera: str, z: float = 1.0) -> utils.Result:
    """Creates UVs for the current camera view using a planar projection.

    Args:
        node (str): The target node to project UVs onto.
        camera (str): The name of the camera to use for the projection.
        z (float): The depth offset. Defaults to 1.0.

    Returns:
        utils.Result: The result object containing the operation status.
    """
    result: utils.Result = utils.Result()
    shapes: list[str] = (
        cmds.listRelatives(node, shapes=True, fullPath=True) or []
    )
    if not shapes:
        result.add_failure(node, "Shape does not exist.")
        return result

    if cmds.objectType(shapes[0]) != "mesh":
        result.add_failure(node, "Mesh does not exist.")
        return result

    parent: list[str] = (
        cmds.listRelatives(node, parent=True, fullPath=True) or []
    )

    # Deal with fact that parent is not deleted when combining.
    is_parent_locked: bool = False
    if parent:
        is_parent_locked = cmds.lockNode(parent[0], query=True, lock=True)[0]  # type: ignore
        cmds.lockNode(parent[0], lock=True)

    plane: str = create_guide_plane(camera, z)

    combined_node: str = cmds.polyUnite(
        plane,
        node,
        mergeUVSets=1,
        centerPivot=True,
        constructionHistory=False,  # type: ignore
    )[
        0
    ]  # type: ignore

    # Remove leftover nodes generated during the combine.
    cmds.delete(combined_node, constructionHistory=True)
    if cmds.objExists(node):
        cmds.delete(node)

    node = cmds.rename(combined_node, node.split("|")[-1])
    cmds.polyProjection(f"{node}.f[*]", type="Planar", mapDirection="p")

    start_uv: list[float] = cmds.polyEditUV(f"{node}.map[0]", query=True)  # type: ignore
    cmds.polyEditUV(
        f"{node}.map[*]",
        uValue=start_uv[0] * -1,
        vValue=start_uv[1] * -1,
    )

    end_uv: list[float] = cmds.polyEditUV(f"{node}.map[2]", query=True)  # type: ignore
    cmds.polyEditUV(
        f"{node}.map[*]",
        pivotU=0.0,
        pivotV=0.0,
        scaleU=1.0 / end_uv[0],
        scaleV=1.0 / end_uv[1],
    )
    cmds.delete(f"{node}.f[0]")
    cmds.delete(node, constructionHistory=True)

    if parent:
        cmds.parent(node, parent[0])
        if not is_parent_locked:
            cmds.lockNode(parent[0], lock=False)

    return result


def main() -> None:
    """Executes the camera UV projection on selected objects.

    Returns:
        None
    """
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error("Select polygons to create UVs.")
        return

    result: utils.Result = utils.Result()
    camera: str = dcc.viewport.get_current_camera()
    for node in selection:
        r: utils.Result = project_uvs(node, camera, 1.0)
        result.merge(r)

    cmds.select(*selection)
    result.log(_logger, f"Projected UVs from {camera}.")
