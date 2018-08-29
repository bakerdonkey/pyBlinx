#import numpy
from math import sin
from math import cos


def transform(vertex, world) :
    '''
    Transform a vertex array by a world coordinate array.
    '''
    t = translate(vertex, world[0:3])
    r = rotate(t, world[3:6])
    v = scale(r, world[6:9])
    
    return v

def translate(vertex, world) :
    '''
    Translate a vertex by a world array by piecewise adding
    '''
    x = vertex[0] + world[0]
    y = vertex[1] + world[1]
    z = vertex[2] + world[2]

    return  (x, y, z)

# TODO: Use homogenius matrix transforms
def rotate(vertex, world) :
    '''
    Rotate a vertex around its origin by a world array denoting [x, y, z]. Assumes radions.
    '''
    #TODO: verify it works
    x, y, z = vertex[0], vertex[1], vertex[2]

    # x axis rotation
    q = world[0]
    x_prime = x
    y_prime = y*cos(q) - z*sin(q)
    z_prime = y*sin(q) + z*cos(q)
    x, y, z = x_prime, y_prime, z_prime

    # y axis rotation
    q = world[1]
    x_prime = z*sin(q) + x*cos(q)
    y_prime = y
    z_prime = z*cos(q) - x*sin(q)
    x, y, z = x_prime, y_prime, z_prime

    # z axis rotation
    q = world[2]
    x_prime = x*cos(q) - y*sin(q)
    y_prime = x*sin(q) + y*cos(q)    
    z_prime = z
    x, y, z = x_prime, y_prime, z_prime

    return(x, y, z)


def scale(vertex, world) :
    '''
    Scale a vertex by a world array.
    '''
    x = vertex[0] * world[0]
    y = vertex[1] * world[1]
    z = vertex[2] * world[2]

    return  (x, y, z)