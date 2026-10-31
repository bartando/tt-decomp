"""Complete constant-program packets, publication/refill boundaries, reset
helper and dirty bits. Run the retail reset helper; downstream group flushing
and scissor submission are observed boundaries. Includes callee state changes.
All commands, source program bytes and guarded storage compare exactly.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, refill
FUNCTION = 'grcCommandBuffer_initShaderConstants'
ADDRESS = 0x8235CB48
SOURCE = 'src/graphics/grc_state_helpers.cpp'
TRIALS = 800


def scissor(c):
    p = c.r(3)
    c.write(p + 0x30, c.rng.getrandbits(64).to_bytes(8, 'big'))
    c.write(p + 0x28C1, bytes([c.rng.randrange(256)]))
    c.ret()

CALLS = {
    'grc_3E20': stub(ret='void', args=('r3',)),
    'rage_A980': model(refill, args=('r3',)),
    'grc_DBF8': run(args=('r3', 'r4')),
    'grcDevice_SetScissorRect': model(scissor, args=('r3', 'r4', 'r5', 'r6', 'r7')),
}


def inputs(t):
    p, _ = device(t)
    cursor = t.alloc(2048, 'shaderCommandStorage') + 16
    t.w32(p, cursor)
    t.w32(p + 8, cursor + t.rng.choice([-4, 0, 4, 116, 120, 176, 180, 2044]))
    t.args(r3=p)
