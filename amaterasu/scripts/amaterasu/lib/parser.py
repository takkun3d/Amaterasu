# ==============================================================================
#
# Settings
#
# ==============================================================================
from __future__ import annotations
from typing import Generic, TypeVar, Type, Callable, Any, Iterator, cast
import pathlib
import json
import re
import amaterasu


# ==============================================================================
#
# Variables
#
# ==============================================================================
__doc__ = 'Save and load the Amaterasu tool settings.'
BAD_FILE_NAME: str = r'[\\|/|:|?|.|"|<|>|\||\r|\n|\t|\v|\s]'
SelfToolSettings = TypeVar('SelfToolSettings', bound='ToolSettings')
T = TypeVar('T')


# ==============================================================================
#
# Meta Classes
#
# ==============================================================================
class SingletonMeta(type):
    '''Singleton metaclass.'''

    def __init__(
        cls, name: str, bases: tuple[type], attributes: dict[Any, Any]
    ) -> None:
        super().__init__(name, bases, attributes)
        cls.__instance: object | None = None

    def __call__(
        cls: SingletonMeta, *args: list[Any], **kwargs: dict[Any, Any]
    ) -> object:
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)

        return cls.__instance


class EnumMeta(type):
    '''Enum metaclass'''

    def __init__(
        cls, name: str, bases: tuple[type], attributes: dict[Any, Any]
    ) -> None:
        super().__init__(name, bases, attributes)
        cls.__values: list[Any] = []
        for key, value in attributes.items():
            if isinstance(value, Variant):
                value.set_name(key)
                cls.__values.append(value)

    def __getitem__(cls: EnumMeta, key: str) -> Variant[Any]:
        '''Return a variant from speciced key.'''
        return cast(Variant[Any], getattr(cls, key))

    def __iter__(cls) -> Iterator[Any]:
        return iter(cls.__values)


class SettingsMeta(EnumMeta, SingletonMeta):
    '''Blend metaclass Enum and Singleton'''


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Variant(Generic[T]):
    '''Enum attribute.'''

    def __init__(self, default_value: T) -> None:
        self.__name: str = ''
        self.__value: T = default_value
        self.__default_value: T = default_value
        self.__bind_setter: Callable[[Any], None] | None = None
        self.__bind_getter: Callable[[], Any] | None = None
        self.__encoder: Callable[[Any], Any] | None = None
        self.__decoder: Callable[[Any], Any] | None = None

    def name(self) -> str:
        '''Return attribute name.'''
        return self.__name

    def set_name(self, name: str) -> None:
        '''Set attribute name.'''
        self.__name = name

    def value(self) -> T:
        '''Return attribute value.'''
        return self.__value

    def set_value(self, value: T) -> None:
        '''Set attribute value.'''
        self.__value = value
        self.commit()

    def reset(self) -> None:
        '''Reset attribute value.'''
        self.__value = self.__default_value

    def bind(
        self,
        setter: Callable[[Any], None],
        getter: Callable[[], Any],
        encoder: Callable[[Any], Any] | None = None,
        decoder: Callable[[Any], Any] | None = None,
    ) -> None:
        '''
        Bind methods to this setting.

        e.g)
            settings.window_geo.bind(
                setter=self.restoreGeometry,
                getter=self.saveGeometry,
                encoder=widgets.to_ascii,
                decoder=widgets.to_qt
            )
        '''
        self.__bind_setter = setter
        self.__bind_getter = getter
        self.__encoder = encoder
        self.__decoder = decoder
        self.commit()

    def commit(self) -> None:
        '''Commits the current value to the bound object.'''
        if self.__bind_setter:
            value: T = self.__value
            if self.__decoder:
                value = self.__decoder(value)

            # Special handling may be required here
            # when considering signal blocking.
            self.__bind_setter(value)

    def fetch(self) -> None:
        '''Fetches the value from the bound object.'''
        if self.__bind_getter:
            value: T = self.__bind_getter()
            if self.__encoder:
                value = self.__encoder(value)

            self.__value = value


class BaseHandler:
    '''This class is a handle to save settings.'''

    def __init__(self, file_name: pathlib.Path | None = None) -> None:
        if file_name is None:
            file_name = pathlib.Path()

        self.__file_name: pathlib.Path = file_name

    def file_name(self) -> pathlib.Path:
        '''Return file name.'''
        return self.__file_name

    def read(self) -> dict[str, Any]:
        '''Read data from file.'''
        return {}

    def write(self, data: dict[str, Any]) -> bool:
        '''Write data to file.'''
        print(data)
        return True


class JsonHandler(BaseHandler):
    '''This class is a handle to save settings as json.'''

    def __init__(self, file_name: pathlib.Path) -> None:
        super().__init__(file_name)

    def read(self) -> dict[str, Any]:
        '''Read data from json.'''
        if not self.file_name().exists():
            return {}

        try:
            with self.file_name().open('r', encoding='utf-8') as f:
                data: dict[str, Any] = json.load(f)

        except IOError as e:
            raise IOError(f'Failed to open file. {self.file_name()}') from e

        return data

    def write(self, data: dict[str, Any]) -> bool:
        '''Write data to file as json.'''
        try:
            self.file_name().parent.mkdir(parents=True, exist_ok=True)

        except IOError as e:
            raise IOError(
                f'Failed to create directory. {self.file_name().parent}'
            ) from e

        try:
            with self.file_name().open('w', encoding='utf-8') as fw:
                json.dump(data, fw, sort_keys=True, indent=4)

        except IOError as e:
            raise IOError(f'Failed to write file. {self.file_name()}') from e

        return True


class Singleton(metaclass=SingletonMeta):
    '''This class is designed for singleton.'''


class BaseSettings(metaclass=EnumMeta):
    '''This class is basic settings for tool.'''

    def __init__(self, handler: BaseHandler | None = None) -> None:
        if handler is None:
            handler = BaseHandler()

        super().__init__()
        self.__handler: BaseHandler = handler
        self.read()

    def __getitem__(self, key: str) -> Any:
        '''Return enum value'''
        return getattr(self.__class__, key)

    def __iter__(self) -> Iterator[Variant[Any]]:
        '''Return enum items.'''
        return iter(self.__class__)

    def reset(self) -> None:
        '''Reset enum value'''
        for element in self:
            element.reset()

    def handler(self) -> BaseHandler:
        '''Return handler'''
        return self.__handler

    def set_handler(self, handler: BaseHandler) -> None:
        '''Set handler.'''
        self.__handler = handler

    def read(self) -> None:
        '''Read enum value from file by handler.'''
        data: dict[str, Any] = self.__handler.read()
        for name, value in data.items():
            if not hasattr(self, name):
                continue

            element: Variant[Any] = getattr(self, name)
            element.set_value(value)

    def write(self) -> None:
        '''Write enum value to file by handler.'''
        data: dict[str, Any] = {}
        for element in self:
            element.fetch()
            data[element.name()] = element.value()

        self.__handler.write(data)


class ToolSettings(BaseSettings, metaclass=SettingsMeta):
    '''Settings for a tool of Amaterasu.'''

    @classmethod
    def instance(
        cls: Type[SelfToolSettings], file_name: str, auto_path: bool = False
    ) -> SelfToolSettings:
        '''Return instance.'''
        if auto_path:
            file_path: pathlib.Path = cls.build_file_name(file_name)
        else:
            file_path = pathlib.Path(file_name)

        handler: JsonHandler = JsonHandler(file_path)
        return cls(handler)

    @staticmethod
    def build_file_name(file_name: str) -> pathlib.Path:
        '''Build file name of Settings for tool.'''
        file_name = re.sub(BAD_FILE_NAME, '_', file_name)
        file_name = file_name.lower()
        result: pathlib.Path = amaterasu.USER_DATA_DIR / f'{file_name}.json'
        return result


# ==============================================================================
#
# Functions
#
# ==============================================================================
