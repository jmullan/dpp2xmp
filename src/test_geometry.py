"""
Tests for geometry
"""
import math
import geometry


def assertEqual(actual, expected):
    assert expected == actual, 'Expected %r, got %r' % (expected, actual)

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

def test_Point_10():
    point = geometry.Point(10, 10)
    assert isinstance(point, geometry.Point)
    assertEqual(point.x, 10)
    assertEqual(point.y, 10)

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

def test_Rectangle():
    rectangle = geometry.Rectangle(geometry.Point(10, 10), 20, 20, geometry.RotationDegrees(0))
    print rectangle
    print 'ul %r' % rectangle.upper_left
    print 'lr %r' % rectangle.lower_right
    print 'll %r' % rectangle.lower_left
    print 'ur %r' % rectangle.upper_right
    assert (rectangle.upper_left.x, rectangle.upper_left.y) == (0, 20)
    assert (rectangle.lower_left.x, rectangle.lower_left.y) == (0, 0)
    assert (rectangle.lower_right.x, rectangle.lower_right.y) == (20, 0)
    assert (rectangle.upper_right.x, rectangle.upper_right.y) == (20, 20)

def test_Rectangle_bounding_box():
    rectangle = geometry.Rectangle(geometry.Point(10, 10), 20, 20, geometry.RotationDegrees(0))
    bounding_box = rectangle.bounding_box
    assert (bounding_box.upper_left.x, bounding_box.upper_left.y) == (0, 20)
    assert (bounding_box.lower_left.x, bounding_box.lower_left.y) == (0, 0)
    assert (bounding_box.lower_right.x, bounding_box.lower_right.y) == (20, 0)
    assert (bounding_box.upper_right.x, bounding_box.upper_right.y) == (20, 20)

def test_Rectangle_fifteen():
    rectangle = geometry.Rectangle(geometry.Point(10, 10), 20, 20, geometry.RotationDegrees(15))
    assert rectangle.center.x == 10
    assert rectangle.center.y == 10
    print 'rect %r' % rectangle
    print 'ul %r' % rectangle.upper_left
    print 'lr %r' % rectangle.lower_right
    print 'll %r' % rectangle.lower_left
    print 'ur %r' % rectangle.upper_right
    assert (rectangle.upper_left.x, rectangle.upper_left.y) == (-2.247, 17.071)
    assert (rectangle.lower_right.x, rectangle.lower_right.y) == (22.247, 2.929)
    assert (rectangle.lower_left.x, rectangle.lower_left.y) == (2.929, -2.247)
    assert (rectangle.upper_right.x, rectangle.upper_right.y) == (17.071, 22.247)
