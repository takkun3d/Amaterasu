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
"""Multiton pattern implementation for Amaterasu.

This module provides a metaclass and a base class for the Multiton pattern,
which is an extension of the Singleton pattern that allows managing multiple
unique instances identified by a key (instance_id).
"""
from __future__ import annotations
from typing import Any


class MultitonMeta(type):
    """Metaclass for Multiton pattern (ID-based Singleton).

    This metaclass manages a global dictionary of instances. Unlike a standard
    Singleton, it returns the same instance only if both the class and the
    provided 'instance_id' match.
    """

    _instances: dict[tuple[type, str], Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Get or create an instance for the given class and ID.

        Args:
            *args (Any): Positional arguments for the class constructor.
            **kwargs (Any): Keyword arguments for the class constructor.
                Expected to contain 'instance_id'.

        Returns:
            Any: The existing or newly created instance for the specified ID.
        """
        instance_id: str = kwargs.get("instance_id", "default")
        key: tuple[type, str] = (cls, instance_id)
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)

        return cls._instances[key]


class Multiton(metaclass=MultitonMeta):
    """Base class to easily implement the Multiton pattern.

    Inheriting from this class allows managing multiple instances of a tool
    or setting based on a unique identifier, ensuring that the same object
    is returned for the same ID within the same class.
    """

    def __init__(self, instance_id: str = "default") -> None:
        """Initialize the Multiton instance.

        Args:
            instance_id (str, optional): The unique identifier for this instance.
                Defaults to "default".
        """
