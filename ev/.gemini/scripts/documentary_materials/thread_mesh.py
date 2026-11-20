"""Solid shaft with a continuous swept helical ridge; illustrative pitch."""
from functools import lru_cache
import math

import numpy as np


@lru_cache(maxsize=1)
def threaded_rod_mesh():
    sides, turns, steps = 24, 10, 240
    # Short shaft faces avoid depth-sort occlusion across multiple thread turns.
    levels=32
    vertices = [[.39*math.cos(2*math.pi*i/sides), -.5+j/levels, .39*math.sin(2*math.pi*i/sides)]
                for j in range(levels+1) for i in range(sides)]
    faces = [[j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i]
             for j in range(levels) for i in range(sides)]
    faces += [list(reversed(range(sides))),list(range(levels*sides,(levels+1)*sides))]
    offset=len(vertices)
    for i in range(steps+1):
        t=i/steps
        angle=2*math.pi*turns*t
        y=-.476+.952*t
        for radius,dy in ((.39,-.024),(.5,0),(.39,.024)):
            vertices.append([radius*math.cos(angle),y+dy,radius*math.sin(angle)])
    for i in range(steps):
        for j in range(3):
            faces.append([offset+3*i+j,offset+3*(i+1)+j,
                          offset+3*(i+1)+(j+1)%3,offset+3*i+(j+1)%3])
    faces += [[offset+2,offset+1,offset],
              [offset+3*steps,offset+3*steps+1,offset+3*steps+2]]
    return np.asarray(vertices,dtype=float),faces
