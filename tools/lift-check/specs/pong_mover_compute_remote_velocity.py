"""0x820CA790: remote threshold, override callback and normalized approach.

Noncanonical flag bytes, callback returned-buffer choice and every observable
write are compared. On the normalizing path ONLY, output w is unspecified:
0x820CA820 loads its source from the unwritten scratch word sp+0x5C. The lift
chooses zero for that scratch lane; ignore just the resulting output w. The
inactive/arrival paths must preserve w; the callback must copy its returned w.
Finite geometry avoids overflow; true-estimate rsqrt is a harness limitation.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_ComputeRemoteVelocity"
ADDRESS = 0x820CA790
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
EXTERNS = {"g_hudShell_UpdateBlock": 0x825CAEB8}


def blend(ctx):
    ctx.ret(f1=struct.unpack('>f', ctx.read(ctx.r(3) + 0xD0, 4))[0])


def override(ctx):
    data = ctx.r(4)
    ctx.write(ctx.r(3), ctx.read(data, 16))
    alternate = int.from_bytes(ctx.read(data + 16, 4), 'big')
    ctx.ret(r3=alternate or ctx.r(3))


CALLS = {0x820CB598: model(blend, args=("r3",)),
         "velocityOverride": model(override, args=("r3", "r4", "f1")),
         0x824301D0: run(args=("f1",))}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x100, "mover")
    creature = t.alloc(0xD0, "creature")
    instance = t.alloc(0x80, "instance")
    t.w32(mover + 0x70, creature)
    t.w32(creature + 0xA4, instance)
    weight = (0., -1., 0.5, float('nan'))[t.index % 4]
    t.wf32(mover + 0xD0, weight)
    t.floats(instance + 0x40, 4, -5, 5)
    t.floats(mover + 0x10, 4, -5, 5)
    kind = t.index % 12
    flags = rng.randrange(256)
    t.w8(mover + 0x40, flags)
    creature_type = rng.choice((0, 1, 2, 3))
    t.w32(creature + 0xC8, creature_type)
    threshold = rng.choice((-1., 0., 1., 100.))
    t.wf32(mover + 0x54, threshold)
    t.wf32(mover + 0x48, rng.choice((0., 1., 50., -2., float('nan'))))
    t.wf32(t.sym("g_hudShell_UpdateBlock") + 12, rng.choice((0., 1., 60., -2.)))
    callback = kind == 2
    data = t.alloc(48, "callback data")
    t.floats(data, 12, -20, 20)
    t.w32(data + 16, data + 32 if t.index % 24 < 12 else 0)
    t.w32(mover + 0xE0, data)
    t.w32(mover + 0xE4, t.fake_fn("velocityOverride") if callback else 0)
    out = t.alloc(48, "output with guards") + 16
    def f32_at(address):
        offset = address - 0x40000000
        return struct.unpack('>f', t.arena[offset:offset + 4])[0]
    x = f32_at(mover + 0x10) - f32_at(instance + 0x40)
    z = f32_at(mover + 0x14) - f32_at(instance + 0x48)
    effective_threshold = threshold if creature_type == 2 and not flags & 0x20 else 1e-6
    if weight > 0 and not callback and x*x + z*z > effective_threshold:
        # The sole undefined word; all other output bytes are compared.
        t.ignore(out + 12, 4)
    t.args(r3=out, r4=mover)
