"""
From https://gist.github.com/jul/9286835
"""

import cmath
import math


class Vector(complex):
    """
    A magnitude and direction
    """
    def __repr__(self):
        return "<Vector r:%.3f theta:%.3f>" % (self.magnitude, self.degrees)

    def __add__(self, other):
        klazz = type(self)
        sum = complex(self) + complex(other)
        return klazz(sum)

    def __sub__(self, other):
        klazz = type(self)
        sum = complex(self) - complex(other)
        return klazz(sum)

    def __mul__(self, other):
        klazz = type(self)
        product = complex(self) * complex(other)
        return klazz(product)

    def __div__(self, other):
        klazz = type(self)
        product = complex(self) / complex(other)
        return klazz(product)

    @property
    def magnitude(self):
        return abs(self)

    @property
    def radians(self):
        return cmath.phase(self)

    @property
    def degrees(self):
        return math.degrees(self.radians)

    def draw(self, canvas):
        mid_x = canvas.winfo_width() / 2
        mid_y = canvas.winfo_height() / 2
        canvas.create_line(mid_x, mid_y, mid_x + self.real, mid_y - self.imag, fill="red", dash=(2, 2))


class Point(Vector):
    """
    A point relative to an origin.
    Equivalent to a vector from the origin.
    """

    @property
    def x(self):
        return round(self.real, 3)

    @property
    def y(self):
        return round(self.imag, 3)

    def __repr__(self):
        return "<Point x:%.3f y:%.3f>" % (self.x, self.y)

    @classmethod
    def origin(cls):
        return cls(0, 0)

    def as_euclidian(self):
        return self.x, self.y

    def as_polar_radians(self):
        return abs(self), self.radians

    def as_polar_degrees(self):
        return abs(self), self.degrees

    def draw(self, canvas):
        mid_x = canvas.winfo_width() / 2
        mid_y = canvas.winfo_height() / 2
        canvas.create_oval(mid_x + self.x, mid_y - self.y, mid_x + self.x + 1, mid_y - (self.y + 1))


class Rotation(Vector):
    """
    An angle.
    Although this subclasses Vector, by convention, the magnitude is always 1.
    """

    def __repr__(self):
        return "<Rotation m:%.3f theta:%.3f degrees>" % (self.magnitude, self.degrees)

    def __init__(self, *a, **kw):
        super(Rotation, self).__init__(*a, **kw)
        if abs(abs(self) - 1.0) > .0001 and cmath.phase(self) != 0:
            raise ValueError("norm must be 1")

    def draw(self, canvas):
        mid_x = canvas.winfo_width() / 2
        mid_y = canvas.winfo_height() / 2
        canvas.create_arc(mid_x - self.x, mid_y - self.y, mid_x + self.x, mid_y + self.y, start=0, extent=self.degrees)


class RotationRadians(Rotation):
    """
    An angle, to be instantiated with a scalar number representing radians.
    """
    def __repr__(self):
        return "<RotationRadians m:%.3f theta:%.3f radians>" % (self.magnitude, self.radians)

    def __new__(cls, radians):
        return super(RotationRadians, cls).__new__(cls, cmath.rect(1, radians))


class RotationDegrees(RotationRadians):
    """
    An angle, to be instantiated with a scalar number representing degrees.
    """
    def __repr__(self):
        return "<RotationDegrees m:%.3f theta:%.3f degrees>" % (self.magnitude, self.degrees)

    def __new__(cls, degrees):
        degrees = (degrees + 360) % 360
        return super(RotationDegrees, cls).__new__(cls, math.radians(degrees))


class Rectangle(object):
    """
    A rectangle, possibly angled, defined relative to the origin.
    """

    def __init__(self, center, height, width, rotation):
        """
        Instantiate a rectangle with two a height, width, and a rotation around
        a center point. The rotation is assumed to be the counter-clockwise
        rotation of the whole rectangle.
        """
        if not isinstance(center, Point):
            raise ValueError('center must be a Point, was %r', center)
        if not isinstance(rotation, Rotation):
            raise ValueError('rotation must be a Rotation, was %r', rotation)
        self.center = center
        self.height = abs(height)
        self.width = abs(width)
        self.rotation = rotation

    @property
    def diagonal(self):
        return self.upper_left - self.lower_right

    def _corner(self, right, up):
        cr = math.cos(self.rotation.radians)
        sr = math.sin(self.rotation.radians)

        x = right * cr - up * sr
        y = right * sr + up * cr
        point = Point(x, y)
        return self.center + point

    @property
    def upper_left(self):
        up = self.height / 2
        right = self.width / 2
        return self._corner(-right, up)

    @property
    def upper_right(self):
        up = self.height / 2
        right = self.width / 2
        return self._corner(right, up)

    @property
    def lower_right(self):
        up = self.height / 2
        right = self.width / 2
        return self._corner(right, -up)

    @property
    def lower_left(self):
        up = self.height / 2
        right = self.width / 2
        return self._corner(-right, -up)

    @property
    def hypotenuse(self):
        return abs(self.diagonal)

    @property
    def bounding_box(self):
        points = self.as_points()
        min_x = min([point.x for point in points])
        min_y = min([point.y for point in points])
        max_x = max([point.x for point in points])
        max_y = max([point.y for point in points])
        return Rectangle(self.center, max_y - min_y, max_x - min_x, RotationDegrees(0))

    def __repr__(self):
        points = ', '.join(['%r' % p for p in self.as_points()])
        return "<Rectangle: Center %r, height %r, width %r, rotation %r, points %s>" % (
            self.center, self.height, self.width, self.rotation.degrees, points)

    def area(self):
        return self.height * self.width

    def as_points(self):
        return [
            self.upper_left,
            self.upper_right,
            self.lower_right,
            self.lower_left
        ]

    def translation(self, vector):
        # Quite trivial, pretty useless method
        self.center += Vector(vector)

    def rotate(self, rotation):
        self.rotation *= rotation

    def rotate_from_origin(self, rotation):
        self.center *= rotation
        self.rotation *= rotation

    def as_polar_radians(self):
        # just for convenience, but really useless
        return [p.as_polar_radians() for p in self.as_points()]

    def as_polar_degrees(self):
        # just for convenience, but really useless
        return [p.as_polar_degrees() for p in self.as_points()]

    def as_euclidians(self):
        return [p.as_euclidian() for p in self.as_points()]

    def rotate_from_point(self, point, rotation):
        self.center -= Point(point)
        self.rotate_from_origin(rotation)
        self.center += Point(point)

    def draw(self, canvas):
        mid_x = canvas.winfo_width() / 2
        mid_y = canvas.winfo_height() / 2
        canvas.create_line(
            mid_x + self.upper_left.x, mid_y - self.upper_left.y,
            mid_x + self.upper_right.x, mid_y - self.upper_right.y,
            mid_x + self.lower_right.x, mid_y - self.lower_right.y,
            mid_x + self.lower_left.x, mid_y - self.lower_left.y,
            mid_x + self.upper_left.x, mid_y - self.upper_left.y
        )
