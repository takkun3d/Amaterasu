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
"""Amaterasu Menus Construction.

Handles the creation of Amaterasu menus in the main window and channel box,
leveraging the amaterasu.base framework for UI and settings.
"""

from __future__ import annotations
from typing import cast
from types import ModuleType
import importlib
import json
import pathlib
from functools import partial
from typing import Any
from maya import cmds, mel
from amaterasu.base import framework, dcc, utils
from amaterasu.base.qt import QtCore, QtGui, QtWidgets

MAIN_MENU_NAME: str = "AmaterasuMenu"
MAIN_MENU_LABEL: str = "Amaterasu"
CB_MENU_NAME: str = "AmaterasuChannelBoxMenu"
CB_MENU_LABEL: str = "A"
SHELF_ICON: str = "a_shelf.png"
MAX_HISTORY: int = 10
ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent
JSON_PATH: pathlib.Path = (
    ROOT_PATH.parent.parent / "resource" / "data" / "menu.json"
)


class Settings(framework.ToolSettings):
    """Settings for managing menu state and recent tools history.

    Attributes:
        recent_tools (framework.Variant[list[dict[str, str]]]): A list of
            dictionaries storing the recent tools history.
    """

    recent_tools: framework.Variant[list[dict[str, str]]] = framework.Variant(
        []
    )

    def add_history(self, label: str, module_path: str, func_name: str) -> None:
        """Adds a tool to the recent tools history.

        If the tool already exists in the history, it will be moved to the top.
        The history is truncated to keep only the latest `MAX_HISTORY` items.

        Args:
            label (str): The display label of the tool.
            module_path (str): The Python module path
                (e.g., 'amaterasu.tools.my_tool').
            func_name (str): The function name to execute (e.g., 'main()').
        """
        history: list[dict[str, str]] = self.recent_tools.value()
        history = [
            item
            for item in history
            if not (item["module"] == module_path and item["func"] == func_name)
        ]

        history.insert(
            0, {"label": label, "module": module_path, "func": func_name}
        )
        history = history[:MAX_HISTORY]
        self.recent_tools.set_value(history)
        self.write()


class Menu:
    """Context manager for creating Maya menus.

    Allows building Maya menus elegantly using Python's `with` statement.
    """

    def __init__(self, object_name: str = "", **kwargs: Any) -> None:
        """Initializes the Menu context manager.

        Args:
            object_name (str, optional): The internal name of the Maya menu.
                Defaults to "".
            **kwargs (Any): Additional arguments passed to `cmds.menu`.
        """
        self.__object_name: str = object_name
        self.__kwargs: dict[str, Any] = kwargs
        if "tearOff" not in self.__kwargs:
            self.__kwargs["tearOff"] = True

    def __enter__(self) -> Menu:
        """Creates the Maya menu and enters the context.

        Returns:
            Menu: The current Menu instance.
        """
        if self.__object_name:
            if cmds.menu(self.__object_name, exists=True):
                cmds.deleteUI(self.__object_name)

            cmds.menu(self.__object_name, **self.__kwargs)
        else:
            cmds.menu(**self.__kwargs)

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exits the context by setting the Maya parent one level up."""
        cmds.setParent("..", menu=True)

    @staticmethod
    def create_python_command(module_path: str, func_name: str) -> str:
        """Generates a Python command string for the menu item.

        Args:
            module_path (str): The Python module path.
            func_name (str): The function name to execute.

        Returns:
            str: The formatted Python command string.
        """
        return f"import {module_path}\n{module_path}.{func_name}"

    def add_item(
        self,
        label: str,
        module: str,
        main_func: str = "main()",
        option_func: str | None = None,
        is_window_only: bool = False,
        **kwargs: Any,
    ) -> None:
        """Adds a menu item with optional settings and history tracking.

        Args:
            label (str): The display label of the menu item.
            module (str): The Python module path.
            main_func (str, optional): The primary function to execute.
                Defaults to "main()".
            option_func (str | None, optional): The function to execute for
                the option box. Defaults to None.
            is_window_only (bool, optional): If True, appends '...' to
                the label. Defaults to False.
            **kwargs (Any): Additional arguments passed to `cmds.menuItem`.
        """

        if is_window_only and not label.endswith("..."):
            label += "..."

        command: str = self.create_python_command(module, main_func)
        menu_item: str = cmds.menuItem(
            label=label,
            command=command,
            sourceType="python",
            **kwargs,
        )  # type: ignore

        settings: Settings = Settings.instance(__name__, True)
        action: QtGui.QAction | None = dcc.find_menu_item(
            menu_item, QtGui.QAction
        )
        if action is not None:
            action.triggered.connect(
                partial(settings.add_history, label, module, main_func)
            )

        if option_func:
            base_label: str = label[:-3] if label.endswith("...") else label
            option_label: str = f"{base_label} Option"
            command = self.create_python_command(module, option_func)
            menu_item = cmds.menuItem(
                label=option_label,
                command=command,
                sourceType="python",
                optionBox=True,
            )  # type: ignore

            action = dcc.find_menu_item(menu_item, QtGui.QAction)
            if action is not None:
                action.triggered.connect(
                    partial(
                        settings.add_history, option_label, module, option_func
                    )
                )

    def add_divider(self, label: str | None = None) -> None:
        """Adds a visual divider to the menu.

        Args:
            label (str | None, optional): Optional text label for the divider.
                Defaults to None.
        """
        if label:
            cmds.menuItem(divider=True, dividerLabel=label)
        else:
            cmds.menuItem(divider=True)


class SubMenu(Menu):
    """Context manager for creating Maya submenus."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the SubMenu context manager.

        Args:
            *args (Any): Positional arguments passed to `cmds.menuItem`.
            **kwargs (Any): Keyword arguments passed to `cmds.menuItem`.
        """
        super().__init__(*args, **kwargs)
        self.__args: tuple[Any, ...] = args
        self.__kwargs: dict[str, Any] = kwargs
        if "tearOff" not in self.__kwargs:
            self.__kwargs["tearOff"] = True

        if "subMenu" not in self.__kwargs:
            self.__kwargs["subMenu"] = True

        if "allowOptionBoxes" not in self.__kwargs:
            self.__kwargs["allowOptionBoxes"] = True

    def __enter__(self) -> SubMenu:
        """Creates the Maya submenu item and enters the context.

        Returns:
            SubMenu: The current SubMenu instance.
        """
        cmds.menuItem(*self.__args, **self.__kwargs)
        return self


class MayaContextMenuFilter(QtCore.QObject):
    """Event filter to handle right-clicks on Maya menu items.

    Detects right-click events on the target menu to display the dynamic
    recent tools history QMenu.
    """

    def __init__(
        self,
        target_menu_name: str,
        menu_builder: MenuBuilder,
        parent: QtCore.QObject | None = None,
    ) -> None:
        """Initializes the MayaContextMenuFilter.

        Args:
            target_menu_name (str): The objectName of the target menu to filter.
            menu_builder (MenuBuilder): The builder instance to generate
                the history menu.
            parent (QtCore.QObject | None, optional): The parent QObject.
                Defaults to None.
        """
        super().__init__(parent)
        self.__target_menu_name: str = target_menu_name
        self.__menu_builder: MenuBuilder = menu_builder

    def eventFilter(
        self,
        watched: QtCore.QObject,
        event: QtCore.QEvent,
    ) -> bool:
        """Intercepts events on the menu bar.

        Args:
            watched (QtCore.QObject): The monitored menu bar.
            event (QtCore.QEvent): The Qt event.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        menu_bar: QtWidgets.QMenuBar = cast(QtWidgets.QMenuBar, watched)
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            event = cast(QtGui.QMouseEvent, event)
            if event.button() == QtCore.Qt.MouseButton.RightButton:
                action: QtGui.QAction = menu_bar.actionAt(event.pos())
                if (
                    action
                    and action.menu()
                    and action.menu().objectName() == self.__target_menu_name
                ):
                    self.__menu_builder.build_history_qmenu(menu_bar, action)
                    return True

        return super().eventFilter(menu_bar, event)


class MenuBuilder(utils.Singleton):
    """Constructs the Amaterasu menus from a JSON configuration file."""

    def __init__(self, json_path: pathlib.Path) -> None:
        """Initializes the MenuBuilder.

        Args:
            json_path (pathlib.Path): The path to the menu JSON configuration file.
        """
        self.__json_path: pathlib.Path = json_path
        self.__menu_data: dict[str, Any] | None = None
        self.__event_filter: MayaContextMenuFilter | None = None

    def load_data(self) -> dict[str, Any]:
        """Loads and returns the menu structure from the JSON file.

        Returns:
            dict[str, Any]: The loaded menu configuration data.
        """
        if self.__menu_data is not None:
            return self.__menu_data

        if not self.__json_path.exists():
            self.__menu_data = {"MAIN_MENU": [], "CHANNEL_BOX_MENU": []}
            return self.__menu_data

        with open(self.__json_path, "r", encoding="utf-8") as f:
            self.__menu_data = json.load(f)

        return self.__menu_data

    def build_items(self, menu: Menu, items: list[dict[str, Any]]) -> None:
        """Recursively builds menu items and submenus from the parsed data.

        Args:
            menu (Menu): The parent Menu or SubMenu context manager.
            items (list[dict[str, Any]]): A list of item configurations.
        """
        for item in items:
            if "divider" in item:
                val: str | bool = item["divider"]
                divide_label: str | None = val if isinstance(val, str) else None
                menu.add_divider(divide_label)

            elif "items" in item:
                kwargs: dict[str, Any] = {"label": item["label"]}
                args: list[str] = []
                if "name" in item:
                    args.append(item["name"])

                if "postMenuCommand" in item:
                    kwargs["postMenuCommand"] = item["postMenuCommand"]

                with SubMenu(*args, **kwargs) as sub:
                    self.build_items(sub, item["items"])

            else:
                kwargs = item.copy()
                label: str = kwargs.pop("label")
                module: str = kwargs.pop("module")
                menu.add_item(label, module, **kwargs)

    def build_main_menu(self) -> None:
        """Builds the primary Amaterasu menu in the Maya main window."""
        cmds.setParent(mel.eval("$gMainWindow=$gMainWindow"))
        data: list[dict[str, Any]] = self.load_data().get("MAIN_MENU", [])

        with Menu(
            MAIN_MENU_NAME, label=MAIN_MENU_LABEL, familyImage=SHELF_ICON
        ) as mm:
            self.build_items(mm, data)

            maya_window: QtWidgets.QMainWindow | None = dcc.get_maya_window()
            if maya_window is not None:
                menu_bar: QtWidgets.QMenuBar = maya_window.menuBar()
                self.__event_filter = MayaContextMenuFilter(
                    MAIN_MENU_NAME, self
                )
                menu_bar.installEventFilter(self.__event_filter)

    def build_channelbox_menu(self) -> None:
        """Builds the Amaterasu menu in the Maya channel box."""
        channel_box: str = mel.eval("$gChannelBoxForm=$gChannelBoxForm")
        cmds.setParent(f"{channel_box}|menuBarLayout1")
        data: list[dict[str, Any]] = self.load_data().get(
            "CHANNEL_BOX_MENU", []
        )

        with Menu(CB_MENU_NAME, label=CB_MENU_LABEL) as mm:
            self.build_items(mm, data)

    def build_history_menu(self, menu_name: str) -> None:
        """Builds a standard Maya menu populated with recent tools history.

        Args:
            menu_name (str): The target Maya menu name to populate.
        """
        cmds.menu(menu_name, edit=True, deleteAllItems=True)

        settings: Settings = Settings.instance(__name__, True)
        history: list[dict[str, str]] = settings.recent_tools.value()

        if not history:
            cmds.menuItem(
                label="No Recent Tools", enable=False, parent=menu_name
            )
            return

        for item in history:
            command: str = Menu.create_python_command(
                item["module"], item["func"]
            )
            menu_item: str = cmds.menuItem(
                label=item["label"],
                command=command,
                sourceType="python",
                parent=menu_name,
            )  # type: ignore
            action: QtGui.QAction | None = dcc.find_menu_item(
                menu_item, QtGui.QAction
            )
            if action is not None:
                action.triggered.connect(
                    partial(
                        settings.add_history,
                        item["label"],
                        item["module"],
                        item["func"],
                    )
                )

    def build_history_qmenu(
        self,
        parent: QtWidgets.QMenuBar,
        action: QtGui.QAction,
    ) -> None:
        """Builds and displays a Qt QMenu for recent tools history.

        Args:
            parent (QtWidgets.QMenuBar): The parent menu bar widget.
            action (QtGui.QAction): The action triggered to spawn this menu.
        """
        settings: Settings = Settings.instance(__name__, True)
        history: list[dict[str, str]] = settings.recent_tools.value()

        recent_tool_menu: QtWidgets.QMenu = QtWidgets.QMenu(
            f"{MAIN_MENU_LABEL} Recent Tools", parent
        )
        recent_tool_menu.setTearOffEnabled(True)
        if not history:
            _action: QtGui.QAction = recent_tool_menu.addAction(
                "No Recent Tools"
            )
            _action.setEnabled(False)

        else:
            for item in history:
                _action = recent_tool_menu.addAction(item["label"])
                _action.triggered.connect(
                    partial(
                        self.execute_recent_tool,
                        item["module"],
                        item["func"],
                    )
                )
                _action.triggered.connect(
                    partial(
                        settings.add_history,
                        item["label"],
                        item["module"],
                        item["func"],
                    )
                )

        rect: QtCore.QRect = parent.actionGeometry(action)
        pos: QtCore.QPoint = parent.mapToGlobal(rect.bottomLeft())
        recent_tool_menu.exec_(pos)

    @dcc.undo
    def execute_recent_tool(self, module_path: str, func_name: str) -> None:
        """Executes a tool from the recent history.

        Args:
            module_path (str): The Python module path.
            func_name (str): The function name to execute.
        """
        module: ModuleType = importlib.import_module(module_path)
        eval(func_name, module.__dict__)


def create_main_menu() -> None:
    """Create an Amaterasu menu in main window."""
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_main_menu()


def create_channelbox_menu() -> None:
    """Create an Amaterasu menu in channel box."""
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_channelbox_menu()


def build_history_menu(menu_name: str) -> None:
    """Build history menu"""
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_history_menu(menu_name)
