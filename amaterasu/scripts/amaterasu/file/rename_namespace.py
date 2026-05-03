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
"""Renames the namespace of selected reference nodes to match their filenames.

This tool updates the namespace of currently selected references (either
in the viewport or the Reference Editor) to align with their respective
source file names.
"""

from __future__ import annotations
from amaterasu.base import dcc, utils

__product__: str = "Rename Namespace"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def main() -> None:
    """Executes the namespace renaming operation for selected references.

    Retrieves the selected reference nodes and updates their namespaces
    sequentially. Results and potential errors are accumulated and logged
    at the end of the process.
    """
    references: list[str] = dcc.reference.get_selected_reference_nodes()

    if not references:
        _logger.error(
            "Select node or Reference Editor item to rename namespace."
        )
        return

    result: utils.Result = utils.Result()
    for reference in references:
        r: utils.Result = dcc.reference.update_namespace(reference)
        result.merge(r)

    result.log(_logger)
