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
"""Singleton pattern implementation for Amaterasu.

This module provides metaclass and base class implementations of the
Singleton pattern, ensuring that only one instance of a class exists
throughout the application lifecycle.
"""
from __future__ import annotations
from typing import Any


class SingletonMeta(type):
    """Metaclass for creating Singleton classes.

    When a class uses this metaclass, it ensures that every instantiation
    call returns the same instance, creating it only if it doesn't already exist.
    """

    def __init__(
        cls, name: str, bases: tuple[type], attributes: dict[Any, Any]
    ) -> None:
        """Initialize the singleton class.

        Args:
            name (str): The name of the class.
            bases (tuple[type]): The base classes.
            attributes (dict[Any, Any]): The class attributes.
        """
        super().__init__(name, bases, attributes)
        cls.__instance: object | None = None

    def __call__(cls, *args: Any, **kwargs: Any) -> object:
        """Return the singleton instance, creating it if necessary.

        Args:
            *args (Any): Variable length argument list for class instantiation.
            **kwargs (Any): Arbitrary keyword arguments for class instantiation.

        Returns:
            object: The unique instance of the class.
        """
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


class Singleton(metaclass=SingletonMeta):
    """Base class to easily implement the Singleton pattern.

    Inheriting from this class will automatically make the subclass a Singleton.
    """
