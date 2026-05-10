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
"""Custom form layout for Amaterasu.

This module provides the `FormLayout` class, which extends `QFormLayout`
with utility methods to easily toggle visibility and enabled states
for entire rows (both labels and fields).
"""
from __future__ import annotations
from amaterasu.base.qt import QtWidgets


class FormLayout(QtWidgets.QFormLayout):
    """A custom form layout with row-level control utilities."""

    def set_row_enabled(self, row: int, enabled: bool) -> None:
        """Enable or disable all widgets in a specific row.

        Args:
            row (int): The index of the row to modify.
            enabled (bool): True to enable the widgets, False to disable them.
        """
        for role in (
            QtWidgets.QFormLayout.ItemRole.LabelRole,
            QtWidgets.QFormLayout.ItemRole.FieldRole,
        ):
            layout_item: QtWidgets.QLayoutItem | None = self.itemAt(row, role)
            if not layout_item:
                continue

            layout: QtWidgets.QLayout = layout_item.layout()
            if layout:
                layout.setEnabled(enabled)
                for i in range(layout.count()):
                    widget: QtWidgets.QWidget = layout.itemAt(i).widget()
                    if not widget:
                        continue

                    widget.setEnabled(enabled)

            widget = layout_item.widget()
            if widget:
                widget.setEnabled(enabled)

    def set_row_visible(self, row: int, visible: bool) -> None:
        """Show or hide all widgets in a specific row.

        Args:
            row (int): The index of the row to modify.
            visible (bool): True to show the widgets, False to hide them.
        """
        for role in (
            QtWidgets.QFormLayout.ItemRole.LabelRole,
            QtWidgets.QFormLayout.ItemRole.FieldRole,
        ):
            layout_item: QtWidgets.QLayoutItem | None = self.itemAt(row, role)
            if not layout_item:
                continue

            layout: QtWidgets.QLayout = layout_item.layout()
            if layout:
                # layout.setEnabled(enabled)
                for i in range(layout.count()):
                    widget: QtWidgets.QWidget = layout.itemAt(i).widget()
                    if not widget:
                        continue

                    widget.setVisible(visible)

            widget = layout_item.widget()
            if widget:
                widget.setVisible(visible)

    def row_id(self) -> int:
        """Get the index of the last row added to the layout.

        Returns:
            int: The index of the last row (rowCount - 1).
        """
        return self.rowCount() - 1
