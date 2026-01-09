# ==============================================================================
#
# Open Work Directory
#
# ==============================================================================
from __future__ import annotations
import logging
from maya import cmds
from ..lib import utility

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Open Work Directory'
__version__: str = '1.00'
__doc__ = 'Open directory of project in Explorer.'
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
def main() -> None:
    '''Open the project in Explorer.'''
    project_path: str = cmds.workspace(query=True, rootDirectory=True)
    result: bool = utility.open_directory(project_path)
    if result == -2:
        _logger.error('Not supported os.')
    elif result == -1:
        _logger.error('Does not exists path : %s', project_path)
    else:
        _logger.info('Done.')
