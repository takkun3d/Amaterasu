# ==============================================================================
#
# Amaterasu Menus
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import os
import json
from functools import partial

try:
    from PySide2.QtWidgets import QAction

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtGui import QAction

from maya import cmds, mel
from .lib import parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__doc__ = '''Build amaterasu menu at a main window.'''
MAIN_MENU_NAME: str = 'AmaterasuMenu'
MAIN_MENU_LABEL: str = 'Amaterasu'
CB_MENU_NAME: str = 'AmaterasuChannelBoxMenu'
CB_MENU_LABEL: str = 'A'
SHELF_ICON: str = 'a_shelf.png'
MAX_HISTORY: int = 10
JSON_PATH: str = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), '..', '..', 'resource', 'data', 'menu.json'
    )
)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings'''

    recent_tools: parser.Variant[list[dict[str, str]]] = parser.Variant([])

    def add_history(self, label: str, module_path: str, func_name: str) -> None:
        '''Add history'''
        history: list[dict[str, str]] = self.recent_tools.value()
        history = [
            item
            for item in history
            if not (item['module'] == module_path and item['func'] == func_name)
        ]

        history.insert(
            0, {'label': label, 'module': module_path, 'func': func_name}
        )
        history = history[:MAX_HISTORY]
        self.recent_tools.set_value(history)
        self.write()


class Menu:
    '''This class creates menu in with statements.'''

    def __init__(self, object_name: str = '', **kwargs: Any) -> None:
        '''Get arguments for menu.'''
        self.__object_name: str = object_name
        self.__kwargs: dict[str, Any] = kwargs
        if 'tearOff' not in self.__kwargs:
            self.__kwargs['tearOff'] = True

    def __enter__(self) -> Menu:
        '''Create a menu.'''
        if self.__object_name:
            if cmds.menu(self.__object_name, exists=True):
                cmds.deleteUI(self.__object_name)

            cmds.menu(self.__object_name, **self.__kwargs)
        else:
            cmds.menu(**self.__kwargs)

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        '''Set to one level up in the menu hierarchy.'''
        cmds.setParent('..', menu=True)

    @staticmethod
    def create_python_command(module_path: str, func_name: str) -> str:
        '''Create a python command to run the tool.'''
        return f'import {module_path}\n{module_path}.{func_name}'

    def add_item(
        self,
        label: str,
        module: str,
        main_func: str = 'main()',
        option_func: str | None = None,
        is_window_only: bool = False,
        **kwargs: Any,
    ) -> None:
        '''Add a menu item with optional settings.'''

        if is_window_only and not label.endswith('...'):
            label += '...'

        command: str = self.create_python_command(module, main_func)
        menu_item: str = cmds.menuItem(
            label=label,
            command=command,
            sourceType='python',
            **kwargs,
        )  # type: ignore

        settings: Settings = Settings.instance(__name__, True)
        action: QAction = widgets.maya_menu_item_to_qt(menu_item)
        action.triggered.connect(
            partial(settings.add_history, label, module, main_func)
        )

        if option_func:
            base_label: str = label[:-3] if label.endswith('...') else label
            option_label: str = f'{base_label} Option'
            command = self.create_python_command(module, option_func)
            menu_item = cmds.menuItem(
                label=option_label,
                command=command,
                sourceType='python',
                optionBox=True,
            )  # type: ignore

            action = widgets.maya_menu_item_to_qt(menu_item)
            action.triggered.connect(
                partial(settings.add_history, option_label, module, option_func)
            )

    def add_divider(self, label: str | None = None) -> None:
        '''Add a divider.'''
        if label:
            cmds.menuItem(divider=True, dividerLabel=label)
        else:
            cmds.menuItem(divider=True)


class SubMenu(Menu):
    '''This class creates submenu in with statements.'''

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        '''Get arguments for menuItem.'''
        super().__init__(*args, **kwargs)
        self.__args: tuple[Any, ...] = args
        self.__kwargs: dict[str, Any] = kwargs
        if 'tearOff' not in self.__kwargs:
            self.__kwargs['tearOff'] = True

        if 'subMenu' not in self.__kwargs:
            self.__kwargs['subMenu'] = True

        if 'allowOptionBoxes' not in self.__kwargs:
            self.__kwargs['allowOptionBoxes'] = True

    def __enter__(self) -> SubMenu:
        '''Create a submenu.'''
        cmds.menuItem(*self.__args, **self.__kwargs)
        return self


class MenuBuilder(parser.Singleton):
    '''Menu Builder'''

    def __init__(self, json_path: str) -> None:
        '''Initialize'''
        self.__json_path: str = json_path
        self.__menu_data: dict[str, Any] | None = None

    def load_data(self) -> dict[str, Any]:
        '''Returns json data'''
        if self.__menu_data is not None:
            return self.__menu_data

        if not os.path.exists(self.__json_path):
            self.__menu_data = {'MAIN_MENU': [], 'CHANNEL_BOX_MENU': []}
            return self.__menu_data

        with open(self.__json_path, 'r', encoding='utf-8') as f:
            self.__menu_data = json.load(f)

        return self.__menu_data

    def build_items(self, menu: Menu, items: list[dict[str, Any]]) -> None:
        '''Build menu item'''
        for item in items:
            if 'divider' in item:
                val: str | bool = item['divider']
                divide_label: str | None = val if isinstance(val, str) else None
                menu.add_divider(divide_label)

            elif 'items' in item:
                kwargs: dict[str, Any] = {'label': item['label']}
                args: list[str] = []
                if 'name' in item:
                    args.append(item['name'])

                if 'postMenuCommand' in item:
                    kwargs['postMenuCommand'] = item['postMenuCommand']

                with SubMenu(*args, **kwargs) as sub:
                    self.build_items(sub, item['items'])

            else:
                kwargs = item.copy()
                label: str = kwargs.pop('label')
                module: str = kwargs.pop('module')
                menu.add_item(label, module, **kwargs)

    def build_main_menu(self) -> None:
        '''Build Main Menu'''
        cmds.setParent(mel.eval('$gMainWindow=$gMainWindow'))
        data: list[dict[str, Any]] = self.load_data().get('MAIN_MENU', [])

        with Menu(
            MAIN_MENU_NAME, label=MAIN_MENU_LABEL, familyImage=SHELF_ICON
        ) as mm:
            self.build_items(mm, data)

    def build_channelbox_menu(self) -> None:
        '''Build Channel Box Menu'''
        channel_box: str = mel.eval('$gChannelBoxForm=$gChannelBoxForm')
        cmds.setParent(f'{channel_box}|menuBarLayout1')
        data: list[dict[str, Any]] = self.load_data().get(
            'CHANNEL_BOX_MENU', []
        )

        with Menu(CB_MENU_NAME, label=CB_MENU_LABEL) as mm:
            self.build_items(mm, data)

    def build_history_menu(self, menu_name: str) -> None:
        '''Build history menu'''
        cmds.menu(menu_name, edit=True, deleteAllItems=True)

        settings: Settings = Settings.instance(__name__, True)
        history: list[dict[str, str]] = settings.recent_tools.value()

        if not history:
            cmds.menuItem(
                label='No Recent Tools', enable=False, parent=menu_name
            )
            return

        for item in history:
            label: str = item['label']
            module_path: str = item['module']
            func_name: str = item['func']
            command: str = f'import {module_path}\n{module_path}.{func_name}'
            cmds.menuItem(
                label=label,
                command=command,
                sourceType='python',
                parent=menu_name,
            )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def create_main_menu() -> None:
    '''Create an Amaterasu menu in main window.'''
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_main_menu()


def create_channelbox_menu() -> None:
    '''Create an Amaterasu menu in channel box.'''
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_channelbox_menu()


def build_history_menu(menu_name: str) -> None:
    '''Build history menu'''
    menu_builder: MenuBuilder = MenuBuilder(JSON_PATH)
    menu_builder.build_history_menu(menu_name)
