# ==============================================================================
#
# Rename Namespace
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
__doc__ = 'Rename namespace from referenced file.'
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
def main() -> None:
    '''Rename namespace from referenced file.'''
    references: list[str] = replace_reference.get_selected_references()
    if not references:
        references = replace_reference.get_reference_nodes(
            cmds.ls(selection=True)
        )

    if not references:
        _logger.error(
            'Select node or Reference Editor item to rename namespace.'
        )
        return

    for reference in references:
        replace_reference.set_namespace_from_filename(reference)

    _logger.info('Done.')
