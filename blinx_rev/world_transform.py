#import numpy

# TODO: Use matrix transforms (with numpy)

def transform(vertex, world) :
    #v = scale(vertex, world[6:9])
    #r = [rotate(vertex, world[3:6])]
    t = translate(vertex, world[0:3])
    return t

def translate(vertex, world) :
    x = world[0] + vertex[0]
    y = world[1] + vertex[1]
    z = world[2] + vertex[2]
    return  (x, y, z)

def rotate(vertex, world) :
    pass

def scale(vertex, world) :
    x = world[6] * vertex[0]
    y = world[7] * vertex[1]
    z = world[8] * vertex[2]
    return  (x, y, z)