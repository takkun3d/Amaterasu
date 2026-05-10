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
"""Provides utilities for managing Maya scene files."""

from __future__ import annotations
from typing import Any
from maya import cmds, mel
from maya.api import OpenMaya
from amaterasu.base import utils


def prompt_save_changes() -> bool:
    """Prompts the user to save changes if the current scene is modified.

    Returns:
        bool: True if it is safe to proceed (saved or ignored),
            False if cancelled.
    """
    if not cmds.file(query=True, modified=True):
        return True

    save: str = "Save"
    dont_save: str = "Don't Save"
    cancel: str = "Cancel"

    filename: str = cmds.file(query=True, sceneName=True)  # type: ignore
    if filename:
        result: str = cmds.confirmDialog(
            title="Save Changes",
            message=f"Save changes to {filename}",
            button=[save, dont_save, cancel],
            defaultButton=save,
            cancelButton=cancel,
        )
        if result == save:
            cmds.file(save=True)
            return True

        elif result == dont_save:
            return True

        return False

    else:
        result = cmds.confirmDialog(
            title="Warning: Scene Not Saved",
            message="Save changes to untitled scene?",
            button=[save, dont_save, cancel],
            defaultButton=save,
            cancelButton=cancel,
        )
        if result == save:
            res: int = mel.eval('projectViewer("SaveAs")')
            return bool(res)

        elif result == dont_save:
            return True

        return False


def prompt_select_file() -> str:
    """Opens a Maya dialog for selecting a scene file.

    Returns:
        str: The selected file path, or an empty string if cancelled.
    """
    file_filter: str = mel.eval("buildDefaultMayaOpenFilterList()")
    starting_directory: str = cmds.workspace(query=True, fullName=True)  # type: ignore

    file_names: list[str] | None = cmds.fileDialog2(
        returnFilter=True,
        caption="Open (Amaterasu)",
        fileMode=1,
        okCaption="Open",
        optionsUICreate="fileOperationsOptionsUISetup Open",  # type: ignore
        optionsUIInit="fileOperationsOptionsUIInitValues Open",  # type: ignore
        selectionChanged="fileOperationsSelectionChangedCallback Open",  # type: ignore
        optionsUICommit2="fileOperationsOptionsUICallback Open",  # type: ignore
        fileTypeChanged="setCurrentFileTypeOption Open",  # type: ignore
        fileFilter=file_filter,
        selectFileFilter="Maya Scenes",
        startingDirectory=starting_directory,
        optionsUICancel="fileOptionsCancel",  # type: ignore
    )

    return file_names[0] if file_names else ""


def open_file(file_path: str) -> utils.Result:
    """Opens the specified Maya scene file safely applying user options.

    Args:
        file_path (str): The path to the Maya scene file.

    Returns:
        utils.Result: The result of the open operation.
    """
    result: utils.Result = utils.Result()
    kwargs: dict[str, Any] = {}

    option: str = mel.eval("$temp = $gFileOptionsString;")
    if option:
        kwargs["options"] = option

    if cmds.optionVar(exists="fileExecuteSN") and not cmds.optionVar(
        query="fileExecuteSN"
    ):
        kwargs["executeScriptNodes"] = False

    if cmds.optionVar(exists="fileIgnoreVersion") and cmds.optionVar(
        query="fileIgnoreVersion"
    ):
        kwargs["ignoreVersion"] = True

    if cmds.optionVar(exists="fileOpenRefLoadSetting"):
        ref_load_setting: str = cmds.optionVar(query="fileOpenRefLoadSetting")  # type: ignore
        if ref_load_setting != "default":
            kwargs["loadReferenceDepth"] = ref_load_setting

    if cmds.optionVar(query="fileOpenReserveNamespaces"):
        kwargs["reserveNamespaces"] = True

    file_types: list[str] | None = cmds.file(file_path, query=True, type=True)  # type: ignore
    if file_types:
        kwargs["type"] = file_types[0]

    kwargs["open"] = True

    try:
        cmds.file(file_path, force=True, **kwargs)
        if file_types:
            mel.eval(f'addRecentFile("{file_path}", "{file_types[0]}")')

    except RuntimeError as e:
        result.set_error(str(e))

    return result


def remove_node_editor_info() -> utils.Result:
    """Removes all nodeGraphEditorInfo nodes from the current scene.

    Safely disconnects any connected plugs before deleting the nodes
    to prevent dependency graph issues.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    nodes: list[str] = cmds.ls(type="nodeGraphEditorInfo") or []

    for node in nodes:
        try:
            connections: list[str] = (
                cmds.listConnections(node, connections=True, plugs=True) or []
            )
            # for dst_plug, src_plug in zip(connections[::2], connections[1::2]):
            #     cmds.disconnectAttr(src_plug, dst_plug)

            # cmds.delete(node)
            for i in range(0, len(connections), 2):
                node_plug: str = connections[i]
                connected_plug: str = connections[i + 1]

                if cmds.connectionInfo(node_plug, isDestination=True):
                    cmds.disconnectAttr(connected_plug, node_plug)

                else:
                    cmds.disconnectAttr(node_plug, connected_plug)

            cmds.delete(node)
            result.add_info(node, "Removed nodeGraphEditorInfo")

        except (RuntimeError, ValueError):
            result.add_failure(node, "Failed to remove")

    return result


def remove_unknown_nodes() -> utils.Result:
    """Removes all unknown nodes from the current scene.

    Unlocks the nodes before attempting deletion. Ignores nodes that
    are automatically deleted in conjunction with others.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    nodes: list[str] = cmds.ls(type="unknown") or []

    for node in nodes:
        try:
            cmds.lockNode(node, lock=False)
            cmds.delete(node)
            result.add_info(node, "Removed unknown node")

        except RuntimeError:
            result.add_failure(node, "Cannot delete node")

        except ValueError:
            pass

    return result


def find_duplicate_name_nodes() -> list[str]:
    """Finds all nodes in the scene that have non-unique names (long paths).

    Returns:
        list[str]: A list of full DAG paths for nodes with duplicate short names.
    """
    result: list[str] = []
    iter_dag: OpenMaya.MItDag = OpenMaya.MItDag(
        OpenMaya.MItDag.kDepthFirst, OpenMaya.MFn.kBase
    )
    dag_fn: OpenMaya.MFnDagNode = OpenMaya.MFnDagNode()
    while not iter_dag.isDone():
        dag_fn.setObject(iter_dag.currentItem())
        if not dag_fn.isInstanced():
            path: OpenMaya.MDagPath = dag_fn.getPath()
            node_name: str = path.partialPathName()
            if len(node_name.split('|')) >= 2:
                result.append(node_name)

        iter_dag.next()

    return result
