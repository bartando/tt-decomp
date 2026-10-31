"""Boundary-sector geometry, live entry changes and low-byte virtual booleans.

Only the three object callbacks and animation duration are modeled. The angle
wrapper runs its recovered PPC/C++ body; its CRT remainder boundary is modeled.
Callback changes distinguish entry reads before/after each dispatch. Every game
memory byte, call and returned float is compared, with no tolerance/exclusions.
"""
import struct
from liftcheck.spec import *
from specs._creature_angle_common import CALLS as ANGLE_CALLS


def u32(c, a):
    return struct.unpack('>I', c.read(a, 4))[0]


def bounds(c):
    obj = c.r(3)
    c.write(c.r(4), c.read(obj + 0x160, 16))
    c.write(c.r(5), c.read(obj + 0x170, 16))
    c.ret(r3=u32(c, obj + 0x158))


def position(c):
    obj, output = c.r(4), c.r(3)
    c.write(output, c.read(obj + 0x180, 16))
    c.write(obj + 0x130, c.read(obj + 0x154, 4))
    c.write(obj + 0x1c, c.read(obj + 0x150, 4))
    c.ret(r3=output)


def side(c):
    obj = c.r(3)
    entry = u32(c, obj + 0x154)
    index = struct.unpack('>i', c.read(obj + 0x150, 4))[0]
    # The original has already cached this range when it asks for the side.
    c.write(entry + index * 68 + 0x38, c.read(obj + 0x190, 8))
    c.ret(r3=u32(c, obj + 0x15c))


def duration(c):
    obj = c.r(3)
    c.write(obj + 0x130, c.read(obj + 0x1b8, 4))
    c.write(obj + 0x1c, c.read(obj + 0x1bc, 4))
    c.ret(f1=struct.unpack('>f', c.read(obj + 0x1b4, 4))[0])


CALLS = dict(ANGLE_CALLS)
CALLS.update({
    'headingState.vfn_11': model(duration, args=('r3',)),
    'headingState.vfn_12': model(bounds, args=('r3', 'r4', 'r5')),
    'headingState.vfn_13': model(position, args=('r3', 'r4')),
    'headingState.vfn_14': model(side, args=('r3',)),
    'LocomotionStateAnim_WrapAngle': run(),
    'LocomotionStateAnim_ClampHeading': run(),
})


def f32(x):
    return struct.unpack('>f', struct.pack('>f', x))[0]


def inputs(t):
    obj = t.alloc(0x260, 'stateAndGuards') + 32
    t.w32(obj, t.vtable('headingState', 15))
    tables = []
    for n in range(3):
        table = t.alloc(6 * 68, 'animationTable' + str(n)) + 68
        tables.append(table)
        for k in range(-1, 5):
            start, end = t.pick(((0., 1.), (1., 2.), (2., 2.), (2., 1.),
                                (-2., 2.), (-1., 0.), (0.2, 3.), (0., 8.),
                                (float('nan'), 2.), (0., float('nan'))))
            t.wf32(table + k * 68 + 0x38, start)
            t.wf32(table + k * 68 + 0x3c, end)
    t.w32(obj + 0x130, tables[0])
    t.w32(obj + 0x1c, t.pick((-1, 0, 1, 2, 3)))
    t.w32(obj + 0x154, tables[1])
    t.w32(obj + 0x150, t.pick((-1, 0, 1, 2, 3)))
    t.w32(obj + 0x1b8, tables[2])
    t.w32(obj + 0x1bc, t.pick((-1, 0, 1, 2, 3)))
    t.w32(obj + 0x158, t.pick((0, 1, 0x100, 0x101, 0xff, 0xffffff00)))
    t.w32(obj + 0x15c, t.pick((0, 1, 0x100, 0x101, 0xff, 0xffffff00)))
    for off, vector in ((0x160, (-4., -3., -5., 1.)),
                        (0x170, (4., 3., 5., 1.)),
                        (0x180, (t.pick((-7., -4., -3.9, -3., -2., 0., 2., 3., 3.9, 4., 7.)),
                                 t.rng.uniform(-10, 10),
                                 t.pick((-8., -5., -4.9, -4., -3., 0., 3., 4., 4.9, 5., 8.)), 1.))):
        for k, value in enumerate(vector):
            t.wf32(obj + off + k * 4, value)
    if t.index % 17 == 0:
        t.wf32(obj + t.pick((0x160, 0x168, 0x170, 0x178, 0x180, 0x188)),
               t.pick((float('nan'), float('inf'), -float('inf'))))
    t.wf32(obj + 0x190, 17.)
    t.wf32(obj + 0x194, -4.)
    t.wf32(obj + 0x1b4, t.pick((-3., -2., -1., 0., .1, .5, .99, 1., 1.01, 1.5, 2., 3., 8., float('nan'))))
    angles = (0., -0., .1, -.1, .7853981852531433, -.7853981852531433,
              .7853982448577881, -.7853982448577881, 1., -1.,
              1.5707963705062866, -1.5707963705062866, 2., -2.,
              2.356194257736206, -2.356194257736206, 2.356194496154785,
              -2.356194496154785, 3., -3., 3.1415927410125732,
              -3.1415927410125732, float('nan'))
    heading = angles[t.index % len(angles)] if t.index % 4 else t.rng.uniform(-3.2, 3.2)
    t.args(r3=obj, f1=f32(heading))
    return obj, f32(heading)
