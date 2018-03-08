import numpy as np
import math

def rotyaxis(x, z, angle):
    z = x * math.cos(angle) - z *  math.sin(angle)
    x = x * math.sin(angle) + z * math.cos(angle) 

    return x, z

def plane(width=10, height=10, subd=10, roty=0, noise=.5):

    width_half = width / 2
    height_half = height / 2

    gridX = subd
    gridY = subd

    gridX1 = gridX + 1
    gridY1 = gridY + 1

    segment_width = width / gridX
    segment_height = height / gridY

    faces = []
    vertices = []

    for iy in range(gridY1):

        y = iy * segment_height - height_half

        for ix in range(gridX1):

            x = ix * segment_width - width_half
            vertices.append( [x, - y, np.random.normal()*noise] )


    for iy in range(gridY):

        for ix in range(gridX):

            a = ix + gridX1 * iy
            b = ix + gridX1 * ( iy + 1 )
            c = ( ix + 1 ) + gridX1 * ( iy + 1 )
            d = ( ix + 1 ) + gridX1 * iy

            faces.append([a, b, d])
            faces.append([b, c, d])

    return np.array(vertices), np.array(faces)