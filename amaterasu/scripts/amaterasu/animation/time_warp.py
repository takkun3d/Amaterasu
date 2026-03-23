# ==============================================================================
#
# Time Warp
#
# ==============================================================================
from __future__ import annotations
from maya import cmds
from ..lib import logger, utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Time Warp'
__version__: str = '1.20'
__doc__ = 'Set up a time warp for the animation of the selected node.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

ATTR_NAME: str = 'frame'


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
def apply(nodes: list[str]) -> None:
    '''Set up a time warp for the animation.'''

    controller: str = cmds.sets(nodes, name='time_warp#')
    cmds.addAttr(controller, longName=ATTR_NAME, attributeType='time')

    plug: str = f'{controller}.{ATTR_NAME}'
    cmds.setAttr(plug, edit=True, keyable=True)

    start_frame: float = cmds.playbackOptions(
        query=True, animationStartTime=True
    )
    end_frame: float = cmds.playbackOptions(query=True, animationEndTime=True)

    cmds.setKeyframe(
        plug,
        time=start_frame,
        value=start_frame,
        inTangentType='linear',
        outTangentType='linear',
    )
    cmds.setKeyframe(
        plug,
        time=end_frame,
        value=end_frame,
        inTangentType='linear',
        outTangentType='linear',
    )

    for node in nodes:
        attrs: list[str] = cmds.listAttr(node, keyable=True)
        if not attrs:
            continue

        for attr in attrs:
            connection: str = utility.get_anim_curve(node, attr)
            if connection:
                cmds.connectAttr(plug, f'{connection}.input', force=True)


def main() -> None:
    '''Do it.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node to setup time wrap.')
        return

    apply(selection)
    _logger.info('Done.')
