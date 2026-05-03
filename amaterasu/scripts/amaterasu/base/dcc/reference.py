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
"""Provides utilities for managing Maya references."""

from __future__ import annotations
import os
from maya import cmds, mel
from amaterasu.base import utils

FILE_FORMAT: dict[str, str] = {".ma": "mayaAscii", ".mb": "mayaBinary"}


def get_selected_reference_nodes() -> list[str]:
    """Gets reference nodes from the current selection or Reference Editor.

    It first checks the Maya Reference Editor for selected items. If none
    are found, it falls back to finding reference nodes associated with
    the currently selected objects in the viewport/outliner.

    Returns:
        list[str]: A list of reference node names.
    """
    references: list[str] = []

    reference_editor: str = mel.eval("$temp = $gReferenceEditorPanel;")
    if reference_editor:
        editor_refs: str = cmds.sceneEditor(
            reference_editor, query=True, selectReference=True
        )  # type: ignore
        if editor_refs:
            references.extend(editor_refs)

    if not references:
        nodes: list[str] = cmds.ls(selection=True)
        references = [
            cmds.referenceQuery(node, referenceNode=True) for node in nodes  # type: ignore
        ]

    return list(set(references))


def replace(reference_node: str, file_path: str) -> utils.Result:
    """Replaces the specified reference with a new file.

    Args:
        reference_node (str): The name of the reference node.
        file_path (str): The absolute path to the new Maya file.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    if not os.path.exists(file_path):
        result.set_error(f"File does not exist: {file_path}")
        return result

    ext: str = os.path.splitext(file_path)[-1].lower()
    file_format: str = FILE_FORMAT.get(ext, "mayaBinary")

    try:
        cmds.file(
            file_path,
            loadReference=reference_node,
            type=file_format,
            options="v=0;",
        )

    except RuntimeError as e:
        result.set_error(f"Failed to replace reference '{reference_node}': {e}")

    return result


def update_namespace(reference_node: str) -> utils.Result:
    """Updates the namespace of a reference to match its current filename.

    Args:
        reference_node (str): The name of the reference node.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    try:
        file_path: str = cmds.referenceQuery(reference_node, filename=True)  # type: ignore
        basename: str = os.path.splitext(os.path.basename(file_path))[0]
        cmds.file(file_path, edit=True, namespace=basename)

    except RuntimeError as e:
        result.set_error(
            f"Failed to update namespace for '{reference_node}': {e}"
        )

    return result


def update_name(reference_node: str) -> utils.Result:
    """Updates the reference node name to match its current filename.

    Args:
        reference_node (str): The name of the reference node.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    try:
        file_path: str = cmds.referenceQuery(reference_node, filename=True)  # type: ignore
        basename: str = os.path.splitext(os.path.basename(file_path))[0]
        new_name: str = f"{basename}RN"

        cmds.lockNode(reference_node, lock=False)
        cmds.rename(reference_node, new_name)
        cmds.lockNode(new_name, lock=True)

    except RuntimeError as e:
        result.set_error(
            f"Failed to update reference name for '{reference_node}': {e}"
        )

    return result
