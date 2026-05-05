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
"""Attribute manipulation utilities for Maya nodes.

This sub-package provides a collection of functions to handle Maya node
attributes safely and efficiently. It acts as a centralized facade,
aggregating various attribute operations (such as locking, hiding, and
future additions like connecting or querying) to keep tool logic clean
and decoupled from direct DCC API calls.
"""

from __future__ import annotations
from amaterasu.base.dcc.attribute.create import (
    add_integer,
    add_float,
    add_string,
    add_boolean,
    add_enum,
    add_vector,
    add_color,
    add_separator,
)
from amaterasu.base.dcc.attribute.query import get_default_value, get_range
from amaterasu.base.dcc.attribute.lock import (
    lock,
    unlock,
    lock_and_hide,
    unlock_and_show,
)

__all__: list[str] = [
    # create
    "add_integer",
    "add_float",
    "add_string",
    "add_boolean",
    "add_enum",
    "add_vector",
    "add_color",
    "add_separator",
    # query
    "get_default_value",
    "get_range",
    # lock
    "lock",
    "unlock",
    "lock_and_hide",
    "unlock_and_show",
]
