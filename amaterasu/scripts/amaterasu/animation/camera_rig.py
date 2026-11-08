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
"""Module for building an advanced camera rig in Autodesk Maya.

This module provides functions to create a highly customizable camera rig
with features like camera shake, film offset, aim target switching, and
custom viewport guides.
"""

from __future__ import annotations

from maya import cmds

from amaterasu.base import dcc, utils

__product__: str = "Camera Rig"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)


def apply(
    name: str = "render_cam",
) -> str:
    """Builds the complete camera rig hierarchy and node network.

    Constructs all controllers, offset nodes, matrix calculations, and custom
    viewport guides necessary for the advanced camera rig.

    Args:
        camera_group (str, optional): The name of the top-level group for the rig.
            Defaults to "camera_grp".
        camera (str, optional): The name of the camera to create and rig.
            Defaults to "render_cam".

    Returns:
        str: The name of the created camera node.
    """
    locked_dg_nodes: list[str] = []

    _tl: list[str] = name.split("_")
    base_name: str = _tl[0] + "".join(_t.capitalize() for _t in _tl[1:])

    # --------------------------------------------------------------------------
    # Root
    camera_grp: str = cmds.createNode("transform", name=f"{base_name}_grp")

    # --------------------------------------------------------------------------
    # Camera
    result_camera: list[str] = cmds.camera()  # type:ignore
    result_camera[0] = cmds.parent(result_camera[0], camera_grp)[0]
    name = cmds.rename(result_camera[0], name)
    cmds.setAttr(f"{name}.visibility", False)

    camera_shape: str = cmds.listRelatives(name, shapes=True, path=True)[0]
    cmds.setAttr(f"{camera_shape}.overrideDisplayType", 2)
    cmds.setAttr(f"{camera_shape}.overrideEnabled", 1)
    cmds.setAttr(f"{camera_shape}.renderable", 0)
    cmds.setAttr(f"{camera_shape}.horizontalFilmAperture", 1.41732)
    cmds.setAttr(f"{camera_shape}.verticalFilmAperture", 0.94488)
    cmds.setAttr(f"{camera_shape}.filmFit", 1)
    cmds.setAttr(f"{camera_shape}.overscan", 1.3)
    cmds.setAttr(f"{camera_shape}.nearClipPlane", 10)
    cmds.setAttr(f"{camera_shape}.farClipPlane", 100)
    cmds.setAttr(f"{camera_shape}.orthographicWidth", 30)
    cmds.setAttr(f"{camera_shape}.imageName", "camera1", type="string")
    cmds.setAttr(f"{camera_shape}.depthName", "camera1_depth", type="string")
    cmds.setAttr(f"{camera_shape}.maskName", "camera1_mask", type="string")
    cmds.setAttr(f"{camera_shape}.displayResolution", 1)
    cmds.setAttr(f"{camera_shape}.bestFitClippingPlanes", 0)
    cmds.setAttr(f"{camera_shape}.displayGateMaskColor", 0, 0, 0, type="float3")

    cmds.setAttr(f"{camera_shape}.cameraScale", lock=True)
    cmds.setAttr(f"{camera_shape}.lensSqueezeRatio", lock=True)
    cmds.setAttr(f"{camera_shape}.preScale", lock=True)
    cmds.setAttr(f"{camera_shape}.filmFit", lock=True)
    cmds.setAttr(f"{camera_shape}.filmTranslateH", lock=True)
    cmds.setAttr(f"{camera_shape}.filmTranslateV", lock=True)
    cmds.setAttr(f"{camera_shape}.horizontalRollPivot", lock=True)
    cmds.setAttr(f"{camera_shape}.verticalRollPivot", lock=True)
    cmds.setAttr(f"{camera_shape}.filmRollValue", lock=True)

    # --------------------------------------------------------------------------
    # Container
    ctrl_grp: str = cmds.createNode(
        "transform", name="controller_grp", parent=camera_grp
    )

    setup_grp: str = cmds.createNode(
        "transform", name="setup_grp", parent=camera_grp
    )

    # --------------------------------------------------------------------------
    # Controllers
    root_ctrl: str = dcc.curve.create_curve(
        "root_C_ctrl", ctrl_grp, dcc.curve.ROOT
    )
    cmds.setAttr(f"{root_ctrl}.ove", 1)
    cmds.setAttr(f"{root_ctrl}.ovc", 13)
    cmds.setAttr(f"{root_ctrl}.uocol", 1)
    cmds.setAttr(f"{root_ctrl}.oclr", 1, 0, 0, type="float3")

    local_ctrl: str = dcc.curve.create_curve(
        "local_C_ctrl", root_ctrl, dcc.curve.LOCAL
    )
    cmds.setAttr(f"{local_ctrl}.ove", 1)
    cmds.setAttr(f"{local_ctrl}.ovc", 6)
    cmds.setAttr(f"{local_ctrl}.uocol", 1)
    cmds.setAttr(f"{local_ctrl}.oclr", 1, 0.167, 0, type="float3")

    body_ctrl: str = dcc.curve.create_curve(
        "body_C_ctrl", local_ctrl, dcc.curve.BODY
    )
    cmds.setAttr(f"{body_ctrl}.ove", 1)
    cmds.setAttr(f"{body_ctrl}.ovc", 17)
    cmds.setAttr(f"{body_ctrl}.uocol", 1)
    cmds.setAttr(f"{body_ctrl}.oclr", 1, 0.333, 0, type="float3")

    cam_ctrl: str = dcc.curve.create_curve(
        "camera_C_ctrl", body_ctrl, dcc.curve.CAMERA
    )
    cmds.setAttr(f"{cam_ctrl}.ove", 1)
    cmds.setAttr(f"{cam_ctrl}.ovc", 27)
    cmds.setAttr(f"{cam_ctrl}.uocol", 1)
    cmds.setAttr(f"{cam_ctrl}.oclr", 1, 0.5, 0, type="float3")
    dcc.attribute.add_separator(cam_ctrl, "camera", keyable=True)
    dcc.attribute.promote_attribute(cam_ctrl, f"{camera_shape}.focalLength")
    dcc.attribute.promote_attribute(cam_ctrl, f"{camera_shape}.postScale")

    film_ctrl: str = dcc.curve.create_curve(
        "filmOffset_C_ctrl", ctrl_grp, dcc.curve.FILM_OFFSET
    )
    cmds.setAttr(f"{film_ctrl}.ove", 1)
    cmds.setAttr(f"{film_ctrl}.ovc", 17)
    cmds.setAttr(f"{film_ctrl}.uocol", 1)
    cmds.setAttr(f"{film_ctrl}.oclr", 1, 1, 0, type="float3")

    aim_ctrl: str = dcc.curve.create_curve(
        "aimTarget_C_ctrl", ctrl_grp, dcc.curve.AIM_TARGET
    )
    cmds.setAttr(f"{aim_ctrl}.ove", 1)
    cmds.setAttr(f"{aim_ctrl}.ovc", 13)
    cmds.setAttr(f"{aim_ctrl}.uocol", 1)
    cmds.setAttr(f"{aim_ctrl}.oclr", 0, 1, 0, type="float3")
    dcc.attribute.add_separator(aim_ctrl, "aimOption", keyable=True)
    dcc.attribute.add_enum(
        aim_ctrl, "parent", "Camera:Body:Local:Root:None", 1, keyable=True
    )
    dcc.attribute.add_float(aim_ctrl, "aim", 0, 1, 0, keyable=True)
    dcc.attribute.add_float(aim_ctrl, "roll", keyable=True)

    near_ctrl: str = dcc.curve.create_curve(
        "nearClipPlane_C_ctrl", ctrl_grp, dcc.curve.CLIP_PLANE
    )
    cmds.setAttr(f"{near_ctrl}.ove", 1)
    cmds.setAttr(f"{near_ctrl}.ovc", 20)
    cmds.setAttr(f"{near_ctrl}.uocol", 1)
    cmds.setAttr(f"{near_ctrl}.oclr", 0, 1, 1, type="float3")
    cmds.setAttr(f"{near_ctrl}.ls", 3)
    cmds.setAttr(f"{near_ctrl}.translateZ", 1)
    cmds.connectAttr(f"{near_ctrl}.tz", f"{camera_shape}.ncp", force=True)

    far_ctrl: str = dcc.curve.create_curve(
        "farClipPlane_C_ctrl", ctrl_grp, dcc.curve.CLIP_PLANE
    )
    cmds.setAttr(f"{far_ctrl}.ove", 1)
    cmds.setAttr(f"{far_ctrl}.ovc", 18)
    cmds.setAttr(f"{far_ctrl}.uocol", 1)
    cmds.setAttr(f"{far_ctrl}.oclr", 0, 1, 1, type="float3")
    cmds.setAttr(f"{far_ctrl}.ls", 3)
    cmds.setAttr(f"{far_ctrl}.translateZ", 10000)
    cmds.connectAttr(f"{far_ctrl}.tz", f"{camera_shape}.fcp", force=True)

    settings_ctrl: str = dcc.curve.create_curve(
        "settings_C_ctrl", ctrl_grp, dcc.curve.SETTING
    )
    cmds.setAttr(f"{settings_ctrl}.translateY", 15)
    cmds.setAttr(f"{settings_ctrl}.ove", 1)
    cmds.setAttr(f"{settings_ctrl}.ovc", 9)
    cmds.setAttr(f"{settings_ctrl}.uocol", 1)
    cmds.setAttr(f"{settings_ctrl}.oclr", 1, 0, 1, type="float3")
    dcc.attribute.add_separator(settings_ctrl, "display", keyable=True)
    dcc.attribute.add_float(
        settings_ctrl, "rigSize", 0.0001, default_val=1, keyable=True
    )
    dcc.attribute.add_float(settings_ctrl, "gateOpacity", 0, 1, 1, keyable=True)
    dcc.attribute.promote_attribute(
        settings_ctrl, f"{camera_shape}.dgo", "gateOpacity", 1
    )

    dcc.attribute.add_separator(settings_ctrl, "playback", keyable=True)
    dcc.attribute.promote_attribute(
        settings_ctrl, f"{ctrl_grp}.hpb", "hideRigOnPlayblack", True
    )
    dcc.attribute.promote_attribute(
        settings_ctrl, f"{setup_grp}.hpb", "hideGuideOnPlayblack"
    )

    dcc.attribute.add_separator(settings_ctrl, "guide", keyable=True)
    dcc.attribute.promote_attribute(
        settings_ctrl, f"{setup_grp}.v", "allGuide", True
    )
    dcc.attribute.add_boolean(settings_ctrl, "gridGuide", True, keyable=True)
    dcc.attribute.add_boolean(settings_ctrl, "frustumGuide", True, keyable=True)
    dcc.attribute.add_boolean(settings_ctrl, "perspGuide", True, keyable=True)
    dcc.attribute.add_float(settings_ctrl, "perspGuideOffset", keyable=True)
    dcc.attribute.add_float(
        settings_ctrl,
        "perspGuideOpacity",
        keyable=True,
        min_val=0.0,
        max_val=1.0,
        default_val=0.3,
    )

    # --------------------------------------------------------------------------
    # Aim Up
    aimUp_null: str = cmds.createNode(
        "transform", name="aimUpTarget_C_null", parent=setup_grp
    )

    # --------------------------------------------------------------------------
    # Shake Camera
    shake_cam: str = cmds.createNode(
        "transform", name="shakeCamera_C_null", parent=setup_grp
    )
    dcc.attribute.add_separator(shake_cam, "shake", keyable=True)
    dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.shake")

    dcc.attribute.add_boolean(shake_cam, "enableShake", keyable=True)
    dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.enableShake")

    for a in ["TX", "TY", "TZ", "RX", "RY", "RZ"]:
        dcc.attribute.add_boolean(shake_cam, f"enable{a}", keyable=True)
        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.enable{a}")

    for n in ["A", "B", "C", "D"]:
        dcc.attribute.add_separator(shake_cam, f"noise{n}", keyable=True)
        dcc.attribute.add_boolean(shake_cam, f"enableNoise{n}", keyable=True)
        dcc.attribute.add_float(shake_cam, f"seed{n}", keyable=True)
        dcc.attribute.add_float(shake_cam, f"speed{n}", keyable=True)
        dcc.attribute.add_float(shake_cam, f"magnitude{n}", keyable=True)

        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.noise{n}")
        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.enableNoise{n}")
        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.seed{n}")
        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.speed{n}")
        dcc.attribute.promote_attribute(cam_ctrl, f"{shake_cam}.magnitude{n}")

    exp_cam: str = f"""
if({shake_cam}.enableShake == true){{
    float $txA = 0.0;
    float $tyA = 0.0;
    float $tzA = 0.0;
    if({shake_cam}.enableNoiseA == true){{
        $txA = noise({shake_cam}.seedA + (time * {shake_cam}.speedA)) * {shake_cam}.magnitudeA;
        $tyA = noise({shake_cam}.seedA + ((time + 1) * {shake_cam}.speedA)) * {shake_cam}.magnitudeA;
        $tzA = noise({shake_cam}.seedA + ((time + 2) * {shake_cam}.speedA)) * {shake_cam}.magnitudeA;
    }}

    float $txB = 0.0;
    float $tyB = 0.0;
    float $tzB = 0.0;
    if({shake_cam}.enableNoiseB == true){{
        $txB = noise({shake_cam}.seedB + ((time + 3) * {shake_cam}.speedB)) * {shake_cam}.magnitudeB;
        $tyB = noise({shake_cam}.seedB + ((time + 4) * {shake_cam}.speedB)) * {shake_cam}.magnitudeB;
        $tzB = noise({shake_cam}.seedB + ((time + 5) * {shake_cam}.speedB)) * {shake_cam}.magnitudeB;
    }}

    float $rxA = 0.0;
    float $ryA = 0.0;
    float $rzA = 0.0;
    if({shake_cam}.enableNoiseC == true){{
        $rxA = noise({shake_cam}.seedC + ((time + 6) * {shake_cam}.speedC)) * {shake_cam}.magnitudeC;
        $ryA = noise({shake_cam}.seedC + ((time + 7) * {shake_cam}.speedC)) * {shake_cam}.magnitudeC;
        $rzA = noise({shake_cam}.seedC + ((time + 8) * {shake_cam}.speedC)) * {shake_cam}.magnitudeC;
    }}

    float $rxB = 0.0;
    float $ryB = 0.0;
    float $rzB = 0.0;
    if({shake_cam}.enableNoiseD == true){{
        $rxB = noise({shake_cam}.seedD + ((time + 9) * {shake_cam}.speedD)) * {shake_cam}.magnitudeD;
        $ryB = noise({shake_cam}.seedD + ((time + 10) * {shake_cam}.speedD)) * {shake_cam}.magnitudeD;
        $rzB = noise({shake_cam}.seedD + ((time + 11) * {shake_cam}.speedD)) * {shake_cam}.magnitudeD;
    }}

    {shake_cam}.translateX = ($txA + $txB) * {shake_cam}.enableTX;
    {shake_cam}.translateY = ($tyA + $tyB) * {shake_cam}.enableTY;
    {shake_cam}.translateZ = ($tzA + $tzB) * {shake_cam}.enableTZ;
    {shake_cam}.rotateX = ($rxA + $rxB) * {shake_cam}.enableRX;
    {shake_cam}.rotateY = ($ryA + $ryB) * {shake_cam}.enableRY;
    {shake_cam}.rotateZ = ($rzA + $rzB) * {shake_cam}.enableRZ;

}}else{{
    {shake_cam}.translateX = 0;
    {shake_cam}.translateY = 0;
    {shake_cam}.translateZ = 0;
    {shake_cam}.rotateX = 0;
    {shake_cam}.rotateY = 0;
    {shake_cam}.rotateZ = 0;
}}
""".replace("\n", "").replace(" ", "")
    camera_exp: str = cmds.expression(name="cameraNoise_exp", string=exp_cam)  # type: ignore
    locked_dg_nodes.append(camera_exp)

    # --------------------------------------------------------------------------
    # Shake Film
    shake_film: str = cmds.createNode(
        "transform", name="shakeFilm_C_null", parent=setup_grp
    )
    dcc.attribute.add_separator(shake_film, "shake", keyable=True)
    dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.shake")

    dcc.attribute.add_boolean(shake_film, "enableShake", keyable=True)
    dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.enableShake")

    for a in ["TX", "TY"]:
        dcc.attribute.add_boolean(shake_film, f"enable{a}", keyable=True)
        dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.enable{a}")

    for n in ["A", "B"]:
        dcc.attribute.add_separator(shake_film, f"noise{n}", keyable=True)
        dcc.attribute.add_boolean(shake_film, f"enableNoise{n}", keyable=True)
        dcc.attribute.add_float(shake_film, f"seed{n}", keyable=True)
        dcc.attribute.add_float(shake_film, f"speed{n}", keyable=True)
        dcc.attribute.add_float(shake_film, f"magnitude{n}", keyable=True)

        dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.noise{n}")
        dcc.attribute.promote_attribute(
            film_ctrl, f"{shake_film}.enableNoise{n}"
        )
        dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.seed{n}")
        dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.speed{n}")
        dcc.attribute.promote_attribute(film_ctrl, f"{shake_film}.magnitude{n}")

    exp_film: str = f"""
if({shake_film}.enableShake == true){{
    float $txA = 0.0;
    float $tyA = 0.0;
    if({shake_film}.enableNoiseA == true){{
        $txA = noise({shake_film}.seedA + time * {shake_film}.speedA) * {shake_film}.magnitudeA;
        $tyA = noise({shake_film}.seedA + time * {shake_film}.speedA + 1) * {shake_film}.magnitudeA;
    }}

    float $txB = 0.0;
    float $tyB = 0.0;
    if({shake_film}.enableNoiseB == true){{
        $txB = noise({shake_film}.seedB + time * {shake_film}.speedB + 2) * {shake_film}.magnitudeB;
        $tyB = noise({shake_film}.seedB + time * {shake_film}.speedB + 3) * {shake_film}.magnitudeB;
    }}

    {shake_film}.translateX = ($txA + $txB) * {shake_film}.enableTX;
    {shake_film}.translateY = ($tyA + $tyB) * {shake_film}.enableTY;

}}else{{
    {shake_film}.translateX = 0;
    {shake_film}.translateY = 0;
}}
""".replace("\n", "").replace(" ", "")
    film_exp: str = cmds.expression(name="filmNoise_exp", string=exp_film)  # type: ignore
    locked_dg_nodes.append(film_exp)

    # --------------------------------------------------------------------------
    # Shake Aim
    shake_aim: str = cmds.createNode(
        "transform", name="shakeAimTarget_C_null", parent=setup_grp
    )
    dcc.attribute.add_separator(shake_aim, "shake", keyable=True)
    dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.shake")

    dcc.attribute.add_boolean(shake_aim, "enableShake", keyable=True)
    dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.enableShake")

    for a in ["TX", "TY", "TZ"]:
        dcc.attribute.add_boolean(shake_aim, f"enable{a}", keyable=True)
        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.enable{a}")

    for n in ["A", "B"]:
        dcc.attribute.add_separator(shake_aim, f"noise{n}", keyable=True)
        dcc.attribute.add_boolean(shake_aim, f"enableNoise{n}", keyable=True)
        dcc.attribute.add_float(shake_aim, f"seed{n}", keyable=True)
        dcc.attribute.add_float(shake_aim, f"speed{n}", keyable=True)
        dcc.attribute.add_float(shake_aim, f"magnitude{n}", keyable=True)

        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.noise{n}")
        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.enableNoise{n}")
        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.seed{n}")
        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.speed{n}")
        dcc.attribute.promote_attribute(aim_ctrl, f"{shake_aim}.magnitude{n}")

    exp_aim: str = f"""
if({shake_aim}.enableShake == true){{
    float $txA = 0.0;
    float $tyA = 0.0;
    float $tzA = 0.0;
    if({shake_aim}.enableNoiseA == true){{
        $txA = noise({shake_aim}.seedA + (time * {shake_aim}.speedA)) * {shake_aim}.magnitudeA;
        $tyA = noise({shake_aim}.seedA + ((time + 1) * {shake_aim}.speedA)) * {shake_aim}.magnitudeA;
        $tzA = noise({shake_aim}.seedA + ((time + 2) * {shake_aim}.speedA)) * {shake_aim}.magnitudeA;
    }}

    float $txB = 0.0;
    float $tyB = 0.0;
    float $tzB = 0.0;
    if({shake_aim}.enableNoiseB == true){{
        $txB = noise({shake_aim}.seedB + ((time + 3) * {shake_aim}.speedB)) * {shake_aim}.magnitudeB;
        $tyB = noise({shake_aim}.seedB + ((time + 4) * {shake_aim}.speedB)) * {shake_aim}.magnitudeB;
        $tzB = noise({shake_aim}.seedB + ((time + 5) * {shake_aim}.speedB)) * {shake_aim}.magnitudeB;
    }}

    {shake_aim}.translateX = ($txA + $txB) * {shake_aim}.enableTX;
    {shake_aim}.translateY = ($tyA + $tyB) * {shake_aim}.enableTY;
    {shake_aim}.translateZ = ($tzA + $tzB) * {shake_aim}.enableTZ;

}}else{{
    {shake_aim}.translateX = 0;
    {shake_aim}.translateY = 0;
    {shake_aim}.translateZ = 0;
}}
""".replace("\n", "").replace(" ", "")
    aim_exp: str = cmds.expression(name="aimTargetNoise_exp", string=exp_aim)  # type: ignore
    locked_dg_nodes.append(aim_exp)

    # --------------------------------------------------------------------------
    # Guide
    grid_crv: str = dcc.curve.create_curve(
        "gridGuide_C_crv", setup_grp, dcc.curve.GRID
    )
    cmds.setAttr(f"{grid_crv}.ovdt", 2)
    cmds.setAttr(f"{grid_crv}.ove", 1)
    cmds.setAttr(f"{grid_crv}.ovc", 1)
    cmds.connectAttr(f"{settings_ctrl}.gridGuide", f"{grid_crv}.v")

    frustum_crv: str = dcc.curve.create_curve(
        "frustum_C_crv", setup_grp, dcc.curve.FRUSTUM
    )
    cmds.setAttr(f"{frustum_crv}.ovdt", 2)
    cmds.setAttr(f"{frustum_crv}.ove", 1)
    cmds.connectAttr(f"{settings_ctrl}.frustumGuide", f"{frustum_crv}.v")

    film_area_crv: str = dcc.curve.create_curve(
        "filmOffsetSliderArea_C_crv", setup_grp, dcc.curve.FILM_AREA
    )
    cmds.setAttr(f"{film_area_crv}.ovdt", 2)
    cmds.setAttr(f"{film_area_crv}.ove", 1)
    cmds.setAttr(f"{film_area_crv}.ovc", 1)
    cmds.setAttr(f"{film_area_crv}.ls", 3)

    film_offset_null: str = cmds.createNode(
        "transform", name="filmOffsetSliderOffset_C_null", parent=film_area_crv
    )
    cmds.setAttr(f"{film_offset_null}.ihi", 0)
    cmds.setAttr(f"{film_offset_null}.s", 5, 5, 5, type="double3")

    # --------------------------------------------------------------------------
    # Persp Guide
    persp_guide_grp: str = cmds.createNode(
        "transform", name="perspGuide_null", parent=setup_grp
    )
    cmds.connectAttr(
        f"{settings_ctrl}.perspGuideOffset", f"{persp_guide_grp}.ry"
    )
    cmds.connectAttr(f"{settings_ctrl}.perspGuide", f"{persp_guide_grp}.v")

    eye_level_crv: str = cmds.circle(
        name="perspGuideEyeLevel_C_crv",
        radius=1,
        normal=(0, 1, 0),
        sections=64,
        degree=3,
        constructionHistory=False,
    )[0]  # type: ignore
    cmds.setAttr(f"{eye_level_crv}.lineWidth", 4.0)
    dcc.node.set_drawing_rgb_color(rgb=[0.2, 0.7, 1.0], nodes=[eye_level_crv])
    eye_level_crv = cmds.parent(eye_level_crv, persp_guide_grp)[0]

    persp_guide_x_crv: str = dcc.curve.create_spherical_grid(
        "perspGuide", persp_guide_grp, 0, 1
    )
    cmds.connectAttr(
        f"{settings_ctrl}.perspGuideOpacity", f"{persp_guide_x_crv}.ovca"
    )

    persp_guide_y_crv: str = dcc.curve.create_spherical_grid(
        "perspGuide", persp_guide_grp, 1, 1
    )
    cmds.connectAttr(
        f"{settings_ctrl}.perspGuideOpacity", f"{persp_guide_y_crv}.ovca"
    )

    persp_guide_z_crv: str = dcc.curve.create_spherical_grid(
        "perspGuide", persp_guide_grp, 2, 1
    )
    cmds.connectAttr(
        f"{settings_ctrl}.perspGuideOpacity", f"{persp_guide_z_crv}.ovca"
    )

    # --------------------------------------------------------------------------
    # Rig Matrix
    all_rig_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}AllRigMatrix_mulMtx"
    )
    cmds.connectAttr(f"{shake_cam}.m", f"{all_rig_mtx}.i[0]")
    cmds.connectAttr(f"{cam_ctrl}.m", f"{all_rig_mtx}.i[1]")
    cmds.connectAttr(f"{body_ctrl}.m", f"{all_rig_mtx}.i[2]")
    cmds.connectAttr(f"{local_ctrl}.m", f"{all_rig_mtx}.i[3]")
    cmds.connectAttr(f"{root_ctrl}.m", f"{all_rig_mtx}.i[4]")
    locked_dg_nodes.append(all_rig_mtx)

    aim_blend_mtx: str = cmds.createNode(
        "blendMatrix", name=f"{base_name}AimBlend_blendMtx"
    )
    cmds.setAttr(f"{aim_blend_mtx}.tgt[0].sca", 0)
    cmds.setAttr(f"{aim_blend_mtx}.tgt[0].tra", 0)
    cmds.setAttr(f"{aim_blend_mtx}.tgt[0].she", 0)
    cmds.connectAttr(f"{aim_ctrl}.aim", f"{aim_blend_mtx}.tgt[0].wgt")
    cmds.connectAttr(f"{all_rig_mtx}.o", f"{aim_blend_mtx}.imat")
    locked_dg_nodes.append(aim_blend_mtx)

    all_rig_transform: str = cmds.createNode(
        "decomposeMatrix", name=f"{base_name}AllRigTransform_dcpMtx"
    )
    cmds.connectAttr(f"{all_rig_transform}.ot", f"{name}.t", force=True)
    cmds.connectAttr(f"{all_rig_transform}.or", f"{name}.r", force=True)
    cmds.connectAttr(f"{all_rig_transform}.os", f"{name}.s", force=True)
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{all_rig_transform}.imat")
    cmds.connectAttr(f"{all_rig_transform}.osh", f"{name}.sh", force=True)
    cmds.connectAttr(f"{all_rig_transform}.ot", f"{persp_guide_grp}.t")
    locked_dg_nodes.append(all_rig_transform)

    camera_aim_mtx: str = cmds.createNode(
        "aimMatrix", name=f"{base_name}Aim_aimMtx"
    )
    cmds.setAttr(f"{camera_aim_mtx}.pmi", 0, 0, -1, type="double3")
    cmds.setAttr(f"{camera_aim_mtx}.sm", 1)
    cmds.connectAttr(f"{all_rig_mtx}.o", f"{camera_aim_mtx}.imat")
    cmds.connectAttr(f"{camera_aim_mtx}.tmat", f"{aim_blend_mtx}.tgt[0].tmat")
    locked_dg_nodes.append(camera_aim_mtx)

    # --------------------------------------------------------------------------
    # Aim Parent Switch
    body_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}Body_mulMtx"
    )
    cmds.connectAttr(f"{body_ctrl}.m", f"{body_mtx}.i[0]")
    cmds.connectAttr(f"{local_ctrl}.m", f"{body_mtx}.i[1]")
    cmds.connectAttr(f"{root_ctrl}.m", f"{body_mtx}.i[2]")
    locked_dg_nodes.append(body_mtx)

    local_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}Local_mulMtx"
    )
    cmds.connectAttr(f"{local_ctrl}.m", f"{local_mtx}.i[0]")
    cmds.connectAttr(f"{root_ctrl}.m", f"{local_mtx}.i[1]")
    locked_dg_nodes.append(local_mtx)

    root_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}Root_mulMtx"
    )
    cmds.connectAttr(f"{root_ctrl}.m", f"{root_mtx}.i[0]")
    locked_dg_nodes.append(root_mtx)

    identity_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}Identity_4x4Mtx"
    )
    locked_dg_nodes.append(identity_mtx)

    aim_parent_switch: str = cmds.createNode(
        "choice", name=f"{base_name}AimParentSwitch_choice"
    )
    cmds.connectAttr(f"{aim_ctrl}.parent", f"{aim_parent_switch}.selector")
    cmds.connectAttr(f"{root_mtx}.matrixSum", f"{aim_parent_switch}.input[0]")
    cmds.connectAttr(f"{local_mtx}.matrixSum", f"{aim_parent_switch}.input[1]")
    cmds.connectAttr(f"{body_mtx}.matrixSum", f"{aim_parent_switch}.input[2]")
    cmds.connectAttr(
        f"{all_rig_mtx}.matrixSum", f"{aim_parent_switch}.input[3]"
    )
    cmds.connectAttr(f"{identity_mtx}.o", f"{aim_parent_switch}.input[4]")
    locked_dg_nodes.append(aim_parent_switch)

    # --------------------------------------------------------------------------
    # Aim Space
    aim_target_space_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}AimTargetSpace_4x4Mtx"
    )
    cmds.setAttr(f"{aim_target_space_mtx}.i32", -100)
    locked_dg_nodes.append(aim_target_space_mtx)

    aim_target_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}AimTargetOffset_mulMtx"
    )
    cmds.connectAttr(
        f"{aim_target_space_mtx}.o", f"{aim_target_offset_mtx}.i[0]"
    )
    cmds.connectAttr(
        f"{aim_parent_switch}.output", f"{aim_target_offset_mtx}.matrixIn[1]"
    )
    cmds.connectAttr(f"{aim_target_offset_mtx}.o", f"{aim_ctrl}.opm")
    locked_dg_nodes.append(aim_target_offset_mtx)

    aim_target_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}AimTarget_mulMtx"
    )
    cmds.connectAttr(f"{shake_aim}.m", f"{aim_target_mtx}.i[0]")
    cmds.connectAttr(f"{aim_ctrl}.m", f"{aim_target_mtx}.i[1]")
    cmds.connectAttr(f"{aim_target_offset_mtx}.o", f"{aim_target_mtx}.i[2]")
    cmds.connectAttr(f"{aim_target_mtx}.o", f"{camera_aim_mtx}.pmat")
    locked_dg_nodes.append(aim_target_mtx)

    aim_up_target_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}AimUpTarget_mulMtx"
    )
    cmds.connectAttr(f"{aimUp_null}.m", f"{aim_up_target_mtx}.i[0]")
    cmds.connectAttr(f"{aimUp_null}.opm", f"{aim_up_target_mtx}.i[1]")
    cmds.connectAttr(f"{aim_up_target_mtx}.o", f"{camera_aim_mtx}.smat")
    locked_dg_nodes.append(aim_up_target_mtx)

    # --------------------------------------------------------------------------
    # Film Offset
    film_offset_add: str = cmds.createNode(
        "plusMinusAverage", name=f"{base_name}FilmOffset_add"
    )
    cmds.connectAttr(f"{film_ctrl}.tx", f"{film_offset_add}.i2[0].i2x")
    cmds.connectAttr(f"{film_ctrl}.ty", f"{film_offset_add}.i2[0].i2y")
    cmds.connectAttr(f"{shake_film}.tx", f"{film_offset_add}.i2[1].i2x")
    cmds.connectAttr(f"{shake_film}.ty", f"{film_offset_add}.i2[1].i2y")
    cmds.connectAttr(
        f"{film_offset_add}.o2x", f"{camera_shape}.hfo", force=True
    )
    cmds.connectAttr(
        f"{film_offset_add}.o2y", f"{camera_shape}.vfo", force=True
    )
    locked_dg_nodes.append(film_offset_add)

    # --------------------------------------------------------------------------
    # Camera Size
    locator_scale_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}LocatorScale_mul"
    )
    cmds.setAttr(f"{locator_scale_mul}.i2", 5, 1, 1, type="float3")
    cmds.connectAttr(f"{settings_ctrl}.rigSize", f"{locator_scale_mul}.i1x")
    cmds.connectAttr(
        f"{locator_scale_mul}.ox", f"{camera_shape}.lls", force=True
    )
    locked_dg_nodes.append(locator_scale_mul)

    # --------------------------------------------------------------------------
    # Rig Size
    rig_size_mtx: str = cmds.createNode(
        "composeMatrix", name=f"{base_name}RigSize_cmpMtx"
    )
    cmds.connectAttr(f"{settings_ctrl}.rigSize", f"{rig_size_mtx}.isx")
    cmds.connectAttr(f"{settings_ctrl}.rigSize", f"{rig_size_mtx}.isy")
    cmds.connectAttr(f"{settings_ctrl}.rigSize", f"{rig_size_mtx}.isz")
    locked_dg_nodes.append(rig_size_mtx)

    shape_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}ShapeOffset_mulMtx"
    )
    cmds.connectAttr(f"{rig_size_mtx}.omat", f"{shape_offset_mtx}.i[0]")
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{shape_offset_mtx}.i[1]")
    cmds.connectAttr(
        f"{cam_ctrl}.worldInverseMatrix[0]", f"{shape_offset_mtx}.i[2]"
    )
    locked_dg_nodes.append(shape_offset_mtx)

    dcc.shape.insert_transform_geometry(root_ctrl, f"{rig_size_mtx}.omat")
    dcc.shape.insert_transform_geometry(local_ctrl, f"{rig_size_mtx}.omat")
    dcc.shape.insert_transform_geometry(body_ctrl, f"{rig_size_mtx}.omat")
    dcc.shape.insert_transform_geometry(cam_ctrl, f"{shape_offset_mtx}.o")
    dcc.shape.insert_transform_geometry(aim_ctrl, f"{rig_size_mtx}.omat")

    # --------------------------------------------------------------------------
    # Near / Far Clipping Plane
    film_slider_space_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}FilmOffsetSliderSpace_4x4Mtx"
    )
    cmds.setAttr(f"{film_slider_space_mtx}.i31", 10)
    locked_dg_nodes.append(film_slider_space_mtx)

    film_area_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}FilmAreaOffset_mulMtx"
    )
    cmds.connectAttr(
        f"{film_slider_space_mtx}.o", f"{film_area_offset_mtx}.i[0]"
    )
    cmds.connectAttr(f"{rig_size_mtx}.omat", f"{film_area_offset_mtx}.i[1]")
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{film_area_offset_mtx}.i[2]")
    cmds.connectAttr(f"{film_area_offset_mtx}.o", f"{film_area_crv}.opm")
    locked_dg_nodes.append(film_area_offset_mtx)

    film_slider_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}FilmOffsetSlider_mulMtx"
    )
    cmds.connectAttr(f"{film_offset_null}.m", f"{film_slider_mtx}.i[0]")
    cmds.connectAttr(f"{film_area_offset_mtx}.o", f"{film_slider_mtx}.i[1]")
    cmds.connectAttr(f"{film_slider_mtx}.o", f"{film_ctrl}.opm")
    locked_dg_nodes.append(film_slider_mtx)

    post_scale_ratio_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}PostScaleRatio_mul"
    )
    cmds.setAttr(f"{post_scale_ratio_mul}.op", 2)
    cmds.setAttr(f"{post_scale_ratio_mul}.i1", 1, 1, 1, type="float3")
    cmds.connectAttr(f"{camera_shape}.ptsc", f"{post_scale_ratio_mul}.i2x")
    cmds.connectAttr(f"{camera_shape}.ptsc", f"{post_scale_ratio_mul}.i2y")
    locked_dg_nodes.append(post_scale_ratio_mul)

    post_scale_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}PostScale_4x4Mtx"
    )
    cmds.connectAttr(f"{post_scale_ratio_mul}.ox", f"{post_scale_mtx}.i00")
    cmds.connectAttr(f"{post_scale_ratio_mul}.oy", f"{post_scale_mtx}.i11")
    locked_dg_nodes.append(post_scale_mtx)

    aperture_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}Aperture_mul"
    )
    cmds.setAttr(f"{aperture_mul}.i2", 25.4, 25.4, 1, type="float3")
    cmds.connectAttr(f"{camera_shape}.hfa", f"{aperture_mul}.i1x")
    cmds.connectAttr(f"{camera_shape}.vfa", f"{aperture_mul}.i1y")
    locked_dg_nodes.append(aperture_mul)

    film_offset_rate_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}FilmOffsetRate_mul"
    )
    cmds.setAttr(f"{film_offset_rate_mul}.op", 2)
    cmds.connectAttr(f"{camera_shape}.hfo", f"{film_offset_rate_mul}.i1x")
    cmds.connectAttr(f"{camera_shape}.vfo", f"{film_offset_rate_mul}.i1y")
    cmds.connectAttr(f"{camera_shape}.vfa", f"{film_offset_rate_mul}.i2y")
    cmds.connectAttr(f"{camera_shape}.hfa", f"{film_offset_rate_mul}.i2x")
    locked_dg_nodes.append(film_offset_rate_mul)

    aperture_rate_div: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}ApertureRate_div"
    )
    cmds.setAttr(f"{aperture_rate_div}.op", 2)
    cmds.connectAttr(f"{aperture_mul}.ox", f"{aperture_rate_div}.i1x")
    cmds.connectAttr(f"{aperture_mul}.oy", f"{aperture_rate_div}.i1y")
    cmds.connectAttr(f"{camera_shape}.fl", f"{aperture_rate_div}.i2x")
    cmds.connectAttr(f"{camera_shape}.fl", f"{aperture_rate_div}.i2y")
    locked_dg_nodes.append(aperture_rate_div)

    near_dist_scale_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}NearDistanceScale_mul"
    )
    cmds.connectAttr(f"{aperture_rate_div}.ox", f"{near_dist_scale_mul}.i1x")
    cmds.connectAttr(f"{aperture_rate_div}.oy", f"{near_dist_scale_mul}.i1y")
    cmds.connectAttr(f"{camera_shape}.ncp", f"{near_dist_scale_mul}.i2x")
    cmds.connectAttr(f"{camera_shape}.ncp", f"{near_dist_scale_mul}.i2y")
    locked_dg_nodes.append(near_dist_scale_mul)

    near_film_offset_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}NearFilmOffset_mul"
    )
    cmds.connectAttr(f"{near_dist_scale_mul}.ox", f"{near_film_offset_mul}.i1x")
    cmds.connectAttr(f"{near_dist_scale_mul}.oy", f"{near_film_offset_mul}.i1y")
    cmds.connectAttr(
        f"{film_offset_rate_mul}.oy", f"{near_film_offset_mul}.i2y"
    )
    cmds.connectAttr(
        f"{film_offset_rate_mul}.ox", f"{near_film_offset_mul}.i2x"
    )
    locked_dg_nodes.append(near_film_offset_mul)

    film_aspect_div: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}FilmAspectRatio_div"
    )
    cmds.setAttr(f"{film_aspect_div}.op", 2)
    cmds.connectAttr(f"{camera_shape}.hfa", f"{film_aspect_div}.i1x")
    cmds.connectAttr(f"{camera_shape}.vfa", f"{film_aspect_div}.i2x")
    locked_dg_nodes.append(film_aspect_div)

    horiz_res_gate_ratio_div: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}HorizontaResolutionGateRatio_div"
    )
    cmds.setAttr(f"{horiz_res_gate_ratio_div}.op", 2)
    cmds.connectAttr(f"{film_aspect_div}.ox", f"{horiz_res_gate_ratio_div}.i1x")
    cmds.connectAttr("defaultResolution.dar", f"{horiz_res_gate_ratio_div}.i2x")
    locked_dg_nodes.append(horiz_res_gate_ratio_div)

    near_fit_res_gate_mul: str = cmds.createNode(
        "multiplyDivide", name="nearFitResolutionGate_mul"
    )
    cmds.connectAttr(f"{near_dist_scale_mul}.o", f"{near_fit_res_gate_mul}.i1")
    cmds.connectAttr(
        f"{horiz_res_gate_ratio_div}.ox", f"{near_fit_res_gate_mul}.i2y"
    )
    locked_dg_nodes.append(near_fit_res_gate_mul)

    near_clip_offset_mtx: str = cmds.createNode(
        "composeMatrix", name=f"{base_name}NearClipPlaneOffset_cmpMtx"
    )
    cmds.connectAttr(
        f"{near_film_offset_mul}.ox", f"{near_clip_offset_mtx}.itx"
    )
    cmds.connectAttr(
        f"{near_film_offset_mul}.oy", f"{near_clip_offset_mtx}.ity"
    )
    cmds.connectAttr(
        f"{near_fit_res_gate_mul}.ox", f"{near_clip_offset_mtx}.isx"
    )
    cmds.connectAttr(
        f"{near_fit_res_gate_mul}.oy", f"{near_clip_offset_mtx}.isy"
    )
    locked_dg_nodes.append(near_clip_offset_mtx)

    clipping_space_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}ClippingOffset_4x4Mtx"
    )
    cmds.setAttr(f"{clipping_space_mtx}.i22", -1)
    locked_dg_nodes.append(clipping_space_mtx)

    near_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}NearClipPlaneOffset_mulMtx"
    )
    cmds.connectAttr(f"{post_scale_mtx}.o", f"{near_offset_mtx}.i[0]")
    cmds.connectAttr(f"{near_clip_offset_mtx}.omat", f"{near_offset_mtx}.i[1]")
    cmds.connectAttr(f"{clipping_space_mtx}.o", f"{near_offset_mtx}.i[2]")
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{near_offset_mtx}.i[3]")
    cmds.connectAttr(f"{near_offset_mtx}.o", f"{near_ctrl}.opm")
    locked_dg_nodes.append(near_offset_mtx)

    far_dist_scale_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}FarDistanceScale_mul"
    )
    cmds.connectAttr(f"{aperture_rate_div}.ox", f"{far_dist_scale_mul}.i1x")
    cmds.connectAttr(f"{aperture_rate_div}.oy", f"{far_dist_scale_mul}.i1y")
    cmds.connectAttr(f"{camera_shape}.fcp", f"{far_dist_scale_mul}.i2x")
    cmds.connectAttr(f"{camera_shape}.fcp", f"{far_dist_scale_mul}.i2y")
    locked_dg_nodes.append(far_dist_scale_mul)

    far_film_offset_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}FarFilmOffset_mul"
    )
    cmds.connectAttr(f"{far_dist_scale_mul}.ox", f"{far_film_offset_mul}.i1x")
    cmds.connectAttr(f"{far_dist_scale_mul}.oy", f"{far_film_offset_mul}.i1y")
    cmds.connectAttr(f"{film_offset_rate_mul}.oy", f"{far_film_offset_mul}.i2y")
    cmds.connectAttr(f"{film_offset_rate_mul}.ox", f"{far_film_offset_mul}.i2x")
    locked_dg_nodes.append(far_film_offset_mul)

    far_fit_res_gate_mul: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}FarFitResolutionGate_mul"
    )
    cmds.connectAttr(f"{far_dist_scale_mul}.o", f"{far_fit_res_gate_mul}.i1")
    cmds.connectAttr(
        f"{horiz_res_gate_ratio_div}.ox", f"{far_fit_res_gate_mul}.i2y"
    )
    locked_dg_nodes.append(far_fit_res_gate_mul)

    far_clip_offset_mtx: str = cmds.createNode(
        "composeMatrix", name=f"{base_name}FarClipPlaneOffset_cmpMtx"
    )
    cmds.connectAttr(f"{far_film_offset_mul}.ox", f"{far_clip_offset_mtx}.itx")
    cmds.connectAttr(f"{far_film_offset_mul}.oy", f"{far_clip_offset_mtx}.ity")
    cmds.connectAttr(f"{far_fit_res_gate_mul}.ox", f"{far_clip_offset_mtx}.isx")
    cmds.connectAttr(f"{far_fit_res_gate_mul}.oy", f"{far_clip_offset_mtx}.isy")
    locked_dg_nodes.append(far_clip_offset_mtx)

    far_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}FarClipPlaneOffset_mulMtx"
    )
    cmds.connectAttr(f"{post_scale_mtx}.o", f"{far_offset_mtx}.i[0]")
    cmds.connectAttr(f"{far_clip_offset_mtx}.omat", f"{far_offset_mtx}.i[1]")
    cmds.connectAttr(f"{clipping_space_mtx}.o", f"{far_offset_mtx}.i[2]")
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{far_offset_mtx}.i[3]")
    cmds.connectAttr(f"{far_offset_mtx}.o", f"{far_ctrl}.opm")
    locked_dg_nodes.append(far_offset_mtx)

    # --------------------------------------------------------------------------
    # Space
    setting_space_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}SettingSpace_mulMtx"
    )
    cmds.connectAttr(f"{rig_size_mtx}.omat", f"{setting_space_mtx}.i[0]")
    cmds.connectAttr(f"{aim_blend_mtx}.omat", f"{setting_space_mtx}.i[1]")
    cmds.connectAttr(f"{setting_space_mtx}.o", f"{settings_ctrl}.opm")
    locked_dg_nodes.append(setting_space_mtx)

    aim_up_space_mtx: str = cmds.createNode(
        "fourByFourMatrix", name=f"{base_name}AimUpTargetSpace_4x4Mtx"
    )
    cmds.setAttr(f"{aim_up_space_mtx}.i31", 50)
    locked_dg_nodes.append(aim_up_space_mtx)

    aim_up_roll_mtx: str = cmds.createNode(
        "composeMatrix", name=f"{base_name}AimUpTargetRoll_cmpMtx"
    )
    cmds.connectAttr(f"{aim_ctrl}.roll", f"{aim_up_roll_mtx}.irz")
    locked_dg_nodes.append(aim_up_roll_mtx)

    aim_up_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}AimUpTargetOffset_mulMtx"
    )
    cmds.connectAttr(f"{aim_up_space_mtx}.o", f"{aim_up_offset_mtx}.i[0]")
    cmds.connectAttr(f"{aim_up_roll_mtx}.omat", f"{aim_up_offset_mtx}.i[1]")
    cmds.connectAttr(f"{all_rig_mtx}.o", f"{aim_up_offset_mtx}.i[2]")
    cmds.connectAttr(f"{aim_up_offset_mtx}.o", f"{aimUp_null}.opm")
    locked_dg_nodes.append(aim_up_offset_mtx)

    grid_offset_mtx: str = cmds.createNode(
        "multMatrix", name=f"{base_name}GridOffset_mulMtx"
    )
    cmds.connectAttr(f"{near_ctrl}.m", f"{grid_offset_mtx}.i[0]")
    cmds.connectAttr(f"{near_offset_mtx}.o", f"{grid_offset_mtx}.i[1]")
    cmds.connectAttr(f"{grid_offset_mtx}.o", f"{grid_crv}.opm")
    locked_dg_nodes.append(grid_offset_mtx)

    # --------------------------------------------------------------------------
    # Persp Guide Space
    clip_plane_dist_add: str = cmds.createNode(
        "addDoubleLinear", name=f"{base_name}ClipPlaneDist_add"
    )
    cmds.connectAttr(f"{camera_shape}.ncp", f"{clip_plane_dist_add}.i1")
    cmds.connectAttr(f"{camera_shape}.fcp", f"{clip_plane_dist_add}.i2")
    locked_dg_nodes.append(clip_plane_dist_add)

    half_clip_plane_dist_num: str = cmds.createNode(
        "multiplyDivide", name=f"{base_name}HalfClipPlaneDist_mul"
    )
    cmds.setAttr(f"{half_clip_plane_dist_num}.i2", 0.5, 0.5, 0.5, type="float3")
    cmds.connectAttr(
        f"{clip_plane_dist_add}.o", f"{half_clip_plane_dist_num}.i1x"
    )
    cmds.connectAttr(
        f"{clip_plane_dist_add}.o", f"{half_clip_plane_dist_num}.i1y"
    )
    cmds.connectAttr(
        f"{clip_plane_dist_add}.o", f"{half_clip_plane_dist_num}.i1z"
    )
    cmds.connectAttr(f"{half_clip_plane_dist_num}.o", f"{persp_guide_grp}.s")
    locked_dg_nodes.append(half_clip_plane_dist_num)

    # --------------------------------------------------------------------------
    # Frustum
    clips: list[tuple[str, str, int]] = [
        (near_ctrl, "A", 0),
        (far_ctrl, "B", 1),
    ]
    frustum_shapes: list[str] = cmds.listRelatives(
        frustum_crv, shapes=True, path=True
    )
    for i, letter in enumerate(["A", "B", "C", "D"]):
        for clip, suffix, index in clips:
            point_info: str = cmds.createNode(
                "pointOnCurveInfo",
                name=f"{base_name}Frustum{letter}{suffix}_pointInfo",
            )
            clip_shape: str = cmds.listRelatives(clip, shapes=True, path=True)[
                0
            ]
            cmds.setAttr(f"{point_info}.pr", i)
            cmds.connectAttr(f"{clip_shape}.ws", f"{point_info}.ic")
            cmds.connectAttr(
                f"{point_info}.p", f"{frustum_shapes[i]}.cp[{index}]"
            )
            locked_dg_nodes.append(point_info)

    # --------------------------------------------------------------------------
    # Hide History
    hide_history_ctrls: list[str] = [
        root_ctrl,
        local_ctrl,
        body_ctrl,
        cam_ctrl,
        film_ctrl,
        film_area_crv,
        film_offset_null,
        aim_ctrl,
        near_ctrl,
        far_ctrl,
        settings_ctrl,
        grid_crv,
        frustum_crv,
        eye_level_crv,
        persp_guide_x_crv,
        persp_guide_y_crv,
        persp_guide_z_crv,
    ]
    for node in hide_history_ctrls:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        target: list[str] = [node] + shapes
        dcc.node.hide_history(target)

    dcc.node.hide_history(locked_dg_nodes)

    # --------------------------------------------------------------------------
    # Lock Attributs
    all_lock_ctrls: list[str] = [
        camera_grp,
        ctrl_grp,
        setup_grp,
        aimUp_null,
        shake_cam,
        shake_film,
        shake_aim,
        grid_crv,
        frustum_crv,
        film_area_crv,
        film_offset_null,
        persp_guide_grp,
        eye_level_crv,
        persp_guide_x_crv,
        persp_guide_y_crv,
        persp_guide_z_crv,
        settings_ctrl,
    ]
    dcc.attribute.lock_and_hide(all_lock_ctrls, True, True, True, True)

    scale_lock_ctrls: list[str] = [root_ctrl, local_ctrl, body_ctrl, cam_ctrl]
    dcc.attribute.lock_and_hide(scale_lock_ctrls, False, False, True, True)

    dcc.attribute.lock_and_hide([aim_ctrl], False, True, True, True)

    for attr in ["tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
        cmds.setAttr(f"{film_ctrl}.{attr}", lock=True, keyable=False)

    for node in [near_ctrl, far_ctrl]:
        for attr in ["tx", "ty", "rx", "ry", "rz", "sx", "sy", "sz", "v"]:
            cmds.setAttr(f"{node}.{attr}", lock=True, keyable=False)

    dcc.attribute.lock_all_attributes(locked_dg_nodes)

    return name


def main(name: str = "render_cam") -> str:
    """Executes the camera rig creation process.

    Returns:
        str: The name of the created camera node.
    """
    camera: str = apply(name)
    _logger.info("Done.")
    return camera
