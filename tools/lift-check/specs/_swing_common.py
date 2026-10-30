"""Inputs shared by the swing lifts; no writes or bytes are ignored."""
import struct
from liftcheck.spec import *


def settings(t):
    obj = t.alloc(0x160, "settings")
    dims = t.alloc(32, "tableDims")
    t.w32(0x825EAB28, obj)
    t.w32(0x8271A304, dims)
    t.floats(obj + 128, 3, 0.5, 20)
    t.wf32(dims + 24, t.f32(0.5, 10))
    for i in range(8):
        t.w8(obj + 64 + i, t.pick([0, 1, 2, 255]))
    return obj


def creature(t, name):
    obj = t.alloc(0x200, name)
    pose = t.alloc(0x60, name + ".pose")
    t.floats(pose + 0x40, 4, -30, 30)
    if t.index % 4 == 0:
        for lane in range(4):
            t.w32(pose + 0x40 + lane * 4, t.pick([0, 0x80000000, 1, 0x80000001, 0x00800000]))
    t.w32(obj + 0xA4, pose)
    t.w32(obj + 0xCC, t.pick(range(8)))
    return obj


def swing(t):
    obj = t.alloc(0x190, "swing", ctype="pongSwingData")
    source = t.alloc(16, "strengthSource")
    t.w32(source, t.vtable("strength"))
    t.w32(obj + 0xC0, source)
    t.w32(obj + 0x150, creature(t, "swing.creature"))
    t.w32(obj + 0x24, t.pick([0, 9, 1, 2, -1, 10]))
    t.floats(obj + 0x180, 4, -100, 100)
    if t.index % 4 == 0:
        for lane in range(4):
            t.w32(obj + 0x180 + lane * 4, t.pick([1, 0x80000001, 0x00800000, 0x80800000]))
    return obj


def edge_float(t):
    return struct.unpack(">f", struct.pack(">f", t.pick([0.0, -0.0, -1.0, 0.1, 1.0, 2.0, 1e-40, 1e38, float("nan"),
                   float("inf"), -float("inf"), t.f32(-5, 5)])))[0]
