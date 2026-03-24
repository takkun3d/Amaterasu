# ==============================================================================
#
# Amaterasu Menus
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from types import ModuleType
import os
import json
import importlib
from functools import partial

try:
    from PySide2.QtCore import QObject, Qt, QEvent, QRect, QPoint
    from PySide2.QtWidgets import QMainWindow, QMenuBar, QMenu, QAction

    PYSIDE_VERSION: int = 2

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import QObject, Qt, QEvent, QRect, QPoint
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu

        PYSIDE_VERSION = 6

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


class MayaContextMenuFilter(QObject):
    '''Maya Context Menu Filter'''

    def __init__(
        self,
        target_menu_name: str,
        menu_builder: MenuBuilder,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.__target_menu_name: str = target_menu_name
        self.__menu_builder: MenuBuilder = menu_builder

    def eventFilter(self, menu_bar: QMenuBar, event: QEvent) -> bool:
        '''eventFilter (override)'''
        if (
            event.type() == QEvent.MouseButtonPress
            and event.button() == Qt.RightButton
        ):
            action: QAction = menu_bar.actionAt(event.pos())
            if (
                action
                and action.menu()
                and action.menu().objectName() == self.__target_menu_name
            ):
                self.__menu_builder.build_history_qmenu(menu_bar, action)
                return True

        return super().eventFilter(menu_bar, event)


class MenuBuilder(parser.Singleton):
    '''Menu Builder'''

    def __init__(self, json_path: str) -> None:
        '''Initialize'''
        self.__json_path: str = json_path
        self.__menu_data: dict[str, Any] | None = None
        self.__event_filter: MayaContextMenuFilter | None

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

            maya_window: QMainWindow = widgets.maya_window_to_qt()
            menu_bar: QMenuBar = maya_window.menuBar()
            self.__event_filter = MayaContextMenuFilter(MAIN_MENU_NAME, self)
            menu_bar.installEventFilter(self.__event_filter)

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
            command: str = Menu.create_python_command(
                item['module'], item['func']
            )
            cmds.menuItem(
                label=item['label'],
                command=command,
                sourceType='python',
                parent=menu_name,
            )

    def build_history_qmenu(self, parent: QMenuBar, action: QAction) -> None:
        '''Build recent tool QMenu'''
        settings: Settings = Settings.instance(__name__, True)
        history: list[dict[str, str]] = settings.recent_tools.value()

        recent_tool_menu: QMenu = QMenu(parent)
        if not history:
            _action: QAction = recent_tool_menu.addAction('No Recent Tools')
            _action.setEnabled(False)

        else:
            for item in history:
                _action = recent_tool_menu.addAction(item['label'])
                _action.triggered.connect(
                    partial(
                        self.execute_recent_tool,
                        item['module'],
                        item['func'],
                    )
                )

        rect: QRect = parent.actionGeometry(action)
        pos: QPoint = parent.mapToGlobal(rect.bottomLeft())
        if PYSIDE_VERSION == 2:
            recent_tool_menu.exec_(pos)

        else:
            recent_tool_menu.exec(pos)

    @widgets.undo
    def execute_recent_tool(self, module_path: str, func_name: str) -> None:
        '''Excute Recent Tool'''
        module: ModuleType = importlib.import_module(module_path)
        eval(func_name, module.__dict__)


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
