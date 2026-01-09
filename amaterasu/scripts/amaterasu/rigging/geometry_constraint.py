# ==============================================================================
#
# Geometry Constraint
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
__product__: str = 'Geometry Constraint'
__version__: str = '1.11'
__doc__ = 'Create geometry constraint rig.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
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
def apply(
    geometry: str,
    markers: list[str],
    parent: str = 'geometryConstraint_grp',
    mode: int = 1,
) -> bool:
    '''
    Create geometry constraint rig.
    mode: 1=parentConstraint, 2=pointConstraint
    '''
    geo_shapes: list[str] = (
        cmds.listRelatives(geometry, shapes=True, path=True) or []
    )
    if not geo_shapes:
        _logger.error('Failed to get shape from destination node.')
        return False

    geo_shape: str = geo_shapes[0]
    shape_type: str = cmds.objectType(geo_shape)
    if shape_type not in ('mesh', 'nurbsSurface'):
        _logger.error('Destination node is not supported.')
        return False

    if not cmds.objExists(parent):
        parent = cmds.createNode('transform', name=parent)

    for marker in markers:
        position: list[float] = cmds.xform(
            marker, query=True, worldSpace=True, pivots=True
        )
        closestPoint: str = ''
        if shape_type == 'mesh':
            closestPoint = cmds.createNode('closestPointOnMesh')
            cmds.connectAttr(f'{geo_shape}.worldMesh', f'{closestPoint}.im')
            cmds.connectAttr(f'{geometry}.worldMatrix[0]', f'{closestPoint}.ix')

        else:
            closestPoint = cmds.createNode('closestPointOnSurface')
            cmds.connectAttr(f'{geo_shape}.worldSpace', f'{closestPoint}.is')

        lenght_uv: list[float] = [1.0, 1.0]
        if shape_type == 'nurbsSurface':
            min_u, max_u = cmds.getAttr(f'{geo_shape}.minMaxRangeU')[0]
            min_v, max_v = cmds.getAttr(f'{geo_shape}.minMaxRangeV')[0]
            lenght_uv = [(max_u - min_u), (max_v - min_v)]

        cmds.setAttr(f'{closestPoint}.ip', *position[:3])
        u: float = cmds.getAttr(f'{closestPoint}.u')
        v: float = cmds.getAttr(f'{closestPoint}.v')
        cmds.delete(closestPoint)

        follicle_transform: str = cmds.createNode(
            'transform', name=f'{marker}_follicle'
        )
        cmds.setAttr(f'{follicle_transform}.v', False)

        follicle_shape: str = cmds.createNode(
            'follicle',
            name=f'{marker}_follicleShape',
            parent=follicle_transform,
        )
        cmds.setAttr(f'{follicle_shape}.pu', (u / lenght_uv[0]))
        cmds.setAttr(f'{follicle_shape}.pv', (v / lenght_uv[1]))

        if shape_type == 'mesh':
            cmds.connectAttr(f'{geo_shape}.outMesh', f'{follicle_shape}.inm')

        else:
            cmds.connectAttr(f'{geo_shape}.local', f'{follicle_shape}.is')

        cmds.connectAttr(f'{geometry}.worldMatrix[0]', f'{follicle_shape}.iwm')
        cmds.connectAttr(f'{follicle_shape}.otx', f'{follicle_transform}.tx')
        cmds.connectAttr(f'{follicle_shape}.oty', f'{follicle_transform}.ty')
        cmds.connectAttr(f'{follicle_shape}.otz', f'{follicle_transform}.tz')
        cmds.connectAttr(f'{follicle_shape}.orx', f'{follicle_transform}.rx')
        cmds.connectAttr(f'{follicle_shape}.ory', f'{follicle_transform}.ry')
        cmds.connectAttr(f'{follicle_shape}.orz', f'{follicle_transform}.rz')

        if not cmds.attributeQuery('paramU', node=marker, exists=True):
            cmds.addAttr(
                marker,
                longName='paramU',
                attributeType='double',
                defaultValue=1,
            )
            cmds.setAttr(f'{marker}.paramU', edit=True, keyable=True)

        cmds.setAttr(f'{marker}.paramU', u)
        cmds.connectAttr(f'{marker}.paramU', f'{follicle_shape}.pu')

        if not cmds.attributeQuery('paramV', node=marker, exists=True):
            cmds.addAttr(
                marker,
                longName='paramV',
                attributeType='double',
                defaultValue=1,
            )
            cmds.setAttr(f'{marker}.paramV', edit=True, keyable=True)

        cmds.setAttr(f'{marker}.paramV', v)
        cmds.connectAttr(f'{marker}.paramV', f'{follicle_shape}.pv')

        if mode == 1:
            cmds.parentConstraint(
                follicle_transform, marker, maintainOffset=True
            )
        else:
            cmds.pointConstraint(
                follicle_transform, marker, maintainOffset=True
            )

        cmds.parent(follicle_transform, parent)

    return True


def main() -> None:
    '''Apply from selection.'''
    selection = cmds.ls(selection=True, type='transform')
    if not selection or len(selection) < 2:
        _logger.error('Select source nodes and destination nodes to rivet.')
        return

    result = apply(selection[-1], selection[:-1])
    if result:
        _logger.info('Done')
