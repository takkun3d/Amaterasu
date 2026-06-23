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
"""Provides utilities for interacting with Maya's 3D viewports and cameras."""

from __future__ import annotations
from maya import cmds, OpenMaya, OpenMayaUI, OpenMayaRender


def displayed_nodes() -> list[str]:
    """Selects nodes that are currently visible within the active 3D view.

    This function calculates the screen-space bounding box of the camera's
    frustum and uses OpenMaya to select nodes within that area.

    Returns:
        list[str]: A list of nodes visible in the active viewport.
    """
    active_view: OpenMayaUI.M3dView = OpenMayaUI.M3dView.active3dView()
    port_width: int = active_view.portWidth()
    port_height: int = active_view.portHeight()

    camera_path: OpenMaya.MDagPath = OpenMaya.MDagPath()
    active_view.getCamera(camera_path)
    camera = OpenMaya.MFnCamera(camera_path)

    render_settings = OpenMayaRender.MCommonRenderSettingsData()
    OpenMayaRender.MRenderUtil.getCommonRenderSettings(render_settings)
    overscan: float = camera.overscan()
    hfa: float = render_settings.deviceAspectRatio
    vfa: float = render_settings.pixelAspectRatio

    aspect_ratio: float = hfa / vfa

    port_aspect_ratio: float = float(port_width) / float(port_height)
    port_horiz: bool = port_aspect_ratio > aspect_ratio

    film_fit: OpenMaya.MFnCamera.FilmFit = camera.filmFit()
    if film_fit == OpenMaya.MFnCamera.kFillFilmFit:
        film_fit = (
            OpenMaya.MFnCamera.kHorizontalFilmFit
            if port_horiz
            else OpenMaya.MFnCamera.kVerticalFilmFit
        )

    if film_fit == OpenMaya.MFnCamera.kOverscanFilmFit:
        film_fit = (
            OpenMaya.MFnCamera.kVerticalFilmFit
            if port_horiz
            else OpenMaya.MFnCamera.kHorizontalFilmFit
        )

    x: float = 0.0
    y: float = 0.0
    if film_fit in (
        OpenMaya.MFnCamera.kHorizontalFilmFit,
        OpenMaya.MFnCamera.kInvalid,
    ):
        x = port_width / overscan
        y = x / aspect_ratio

    else:
        y = port_height / overscan
        x = y * aspect_ratio

    x *= camera.lensSqueezeRatio()
    x1: int = int((port_width / 2.0) - (x / 2.0))
    y1: int = int((port_height / 2.0) - (y / 2.0))

    x2: int = int((port_width / 2.0) + (x / 2.0))
    y2: int = int((port_height / 2.0) + (y / 2.0))

    old_sel: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList(old_sel)

    current_selection_mode: OpenMaya.MGlobal.MSelectionMode = (
        OpenMaya.MGlobal.selectionMode()
    )
    OpenMaya.MGlobal.setSelectionMode(OpenMaya.MGlobal.kSelectLeafMode)
    OpenMaya.MGlobal.selectFromScreen(
        x1, y1, x2, y2, OpenMaya.MGlobal.kReplaceList
    )

    nodes: list[str] = cmds.ls(selection=True)
    OpenMaya.MGlobal.setSelectionMode(current_selection_mode)
    OpenMaya.MGlobal.setActiveSelectionList(old_sel)
    return nodes


def get_current_viewport_engine() -> str:
    """Determines the current Maya Viewport 2.0 rendering engine.

    Returns:
        str: "HLSL" if the viewport uses DirectX, otherwise "GLSL".
    """
    engine: str = cmds.optionVar(query="vp2RenderingEngine")  # type: ignore
    return "HLSL" if "DirectX" in engine else "GLSL"
