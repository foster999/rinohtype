# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import binascii
import struct

from .style import Style, Styled
from .dimension import PT


__all__ = ['Color', 'HexColor', 'BLACK', 'WHITE', 'RED', 'GREEN', 'BLUE',
           'Gray', 'GRAY10', 'GRAY25', 'GRAY50', 'GRAY75', 'GRAY90',
           'LineStyle', 'Line', 'Shape', 'Polygon', 'Rectangle']


class Color(object):
    def __init__(self, red, green, blue, alpha=1):
        for value in (red, green, blue, alpha):
            if not 0 <= value <= 1:
                raise ValueError('Color component values can range from 0 to 1')
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha

    def __repr__(self):
        rgba_bytes = struct.pack(4 * 'B', *(int(color * 255)
                                            for color in self.rgba))
        return '#' + binascii.hexlify(rgba_bytes).decode('ascii')

    @property
    def rgba(self):
        return self.r, self.g, self.b, self.a


class HexColor(Color):
    def __init__(self, string):
        if string.startswith('#'):
            string = string[1:]
        try:
            r, g, b = struct.unpack('BBB', binascii.unhexlify(string[:6]))
            if string[6:]:
                a, = struct.unpack('B', binascii.unhexlify(string[6:]))
            else:
                a = 255
        except (struct.error, binascii.Error):
            raise ValueError('Bad color string passed to ' +
                             self.__class__.__name__)
        super().__init__(*(value / 255 for value in (r, g, b, a)))


class Gray(Color):
    def __init__(self, luminance, alpha=1):
        super().__init__(luminance, luminance, luminance, alpha)


BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
GRAY10 = Gray(0.10)
GRAY25 = Gray(0.25)
GRAY50 = Gray(0.50)
GRAY75 = Gray(0.75)
GRAY90 = Gray(0.90)
RED = Color(1, 0, 0)
GREEN = Color(0, 1, 0)
BLUE = Color(0, 0, 1)


class LineStyle(Style):
    attributes = {'stroke_width': 1*PT,
                  'stroke_color': BLACK}


class Line(Styled):
    style_class = LineStyle

    def __init__(self, start, end, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.start = start
        self.end = end

    def render(self, container, offset=0):
        canvas, document = container.canvas, container.document
        stroke_width = self.get_style('stroke_width', document)
        stroke_color = self.get_style('stroke_color', document)
        if not (stroke_width and stroke_color):
            return
        with canvas.save_state():
            points = self.start, self.end
            canvas.line_path(points)
            canvas.stroke(stroke_width, stroke_color)


class ShapeStyle(LineStyle):
    attributes = {'fill_color': GRAY90}


class Shape(Styled):
    style_class = ShapeStyle

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

    def render(self, canvas, offset=0):
        raise NotImplementedError


class Polygon(Shape):
    def __init__(self, points, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.points = points

    def render(self, container, offset=0):
        canvas, document = container.canvas, container.document
        stroke_width = self.get_style('stroke_width', document)
        stroke_color = self.get_style('stroke_color', document)
        fill_color = self.get_style('fill_color', document)
        if not ((stroke_width and stroke_color) or fill_color):
            return
        with canvas.save_state():
            canvas.line_path(self.points)
            canvas.close_path()
            if stroke_width and stroke_color and fill_color:
                canvas.stroke_and_fill(stroke_width, stroke_color,
                                       fill_color)
            elif stroke_width and stroke_color:
                canvas.stroke(stroke_width, stroke_color)
            elif fill_color:
                canvas.fill(fill_color)


class Rectangle(Polygon):
    def __init__(self, bottom_left, width, height, style=None, parent=None):
        bottom_right = (bottom_left[0] + width, bottom_left[1])
        top_right = (bottom_left[0] + width, bottom_left[1] + height)
        top_left = (bottom_left[0], bottom_left[1] + height)
        points = bottom_left, bottom_right, top_right, top_left
        super().__init__(points, style=style, parent=parent)
