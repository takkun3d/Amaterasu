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
"""Amaterasu: Open source toolset for Autodesk Maya."""

from __future__ import annotations
import pathlib
from maya import cmds, utils
from . import env, menu, launcher, splash

__product__: str = env.__product__  # Unused
__version__: int = env.__version__  # Unused

DEFAULT_LICENSE: str = env.DEFAULT_LICENSE

ROOT_PATH: pathlib.Path = env.ROOT_PATH  # Unused
SCRIPT_PATH: pathlib.Path = env.SCRIPT_PATH  # Unused
MODULE_PATH: pathlib.Path = env.MODULE_PATH  # Unused
ICONS_PATH: pathlib.Path = env.ICONS_PATH  # Unused
RESOURCE_PATH: pathlib.Path = env.RESOURCE_PATH
MAYA_APP_DIR: pathlib.Path = env.MAYA_APP_DIR  # Unused
USER_DATA_DIR: pathlib.Path = env.USER_DATA_DIR


def execute_deferred() -> None:
    """Initializes components after Maya is fully loaded."""
    settings: env.Settings = env.Settings.instance(env.__product__, True)
    menu.create_main_menu()
    menu.create_channelbox_menu()
    menu.create_display_layer_menu()

    if settings.check_update.value():
        launcher.main(force_emit=False)

    if settings.latest_version.value() != __version__:
        settings.latest_version.set_value(__version__)
        settings.write()


def main() -> None:
    """The main startup sequence."""
    if not cmds.about(batch=True):
        cmds.setStartupMessage(f"Loading {__product__}...")
        settings: env.Settings = env.Settings.instance(env.__product__, True)
        if settings.override_splash_screen.value():
            splash.override_splash_screen()

        utils.executeDeferred(execute_deferred)
