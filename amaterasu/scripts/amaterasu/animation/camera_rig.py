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
"""Imports and sets up the standard camera rig for the current scene."""

from __future__ import annotations
import os
from maya import cmds
from amaterasu import env
from amaterasu.base import utils

__product__: str = "Camera Rig"
__version__: str = "1.32"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> str:
    """Imports the camera rig data from the resource path into the scene.

    TODO:
        Create the camera rig procedurally via script instead of
        importing a Maya ASCII file.

    Returns:
        str: The full path name of the imported camera transform node.
            Returns an empty string if the import process fails.
    """
    new_nodes: list[str] = cmds.file(
        os.path.join(env.RESOURCE_PATH, "rig", "camera_rig.ma"),
        i=True,
        type="mayaAscii",
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        renamingPrefix="CameraRig",
        options="v=0;",
        preserveReferences=True,
        returnNewNodes=True,
    )  # type: ignore

    if not new_nodes:
        _logger.warning("Failed to import the camera rig file.")
        return ""

    new_cam_shapes: list[str] = cmds.ls(*new_nodes, type="camera")
    if not new_cam_shapes:
        _logger.warning("No camera shapes found in the imported nodes.")
        return ""

    new_cam_transforms: list[str] = cmds.listRelatives(
        new_cam_shapes[0], parent=True, fullPath=True
    )
    if not new_cam_transforms:
        _logger.warning("Could not find the transform node for the camera.")
        return ""

    return new_cam_transforms[0]
