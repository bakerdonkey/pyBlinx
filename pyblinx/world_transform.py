from math import sin
from math import cos

from pyblinx.models.vertex import Vertex


def transform(vertex: Vertex, world: tuple):
    """
    Transform a vertex array by a world coordinate array.
    """
    # v = scale(v, world[6:9])
    vertex = rotate(vertex, world[3:6])
    vertex = translate(vertex, world[0:3])
    return vertex


def translate(vertex: Vertex, world: tuple):
    """
    Translate a vertex by a world array by piecewise adding
    """
    x = vertex.x + world[0]
    y = vertex.y + world[1]
    z = vertex.z + world[2]
    return Vertex(x, y, z)


# TODO: Use homogenius matrix transforms
def rotate(vertex: Vertex, world: tuple):
    """
    Rotate a vertex around its origin by a world array denoting [x, y, z]. Assumes radions.
    """

    # x axis rotation
    q = world[0]
    x_prime = vertex.x
    y_prime = vertex.y * cos(q) - vertex.z * sin(q)
    z_prime = vertex.y * sin(q) + vertex.z * cos(q)
    vertex = Vertex(x_prime, y_prime, z_prime)

    # y axis rotation
    q = world[1]
    x_prime = vertex.z * sin(q) + vertex.x * cos(q)
    y_prime = vertex.y
    z_prime = vertex.z * cos(q) - vertex.x * sin(q)
    vertex = Vertex(x_prime, y_prime, z_prime)

    # z axis rotation
    #    q = world[0]
    #    x_prime = x*cos(q) - y*sin(q)
    #    y_prime = x*sin(q) + y*cos(q)
    #    z_prime = z
    #    x, y, z = x_prime, y_prime, z_prime

    return vertex


def scale(vertex: Vertex, world: tuple):
    """
    Scale a vertex by a world array.
    """
    x = vertex.x * world[0]
    y = vertex.y * world[1]
    z = vertex.z * world[2]
    return Vertex(x, y, z)
