"""Per-child virtual receivers with modeled motion and pointer-array updates."""
import struct
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies


def propagate(ctx):
    body, data, index, replacement = struct.unpack('>4I', ctx.read(ctx.r(3) + 4, 16))
    # Make writes before caching observable; change the table entry too, so the
    # implementation must retain the body pointer captured before dispatch.
    for offset in (0x110, 0x120):
        ctx.write(body + offset, ctx.read(body + offset + 0x20, 16))
    ctx.write(data + 40 + 4 * index, struct.pack('>I', replacement))
    ctx.ret()


def clear(ctx):
    # A visible virtual effect, separate from the body vectors the lift clears.
    ctx.write(ctx.r(3) + 20, b'\0' * 4)
    ctx.ret()


CALLS = {}
for i in range(8):
    CALLS[f'joint{i}.vfn_0'] = model(propagate)
    CALLS[f'joint{i}.vfn_17'] = model(clear)


def inputs(t):
    data, array = bodies(t)
    for i in range(len(array) - 1):
        joint = t.alloc(32, f'joint{i}AndGuards')
        t.w32(joint, t.vtable(f'joint{i}', 18))
        t.w32(joint + 4, array[i + 1])
        t.w32(joint + 8, data)
        t.w32(joint + 12, i + 1)
        t.w32(joint + 16, array[0])
        t.w32(data + 0xA8 + i * 4, joint)
    t.args(r3=data)
