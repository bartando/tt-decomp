"""0x82380540: evaluate frame, select applier, reload arrays, finalize destination.

Models replace the container/frame and destination data after evaluation. Each
applier flips flags, replaces the array and container, and zeroes the frame count.
The loop retains its selected applier, frame and count but reloads array pointers.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim::ProcessAnimationList'
ADDRESS = 0x82380540
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400
EXTERNS = {'g_floatZero': 0x8202D110}


def u(c, a): return int.from_bytes(c.read(a, 4), 'big')
def w(c, a, v): c.write(a, struct.pack('>I', v & 0xFFFFFFFF))


def evaluate(c):
    script = u(c, c.r(3) + 0x20)
    obj, container, destination, data = struct.unpack('>4I', c.read(script, 16))
    w(c, obj + 0x24, container)
    w(c, destination + 4, data)
    c.ret(r3=0)


def apply(c, tag):
    entry, destination = c.r(3), c.r(5)
    script = u(c, destination + 0x30)
    obj, container, _, data, frame, a, b, decoy = struct.unpack('>8I', c.read(script, 32))
    index = u(c, destination + 0x28)
    w(c, destination + 0x28, index + 1)
    w(c, entry + 0x10, tag)
    w(c, frame + 8, a if index % 2 else b)
    c.write(frame + 12, b'\x00\x00')
    w(c, obj + 0x24, decoy)
    w(c, data + 0x14, u(c, data + 0x14) ^ 1)


CALLS = {
    0x822488E0: model(evaluate, args=('r3','r4','r5','r6','r7','f1')),
    0x8224C128: model(lambda c: apply(c, 0xC128), args=('r3','r4','r5','f1')),
    0x8224C288: model(lambda c: apply(c, 0xC288), args=('r3','r4','r5','f1')),
    0x8214C8F8: model(lambda c: c.write(c.r(3) + 0x24, b'DONE'), args=('r3',)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x40, 'state')
    if t.index % 9 == 0:
        t.args(r3=rng.getrandbits(32), r4=0)
        return
    destination = t.alloc(0x50, 'destination skeleton')
    script = t.alloc(0x40, 'callback script')
    clip = t.alloc(0x30, 'clip')
    containers = [t.alloc(16, 'container') for _ in range(3)]
    frames = [t.alloc(0x20, 'frame') for _ in range(3)]
    data = [t.alloc(0x20, 'destination data') for _ in range(2)]
    arrays = [t.alloc(32, 'frame entry array') for _ in range(3)]
    for array in arrays:
        for i in range(8): t.w32(array + i*4, t.alloc(0x20, 'entry'))
    for i in range(3):
        t.w32(containers[i], clip)
        t.w32(containers[i] + 4, frames[i])
        t.w32(frames[i] + 8, arrays[i])
        t.w16(frames[i] + 12, rng.randrange(8))
    count = rng.choice((0, 1, 2, 4, 7))
    t.w16(frames[1] + 12, count)
    t.w32(obj + 0x24, containers[0])
    t.wf32(obj + 8, rng.uniform(-10, 10))
    t.w32(destination + 4, data[0])
    t.w32(destination + 0x28, 0)
    t.w32(destination + 0x30, script)
    t.w32(clip + 0x20, script)
    for i, value in enumerate((obj, containers[1], destination, data[1], frames[1],
                               arrays[1], arrays[2], containers[2])):
        t.w32(script + i*4, value)
    t.w32(data[0] + 0x14, t.u32())
    t.w32(data[1] + 0x14, t.u32())
    t.args(r3=obj, r4=destination)
