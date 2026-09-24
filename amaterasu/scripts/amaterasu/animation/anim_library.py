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
"""Provides animation and pose library functionalities for the Amaterasu toolset.

This module contains classes and UI components to manage, save, and apply
animation and pose data.
"""

from __future__ import annotations
from typing import Any
import os
import json
import datetime
import getpass
from maya import cmds
from amaterasu import env
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Anim Library"
__version__: str = "1.31"
_logger: utils.Logger = utils.get_logger(__product__)

ROOT_DIR: str = os.path.join(env.USER_DATA_DIR, "anim_library")
ICON_SIZE_RANGE: tuple[int, int] = (64, 256)
NO_IMAGE: str = widgets.FileBrowserItem.no_image
DATE_FORMAT: str = "%Y/%m/%d/ %H:%M:%S"

ATTRIBUTE_TYPE_FILTER: list[str] = [
    "double",
    "doubleAngle",
    "doubleLinear",
    "int",
    "short",
    "long",
    "float",
    "bool",
    "string",
    "enum",
]

PLUGINS: str = "atomImportExport.mll"


class Settings(framework.ToolSettings):
    """Settings for the Anim Library tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
        splitter_state (framework.Variant[str]): The saved splitter state.
        root_dir (framework.Variant[str]): The root directory path.
        filter (framework.Variant[str]): The current filter text.
        icon_size (framework.Variant[int]): The icon size in the view.
        pose_method (framework.Variant[int]): The apply method for poses.
        pose_keyframe (framework.Variant[bool]): The keyframe flag for poses.
        anim_method (framework.Variant[int]): The apply method for animations.
        remove_animation (framework.Variant[bool]): The remove animation flag.
        override_animation (framework.Variant[bool]): The override animation
            flag.
        is_time_range (framework.Variant[bool]): The time range toggle flag.
        start_frame (framework.Variant[int]): The start frame for animation.
        end_frame (framework.Variant[int]): The end frame for animation.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    splitter_state: framework.Variant[str] = framework.Variant("")
    root_dir: framework.Variant[str] = framework.Variant(ROOT_DIR)
    filter: framework.Variant[str] = framework.Variant("")
    icon_size: framework.Variant[int] = framework.Variant(128)

    pose_method: framework.Variant[int] = framework.Variant(0)
    pose_keyframe: framework.Variant[bool] = framework.Variant(True)

    anim_method: framework.Variant[int] = framework.Variant(0)
    remove_animation: framework.Variant[bool] = framework.Variant(True)
    override_animation: framework.Variant[bool] = framework.Variant(False)
    is_time_range: framework.Variant[bool] = framework.Variant(False)
    start_frame: framework.Variant[int] = framework.Variant(1)
    end_frame: framework.Variant[int] = framework.Variant(120)


class Pose:
    """Manages pose data, metadata, and application logic.

    Attributes:
        version (float): The current version of the pose data format.
        folder_extension (str): The folder extension for pose data.
        meta_file_name (str): The filename for the metadata JSON.
        data_file_name (str): The filename for the pose data JSON.
    """

    version: float = 1.0
    folder_extension: str = "pose"
    meta_file_name: str = "meta.json"
    data_file_name: str = "data.json"

    def __init__(
        self,
        base_path: str,
        basename: str,
        comment: str = "",
        replace_namespace: str = "",
    ) -> None:
        """Initializes the Pose instance.

        Args:
            base_path (str): The root directory path.
            basename (str): The base name for the pose.
            comment (str, optional): Comment for the pose. Defaults to "".
            replace_namespace (str, optional): Namespace to replace.
                Defaults to "".
        """
        self.__title: str = basename
        self.__metadata: dict[str, Any] = {
            "owner": getpass.getuser(),
            "date": "",
            "version": self.version,
            "maya_version": cmds.about(apiVersion=True),
            "comment": comment,
        }
        self.__replace_namespace: str = replace_namespace
        self.__data: dict[str, dict[str, Any]] = {}

        self.__folder_name: str = f"{basename}.{self.folder_extension}"
        self.__root_path: str = os.path.join(base_path, self.__folder_name)
        self.__thumbnail_file_name: str = os.path.join(
            self.__root_path,
            widgets.FileBrowserItem.thumbnail_filename,
        )
        self.__metadata_file_name: str = os.path.join(
            self.__root_path,
            self.meta_file_name,
        )
        self.__pose_file_name: str = os.path.join(
            self.__root_path,
            self.data_file_name,
        )

    @classmethod
    def from_path(cls, path: str) -> Pose:
        """Returns an instance from the given path.

        Args:
            path (str): The file path.

        Returns:
            Pose: A new Pose instance.
        """
        basename, _ = os.path.splitext(path)
        data_path: str = os.path.dirname(basename)
        basename: str = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(self, method: int = 0, keyframe: bool = False) -> bool:
        """Applies the pose.

        Args:
            method (int, optional): Apply method (0 for selection, 1 for file).
                Defaults to 0.
            keyframe (bool, optional): Whether to keyframe. Defaults to False.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        self.__data = self.read_json(self.__pose_file_name)
        if method == 0:
            return self.apply_from_selection(keyframe)

        else:
            return self.apply_from_file(keyframe)

    def apply_from_selection(self, keyframe: bool = False) -> bool:
        """Applies pose data from the current selection.

        Args:
            keyframe (bool, optional): Whether to keyframe. Defaults to False.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error("Select node to apply pose data.")
            return False

        for node in selection:
            dst_namespace: str = dcc.node.get_namespace(node)
            for src_node, attrs in self.__data.items():
                src_namespace: str = dcc.node.get_namespace(src_node)

                search: str = ""
                replace: str = ""
                prefix: str = ""
                suffix: str = ""
                if not src_namespace and not dst_namespace:
                    # Has not Namespace > Has not Namespace
                    pass

                elif not src_namespace and dst_namespace:
                    # Has not Namespace > Has Namespace
                    prefix = dst_namespace

                elif src_namespace and not dst_namespace:
                    # Has Namespace > Has not Namespace
                    search = src_namespace
                    replace = ""

                elif src_namespace and dst_namespace:
                    # Has Namespace > Has Namespace
                    search = src_namespace
                    replace = dst_namespace

                for attr, value in attrs.items():
                    result: int = Pose.set_value(
                        src_node,
                        attr,
                        value,
                        keyframe,
                        search,
                        replace,
                        prefix,
                        suffix,
                        node,
                    )
                    if result == -1:
                        _logger.warning("%s does not exist. Skipped.", src_node)
                        break

                    elif result == -2:
                        _logger.warning(
                            "Failed to set value. %s.%s", node, attr
                        )
        return True

    def apply_from_file(self, keyframe: bool = False) -> bool:
        """Applies pose data from a file.

        Args:
            keyframe (bool, optional): Whether to keyframe. Defaults to False.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        selection: list[str] = cmds.ls(selection=True)
        dst_namespaces: list[str] = dcc.node.get_namespaces(selection)

        for node, attrs in self.__data.items():
            result: int = 1
            for attr, value in attrs.items():
                src_namespace: str = dcc.node.get_namespace(node)

                if not src_namespace and not dst_namespaces:
                    # Has not Namespace > Has not Namespace
                    result = Pose.set_value(node, attr, value, keyframe)
                    if result == -1:
                        _logger.error(
                            "%s does not exist. Try Selection Mode.", node
                        )
                        break

                    elif result == -2:
                        _logger.warning(
                            "Failed to set value. %s.%s", node, attr
                        )

                elif not src_namespace and dst_namespaces:
                    # Has not Namespace > Has Namespace
                    for dst_namespace in dst_namespaces:
                        result = Pose.set_value(
                            node, attr, value, keyframe, "", "", dst_namespace
                        )
                        if result == -1:
                            _logger.error(
                                "%s does not exist. Try Selection.", node
                            )
                            break

                        elif result == -2:
                            _logger.warning(
                                "Failed to set value. %s.%s", node, attr
                            )
                    else:
                        continue
                    break

                elif src_namespace and not dst_namespaces:
                    dst_namespace = "" if selection else src_namespace
                    result = Pose.set_value(
                        node,
                        attr,
                        value,
                        keyframe,
                        src_namespace,
                        dst_namespace,
                    )
                    if result == -1:
                        _logger.error(
                            "%s does not exist. Try Selection Mode.", node
                        )
                        break

                    elif result == -2:
                        _logger.warning(
                            "Failed to set value. %s.%s", node, attr
                        )

                elif src_namespace and dst_namespaces:
                    # Has Namespace > Has Namespace
                    for dst_namespace in dst_namespaces:
                        result = Pose.set_value(
                            node,
                            attr,
                            value,
                            keyframe,
                            src_namespace,
                            dst_namespace,
                        )
                        if result == -1:
                            _logger.error(
                                "%s does not exist. Try Selection.", node
                            )
                            break

                        elif result == -2:
                            _logger.warning(
                                "Failed to set value. %s.%s", node, attr
                            )
                    else:
                        continue
                    break

        return True

    @staticmethod
    def set_value(
        node: str,
        attr: str,
        value: Any,
        keyframe: bool,
        search: str = "",
        replace: str = "",
        prefix: str = "",
        suffix: str = "",
        filter_str: str = "",
    ) -> int:
        """Sets a value for a specific node attribute.

        Args:
            node (str): The target node name.
            attr (str): The attribute name.
            value (Any): The value to set.
            keyframe (bool): Whether to set a keyframe.
            search (str, optional): String to search. Defaults to "".
            replace (str, optional): String to replace. Defaults to "".
            prefix (str, optional): Prefix string. Defaults to "".
            suffix (str, optional): Suffix string. Defaults to "".
            filter_str (str, optional): Filter node name. Defaults to "".

        Returns:
            int: -1 if object does not exist, -2 if attribute fails,
                0 if filtered, 1 if success.
        """
        node = prefix + node.replace(search, replace) + suffix
        if not cmds.objExists(node):
            return -1

        if filter_str and node != filter_str:
            return 0

        try:
            plug: str = f"{node}.{attr}"
            cmds.setAttr(plug, value)
            if keyframe:
                cmds.setKeyframe(plug)

        except RuntimeError:
            return -2

        return 1

    def read(self) -> None:
        """Reads pose metadata from file."""
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(self, nodes: list[str]) -> bool:
        """Writes pose data from specified objects.

        Args:
            nodes (list[str]): List of nodes to save.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        if not nodes:
            _logger.error("Specify the nodes to save the pose.")
            return False

        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error("Failed to make folder. %s", e)

        result: bool = self.write_json(
            self.__pose_file_name,
            self.read_from_nodes(nodes),
        )
        if not result:
            return False

        self.__metadata["date"] = datetime.datetime.now().strftime(DATE_FORMAT)
        result = self.write_json(self.__metadata_file_name, self.__metadata)
        if not result:
            return False

        return True

    def title(self) -> str:
        """Returns the title of the pose.

        Returns:
            str: Pose title.
        """
        return self.__title

    def owner(self) -> str:
        """Returns the owner in metadata.

        Returns:
            str: Owner name.
        """
        return str(self.__metadata.get("owner", "Unknown"))

    def data_version(self) -> float:
        """Returns the version in metadata.

        Returns:
            float: Version number.
        """
        return float(self.__metadata.get("version", 0.0))

    def maya_version(self) -> int:
        """Returns the maya version in metadata.

        Returns:
            int: Maya version.
        """
        return int(self.__metadata.get("maya_version", 0))

    def comment(self) -> str:
        """Returns the comment in metadata.

        Returns:
            str: Pose comment.
        """
        return str(self.__metadata.get("comment", "Unknown"))

    def nodes(self) -> list[str]:
        """Returns the list of nodes.

        Returns:
            list[str]: Node names.
        """
        result: list[str] = self.__metadata.get("nodes", [])
        return result

    def node_count(self) -> int:
        """Returns the object count of data.

        Returns:
            int: Number of nodes.
        """
        return len(self.__metadata.get("nodes", []))

    def date(self) -> str:
        """Returns the date in metadata.

        Returns:
            str: Creation date.
        """
        return str(self.__metadata.get("date", "Unknown"))

    def thumbnail(self) -> str:
        """Returns the thumbnail file name.

        Returns:
            str: Thumbnail path.
        """
        return self.__thumbnail_file_name

    def set_thumbnail(self, path: str) -> None:
        """Sets the thumbnail file path.

        Args:
            path (str): The thumbnail path.
        """
        self.__thumbnail_file_name = path

    def root_path(self) -> str:
        """Returns the root path.

        Returns:
            str: Root directory path.
        """
        return self.__root_path

    def exists(self) -> bool:
        """Returns True if the path exists, False otherwise.

        Returns:
            bool: Existence state.
        """
        return os.path.exists(self.__root_path)

    def read_from_nodes(self, nodes: list[str]) -> dict[str, dict[str, Any]]:
        """Returns pose data extracted from selection.

        Args:
            nodes (list[str]): List of nodes to read from.

        Returns:
            dict[str, dict[str, Any]]: The extracted pose data.
        """
        self.__metadata["namespace"] = dcc.node.get_namespace(nodes[0])
        if self.__replace_namespace != "":
            self.__metadata["namespace"] = self.__replace_namespace

        self.__data = {}
        self.__metadata["nodes"] = []
        for node in nodes:
            attributes: list[str] = (
                cmds.listAttr(node, keyable=True, unlocked=True) or []
            )

            namespace: str = dcc.node.get_namespace(node)
            save_node_name: str = node
            if self.__replace_namespace != "":
                save_node_name = node.replace(
                    namespace, self.__replace_namespace
                )

            self.__data[save_node_name] = {}
            self.__metadata["nodes"].append(save_node_name)
            for attribute in attributes:
                plug: str = f"{node}.{attribute}"
                try:
                    attribute_type: str = cmds.getAttr(plug, type=True)
                except ValueError:
                    continue

                if attribute_type not in ATTRIBUTE_TYPE_FILTER:
                    continue

                value: Any = cmds.getAttr(plug)
                self.__data[save_node_name][attribute] = value

        return self.__data

    def read_json(self, file_name: str) -> dict[str, Any]:
        """Reads data from a json file.

        Args:
            file_name (str): Path to the json file.

        Returns:
            dict[str, Any]: Loaded dictionary data.
        """
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                datas: dict[str, Any] = json.load(f)
            return datas

        except IOError:
            _logger.error("Failed to read: %s", file_name)
            return {}

    def write_json(self, file_name: str, data: Any) -> bool:
        """Writes data to a json file.

        Args:
            file_name (str): Path to the json file.
            data (Any): Data to write.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(file_name, "w", encoding="utf-8") as fw:
                json.dump(data, fw, sort_keys=True, indent=4)
            return True

        except IOError:
            _logger.error("Failed to write: %s", file_name)
            return False


class Animation:
    """Manages animation data via ATOM export and import.

    Attributes:
        version (float): The current version of the animation data format.
        folder_extension (str): The folder extension for animation data.
        meta_file_name (str): The filename for the metadata JSON.
        data_file_name (str): The filename for the animation ATOM data.
    """

    version: float = 1.0
    folder_extension: str = "anim"
    meta_file_name: str = "meta.json"
    data_file_name: str = "data.atom"

    def __init__(
        self,
        base_path: str,
        basename: str,
        comment: str = "",
        replace_namespace: str = "",
    ) -> None:
        """Initializes the Animation instance.

        Args:
            base_path (str): The root directory path.
            basename (str): The base name for the animation.
            comment (str, optional): Comment for the animation. Defaults to "".
            replace_namespace (str, optional): Namespace to replace.
                Defaults to "".
        """
        self.__title: str = basename
        self.__metadata: dict[str, Any] = {
            "owner": getpass.getuser(),
            "date": "",
            "version": self.version,
            "maya_version": cmds.about(apiVersion=True),
            "comment": comment,
        }
        self.__replace_namespace: str = replace_namespace

        self.__folder_name: str = f"{basename}.{self.folder_extension}"
        self.__root_path: str = os.path.join(base_path, self.__folder_name)
        self.__thumbnail_file_name: str = os.path.join(
            self.__root_path,
            widgets.FileBrowserItem.thumbnail_filename,
        )
        self.__metadata_file_name: str = os.path.join(
            self.__root_path,
            self.meta_file_name,
        )
        self.__anim_file_name: str = os.path.join(
            self.__root_path,
            self.data_file_name,
        )

    @classmethod
    def from_path(cls, path: str) -> Animation:
        """Returns an instance from the given path.

        Args:
            path (str): The file path.

        Returns:
            Animation: A new Animation instance.
        """
        basename, _ = os.path.splitext(path)
        data_path: str = os.path.dirname(basename)
        basename: str = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(
        self,
        method: int = 0,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        """Applies the animation.

        Args:
            method (int, optional): Apply method (0 for selection).
                Defaults to 0.
            remove_animation (bool, optional): Remove existing animation.
                Defaults to True.
            override_animation (bool, optional): Override animation.
                Defaults to False.
            start_frame (int | None, optional): Start frame. Defaults to None.
            end_frame (int | None, optional): End frame. Defaults to None.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        if method == 0:
            return self.apply_from_selection(
                remove_animation,
                override_animation,
                start_frame,
                end_frame,
            )
        else:
            return self.apply_from_file(
                remove_animation,
                override_animation,
                start_frame,
                end_frame,
            )

    def remove_animation(self, nodes: list[str]) -> None:
        """Removes animation from specified nodes.

        Args:
            nodes (list[str]): List of target nodes.
        """
        for node in nodes:
            connections: list[str] = (
                cmds.listConnections(node, source=True, destination=False) or []
            )
            for connection in connections:
                if cmds.nodeType(connection) in dcc.animation.ANIM_CURVES_TYPE:
                    cmds.delete(connection)

    def apply_from_selection(
        self,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        """Applies animation data from selection.

        Args:
            remove_animation (bool, optional): Remove existing. Defaults to True.
            override_animation (bool, optional): Override existing.
                Defaults to False.
            start_frame (int | None, optional): Start frame. Defaults to None.
            end_frame (int | None, optional): End frame. Defaults to None.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            _logger.error("Select node to apply animation data.")
            return False

        if remove_animation:
            self.remove_animation(selection)

        namespaces: dict[str, list[str]] = dcc.node.get_namespace_group(
            selection
        )
        for dst_namespace, nodes in namespaces.items():
            src_namespace: str = self.__metadata["namespace"]
            search: str = ""
            replace: str = ""
            prefix: str = ""
            suffix: str = ""

            if not src_namespace and dst_namespace:
                prefix = dst_namespace

            elif src_namespace and not dst_namespace:
                # Has Namespace > Has not Namespace
                search = src_namespace

            elif src_namespace and dst_namespace:
                # Has Namespace > Has Namespace
                search = src_namespace
                replace = dst_namespace

            result: bool = Animation.import_atom(
                self.__anim_file_name,
                nodes,
                search,
                replace,
                prefix,
                suffix,
                override_animation,
                start_frame,
                end_frame,
                selection,
            )
            if not result:
                _logger.error("Failed to import file.")

        return True

    def apply_from_file(
        self,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        """Applies animation data from file directly.

        Args:
            remove_animation (bool, optional): Remove existing. Defaults to True.
            override_animation (bool, optional): Override existing.
                Defaults to False.
            start_frame (int | None, optional): Start frame. Defaults to None.
            end_frame (int | None, optional): End frame. Defaults to None.

        Returns:
            bool: True if applied successfully, False otherwise.
        """
        selection: list[str] = cmds.ls(selection=True)
        namespaces: list[str] = dcc.node.get_namespaces(selection)
        if not namespaces:
            namespaces.append("")

        if remove_animation:
            self.remove_animation(selection)

        for dst_namespace in namespaces:
            src_namespace: str = self.__metadata["namespace"]
            search: str = ""
            replace: str = ""
            prefix: str = ""
            suffix: str = ""

            if not src_namespace and dst_namespace:
                prefix = dst_namespace

            elif src_namespace and not dst_namespace:
                # Has Namespace > Has not Namespace
                search = src_namespace

            elif src_namespace and dst_namespace:
                # Has Namespace > Has Namespace
                search = src_namespace
                replace = dst_namespace

            result: bool = Animation.import_atom(
                self.__anim_file_name,
                self.__metadata["nodes"],
                search,
                replace,
                prefix,
                suffix,
                override_animation,
                start_frame,
                end_frame,
            )
            if not result:
                _logger.error("Failed to import file.")

        return True

    @staticmethod
    def import_atom(
        anim_file: str,
        nodes: list[str],
        search: str = "",
        replace: str = "",
        prefix: str = "",
        suffix: str = "",
        replace_anim: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
        filter_nodes: list[str] | None = None,
    ) -> bool:
        """Imports animation via ATOM format.

        Args:
            anim_file (str): The atom file path.
            nodes (list[str]): Target nodes.
            search (str, optional): Search string. Defaults to "".
            replace (str, optional): Replace string. Defaults to "".
            prefix (str, optional): Prefix string. Defaults to "".
            suffix (str, optional): Suffix string. Defaults to "".
            replace_anim (bool, optional): Replace animation. Defaults to False.
            start_frame (int | None, optional): Start frame. Defaults to None.
            end_frame (int | None, optional): End frame. Defaults to None.
            filter_nodes (list[str] | None, optional): Nodes to filter. Defaults to None.

        Returns:
            bool: True if imported successfully, False otherwise.
        """
        if filter_nodes is None:
            filter_nodes = []

        processed_nodes: list[str] = [
            prefix + n.replace(search, replace) + suffix for n in nodes
        ]
        if filter_nodes:
            processed_nodes = [n for n in processed_nodes if n in filter_nodes]

        try:
            cmds.select(*processed_nodes)
        except ValueError:
            _logger.error("Node does not exist: %s", processed_nodes)
            return False

        target_time: int = 3
        time_flag: str = ""
        option: str = "insert"
        if start_frame is not None and end_frame is not None:
            option = "scaleReplace"
            time_flag = (
                f"srcTime={start_frame}:{end_frame};"
                f"dstTime={start_frame}:{end_frame};"
            )
            target_time = 1

        if replace_anim:
            option = "scaleReplace"

        options: str = (
            f";;targetTime={target_time};{time_flag}option={option};"
            f"match=string;;selected=selectedOnly;search={search};"
            f"replace={replace};prefix={prefix};suffix={suffix};mapFile=;"
        )
        cmds.file(
            anim_file,
            i=True,
            type="atomImport",
            renameAll=True,
            namespace="AnimLibraryAnimImport",
            options=options,
        )
        return True

    def read(self) -> None:
        """Reads animation metadata from file."""
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(
        self,
        nodes: list[str],
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        """Writes animation data from objects.

        Args:
            nodes (list[str]): List of nodes to export.
            start_frame (int | None, optional): Start frame. Defaults to None.
            end_frame (int | None, optional): End frame. Defaults to None.

        Returns:
            bool: True if written successfully, False otherwise.
        """
        if not nodes:
            _logger.error("Specify the nodes to save the animation.")
            return False

        self.__metadata["nodes"] = []
        filtered_node: list[str] = []
        for node in nodes:
            if not dcc.animation.has_animation(node):
                continue

            namespace: str = dcc.node.get_namespace(node)
            node_name: str = node
            if self.__replace_namespace != "":
                node_name = node.replace(namespace, self.__replace_namespace)

            self.__metadata["nodes"].append(node_name)
            filtered_node.append(node)

        if not filtered_node:
            _logger.error("Specify the nodes to save the animation.")
            return False

        self.__metadata["namespace"] = dcc.node.get_namespace(
            self.__metadata["nodes"][0]
        )
        namespace = dcc.node.get_namespace(filtered_node[0])

        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error("Failed to make folder. %s", e)

        cmds.select(*filtered_node)

        which_range: int = 1
        copy_key_cmd_time_range: str = ""
        if start_frame is not None and end_frame is not None:
            which_range = 2
            copy_key_cmd_time_range = (
                f"-time >{start_frame}:{end_frame}> "
                f"-float >{start_frame}:{end_frame}>"
            )
        else:
            start_frame = 1
            end_frame = 120

        options: str = (
            "precision=8;statics=1;baked=0;sdk=0;constraint=0;animLayers=0;"
            f"selected=selectedOnly;whichRange={which_range};"
            f"range={start_frame}:{end_frame};hierarchy=none;controlPoints=0;"
            f"useChannelBox=1;options=keys;"
            f"copyKeyCmd=-animation objects {copy_key_cmd_time_range} -option keys -hierarchy none -controlPoints 0 "
        )

        try:
            cmds.file(
                self.__anim_file_name,
                force=True,
                options=options,
                constructionHistory=True,
                type="atomExport",
                exportSelected=True,
            )

            if self.__replace_namespace != "":
                with open(self.__anim_file_name, "r", encoding="utf-8") as f:
                    all_lines: list[str] = f.readlines()

                for i, line in enumerate(all_lines):
                    all_lines[i] = line.replace(
                        namespace, self.__replace_namespace
                    )

                with open(
                    self.__anim_file_name, "w", encoding="utf-8", newline="\n"
                ) as fw:
                    fw.writelines(all_lines)

        except RuntimeError as e:
            _logger.error("Failed to export animation data. %s", e)
            return False

        self.__metadata["date"] = datetime.datetime.now().strftime(DATE_FORMAT)
        result: bool = self.write_json(
            self.__metadata_file_name, self.__metadata
        )
        if not result:
            return False

        return True

    def title(self) -> str:
        """Returns the title of the animation.

        Returns:
            str: Animation title.
        """
        return self.__title

    def owner(self) -> str:
        """Returns the owner in metadata.

        Returns:
            str: Owner name.
        """
        return str(self.__metadata.get("owner", "Unknown"))

    def data_version(self) -> float:
        """Returns the version in metadata.

        Returns:
            float: Version number.
        """
        return float(self.__metadata.get("version", 0.0))

    def maya_version(self) -> int:
        """Returns the maya version in metadata.

        Returns:
            int: Maya version.
        """
        return int(self.__metadata.get("maya_version", 0))

    def comment(self) -> str:
        """Returns the comment in metadata.

        Returns:
            str: Animation comment.
        """
        return str(self.__metadata.get("comment", "Unknown"))

    def nodes(self) -> list[str]:
        """Returns the list of nodes.

        Returns:
            list[str]: Node names.
        """
        result: list[str] = self.__metadata.get("nodes", [])
        return result

    def node_count(self) -> int:
        """Returns the object count of data.

        Returns:
            int: Number of nodes.
        """
        return len(self.__metadata.get("nodes", []))

    def date(self) -> str:
        """Returns the date in metadata.

        Returns:
            str: Creation date.
        """
        return str(self.__metadata.get("date", "Unknown"))

    def thumbnail(self) -> str:
        """Returns the thumbnail file name.

        Returns:
            str: Thumbnail path.
        """
        return self.__thumbnail_file_name

    def set_thumbnail(self, path: str) -> None:
        """Sets the thumbnail file path.

        Args:
            path (str): The thumbnail path.
        """
        self.__thumbnail_file_name = path

    def root_path(self) -> str:
        """Returns the root path.

        Returns:
            str: Root directory path.
        """
        return self.__root_path

    def exists(self) -> bool:
        """Returns True if the path exists, False otherwise.

        Returns:
            bool: Existence state.
        """
        return os.path.exists(self.__root_path)

    def read_json(self, file_name: str) -> dict[str, Any]:
        """Reads data from a json file.

        Args:
            file_name (str): Path to the json file.

        Returns:
            dict[str, Any]: Loaded dictionary data.
        """
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                datas: dict[str, Any] = json.load(f)
            return datas

        except IOError:
            _logger.error("Failed to read: %s", file_name)
            return {}

    def write_json(self, file_name: str, data: Any) -> bool:
        """Writes data to a json file.

        Args:
            file_name (str): Path to the json file.
            data (Any): Data to write.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with open(file_name, "w", encoding="utf-8") as fw:
                json.dump(data, fw, sort_keys=True, indent=4)
            return True

        except IOError:
            _logger.error("Failed to write: %s", file_name)
            return False


class SavePoseOption(QtWidgets.QDialog):
    """Dialog for saving a pose."""

    finished_save: QtCore.Signal = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Dialog,
        output_path: str = "",
    ) -> None:
        """Initializes the Save Pose Option dialog.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to Dialog.
            output_path (str, optional): Target save path. Defaults to "".
        """
        if not parent:
            parent = dcc.get_maya_window()

        super().__init__(parent, flag)
        self.__output_path: str = output_path

        self.setObjectName(f"SavePoseOption{id(self)}")
        self.setWindowTitle("Save Pose Options")
        self.resize(512, 256)

        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        self.setLayout(main_layout)

        viewport_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(viewport_layout, 0, 0)

        label: QtWidgets.QLabel = QtWidgets.QLabel("Thumbnail :", self)
        viewport_layout.addWidget(label)

        self.__viewport: widgets.ViewportCapture = widgets.ViewportCapture(self)
        self.__viewport.set_image_size(256, 256)
        viewport_layout.addWidget(self.__viewport)
        viewport_layout.addStretch(True)

        option_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(option_layout, 0, 1)

        label = QtWidgets.QLabel("Name :", self)
        option_layout.addWidget(label)

        self.__name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        option_layout.addWidget(self.__name)

        label = QtWidgets.QLabel("Comment :", self)
        option_layout.addWidget(label)

        self.__comment: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.__comment.setMaximumHeight(50)
        option_layout.addWidget(self.__comment)

        option_layout.addWidget(widgets.HorizontalLine(self))

        label = QtWidgets.QLabel("Replace Namespace : ", self)
        option_layout.addWidget(label)

        self.__replace_namespace: QtWidgets.QLineEdit = QtWidgets.QLineEdit(
            self
        )
        option_layout.addWidget(self.__replace_namespace)
        option_layout.addStretch(True)

        button = QtWidgets.QPushButton("Save", self)
        button.clicked.connect(self.save)
        main_layout.addWidget(button, 1, 0, 1, 2)

    def save(self) -> None:
        """Saves the pose data."""
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()
        replace_namespace: str = self.__replace_namespace.text()
        if replace_namespace != "" and replace_namespace[-1] != ":":
            replace_namespace += ":"

        if name == "":
            QtWidgets.QMessageBox.critical(
                self,
                "Save Pose Option",
                "A name must be entered to save a pose.",
            )
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QtWidgets.QMessageBox.critical(
                self, "Save Pose Option", "Select node(s) to save a pose."
            )
            return

        namespaces: list[str] = dcc.node.get_namespaces(selection)
        if len(namespaces) >= 2:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Pose Option",
                f"You must select only one asset.\n"
                f"Found name spaces {namespaces}",
            )
            return

        pose = Pose(self.__output_path, name, comment, replace_namespace)
        if pose.exists():
            result: QtWidgets.QMessageBox.StandardButton = (
                QtWidgets.QMessageBox.question(
                    self,
                    "Save Pose Option",
                    "Pose already exists.\nDo you want to override?",
                )
            )
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        if not pose.write(selection):
            return

        if not self.__viewport.capture(pose.thumbnail()):
            return

        self.finished_save.emit(pose.root_path())
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handles the close event for the dialog.

        Args:
            event (QtGui.QCloseEvent): The close event.
        """
        self.__viewport.cleanup()
        super().closeEvent(event)


class SaveAnimationOption(QtWidgets.QDialog):
    """Dialog for saving an animation."""

    finished_save: QtCore.Signal = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Dialog,
        output_path: str = "",
    ) -> None:
        """Initializes the Save Animation Option dialog.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to Dialog.
            output_path (str, optional): Target save path. Defaults to "".
        """
        if not parent:
            parent = dcc.get_maya_window()

        super().__init__(parent, flag)
        self.__output_path: str = output_path

        self.setObjectName(f"SaveAnimationOption{id(self)}")
        self.setWindowTitle("Save Animation Options")
        self.resize(512, 256)

        main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        self.setLayout(main_layout)

        viewport_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(viewport_layout, 0, 0)

        label: QtWidgets.QLabel = QtWidgets.QLabel("Thumbnail :", self)
        viewport_layout.addWidget(label)

        self.__viewport: widgets.ViewportCapture = widgets.ViewportCapture(self)
        self.__viewport.set_image_size(256, 256)
        viewport_layout.addWidget(self.__viewport)
        viewport_layout.addStretch(True)

        option_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(option_layout, 0, 1)

        label = QtWidgets.QLabel("Name :", self)
        option_layout.addWidget(label)

        self.__name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        option_layout.addWidget(self.__name)

        label = QtWidgets.QLabel("Comment :", self)
        option_layout.addWidget(label)

        self.__comment: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.__comment.setMaximumHeight(50)
        option_layout.addWidget(self.__comment)

        option_layout.addWidget(widgets.HorizontalLine(self))

        label = QtWidgets.QLabel("Replace Namespace : ", self)
        option_layout.addWidget(label)

        self.__replace_namespace: QtWidgets.QLineEdit = QtWidgets.QLineEdit(
            self
        )
        option_layout.addWidget(self.__replace_namespace)

        option_layout.addWidget(widgets.HorizontalLine(self))

        self.__is_time_range: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Time Range", self
        )
        self.__is_time_range.clicked.connect(self.update_ui_enabled)
        option_layout.addWidget(self.__is_time_range)

        self.__time_range_layout: QtWidgets.QHBoxLayout = (
            QtWidgets.QHBoxLayout()
        )

        self.__start_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self.__start_frame.setRange(-999999, 999999)
        self.__start_frame.setValue(1)
        self.__time_range_layout.addWidget(self.__start_frame, True)

        self.__time_range_layout.addWidget(QtWidgets.QLabel("-", self))

        self.__end_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self.__end_frame.setRange(-999999, 999999)
        self.__end_frame.setValue(120)
        self.__time_range_layout.addWidget(self.__end_frame, True)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Get", self)
        button.clicked.connect(self.set_time_range_from_current)
        self.__time_range_layout.addWidget(button)
        option_layout.addLayout(self.__time_range_layout)
        option_layout.addStretch(True)

        button = QtWidgets.QPushButton("Save", self)
        button.clicked.connect(self.save)
        main_layout.addWidget(button, 1, 0, 1, 2)
        self.update_ui_enabled()

    def update_ui_enabled(self) -> None:
        """Updates UI element enabled states based on settings."""
        for i in range(self.__time_range_layout.count()):
            widget: QtWidgets.QWidget | None = self.__time_range_layout.itemAt(
                i
            ).widget()
            if widget:
                widget.setEnabled(self.__is_time_range.isChecked())

    def set_time_range_from_current(self) -> None:
        """Sets the time range from the current Maya playback options."""
        self.__start_frame.setValue(
            cmds.playbackOptions(query=True, animationStartTime=True)  # type: ignore
        )
        self.__end_frame.setValue(
            cmds.playbackOptions(query=True, animationEndTime=True)  # type: ignore
        )

    def save(self) -> None:
        """Saves the animation data."""
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()
        replace_namespace: str = self.__replace_namespace.text()
        if replace_namespace != "" and replace_namespace[-1] != ":":
            replace_namespace += ":"

        is_time_range: bool = self.__is_time_range.isChecked()
        start_frame: int | None = None
        end_frame: int | None = None
        if is_time_range:
            start_frame = self.__start_frame.value()
            end_frame = self.__end_frame.value()

        if name == "":
            QtWidgets.QMessageBox.critical(
                self,
                "Save Animation Option",
                "A name must be entered to save an animation.",
            )
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Animation Option",
                "Select node(s) to save an animation.",
            )
            return

        namespaces: list[str] = dcc.node.get_namespaces(selection)
        if len(namespaces) >= 2:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Pose Option",
                f"You must select only one asset.\n"
                f"Found name spaces {namespaces}",
            )
            return

        animation = Animation(
            self.__output_path,
            name,
            comment,
            replace_namespace,
        )
        if animation.exists():
            result: QtWidgets.QMessageBox.StandardButton = (
                QtWidgets.QMessageBox.question(
                    self,
                    "Save Animation Option",
                    "Animation already exists.\nDo you want to override?",
                )
            )
            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        if not animation.write(selection, start_frame, end_frame):
            return

        if not self.__viewport.capture(animation.thumbnail()):
            return

        self.finished_save.emit(animation.root_path())
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handles the close event for the dialog.

        Args:
            event (QtGui.QCloseEvent): The close event.
        """
        self.__viewport.cleanup()
        super().closeEvent(event)


class PoseOption(QtWidgets.QWidget):
    """Widget providing options for applying a pose."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the PoseOption widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        self.__pose: Pose = Pose("", "")
        self.__no_image: QtGui.QPixmap = QtGui.QPixmap(
            dcc.get_icon_path(NO_IMAGE)
        )

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("<h2>Pose</h2>"))

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        scroll_area.setMinimumWidth(ICON_SIZE_RANGE[1] + 40)
        scroll_area.setMinimumHeight(1)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        main_layout.addWidget(scroll_area)

        inner_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        scroll_area.setWidget(inner_widget)

        inner_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        inner_widget.setLayout(inner_layout)

        self.__image: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.__image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.__image.setMinimumSize(ICON_SIZE_RANGE[1], ICON_SIZE_RANGE[1])
        self.__image.setPixmap(self.__no_image)
        inner_layout.addWidget(self.__image)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        fileinfo_layout: widgets.FormLayout = widgets.FormLayout()
        fileinfo_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(fileinfo_layout)

        self.__file_name: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("File Name : ", self.__file_name)

        self.__owner: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Owner : ", self.__owner)

        self.__date: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Date : ", self.__date)

        self.__nodes: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Nodes : ", self.__nodes)

        self.__comment: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.__comment.setReadOnly(True)
        self.__comment.setFixedHeight(45)
        fileinfo_layout.addRow("Comment : ", self.__comment)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        option_layout: widgets.FormLayout = widgets.FormLayout()
        option_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(option_layout)

        self.__method: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.__method.addItems(["Selection", "From File"])
        option_layout.addRow(widgets.FormLabel("Method"), self.__method)

        self.__keyframe: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Keyframe")
        option_layout.addRow("", self.__keyframe)
        inner_layout.addStretch(True)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply)
        button_layout.addWidget(button)

        button = QtWidgets.QPushButton("Select", self)
        button.clicked.connect(self.select)
        button_layout.addWidget(button)

    def set_file(self, pose: Pose) -> None:
        """Sets the current pose file to display.

        Args:
            pose (Pose): The pose instance.
        """
        self.__pose = pose
        self.__pose.read()

        if self.__pose.thumbnail() != "":
            pixmap: QtGui.QPixmap = QtGui.QPixmap(self.__pose.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__pose.title())
        self.__owner.setText(self.__pose.owner())
        self.__date.setText(self.__pose.date())
        self.__nodes.setText(f"{self.__pose.node_count()} Object(s)")
        self.__comment.setText(self.__pose.comment())

    def method(self) -> QtWidgets.QComboBox:
        """Returns the method radio buttons widget.

        Returns:
            QtWidgets.QComboBox: The method widget.
        """
        return self.__method

    def keyframe(self) -> QtWidgets.QCheckBox:
        """Returns the keyframe checkbox widget.

        Returns:
            QtWidgets.QCheckBox: The keyframe widget.
        """
        return self.__keyframe

    @dcc.undo
    def apply(self) -> None:
        """Applies the configured pose data to the scene."""
        self.__pose.apply(
            self.__method.currentIndex(), self.__keyframe.isChecked()
        )

    @dcc.undo
    def select(self) -> None:
        """Selects the nodes associated with this pose."""
        try:
            cmds.select(*self.__pose.nodes())
        except ValueError:
            QtWidgets.QMessageBox.critical(
                self, "Import Pose Option", "Node does not exist."
            )


class AnimationOption(QtWidgets.QWidget):
    """Widget providing options for applying an animation."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the AnimationOption widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        self.__anim: Animation = Animation("", "")
        self.__no_image: QtGui.QPixmap = QtGui.QPixmap(
            dcc.get_icon_path(NO_IMAGE)
        )

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(QtWidgets.QLabel("<h2>Animation</h2>"))

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        scroll_area.setMinimumWidth(ICON_SIZE_RANGE[1] + 40)
        scroll_area.setMinimumHeight(1)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        main_layout.addWidget(scroll_area)

        inner_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        scroll_area.setWidget(inner_widget)

        inner_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        inner_widget.setLayout(inner_layout)

        self.__image: QtWidgets.QLabel = QtWidgets.QLabel(self)
        self.__image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.__image.setMinimumSize(ICON_SIZE_RANGE[1], ICON_SIZE_RANGE[1])
        self.__image.setPixmap(self.__no_image)
        inner_layout.addWidget(self.__image)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        fileinfo_layout: widgets.FormLayout = widgets.FormLayout()
        fileinfo_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(fileinfo_layout)

        self.__file_name: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("File Name : ", self.__file_name)

        self.__owner: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Owner : ", self.__owner)

        self.__date: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Date : ", self.__date)

        self.__nodes: QtWidgets.QLabel = QtWidgets.QLabel(self)
        fileinfo_layout.addRow("Nodes : ", self.__nodes)

        self.__comment: QtWidgets.QTextEdit = QtWidgets.QTextEdit(self)
        self.__comment.setReadOnly(True)
        self.__comment.setFixedHeight(45)
        fileinfo_layout.addRow("Comment : ", self.__comment)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        self.__option_layout: widgets.FormLayout = widgets.FormLayout()
        self.__option_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(self.__option_layout)

        self.__method: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.__method.addItems(["Selection", "From File"])
        self.__option_layout.addRow(widgets.FormLabel("Method"), self.__method)

        self.__remove_anim: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Remove current animation.", self
        )
        self.__remove_anim.clicked.connect(self.update_ui_enabled)
        self.__option_layout.addRow("", self.__remove_anim)

        self.__override: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Override animation.", self
        )
        self.__option_layout.addRow("", self.__override)
        self.__override_id: int = self.__option_layout.row_id()

        self.__is_time_range: QtWidgets.QCheckBox = QtWidgets.QCheckBox(
            "Time Range", self
        )
        self.__is_time_range.clicked.connect(self.update_ui_enabled)
        self.__option_layout.addRow("", self.__is_time_range)

        time_range_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()

        self.__start_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self.__start_frame.setRange(-999999, 999999)
        self.__start_frame.setValue(1)
        self.__start_frame.setButtonSymbols(
            QtWidgets.QSpinBox.ButtonSymbols.NoButtons
        )
        time_range_layout.addWidget(self.__start_frame, True)

        time_range_layout.addWidget(QtWidgets.QLabel("-", self))

        self.__end_frame: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self.__end_frame.setRange(-999999, 999999)
        self.__end_frame.setValue(120)
        self.__end_frame.setButtonSymbols(
            QtWidgets.QSpinBox.ButtonSymbols.NoButtons
        )
        time_range_layout.addWidget(self.__end_frame, True)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Get", self)
        button.clicked.connect(self.set_time_range_from_current)
        time_range_layout.addWidget(button)

        self.__option_layout.addRow("Time Range", time_range_layout)
        self.__time_range_id: int = self.__option_layout.row_id()
        inner_layout.addStretch(True)

        button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.apply)
        button_layout.addWidget(button)

        button = QtWidgets.QPushButton("Select", self)
        button.clicked.connect(self.select)
        button_layout.addWidget(button)

        self.update_ui_enabled()

    def update_ui_enabled(self) -> None:
        """Updates the UI enabled states based on settings."""
        self.__option_layout.set_row_enabled(
            self.__override_id, not self.__remove_anim.isChecked()
        )
        self.__option_layout.set_row_enabled(
            self.__time_range_id, self.__is_time_range.isChecked()
        )

    def set_time_range_from_current(self) -> None:
        """Sets the time range values from Maya's current playback settings."""
        self.__start_frame.setValue(
            cmds.playbackOptions(query=True, animationStartTime=True)  # type: ignore
        )
        self.__end_frame.setValue(
            cmds.playbackOptions(query=True, animationEndTime=True)  # type: ignore
        )

    def set_file(self, anim: Animation) -> None:
        """Sets the animation file to display.

        Args:
            anim (Animation): The animation instance.
        """
        self.__anim = anim
        self.__anim.read()

        if self.__anim.thumbnail() != "":
            pixmap: QtGui.QPixmap = QtGui.QPixmap(self.__anim.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__anim.title())
        self.__owner.setText(self.__anim.owner())
        self.__date.setText(self.__anim.date())
        self.__nodes.setText(f"{self.__anim.node_count()} Object(s)")
        self.__comment.setText(self.__anim.comment())

    def method(self) -> QtWidgets.QComboBox:
        """Returns the method widget.

        Returns:
            QtWidgets.QComboBox: The method radio buttons.
        """
        return self.__method

    def remove_animation(self) -> QtWidgets.QCheckBox:
        """Returns the remove animation checkbox widget.

        Returns:
            QtWidgets.QCheckBox: The remove animation widget.
        """
        return self.__remove_anim

    def override_animation(self) -> QtWidgets.QCheckBox:
        """Returns the override animation checkbox widget.

        Returns:
            QtWidgets.QCheckBox: The override animation widget.
        """
        return self.__override

    def is_time_range(self) -> QtWidgets.QCheckBox:
        """Returns the time range checkbox widget.

        Returns:
            QtWidgets.QCheckBox: The time range widget.
        """
        return self.__is_time_range

    def start_frame(self) -> QtWidgets.QSpinBox:
        """Returns the start frame spinbox widget.

        Returns:
            QtWidgets.QSpinBox: The start frame widget.
        """
        return self.__start_frame

    def end_frame(self) -> QtWidgets.QSpinBox:
        """Returns the end frame spinbox widget.

        Returns:
            QtWidgets.QSpinBox: The end frame widget.
        """
        return self.__end_frame

    @dcc.undo
    def apply(self) -> None:
        """Applies the configured animation data to the scene."""
        start_frame: int | None = None
        end_frame: int | None = None
        if self.__is_time_range.isChecked():
            start_frame = self.__start_frame.value()
            end_frame = self.__end_frame.value()

        self.__anim.apply(
            self.__method.currentIndex(),
            self.__remove_anim.isChecked(),
            self.__override.isChecked(),
            start_frame,
            end_frame,
        )

    @dcc.undo
    def select(self) -> None:
        """Selects the nodes from the saved animation data."""
        try:
            cmds.select(*self.__anim.nodes())
        except ValueError:
            QtWidgets.QMessageBox.critical(
                self, "Import Anim Option", "Node does not exist."
            )


class MainWindow(framework.ToolWindow[Settings]):
    """Main window orchestrating the Anim Library interface."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window context.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): An identifier for restoring state.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(1280, 720)
        self.__file_browser: widgets.FileBrowser
        self.__stack_option: QtWidgets.QStackedWidget
        self.__pose_option: PoseOption
        self.__anim_option: AnimationOption

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface elements.

        Args:
            parent (QtWidgets.QWidget): The parent widget for UI containment.
        """
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        # File Brower
        self.__file_browser = widgets.FileBrowser(self)
        self.__file_browser.item_selected.connect(self.on_item_selected)
        self.__file_browser.add_file_view_button(
            1,
            "New Pose",
            "a_add_pose.png",
            self.show_new_pose_option,
        )
        self.__file_browser.add_file_view_button(
            2,
            "New Animation",
            "a_add_motion.png",
            self.show_new_animation_option,
        )
        layout.addWidget(self.__file_browser)

        # Option Widget
        self.__stack_option = QtWidgets.QStackedWidget(self)
        self.__file_browser.add_option_widget(self.__stack_option)

        self.__pose_option = PoseOption(self)
        self.__anim_option = AnimationOption(self)
        self.__stack_option.addWidget(QtWidgets.QWidget(self))
        self.__stack_option.addWidget(self.__pose_option)
        self.__stack_option.addWidget(self.__anim_option)

        # Load standard settings
        self.load_settings()

    @QtCore.Slot(widgets.FileBrowserItem)
    def on_item_selected(self, file_item: widgets.FileBrowserItem) -> None:
        """Handles the callback when a file item is selected.

        Args:
            file_item (widgets.FileBrowserItem): The selected file item.
        """
        extension: str = file_item.extension()
        if extension == "pose":
            self.__stack_option.setCurrentIndex(1)
            pose: Pose = Pose.from_path(file_item.data_path())
            pose.set_thumbnail(file_item.icon_path())
            self.__pose_option.set_file(pose)

        elif extension == "anim":
            self.__stack_option.setCurrentIndex(2)
            anim: Animation = Animation.from_path(file_item.data_path())
            anim.set_thumbnail(file_item.icon_path())
            self.__anim_option.set_file(anim)

        else:
            self.__stack_option.setCurrentIndex(0)

    @QtCore.Slot(str)
    def on_item_saved(self, path: str) -> None:
        """Handles the callback after an item has been saved.

        Args:
            path (str): The path to the newly saved item.
        """
        self.__file_browser.add_item(path)

    def show_new_pose_option(self, path: str) -> None:
        """Displays the dialog for saving a new pose.

        Args:
            path (str): The output directory path.
        """
        option: SavePoseOption = SavePoseOption(output_path=path)
        option.finished_save.connect(self.on_item_saved)
        option.show()

    def show_new_animation_option(self, path: str) -> None:
        """Displays the dialog for saving a new animation.

        Args:
            path (str): The output directory path.
        """
        option: SaveAnimationOption = SaveAnimationOption(output_path=path)
        option.finished_save.connect(self.on_item_saved)
        option.show()

    def load_settings(self) -> None:
        """Loads the UI settings from file."""
        settings: Settings = self.tool_settings()
        self.restoreGeometry(utils.ascii_to_qt(settings.window_geo.value()))
        self.__file_browser.splitter_widget().restoreState(
            utils.ascii_to_qt(settings.splitter_state.value())
        )
        self.__file_browser.set_root_path(settings.root_dir.value())
        self.__file_browser.set_filter_text(settings.filter.value())
        self.__file_browser.set_icon_range(
            settings.icon_size.value(), ICON_SIZE_RANGE[0], ICON_SIZE_RANGE[1]
        )

        # Pose
        self.__pose_option.method().setCurrentIndex(
            settings.pose_method.value()
        )
        self.__pose_option.keyframe().setChecked(settings.pose_keyframe.value())

        # Anim
        self.__anim_option.method().setCurrentIndex(
            settings.anim_method.value()
        )
        self.__anim_option.remove_animation().setChecked(
            settings.remove_animation.value()
        )
        self.__anim_option.override_animation().setChecked(
            settings.override_animation.value()
        )
        self.__anim_option.is_time_range().setChecked(
            settings.is_time_range.value()
        )
        self.__anim_option.start_frame().setValue(settings.start_frame.value())
        self.__anim_option.end_frame().setValue(settings.end_frame.value())

    def save_settings(self) -> None:
        """Saves the current UI settings to file."""
        settings: Settings = self.tool_settings()

        settings.window_geo.set_value(utils.qt_to_ascii(self.saveGeometry()))
        settings.splitter_state.set_value(
            utils.qt_to_ascii(self.__file_browser.splitter_widget().saveState())
        )
        settings.root_dir.set_value(self.__file_browser.root_path())
        settings.filter.set_value(self.__file_browser.filter())
        settings.icon_size.set_value(self.__file_browser.icon_size())

        # Pose
        settings.pose_method.set_value(
            self.__pose_option.method().currentIndex()
        )
        settings.pose_keyframe.set_value(
            self.__pose_option.keyframe().isChecked()
        )

        # Anim
        settings.anim_method.set_value(
            self.__anim_option.method().currentIndex()
        )
        settings.remove_animation.set_value(
            self.__anim_option.remove_animation().isChecked()
        )
        settings.override_animation.set_value(
            self.__anim_option.override_animation().isChecked()
        )
        settings.is_time_range.set_value(
            self.__anim_option.is_time_range().isChecked()
        )
        settings.start_frame.set_value(self.__anim_option.start_frame().value())
        settings.end_frame.set_value(self.__anim_option.end_frame().value())
        settings.write()

    def reset_settings(self) -> None:
        """Resets the UI settings to their defaults."""
        settings: Settings = self.tool_settings()
        settings.reset()
        self.load_settings()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handles the close event to save settings.

        Args:
            event (QtGui.QCloseEvent): The close event.
        """
        self.save_settings()
        super().closeEvent(event)


def main(unique_id: str = "") -> None:
    """Launches the Anim Library tool window.

    Args:
        unique_id (str, optional): A unique identifier for restoring
            window states. Defaults to "".
    """
    dcc.plugin.load(PLUGINS)
    if not os.path.exists(ROOT_DIR):
        try:
            os.makedirs(ROOT_DIR)

        except IOError as e:
            _logger.error("Failed to make folder. %s", e)

    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
