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
"""Amaterasu environment variables and constants module.

This module defines global constants, dynamic file paths, and URLs used
throughout the Amaterasu package. It provides a centralized configuration
to prevent circular imports and hardcoded paths.
"""

from __future__ import annotations
import os
import pathlib
from maya.api import OpenMaya
from amaterasu.base import framework

__product__: str = "Amaterasu"
__version__: int = 20260510

DEFAULT_LICENSE: str = """Copyright (c) 2014-2026 takkun (takkun3d).<br />
<br />
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:<br />
<br />
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.<br />
<br />
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

ROOT_PATH: pathlib.Path = pathlib.Path(__file__).parent
SCRIPT_PATH: pathlib.Path = ROOT_PATH.parent
MODULE_PATH: pathlib.Path = SCRIPT_PATH.parent
ICONS_PATH: pathlib.Path = MODULE_PATH / "icons"
RESOURCE_PATH: pathlib.Path = MODULE_PATH / "resource"
MAYA_APP_DIR: pathlib.Path = pathlib.Path(os.getenv("MAYA_APP_DIR") or "")
USER_DATA_DIR: pathlib.Path = MAYA_APP_DIR / __product__.lower()

GITHUB_URL: str = "https://github.com/takkun3d/Amaterasu"
GITHUB_LATEST_URL: str = f"{GITHUB_URL}/releases/latest"
GITHUB_API_LATEST_URL: str = (
    "https://api.github.com/repos/takkun3d/Amaterasu/releases/latest"
)

NOTION_URL: str = (
    "https://telling-mink-b5d.notion.site/Amaterasu-15c88977f41f80a7af4adcfca26d304a"
)


X_URL: str = "https://x.com/takkun3d"

MAYA_VERSION: int = OpenMaya.MGlobal.apiVersion()


class Settings(framework.ToolSettings):
    """Global settings for the Amaterasu package.

    Attributes:
        latest_version (framework.Variant[int]): The latest executed version of Amaterasu.
        override_splash_screen (framework.Variant[bool]): Whether to override the Maya
            splash screen on startup.
        check_update (framework.Variant[bool]): Whether to automatically check for
            updates when Amaterasu is initialized.
    """

    latest_version: framework.Variant[int] = framework.Variant(0)
    override_splash_screen: framework.Variant[bool] = framework.Variant(True)
    check_update: framework.Variant[bool] = framework.Variant(True)
