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
"""Provides a custom slider widget for interactive dragging operations."""

from __future__ import annotations
from maya import cmds
from amaterasu.base.qt import QtCore, QtWidgets


class DragSlider(QtWidgets.QSlider):
    """Slider widget that emits events for interactive dragging.

    Attributes:
        drag_start (QtCore.Signal): Emitted when dragging starts.
        drag_move (QtCore.Signal): Emitted while dragging with the value.
        drag_end (QtCore.Signal): Emitted when dragging ends.
    """

    drag_start: QtCore.Signal = QtCore.Signal()
    drag_move: QtCore.Signal = QtCore.Signal(int)
    drag_end: QtCore.Signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the slider.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setRange(-100, 100)  # Bug?
        self.setValue(0)
        self.setOrientation(QtCore.Qt.Orientation.Horizontal)

        self.sliderPressed.connect(self.drag_start_callback)
        self.sliderMoved.connect(self.drag_move_callback)
        self.sliderReleased.connect(self.drag_end_callback)

    @QtCore.Slot()
    def drag_start_callback(self) -> None:
        """Handles the slider pressed event."""
        cmds.undoInfo(openChunk=True)
        self.drag_start.emit()

    @QtCore.Slot(int)
    def drag_move_callback(self, value: int) -> None:
        """Handles the slider moved event."""
        self.drag_move.emit(value)

    @QtCore.Slot()
    def drag_end_callback(self) -> None:
        """Handles the slider released event and resets the value."""
        self.setValue(0)
        self.drag_end.emit()
        cmds.undoInfo(closeChunk=True)
