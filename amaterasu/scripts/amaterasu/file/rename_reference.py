# ==============================================================================
#
# Rename Reference
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from . import replace_reference


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Rename Reference'
__version__: str = '1.00'
__doc__ = 'Rename reference node from file name.'
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
    '''Rename reference node from file name.'''
    references: list[str] = replace_reference.get_selected_references()
    if not references:
        references = replace_reference.get_reference_nodes(
            cmds.ls(selection=True)
        )

    if not references:
        _logger.error(
            'Select node or Reference Editor item to rename reference node.'
        )
        return

    for reference in references:
        replace_reference.set_reference_name_from_filename(reference)

    _logger.info('Done.')
