# ==============================================================================
#
# Setup Noice
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide2.QtWidgets import QMessageBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtWidgets import QMessageBox

from maya import cmds
from mtoa import core, aovs
from mtoa.ui import aoveditor
from ..lib import logger, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Setup Noice'
__version__: str = '1.10'
__doc__ = 'Sets up Arnold render settings for Noice denoising.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

PLUGIN_NAME: str = 'mtoa'
IGNORE_VARIANCE_AOVS: list[str] = [
    'pref',
    'albedo',
    'background',
    'coat_albedo',
    'crypto_asset',
    'crypto_material',
    'crypto_object',
    'denoise_albedo',
    'diffuse_albedo',
    'motionvector',
    'rim_light',  # ?
    'sheen_albedo',
    'specular_albedo',
    'sss_albedo',
    'transmission_albedo',
    'volume_albedo',
]
INFO_MSG: str = (
    'Successfully applied Noice settings.\n\n'
    'Turn OFF "Merge AOVs" when rendering in Arnold RenderView to avoid name collisions with Variance AOVs.\n\n'
    'Make sure to turn "Merge AOVs" back ON before Batch Rendering.'
)

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
def create_variance_filter() -> None:
    '''Create variance filter.'''
    driver: str = 'defaultArnoldDriver'
    filter_name: str = 'variance_aiAOVFilter'
    if not cmds.objExists(driver):
        return

    if not cmds.objExists(filter_name):
        filter_name = cmds.createNode('aiAOVFilter', name=filter_name)
        cmds.setAttr(f'{filter_name}.aiTranslator', 'variance', type='string')

    aov_interface: aovs.AOVInterface = aovs.AOVInterface()
    _aovs: list[aovs.SceneAOV] = aov_interface.getAOVs()
    count: int = 0
    for aov in _aovs:
        # Process only color data (RGB: 5, RGBA: 6)
        if aov.type not in (5, 6):
            continue

        if str(aov.name).lower() in IGNORE_VARIANCE_AOVS:
            continue

        indices: list[int] = (
            cmds.getAttr(f'{aov.node}.outputs', multiIndices=True) or []
        )
        has_variance: bool = False
        next_index: int = 0
        for idx in indices:
            if idx >= next_index:
                next_index = idx + 1

            connected_filters: list[str] = cmds.listConnections(
                f'{aov.node}.outputs[{idx}].filter', source=True
            )
            if connected_filters:
                filter_node: str = connected_filters[0]
                translator: str = cmds.getAttr(f'{filter_node}.aiTranslator')
                if translator == 'variance':
                    has_variance = True
                    break

        if has_variance:
            continue

        cmds.connectAttr(
            f'{driver}.message',
            f'{aov.node}.outputs[{next_index}].driver',
            force=True,
        )
        cmds.connectAttr(
            f'{filter_name}.message',
            f'{aov.node}.outputs[{next_index}].filter',
            force=True,
        )
        count += 1

    if count > 0:
        aoveditor.refreshArnoldAOVTab()


def main(is_info: bool = True) -> None:
    '''Executes the Setup Noice tool.'''
    if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
        cmds.loadPlugin(PLUGIN_NAME)
        if not cmds.pluginInfo(PLUGIN_NAME, query=True, loaded=True):
            _logger.error('Failed to load Arnold plugin.')
            return

    render_options: str = 'defaultArnoldRenderOptions'
    driver: str = 'defaultArnoldDriver'
    if not cmds.objExists(render_options):
        core.createOptions()
        _logger.info('Create Arnold Options.')

    cmds.setAttr(f'{render_options}.outputVarianceAOVs', 1)
    cmds.setAttr(f'{render_options}.renderDevice', 0)
    cmds.setAttr(f'{driver}.mergeAOVs', 1)
    cmds.setAttr(f'{driver}.aiTranslator', 'exr', type='string')
    cmds.setAttr(f'{driver}.exrCompression', 3)
    create_variance_filter()

    if is_info:
        QMessageBox.information(
            widgets.maya_window_to_qt(), __product__, INFO_MSG
        )

    _logger.info('Done.')
