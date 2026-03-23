# ==============================================================================
#
# Camera Rig
#
# ==============================================================================
from __future__ import annotations
import os
from maya import cmds
from ..lib import logger
import amaterasu

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Camera Rig'
__version__: str = '1.31'
__doc__ = 'Camera rig.'
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
def main() -> str:
    '''Import camera rig data.'''

    # TODO: Create camera rig by script.
    new_nodes: list[str] = cmds.file(
        os.path.join(amaterasu.RESOURCE_PATH, 'rig', 'camera_rig.ma'),
        i=True,
        type='mayaAscii',
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        renamingPrefix='CameraRig',
        options='v=0;',
        preserveReferences=True,
        returnNewNodes=True,
    )  # type: ignore
    new_cam_shapes: list[str] = cmds.ls(*new_nodes, type='camera')
    new_cam: list[str] = cmds.listRelatives(
        new_cam_shapes[0], parent=True, fullPath=True
    )
    return new_cam[0]
