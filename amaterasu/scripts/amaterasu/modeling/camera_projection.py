# ==============================================================================
#
# Camera Projection
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Camera Projection'
__version__: str = '1.21'
__doc__ = 'Creates UV for the selected object based on the current camera view as a planar projection.'
__copyright__ = 'Copyright(c) 2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


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
def get_current_camera() -> str:
    '''Return currently active viewport camera.'''
    camera: str = 'persp'
    ignore_camera: tuple[str, str, str, str] = ('top', 'side', 'front', 'persp')
    for panel in cmds.getPanel(type='modelPanel'):
        camera = cmds.modelEditor(
            panel, query=True, activeView=True, camera=True
        )
        camera = cmds.ls(camera)[0]
        if camera not in ignore_camera:
            break
    return camera


def create_guide_plane(camera: str, z: float = 1.0) -> str:
    '''Create a plane that coincides with the resolution gate.'''
    focal_length: float = cmds.getAttr(f'{camera}.focalLength')
    film_offset_h: float = cmds.getAttr(f'{camera}.horizontalFilmOffset')
    film_offset_v: float = cmds.getAttr(f'{camera}.verticalFilmOffset')
    film_aperture_h: float = cmds.getAttr(f'{camera}.horizontalFilmAperture')
    film_aperture_v: float = cmds.getAttr(f'{camera}.verticalFilmAperture')
    aspect_ratio: float = cmds.getAttr('defaultResolution.deviceAspectRatio')

    # 25.4 is mm to inch
    ratio_v: float = film_aperture_h / film_aperture_v / aspect_ratio
    distance_scale_h: float = film_aperture_h * 25.4 / focal_length * z
    distance_scale_v: float = film_aperture_v * 25.4 / focal_length * z

    trans_x: float = distance_scale_h * (film_offset_h / film_aperture_h)
    trans_y: float = distance_scale_v * (film_offset_v / film_aperture_v)
    scale_x: float = distance_scale_h
    scale_y: float = distance_scale_v * ratio_v
    film_fit: int = cmds.getAttr(f'{camera}.filmFit')
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

    camera_scale: float = cmds.getAttr(f'{camera}.cameraScale')
    pre_scale: float = 1.0 / cmds.getAttr(f'{camera}.preScale')
    post_scale: float = 1.0 / cmds.getAttr(f'{camera}.postScale')
    plane: str = cmds.polyPlane(
        width=1.0 * pre_scale * post_scale * camera_scale,
        height=1.0 * pre_scale * post_scale * camera_scale,
        subdivisionsX=1,
        subdivisionsY=1,
        axis=(0, 0, 1),
        createUVs=2,
        constructionHistory=True,
    )[0]

    plane = cmds.parent(plane, camera)[0]
    cmds.setAttr(f'{plane}.t', trans_x, trans_y, z * -1, type='double3')
    cmds.setAttr(f'{plane}.r', 0, 0, 0, type='double3')
    cmds.setAttr(f'{plane}.s', scale_x, scale_y, 1, type='double3')

    plane = cmds.parent(plane, world=True)[0]
    return plane


def apply(node: str, camera: str, z: float = 1.0) -> bool:
    '''Creates UV for the current camera view as a planar projection.'''
    shapes: list[str] = cmds.listRelatives(node, shapes=True, fullPath=True)
    if not shapes:
        logging.warning('Does not exists shape : %s', node)
        return False

    if cmds.objectType(shapes[0]) != 'mesh':
        logging.warning('Does not exists mesh : %s', node)
        return False

    parent: list[str] = (
        cmds.listRelatives(node, parent=True, fullPath=True) or []
    )

    # Deal with fact that parent is not deleted when combining.
    is_parent_lock: bool = False
    if parent:
        is_parent_lock = cmds.lockNode(parent[0], query=True, lock=True)[0]
        cmds.lockNode(parent[0], lock=True)

    plane: str = create_guide_plane(camera, z)

    combined_node: str = cmds.polyUnite(
        (plane, node),
        mergeUVSets=1,
        centerPivot=True,
        constructionHistory=False,
    )[0]

    # Remove trash during the combine.
    cmds.delete(combined_node, constructionHistory=True)
    if cmds.objExists(node):
        cmds.delete(node)

    node = cmds.rename(combined_node, node.split('|')[-1])
    cmds.polyProjection(f'{node}.f[*]', type='Planar', mapDirection='p')

    start_uv: list[float] = cmds.polyEditUV(f'{node}.map[0]', query=True)
    cmds.polyEditUV(
        f'{node}.map[*]',
        uValue=start_uv[0] * -1,
        vValue=start_uv[1] * -1,
    )

    end_uv: list[float] = cmds.polyEditUV(f'{node}.map[2]', query=True)
    cmds.polyEditUV(
        f'{node}.map[*]',
        pivotU=0.0,
        pivotV=0.0,
        scaleU=1.0 / end_uv[0],
        scaleV=1.0 / end_uv[1],
    )
    cmds.delete(f'{node}.f[0]')
    cmds.delete(node, constructionHistory=True)

    if parent:
        cmds.parent(node, parent[0])
        if not is_parent_lock:
            cmds.lockNode(parent[0], lock=False)

    return True


def main() -> None:
    '''Creates UV for the selected object.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select polygons to create uv.')
        return

    camera: str = get_current_camera()
    for node in selection:
        apply(node, camera, 1.0)

    cmds.select(*selection)
    _logger.info('Done. : Camera = %s', camera)
