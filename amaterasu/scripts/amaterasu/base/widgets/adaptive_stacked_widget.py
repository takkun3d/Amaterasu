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
"""Provides a stacked widget that dynamically adapts to its current child."""

from __future__ import annotations
from amaterasu.base.qt import QtCore, QtWidgets


class AdaptiveStackedWidget(QtWidgets.QStackedWidget):
    """A QStackedWidget that dynamically adjusts its height.

    This widget automatically updates its geometry to match the height of
    the currently visible child widget.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the adaptive stacked widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        size_policy: QtWidgets.QSizePolicy = self.sizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Policy.Fixed)
        self.setSizePolicy(size_policy)
        self.currentChanged.connect(self.updateGeometry)

    def sizeHint(self) -> QtCore.QSize:
        """Returns the recommended size for the widget.

        Overrides the default sizeHint to return the sizeHint of the
        currently active widget, allowing dynamic resizing.

        Returns:
            QtCore.QSize: The recommended size.
        """
        current: QtWidgets.QWidget = self.currentWidget()
        if current:
            return current.sizeHint()

        return super().sizeHint()

    def minimumSizeHint(self) -> QtCore.QSize:
        """Returns the recommended minimum size for the widget.

        Overrides the default minimumSizeHint to return the
        minimumSizeHint of the currently active widget.

        Returns:
            QtCore.QSize: The recommended minimum size.
        """
        current: QtWidgets.QWidget = self.currentWidget()
        if current:
            return current.minimumSizeHint()

        return super().minimumSizeHint()
