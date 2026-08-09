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
"""Base widgets module for Amaterasu.

This module provides common, reusable UI components for Amaterasu tools.
It serves as a central hub for importing custom widgets, such as buttons,
palettes, layouts, and sliders, ensuring a consistent interface across
the application.
"""

from amaterasu.base.widgets.actionable_check_box import ActionableCheckBox
from amaterasu.base.widgets.browse_widget import BrowseWidget
from amaterasu.base.widgets.color_button import ColorButton
from amaterasu.base.widgets.color_palette import ColorPalette
from amaterasu.base.widgets.color_select_button import ColorSelectButton
from amaterasu.base.widgets.double_range_widget import DoubleRangeWidget
from amaterasu.base.widgets.form_label import FormLabel
from amaterasu.base.widgets.form_layout import FormLayout
from amaterasu.base.widgets.frame_widget import FrameWidget
from amaterasu.base.widgets.horizontal_line import HorizontalLine
from amaterasu.base.widgets.icon_button import IconButton
from amaterasu.base.widgets.index_color_palette import IndexColorPalette
from amaterasu.base.widgets.list_view_widget import ListWidget
from amaterasu.base.widgets.node_picker import NodePicker
from amaterasu.base.widgets.range_slider import RangeSlider
from amaterasu.base.widgets.tab_widget import TabBarPlus, TabWidget
from amaterasu.base.widgets.toast import ToastWidget, ToastSignalEmitter
from amaterasu.base.widgets.tree_widget import TreeWidget
from amaterasu.base.widgets.vertical_line import VerticalLine
from amaterasu.base.widgets.image_drop_widget import ImageDropImage

__all__: list[str] = [
    "ActionableCheckBox",
    "BrowseWidget",
    "ColorButton",
    "ColorPalette",
    "ColorSelectButton",
    "DoubleRangeWidget",
    "IndexColorPalette",
    "FormLabel",
    "FormLayout",
    "FrameWidget",
    "HorizontalLine",
    "IconButton",
    "ListWidget",
    "NodePicker",
    "RangeSlider",
    "TabBarPlus",
    "TabWidget",
    "ToastWidget",
    "ToastSignalEmitter",
    "TreeWidget",
    "VerticalLine",
    "ImageDropImage",
]
