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
"""Connects UV links for multiple specified nodes."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils

__product__: str = "UV Linker"
__version__: str = "1.20"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the tool.

    Attributes:
        window_geo (framework.Variant[str]): The saved window geometry.
    """

    window_geo: framework.Variant[str] = framework.Variant("")


class ItemListWidget(QtWidgets.QWidget):
    """Widget for displaying and managing a list of items.

    Attributes:
        current_changed (QtCore.Signal): Signal emitted when the current item
            selection changes.
    """

    current_changed: QtCore.Signal = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self.__tree = QtWidgets.QTreeWidget(self)
        self.__tree.setColumnCount(1)
        self.__tree.setHeaderLabel("")
        self.__tree.setAlternatingRowColors(True)
        self.__tree.setRootIsDecorated(False)
        self.__tree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.__tree.currentItemChanged.connect(self.on_current_changed)
        main_layout.addWidget(self.__tree)

    def on_current_changed(
        self,
        current: QtWidgets.QTreeWidgetItem | None,
        _previous: QtWidgets.QTreeWidgetItem | None,
    ) -> None:
        """Handles the current item change event.

        Args:
            current (QtWidgets.QTreeWidgetItem | None): The newly selected item.
            previous (QtWidgets.QTreeWidgetItem | None): The previously selected
                item.
        """
        if current is None:
            return

        self.current_changed.emit(current.text(0))

    def set_header_text(self, text: str) -> None:
        """Sets the header text for the list view.

        Args:
            text (str): The header text to display.
        """
        self.__tree.setHeaderLabel(text)

    def get_items(self) -> list[str]:
        """Returns the text of all items in the widget.

        Returns:
            list[str]: A list of item strings.
        """
        return [
            self.__tree.topLevelItem(i).text(0)
            for i in range(self.__tree.topLevelItemCount())
        ]

    def set_items(self, texts: list[str]) -> None:
        """Sets the items in the widget based on the provided text list.

        Args:
            texts (list[str]): A list of string labels for the items.
        """
        self.clear_items()
        icon_path: str = dcc.get_icon_path("view/a_null.png")
        icon: QtGui.QIcon = QtGui.QIcon(icon_path)

        for text in texts:
            item = QtWidgets.QTreeWidgetItem([text])
            item.setIcon(0, icon)
            self.__tree.addTopLevelItem(item)

    def set_icon(self, target_label: str, icon_name: str) -> None:
        """Sets the icon of an item matching the specified label.

        Args:
            target_label (str): The text label of the target item.
            icon_name (str): The name of the icon file to apply.
        """
        items: list[QtWidgets.QTreeWidgetItem] = self.__tree.findItems(
            target_label, QtCore.Qt.MatchFlag.MatchExactly, 0
        )
        icon_path: str = dcc.get_icon_path(icon_name)
        icon: QtGui.QIcon = QtGui.QIcon(icon_path)
        for item in items:
            item.setIcon(0, icon)

    def clear_items(self) -> None:
        """Clears all items from the widget."""
        self.__tree.clear()

    def get_selected_item(self) -> str:
        """Returns the label of the currently selected item.

        Returns:
            str: The text of the selected item, or an empty string if nothing
                is selected.
        """
        item: QtWidgets.QTreeWidgetItem | None = self.__tree.currentItem()
        if item is None:
            return ""

        return item.text(0)


class MainWindow(framework.ToolWindow[Settings]):
    """Main window for the UV Linker tool."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Window.
            unique_id (str, optional): A unique ID for restoring window states.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        self.__geometries: list[str] = []
        self.__uv_set_view: ItemListWidget
        self.__texture_view: ItemListWidget

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout = QtWidgets.QGridLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__uv_set_view = ItemListWidget(parent)
        self.__uv_set_view.set_header_text("UV Sets")
        self.__uv_set_view.current_changed.connect(self.__update_link_icon)
        main_layout.addWidget(self.__uv_set_view, 0, 0)

        self.__texture_view = ItemListWidget(parent)
        self.__texture_view.set_header_text("Textures")
        main_layout.addWidget(self.__texture_view, 0, 1)

        button_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout, 1, 0, 1, 2)

        analyze_btn = QtWidgets.QPushButton("Analyze", parent)
        analyze_btn.clicked.connect(self.analyze_action)
        button_layout.addWidget(analyze_btn)

        connect_btn = QtWidgets.QPushButton("Connect", parent)
        connect_btn.clicked.connect(self.connect_action)
        button_layout.addWidget(connect_btn)

        disconnect_btn = QtWidgets.QPushButton("Disconnect", parent)
        disconnect_btn.clicked.connect(self.disconnect_action)
        button_layout.addWidget(disconnect_btn)

        clear_btn = QtWidgets.QPushButton("Clear", parent)
        clear_btn.clicked.connect(self.clear_action)
        button_layout.addWidget(clear_btn)

        close_btn = QtWidgets.QPushButton("Close", parent)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )

    def __update_link_icon(self, uv_set_name: str) -> None:
        """Updates the link icons based on the selected UV set.

        Args:
            uv_set_name (str): The name of the selected UV set.
        """
        textures: list[str] = self.__texture_view.get_items()
        for texture in textures:
            self.__texture_view.set_icon(texture, "view/a_null.png")

        all_linked_textures: list[list[str]] = []
        for node in self.__geometries:
            index: int = find_uv_set_id_from_name(node, uv_set_name)
            linked_textures: list[str] = cmds.uvLink(
                query=True,
                uvSet=f"{node}.uvSet[{index}].uvSetName",
            )  # type: ignore
            all_linked_textures.append(linked_textures)

        for texture in linked_textures:
            self.__texture_view.set_icon(texture, "view/a_link.png")

        incomplete_link: list[str] = []
        for i in range(0, len(all_linked_textures) - 1, 1):
            incomplete_link.extend(
                set(all_linked_textures[i]) ^ set(all_linked_textures[i + 1])
            )

        for texture in incomplete_link:
            self.__texture_view.set_icon(texture, "view/a_incomplete_link.png")

    @dcc.undo
    def analyze_action(self) -> None:
        """Analyzes selected nodes and displays UV sets and textures."""
        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QtWidgets.QMessageBox.warning(
                self, __product__, "Select geometries to be UV linked."
            )
            return

        uv_sets: list[str] = get_same_uv_set_names(selection)
        uv_sets.sort()

        materials: list[str] = get_materials_from_geometries(selection)
        textures: list[str] = []
        for material in materials:
            textures.extend(get_textures_from_material(material))

        textures.sort()
        self.__geometries = selection
        self.__uv_set_view.set_items(uv_sets)
        self.__texture_view.set_items(textures)

    @dcc.undo
    def clear_action(self) -> None:
        """Clears all items in the lists and resets geometries."""
        self.__geometries.clear()
        self.__uv_set_view.clear_items()
        self.__texture_view.clear_items()

    @dcc.undo
    def connect_action(self) -> None:
        """Connects the UV link based on the selected items in the views."""
        self.save_settings()
        connect_uv_links(
            self.__geometries,
            self.__uv_set_view.get_selected_item(),
            self.__texture_view.get_selected_item(),
        )
        self.__update_link_icon(self.__uv_set_view.get_selected_item())

    @dcc.undo
    def disconnect_action(self) -> None:
        """Disconnects the UV link based on the selected items in the views."""
        self.save_settings()
        disconnect_uv_links(
            self.__geometries,
            self.__uv_set_view.get_selected_item(),
            self.__texture_view.get_selected_item(),
        )
        self.__update_link_icon(self.__uv_set_view.get_selected_item())


def connect_uv_link(node: str, uv_set_name: str, texture: str) -> bool:
    """Connects a UV link for a specified node and UV set name.

    Args:
        node (str): The target node name.
        uv_set_name (str): The name of the UV set.
        texture (str): The name of the texture node.

    Returns:
        bool: True if successful, False otherwise.
    """
    index: int = find_uv_set_id_from_name(node, uv_set_name)
    if index == -1:
        return False

    cmds.uvLink(uvSet=f"{node}.uvSet[{index}].uvSetName", texture=texture)
    return True


def connect_uv_links(nodes: list[str], uv_set_name: str, texture: str) -> bool:
    """Connects UV links for multiple specified nodes and a UV set name.

    Args:
        nodes (list[str]): A list of target node names.
        uv_set_name (str): The name of the UV set.
        texture (str): The name of the texture node.

    Returns:
        bool: True if all connections were successful, False otherwise.
    """
    result: list[bool] = []
    for node in nodes:
        r: bool = connect_uv_link(node, uv_set_name, texture)
        if not r:
            _logger.error("UV set name not found: %s / %s", node, uv_set_name)
            continue

        result.append(r)

    if all(result):
        _logger.info("Done.")
        return True

    return False


def disconnect_uv_link(node: str, uv_set_name: str, texture: str) -> bool:
    """Disconnects a UV link from a specified node and UV set name.

    Args:
        node (str): The target node name.
        uv_set_name (str): The name of the UV set.
        texture (str): The name of the texture node.

    Returns:
        bool: True if successful, False otherwise.
    """
    index: int = find_uv_set_id_from_name(node, uv_set_name)
    if index == -1:
        return False

    cmds.uvLink(
        b=True, uvSet=f"{node}.uvSet[{index}].uvSetName", texture=texture
    )
    return True


def disconnect_uv_links(
    nodes: list[str], uv_set_name: str, texture: str
) -> bool:
    """Disconnects UV links for multiple specified nodes and a UV set name.

    Args:
        nodes (list[str]): A list of target node names.
        uv_set_name (str): The name of the UV set.
        texture (str): The name of the texture node.

    Returns:
        bool: True if all disconnections were successful, False otherwise.
    """
    result: list[bool] = []
    for node in nodes:
        r: bool = disconnect_uv_link(node, uv_set_name, texture)
        if not r:
            _logger.error("UV set name not found: %s / %s", node, uv_set_name)
            continue

        result.append(r)

    if all(result):
        _logger.info("Done.")
        return True

    return False


def get_uv_set_names(node: str) -> list[str]:
    """Retrieves all UV set names associated with the given node.

    Args:
        node (str): The target node name.

    Returns:
        list[str]: A list of UV set names.
    """
    uv_indexes: list[int] = cmds.getAttr(f"{node}.uvSet", multiIndices=True)
    if not uv_indexes:
        return []

    result: list[str] = []
    for index in uv_indexes:
        uv_set_name: str = get_uv_set_name(node, index)
        if uv_set_name == "":
            continue

        result.append(uv_set_name)

    return result


def get_uv_set_name(node: str, index: int) -> str:
    """Retrieves the UV set name from a specific ID.

    Args:
        node (str): The target node name.
        index (int): The UV set ID index.

    Returns:
        str: The UV set name.
    """
    return cmds.getAttr(f"{node}.uvSet[{index}].uvSetName") or ""


def get_same_uv_set_names(nodes: list[str]) -> list[str]:
    """Returns common UV set names shared among specified nodes.

    Args:
        nodes (list[str]): A list of target node names.

    Returns:
        list[str]: A list of shared UV set names.
    """
    result: list[str] = []
    for node in nodes:
        uv_set_names: list[str] = get_uv_set_names(node)
        if not uv_set_names:
            continue

        if not result:
            result = uv_set_names
        else:
            result = list(set(result) & set(uv_set_names))

    return result


def find_uv_set_id_from_name(node: str, uv_set_name: str) -> int:
    """Returns the UV set ID corresponding to a given UV set name.

    Args:
        node (str): The target node name.
        uv_set_name (str): The name of the UV set.

    Returns:
        int: The matching UV set index, or -1 if not found.
    """
    result = -1
    uv_indexes: list[int] = cmds.getAttr(f"{node}.uvSet", multiIndices=True)
    if not uv_indexes:
        return result

    for index in uv_indexes:
        if uv_set_name == get_uv_set_name(node, index):
            return index

    return result


def get_textures_from_material(node: str) -> list[str]:
    """Retrieves texture nodes connected to a specified material.

    Args:
        node (str): The target material node name.

    Returns:
        list[str]: A list of connected texture node names.
    """
    result: list[str] = []
    connected_nodes: list[str] = cmds.listHistory(node)  # type: ignore
    for connected_node in connected_nodes:
        node_type: str = cmds.nodeType(connected_node, derived=True)[0]
        classification: list[str] = cmds.getClassification(node_type) or []
        if not classification:
            continue

        if classification[0].find("texture/2d") != -1:
            result.append(connected_node)

    return result


def get_materials_from_geometries(nodes: list[str]) -> list[str]:
    """Retrieves materials assigned to the specified geometries.

    Args:
        nodes (list[str]): A list of geometry node names.

    Returns:
        list[str]: A list of material node names.
    """
    cmds.hyperShade(shaderNetworksSelectMaterialNodes=True)
    result: list[str] = cmds.ls(selection=True)
    cmds.select(*nodes)
    return result


def main(unique_id: str = "") -> None:
    """Shows the tool window.

    Args:
        unique_id (str, optional): A unique identifier for the window.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
