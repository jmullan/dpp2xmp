"""
Tests for geometry
"""
import math
import geometry


def assertEqual(actual, expected):
    assert expected == actual, 'Expected %r, got %r' % (expected, actual)

def test_Rectangle_new_from_center_plus_corner_vector():
    shape = geometry.Rectangle.new_from_center_plus_corner_vector(
        geometry.Point(2, 2),
        geometry.Vector(1, 1),
        geometry.RotationDegrees(0))
    assertEqual(shape.area(), 4)
    # TODO: upside down
    assertEqual(shape.upper_left.as_euclidian(), (1, 1))
    assertEqual(shape.lower_right.as_euclidian(), (3, 3))
    assertEqual(shape.center.as_euclidian(), (2, 2))
    assertEqual(shape.upper_right.as_euclidian(), (3, 1))
    assertEqual(shape.lower_left.as_euclidian(), (1, 3))

def test_Point():
    point = geometry.Point(1, 1)
    assert isinstance(point, geometry.Point)
    assertEqual(point.x, 1)
    assertEqual(point.y, 1)
    assertEqual(point.degrees, 45)
    assertEqual(point.radians, math.pi / 4)
    assertEqual(point.as_euclidian(), (1, 1))
    assertEqual(point.as_polar_radians(), (math.sqrt(2), math.pi / 4))
    assertEqual(point.as_polar_degrees(), (math.sqrt(2), 45))

def test_Point_add():
    point1 = geometry.Point(0, 0)
    point2 = geometry.Point(1, 1)
    point3 = point1 + point2
    assert isinstance(point3, geometry.Point)
    assertEqual(point3.x, 1)
    assertEqual(point3.y, 1)
    assertEqual(point3.degrees, 45)
    assertEqual(point3.radians, math.pi / 4)
    assertEqual(point3.as_euclidian(), (1, 1))
    assertEqual(point3.as_polar_radians(), (math.sqrt(2), math.pi / 4))
    assertEqual(point3.as_polar_degrees(), (math.sqrt(2), 45))

def test_rotate_a_vector():
    vector = geometry.Vector(1, 1)
    rotation = geometry.RotationDegrees(90)
    rotated = vector * rotation
    assertEqual(rotated.degrees, 45 + 90)
