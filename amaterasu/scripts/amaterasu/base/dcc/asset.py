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
"""Operations and data models for managing external file dependencies in Maya.

This module provides a class and functions to easily manipulate external
files linked to Maya nodes, such as textures, image planes, and references.
"""

from __future__ import annotations
import os
import time
from maya import cmds
from amaterasu.base import utils

_logger: utils.Logger = utils.get_logger("dcc.file_node")

SUPPORTED_NODE_TYPES: tuple[tuple[str, str], ...] = (
    ("File", "file"),
    ("Image Plane", "imagePlane"),
    ("Reference", "reference"),
)


class AssetFile:
    """Represents a Maya node that has an external file dependency.

    Provides properties and methods to retrieve and modify both the DCC
    node attributes and the OS-level file information (size, dates, etc.).
    """

    def __init__(self, node_name: str) -> None:
        """Initializes the ExternalFileNode.

        Args:
            node_name (str): The name of the Maya node.
        """
        self.__node: str = node_name
        self.__node_type: str = cmds.objectType(node_name)  # type: ignore
        self.__file_name: str = ""
        self.__sequence: list[str] = []

        if self.__node_type == "file":
            self.__file_name = cmds.getAttr(f"{node_name}.fileTextureName")

        elif self.__node_type == "reference":
            self.__file_name = cmds.referenceQuery(node_name, filename=True)  # type: ignore

        elif self.__node_type == "imagePlane":
            self.__file_name = cmds.getAttr(f"{node_name}.imageName")

        self.__file_name = self.__file_name.replace("\\", "/")
        self.__display_file_name: str = self.base_name()

        self.parse_sequence()

    def parse_sequence(self) -> None:
        """Parses the file path to detect and build a sequence list."""
        if not self.__file_name:
            return

        temp: list[str] = self.__file_name.split(".")
        if len(temp) >= 2 and temp[-2].isdigit():
            padding: int = len(temp[-2])
            start: int = int(temp[-2])
            format_str: str = self.__file_name.replace(
                temp[-2], f"%0{padding}i"
            )

            while True:
                start += 1
                seq_file_name: str = format_str % start
                if not os.path.exists(seq_file_name):
                    break

                self.__sequence.append(seq_file_name)

            if len(self.__sequence) > 1:
                display_format: str = "[" + ("#" * padding) + "]"
                self.__display_file_name = self.__file_name.replace(
                    temp[-2], display_format
                )

    def change_file_path(self, new_file_path: str) -> None:
        """Changes the file path attribute on the Maya node.

        Args:
            new_file_path (str): The new file path to set.
        """
        self.__file_name = new_file_path.replace("\\", "/")

        if self.__node_type == "file":
            plug: str = f"{self.node}.fileTextureName"
            cmds.setAttr(plug, new_file_path, type="string")

        elif self.__node_type == "reference":
            cmds.file(new_file_path, loadReference=self.node())

        elif self.__node_type == "imagePlane":
            plug = f"{self.node}.imageName"
            cmds.setAttr(plug, new_file_path, type="string")

    def node(self) -> str:
        """str: The Maya node name."""
        return self.__node

    def node_type(self) -> str:
        """str: The Maya node type."""
        return self.__node_type

    def file_name(self) -> str:
        """str: The full path to the external file."""
        return self.__file_name

    def display_file_name(self) -> str:
        """str: The formatted file name for sequence display."""
        return self.__display_file_name

    def display_short_file_name(self) -> str:
        """str: The base name of the display file name."""
        return os.path.basename(self.__display_file_name)

    def sequence(self) -> list[str]:
        """list[str]: A list of full paths for all files in the sequence."""
        return self.__sequence

    def base_name(self) -> str:
        """str: The base name of the file."""
        return os.path.basename(self.__file_name)

    def dir_name(self) -> str:
        """str: The directory name containing the file."""
        return os.path.dirname(self.__file_name)

    def is_valid(self) -> bool:
        """bool: True if the file exists on the OS, False otherwise."""
        if not self.__file_name:
            return False
        return os.path.exists(self.__file_name.split("{")[0])

    def date_accessed(self) -> str:
        """str: Formatted last accessed date string."""
        if not self.is_valid():
            return ""

        return format_time(os.path.getatime(self.file_name()))

    def date_modified(self) -> str:
        """str: Formatted last modified date string."""
        if not self.is_valid():
            return ""

        return format_time(os.path.getmtime(self.file_name()))

    def date_changed(self) -> str:
        """str: Formatted creation/change date string."""
        if not self.is_valid():
            return ""

        return format_time(os.path.getctime(self.file_name()))

    def file_size_string(self) -> str:
        """str: Human-readable file size (e.g., '1.50 MB')."""
        if not self.is_valid():
            return "0 byte"

        bytes_size: float = float(os.path.getsize(self.file_name()))
        return format_size(bytes_size)


def format_time(seconds: float) -> str:
    """Formats a timestamp into a readable string.

    Args:
        seconds (float): The time in seconds since the epoch.

    Returns:
        str: A formatted time string (e.g., 'Jan, 01, 2026, 12:00 PM').
    """
    try:
        t: time.struct_time = time.gmtime(seconds)
        return time.strftime("%b, %d, %Y, %H:%M %p", t)

    except ValueError:
        return ""


def format_size(bytes_size: float) -> str:
    """Formats byte sizes into human-readable strings.

    Args:
        bytes_size (float): The size in bytes.

    Returns:
        str: A formatted string representing the size (e.g., '1.50 MB').
    """
    if bytes_size >= 1099511627776:
        return f"{bytes_size / 1099511627776:0.2f} TB"

    if bytes_size >= 1073741824:
        return f"{bytes_size / 1073741824:0.2f} GB"

    if bytes_size >= 1048576:
        return f"{bytes_size / 1048576:0.2f} MB"

    if bytes_size >= 1024:
        return f"{bytes_size / 1024:0.2f} KB"

    return f"{bytes_size:0.2f} byte"


def get_external_nodes(node_type: str) -> list[AssetFile]:
    """Retrieves a list of ExternalFileNode objects for a given type.

    Args:
        node_type (str): The Maya node type to query.

    Returns:
        list[ExternalFileNode]: A list of external file node instances.
    """
    file_nodes: list[AssetFile] = []
    nodes: list[str] = cmds.ls(type=node_type) or []

    for node in nodes:
        if node == "sharedReferenceNode":
            continue

        node = node.split("->")[-1]
        file_node_inst: AssetFile = AssetFile(node)
        if file_node_inst.file_name():
            file_nodes.append(file_node_inst)

    return file_nodes
