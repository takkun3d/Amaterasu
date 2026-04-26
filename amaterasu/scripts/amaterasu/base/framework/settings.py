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
"""Settings management framework for Amaterasu tools.

This module provides a robust system for managing, saving, and loading
tool settings. It uses metaclasses to automate the registration of
settings variants and supports data binding for automatic UI synchronization.
"""
from __future__ import annotations
from typing import Generic, TypeVar, Type, Callable, Any, Iterator, cast
import pathlib
import json
import re
import amaterasu
from amaterasu.base.utils.singleton import SingletonMeta

BAD_FILE_NAME: str = r"[\\|/|:|?|.|\"|<|>|\||\r|\n|\t|\v|\s]"
SelfToolSettings = TypeVar("SelfToolSettings", bound="ToolSettings")
T = TypeVar("T")


class EnumMeta(type):
    """Metaclass for enum-like variant management.

    This metaclass automatically discovers and registers all `Variant`
    attributes defined in a class, assigning them their attribute names.
    """

    def __init__(
        cls, name: str, bases: tuple[type], attributes: dict[Any, Any]
    ) -> None:
        """Initialize the class by registering all Variant attributes.

        This method scans the class attributes, identifies instances of
        `Variant`, assigns their attribute names to them, and populates
        the internal values list for iteration.

        Args:
            name (str): The name of the class being created.
            bases (tuple[type]): The base classes of the new class.
            attributes (dict[Any, Any]): The dictionary of class attributes.
        """
        super().__init__(name, bases, attributes)
        cls.__values: list[Any] = []
        for key, value in attributes.items():
            if isinstance(value, Variant):
                value.set_name(key)
                cls.__values.append(value)

    def __getitem__(cls: EnumMeta, key: str) -> Variant[Any]:
        """Return a variant by its key name.

        Args:
            key (str): The name of the variant to retrieve.

        Returns:
            Variant[Any]: The variant instance associated with the key.
        """
        return cast(Variant[Any], getattr(cls, key))

    def __iter__(cls) -> Iterator[Any]:
        """Iterate over all registered variants in the class.

        Returns:
            Iterator[Any]: An iterator of Variant instances.
        """
        return iter(cls.__values)


class SettingsMeta(EnumMeta, SingletonMeta):
    """Metaclass blending Enum discovery and Singleton behavior.

    Used by ToolSettings to ensure global availability of settings while
    maintaining automated variant registration.
    """


class Variant(Generic[T]):
    """Represents a single setting entry with optional data binding.

    A Variant holds a specific value and can be bound to UI setter/getter
    methods to automate synchronization between data and interface.
    """

    def __init__(self, default_value: T) -> None:
        """Initialize the Variant.

        Args:
            default_value (T): The initial and fallback value for this setting.
        """
        self.__name: str = ""
        self.__value: T = default_value
        self.__default_value: T = default_value
        self.__bind_setter: Callable[[Any], None] | None = None
        self.__bind_getter: Callable[[], Any] | None = None
        self.__encoder: Callable[[Any], Any] | None = None
        self.__decoder: Callable[[Any], Any] | None = None

    def name(self) -> str:
        """Get the name of the variant.

        Returns:
            str: The attribute name assigned by the metaclass.
        """
        return self.__name

    def set_name(self, name: str) -> None:
        """Set the name of the variant.

        Args:
            name (str): The attribute name to assign.
        """
        self.__name = name

    def value(self) -> T:
        """Get the current value.

        Returns:
            T: The stored setting value.
        """
        return self.__value

    def set_value(self, value: T) -> None:
        """Update the value and trigger a commit to any bound object.

        Args:
            value (T): The new value to set.
        """
        self.__value = value
        self.commit()

    def reset(self) -> None:
        """Reset the value to its default state."""
        self.__value = self.__default_value

    def bind(
        self,
        setter: Callable[[Any], None],
        getter: Callable[[], Any],
        encoder: Callable[[Any], Any] | None = None,
        decoder: Callable[[Any], Any] | None = None,
    ) -> None:
        """Bind UI methods to this setting for automatic synchronization.

        Args:
            setter (Callable[[Any], None]): Method to update the UI from data.
            getter (Callable[[], Any]): Method to retrieve data from the UI.
            encoder (Callable[[Any], Any] | None, optional): Func to process
                data before saving. Defaults to None.
            decoder (Callable[[Any], Any] | None, optional): Func to process
                data after loading. Defaults to None.
        """
        self.__bind_setter = setter
        self.__bind_getter = getter
        self.__encoder = encoder
        self.__decoder = decoder
        self.commit()

    def commit(self) -> None:
        """Push the current value to the bound UI object via the setter."""
        if self.__bind_setter:
            value: T = self.__value
            if self.__decoder:
                value = self.__decoder(value)

            # Special handling may be required here
            # when considering signal blocking.
            self.__bind_setter(value)

    def fetch(self) -> None:
        """Pull the current value from the bound UI object via the getter."""
        if self.__bind_getter:
            value: T = self.__bind_getter()
            if self.__encoder:
                value = self.__encoder(value)

            self.__value = value


class BaseHandler:
    """Abstract base handler for settings persistence."""

    def __init__(self, file_name: pathlib.Path | None = None) -> None:
        """Initialize the handler.

        Args:
            file_name (pathlib.Path | None, optional): Target file path.
        """
        if file_name is None:
            file_name = pathlib.Path()

        self.__file_name: pathlib.Path = file_name

    def file_name(self) -> pathlib.Path:
        """Get the target file path.

        Returns:
            pathlib.Path: The path object.
        """
        return self.__file_name

    def read(self) -> dict[str, Any]:
        """Read and return settings data. Must be implemented by subclasses."""
        return {}

    def write(self, data: dict[str, Any]) -> bool:
        """Write settings data. Must be implemented by subclasses."""
        print(data)
        return True


class JsonHandler(BaseHandler):
    """Persistent storage handler using JSON format."""

    def __init__(self, file_name: pathlib.Path) -> None:
        """Initialize the JSON handler."""
        super().__init__(file_name)

    def read(self) -> dict[str, Any]:
        """Read data from the JSON file.

        Returns:
            dict[str, Any]: The data loaded from file.

        Raises:
            IOError: If the file exists but cannot be read.
        """
        if not self.file_name().exists():
            return {}

        try:
            with self.file_name().open("r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

        except IOError as e:
            raise IOError(f"Failed to open file. {self.file_name()}") from e

        return data

    def write(self, data: dict[str, Any]) -> bool:
        """Serialize and write data to the JSON file.

        Args:
            data (dict[str, Any]): The data dictionary to save.

        Returns:
            bool: True if successful.

        Raises:
            IOError: If directory creation or file writing fails.
        """
        try:
            self.file_name().parent.mkdir(parents=True, exist_ok=True)

        except IOError as e:
            raise IOError(
                f"Failed to create directory. {self.file_name().parent}"
            ) from e

        try:
            with self.file_name().open("w", encoding="utf-8") as fw:
                json.dump(data, fw, sort_keys=True, indent=4)

        except IOError as e:
            raise IOError(f"Failed to write file. {self.file_name()}") from e

        return True


class BaseSettings(metaclass=EnumMeta):
    """Core settings container with iteration and dictionary-like access."""

    def __init__(self, handler: BaseHandler | None = None) -> None:
        """Initialize the settings container and load data.

        Args:
            handler (BaseHandler | None, optional): Storage handler.
        """
        if handler is None:
            handler = BaseHandler()

        super().__init__()
        self.__handler: BaseHandler = handler
        self.read()

    def __getitem__(self, key: str) -> Any:
        """Get a variant via square bracket access."""
        return getattr(self.__class__, key)

    def __iter__(self) -> Iterator[Variant[Any]]:
        """Iterate over all setting variants."""
        return iter(self.__class__)

    def reset(self) -> None:
        """Reset all setting variants to their default values."""
        for element in self:
            element.reset()

    def handler(self) -> BaseHandler:
        """Get the current storage handler."""
        return self.__handler

    def set_handler(self, handler: BaseHandler) -> None:
        """Update the storage handler."""
        self.__handler = handler

    def read(self) -> None:
        """Fetch data from the handler and update variants."""
        data: dict[str, Any] = self.__handler.read()
        for name, value in data.items():
            if not hasattr(self, name):
                continue

            element: Variant[Any] = getattr(self, name)
            element.set_value(value)

    def write(self) -> None:
        """Collect variant data and commit it to the handler."""
        data: dict[str, Any] = {}
        for element in self:
            element.fetch()
            data[element.name()] = element.value()

        self.__handler.write(data)


class ToolSettings(BaseSettings, metaclass=SettingsMeta):
    """Amaterasu-specific settings class with automatic path resolution."""

    @classmethod
    def instance(
        cls: Type[SelfToolSettings], file_name: str, auto_path: bool = False
    ) -> SelfToolSettings:
        """Factory method to get the singleton settings instance.

        Args:
            file_name (str): The target file name or full path.
            auto_path (bool, optional): If True, resolves the file name
                within Amaterasu's user data directory. Defaults to False.

        Returns:
            SelfToolSettings: The singleton instance.
        """
        if auto_path:
            file_path: pathlib.Path = cls.build_file_name(file_name)
        else:
            file_path = pathlib.Path(file_name)

        handler: JsonHandler = JsonHandler(file_path)
        return cls(handler)

    @staticmethod
    def build_file_name(file_name: str) -> pathlib.Path:
        """Sanitize and build a file path within the user data directory.

        Args:
            file_name (str): Raw string to be converted to a file name.

        Returns:
            pathlib.Path: The sanitized path to the settings file.
        """
        file_name = re.sub(BAD_FILE_NAME, "_", file_name)
        file_name = file_name.lower()
        result: pathlib.Path = amaterasu.USER_DATA_DIR / f"{file_name}.json"
        return result
