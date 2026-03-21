# ==============================================================================
#
# Auto Set Project
#
# ==============================================================================
from __future__ import annotations
from typing import Any
import pathlib
from maya import cmds, mel
from ..lib import logger

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Auto Set Project'
__version__: str = '1.00'
__doc__ = 'The project is automatically set when secene is opened in Maya.'
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
def select_maya_scene() -> str:
    '''Opens a dialog for selecting a scene file.'''
    file_filter: str = mel.eval('buildDefaultMayaOpenFilterList()')
    starting_directory: str = cmds.workspace(query=True, fullName=True)
    file_name: list[str] = cmds.fileDialog2(
        returnFilter=True,
        caption='Open (Amaterasu)',
        fileMode=1,
        okCaption='Open',
        optionsUICreate='fileOperationsOptionsUISetup Open',
        optionsUIInit='fileOperationsOptionsUIInitValues Open',
        selectionChanged='fileOperationsSelectionChangedCallback Open',
        optionsUICommit2='fileOperationsOptionsUICallback Open',
        fileTypeChanged='setCurrentFileTypeOption Open',
        fileFilter=file_filter,
        selectFileFilter='Maya Scenes',
        startingDirectory=starting_directory,
        optionsUICancel='fileOptionsCancel',
    )

    if not file_name:
        return ''

    return file_name[0]


def is_save_changes() -> int:
    '''Check to see if it needs to be saved. If necessary, guide them.'''
    return_value: int = 0
    if cmds.file(query=True, modified=True):
        save: str = 'Save'
        dont_save: str = "Don't Save"
        cancel: str = 'Cancel'
        result: str = ''
        filename: str = cmds.file(query=True, sceneName=True)
        if filename != '':
            confirm_message: str = f'Save changes to {filename}'
            result = cmds.confirmDialog(
                title='Save Changes',
                message=confirm_message,
                button=[save, dont_save, cancel],
                defaultButton=save,
                cancelButton=cancel,
            )

            if result == save:
                cmds.file(save=True)
                return_value = 1

            elif result == dont_save:
                return_value = 1

            elif result in (cancel, 'dismiss'):
                return_value = 0

        else:
            result = cmds.confirmDialog(
                title='Warning: Scene Not Saved',
                message='Save changes to untitled scene?',
                button=[save, dont_save, cancel],
                defaultButton=save,
                cancelButton=cancel,
            )
            if result == save:
                return_value = mel.eval('projectViewer("SaveAs")')

            elif result == dont_save:
                return_value = 1

            elif result in (cancel, 'dismiss'):
                return_value = 0
    else:
        return_value = 1

    return return_value


def project_directory(scene_file: str) -> str:
    '''Search workspace.mel.'''
    result: str = ''
    file_path: pathlib.Path = pathlib.Path(scene_file)
    if file_path.is_file():
        file_path = file_path.parent

    work_space_mel: list[pathlib.Path] = list(file_path.glob('workspace.mel'))
    if not work_space_mel:
        if pathlib.Path(file_path.anchor) == file_path:
            # not found workspace.mel
            return ''

        result = project_directory(str(file_path.parent))

    else:
        result = str(work_space_mel[0].parent)

    return result


def open_maya_scene(file_name: str) -> None:
    '''Open the maya scene.'''
    kwargs: dict[str, Any] = {}
    option: str = mel.eval('$temp = $gFileOptionsString;')
    if len(option) > 0:
        kwargs['options'] = option

    if cmds.optionVar(exists='fileExecuteSN') and not cmds.optionVar(
        query='fileExecuteSN'
    ):
        kwargs['executeScriptNodes'] = False

    if cmds.optionVar(exists='fileIgnoreVersion') and cmds.optionVar(
        query='fileIgnoreVersion'
    ):
        kwargs['ignoreVersion'] = True

    if cmds.optionVar(exists='fileOpenRefLoadSetting'):
        ref_load_setting: str = cmds.optionVar(query='fileOpenRefLoadSetting')
        if ref_load_setting != 'default':
            kwargs['loadReferenceDepth'] = ref_load_setting

    if cmds.optionVar(query='fileOpenReserveNamespaces'):
        kwargs['reserveNamespaces'] = True

    file_types: list[str] = cmds.file(file_name, query=True, type=True)
    if file_types:
        kwargs['type'] = file_types[0]

    kwargs['open'] = True

    cmds.file(file_name, force=True, **kwargs)
    mel.eval(f'addRecentFile("{file_name}", "{file_types[0]}")')


def main(force: bool = False) -> None:
    '''Do it.'''
    if not force:
        file_name: str = select_maya_scene()
        if file_name == '':
            return

        is_save: int = is_save_changes()
        if is_save == 0:
            return

    project_path: str = project_directory(file_name)
    if project_path == '':
        _logger.error('The file defining the project does not exist.')
        return

    escaped_project_path: str = project_path.replace('\\', '\\\\')
    mel.eval(f'setProject "{escaped_project_path}"')
    open_maya_scene(file_name)
    _logger.info('Done : %s', project_path)
