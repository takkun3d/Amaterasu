# ==============================================================================
#
# Select Crease Edges
#
# ==============================================================================
from __future__ import annotations
from maya import cmds, mel
from ..lib import logger, utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Crease Edges'
__version__: str = '1.00'
__doc__ = 'Select crease edge from selected node/component.'
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
    '''Do it.'''
    selection: list[str] = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select polygon to converted selection.')
        return

    result: list[str] = []
    for node in selection:
        edges: list[str] = utility.to_edge(node)
        if not edges:
            continue

        crease_values: list[float] = cmds.polyCrease(
            edges, query=True, value=True
        )
        crease_indexes: list[str] = [
            edges[i] for i, x in enumerate(crease_values) if x > 0.0
        ]
        if crease_indexes:
            result += crease_indexes

    if result:
        mel.eval('SelectEdgeMask')
        cmds.select(*result, replace=True)
        _logger.info('Done.')

    else:
        _logger.warning('Does not exists crease edges.')
