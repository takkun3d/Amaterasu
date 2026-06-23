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
"""Provides utilities for managing Maya plugins."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import utils


def remove_unknown() -> utils.Result:
    """Removes unknown plugin requirements from the current scene.

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()
    unknown_plugins: list[str] = cmds.unknownPlugin(query=True, list=True) or []  # type: ignore

    for plugin in unknown_plugins:
        try:
            cmds.unknownPlugin(plugin, remove=True)
            result.add_info(plugin, "Removed plugin")

        except RuntimeError:
            result.add_failure(plugin, "Cannot remove plugin")

    return result


def load(plugin_name: str) -> utils.Result:
    """Loads a Maya plugin if it is not already loaded.

    Args:
        plugin_name (str): The name of the plugin to load (e.g., "dx11Shader.mll").

    Returns:
        utils.Result: The result of the operation.
    """
    result: utils.Result = utils.Result()

    is_loaded: bool = cmds.pluginInfo(plugin_name, query=True, loaded=True)  # type: ignore
    if is_loaded:
        result.add_info(plugin_name, "Plugin is already loaded.")
        return result

    try:
        cmds.loadPlugin(plugin_name, quiet=True)
        result.add_info(plugin_name, "Successfully loaded plugin.")

    except RuntimeError as e:
        result.set_error(f"Failed to load plugin '{plugin_name}': {e}")

    return result
