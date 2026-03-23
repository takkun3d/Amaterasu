# ==============================================================================
#
# Select Displayed Nodes
#
# ==============================================================================
from __future__ import annotations
from maya import OpenMaya, OpenMayaUI, OpenMayaRender
from ..lib import logger

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Displayed Nodes'
__version__: str = '1.00'
__doc__ = 'Select displayed nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main() -> None:
    '''Dot it.'''
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
    non_padded_aspect_ratio: float = aspect_ratio

    port_aspect_ratio: float = float(port_width) / float(port_height)
    port_horiz: bool = port_aspect_ratio > aspect_ratio

    film_fit: OpenMaya.MFnCamera.FilmFit = camera.filmFit()
    if film_fit == OpenMaya.MFnCamera.kFillFilmFit:
        if port_horiz:
            film_fit = OpenMaya.MFnCamera.kHorizontalFilmFit
        else:
            film_fit = OpenMaya.MFnCamera.kVerticalFilmFit

    if film_fit == OpenMaya.MFnCamera.kOverscanFilmFit:
        if port_horiz:
            film_fit = OpenMaya.MFnCamera.kVerticalFilmFit
        else:
            film_fit = OpenMaya.MFnCamera.kHorizontalFilmFit

    x: float = 0
    y: float = 0
    if film_fit in (
        OpenMaya.MFnCamera.kHorizontalFilmFit,
        OpenMaya.MFnCamera.kInvalid,
    ):
        x = port_width / overscan
        y = x / non_padded_aspect_ratio
    else:
        y = port_height / overscan
        x = y * non_padded_aspect_ratio

    x *= camera.lensSqueezeRatio()
    x1: int = int((port_width / 2.0) - (x / 2.0))
    y1: int = int((port_height / 2.0) - (y / 2.0))

    x2: int = int((port_width / 2.0) + (x / 2.0))
    y2: int = int((port_height / 2.0) + (y / 2.0))

    current_celection_mode: OpenMaya.MGlobal.MSelectionMode = (
        OpenMaya.MGlobal.selectionMode()
    )
    OpenMaya.MGlobal.setSelectionMode(OpenMaya.MGlobal.kSelectLeafMode)

    OpenMaya.MGlobal.selectFromScreen(
        x1, y1, x2, y2, OpenMaya.MGlobal.kReplaceList
    )
    OpenMaya.MGlobal.setSelectionMode(current_celection_mode)
    _logger.info('Done.')
