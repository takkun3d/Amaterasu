# ==============================================================================
#
# Camera Rig
#
# ==============================================================================
from __future__ import annotations
import logging
import os
from maya import cmds
import amaterasu

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Camera Rig'
__version__: str = '1.30'
__doc__ = 'Camera rig.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
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
def main() -> None:
    '''Import camera rig data.'''

    # TODO: Create camera rig by script.
    cmds.file(
        os.path.join(amaterasu.RESOURCE_PATH, 'rig', 'camera_rig_v03.ma'),
        i=True,
        type='mayaAscii',
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        renamingPrefix='CameraRig',
        options='v=0;',
        preserveReferences=True,
    )
