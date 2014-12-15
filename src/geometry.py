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

    def __init__(self, upper_left, lower_right, rotation):
        """
        Instantiate a rectangle with two points and a rotation.
        Upper left and lower right are arbitrary terms: they just have to be
        opposite corners. The rotation is assumed to be the counter-clockwise
        rotation of the whole rectangle. The two missing points can be defined
        by reflecting the other two points over a line passing through the
        center.
        """
        if not isinstance(upper_left, Point):
            raise ValueError('upper_left must be a Point, was %r', upper_left)
        if not isinstance(lower_right, Point):
            raise ValueError('lower_right must be a Point, was %r', lower_right)
        if not isinstance(rotation, Rotation):
            raise ValueError('rotation must be a Rotation, was %r', rotation)
        self.upper_left = upper_left
        self.lower_right = lower_right
        self.rotation = rotation

    @classmethod
    def new_from_center_plus_corner_vector(cls, center, corner_vector, rotation):
        """
        Returns a rectangle with the center at center and one corner
        defined by the corner vector.
        """
        if not isinstance(center, Point):
            raise ValueError('center must be a Point, was %r', center)
        if not isinstance(corner_vector, Vector):
            raise ValueError('lower_right must be a Vector, was %r', corner_vector)
        if not isinstance(rotation, Rotation):
            raise ValueError('rotation must be a Rotation, was %r', rotation)
        upper_left = center - corner_vector
        lower_right = center + corner_vector
        return Rectangle(upper_left, lower_right, rotation)

    @property
    def center(self):
        """
        A convenience method to find the center point of the rectangle.
        """
        return (self.upper_left + self.lower_right) / 2

    @property
    def diagonal(self):
        return self.upper_left - self.lower_right

    @property
    def upper_right(self):
        center = self.center
        corner_vector = Vector(center - self.upper_left)
        theta = RotationDegrees(2 * (self.rotation.degrees - corner_vector.degrees))
        upper_right = center + (corner_vector * theta)
        return upper_right

    @property
    def lower_left(self):
        center = self.center
        corner_vector = center - self.upper_left
        # don't judge me.
        theta = RotationDegrees((self.rotation.degrees - corner_vector.degrees) * 2 + 180)
        return center + (corner_vector * theta)

    @property
    def height(self):
        return abs(self.upper_left - self.lower_left)

    @property
    def width(self):
        return abs(self.upper_left - self.upper_right)

    @property
    def hypotenuse(self):
        return abs(self.diagonal)

    def __repr__(self):
        return "<Rectangle: Center %r, shape %r, rotation %r>" % (
            self.center, self.upper_right, self.rotation.as_polar_degrees())

    def area(self):
        vector = self.diagonal
        return vector.x * vector.y

    def as_points(self):
        return [
            Point((p / 2 + self.center) * self.rotation)
            for p in [
                -self.upper_right,
                Vector(-self.upper_right.x, self.upper_right.y),
                self.upper_right,
                Vector(self.upper_right.x, -self.upper_right.y)
            ]
        ]

    def translation(self, vector):
        # Quite trivial, pretty useless method
        self.center += Vector(vector)

    def scale(self, factor):
        self.upper_right *= float(factor)

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
