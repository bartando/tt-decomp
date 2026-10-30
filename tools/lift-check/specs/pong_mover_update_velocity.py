"""0x820CA080 is pongMover::UpdateVelocity, not a capsule operation.

Every branch: timed flag expiry, local/remote selection, speed saturation,
post-blend adjustment, low-speed target flag, both court orientations, stationary
latch expiry and retention. Vary all unrelated flag bits, dt, and boundary values.
Use boundary models for movement helpers (including side effects and alternative
returned vector storage). Compare every byte and call, with exact FP and no
ignored ranges. Scalar NaNs test unordered branch behavior; VMX subnormals test
flush semantics. Helpers' own implementations and invalid pointers are outside
this caller spec; helper outputs are finite and bounded (no arithmetic overflow).
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover::UpdateVelocity"
ADDRESS = 0x820CA080
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def _u(ctx, a):
    return int.from_bytes(ctx.read(a, 4), "big")


def _f(ctx, a):
    return struct.unpack(">f", ctx.read(a, 4))[0]


def _wf(ctx, a, v):
    ctx.write(a, struct.pack(">f", v))


def _blend_weight(ctx):
    mover = ctx.r(3)
    count = _u(ctx, mover + 0xE0)
    # Side effects force the caller to reread flags after the speed callback.
    ctx.write(mover + 0xE0, struct.pack(">I", count + 1))
    ctx.ret(f1=_f(ctx, mover + (0xD0 if count == 0 else 0xD4)))


def _speed(ctx):
    mover = ctx.r(3)
    mask = ctx.read(mover + 0xE4, 1)[0]
    ctx.write(mover + 0x40, bytes([ctx.read(mover + 0x40, 1)[0] ^ mask]))
    ctx.ret(f1=_f(ctx, mover + 0xD8))


def _velocity(ctx, remote):
    mover, out = ctx.r(4), ctx.r(3)
    # Deliberately return a non-out pointer on half the trials: caller uses r3.
    source = _u(ctx, mover + (0xE8 if remote else 0xEC))
    ctx.write(out, ctx.read(source, 12))
    alternate = ctx.read(mover + 0xE5, 1)[0]
    if alternate:
        _wf(ctx, out, _f(ctx, source) + 7.)
    ctx.ret(r3=source if alternate else out)


def _state(ctx):
    mover = ctx.r(3)
    ctx.write(mover + 0x74, ctx.read(mover + 0xE6, 1))
    _wf(ctx, mover + 0x30, 123.)  # the caller must store its blend AFTER this


def _adjust(ctx):
    mover = ctx.r(3)
    _wf(ctx, ctx.r(4), _f(ctx, ctx.r(4)) + _f(ctx, mover + 0xF0))
    _wf(ctx, ctx.r(5), _f(ctx, ctx.r(5)) + _f(ctx, mover + 0xF4))


CALLS = {
    0x820CB598: model(_blend_weight, args=("r3",)),
    0x820CB4D0: model(_speed, args=("r3",)),
    0x820CA640: model(lambda c: _velocity(c, False), args=("r3", "r4")),
    0x820CA790: model(lambda c: _velocity(c, True), args=("r3", "r4")),
    0x820CA390: model(_state, args=("r3",)),
    0x820CA488: model(_adjust, args=("r3", "r4", "r5"), deref={"r4": 4, "r5": 4}),
}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x120, "moverAndGuards") + 16
    creature = t.alloc(0xD0, "creature")
    instance = t.alloc(0x80, "instance")
    players = t.alloc(0xC0, "playerTable")
    t.floats(mover + 0x10, 20, -20, 20)
    t.floats(mover + 0x60, 4, -100, 100)
    t.floats(instance + 0x40, 4, -100, 100)
    t.w32(mover + 0x70, creature)
    t.w32(creature + 0xA4, instance)
    offset = rng.choice((0, 0x50))
    t.w32(creature + 0xCC, offset)
    t.w32(0x825EAB28, players)
    t.w8(players + offset + 0x40, rng.choice((0, 1, 255)))
    flags = rng.randrange(256)
    t.w8(mover + 0x40, flags)
    dt = rng.choice((0., 1/60, 0.5, -0.25))
    t.wf32(0x825CAEC0, dt)
    t.wf32(mover + 0x18, rng.choice((0., dt, dt - 2**-20, dt + 2**-20,
                                                   -1., 1., float("nan"))))
    t.wf32(mover + 0x48, rng.choice((0., 1., 5., -2., rng.uniform(0, 20))))
    t.w8(mover + 0x85, rng.choice((0, 1, 255)))
    t.w8(mover + 0x84, rng.randrange(256))
    t.wf32(mover + 0x80, rng.choice((0., 25., 25. - dt, 25. + dt, float("nan"))))
    t.wf32(0x825C9D64, 25.)
    t.w8(0x82606326, t.index % 2)
    t.w32(mover + 0xE0, 0)
    t.w8(mover + 0xE4, rng.choice((0, 0x10)))
    t.w8(mover + 0xE5, rng.randrange(2))
    t.w8(mover + 0xE6, rng.choice((0, 1, 255)))
    kind = t.index % 12
    t.wf32(mover + 0xD0, rng.choice((0., 1., 0.25, rng.uniform(-1, 2))))
    t.wf32(mover + 0xD4, rng.choice((0., 1., 0.75, rng.uniform(-1, 2))))
    t.wf32(mover + 0xD8, rng.choice((0., -5., 5., rng.uniform(-100, 100), float("nan"))))
    for o in (0xF0, 0xF4):
        t.wf32(mover + o, rng.choice((0., -3., 3.)))
    for o in (0xE8, 0xEC):
        vec = t.alloc(16, f"velocity{o:X}")
        t.floats(vec, 4, -20, 20)
        if kind < 4:
            for lane in range(4):
                t.wf32(vec + lane * 4, 0.)
        if kind == 4:
            t.w32(vec, 1)  # VMX input must flush, not amplify a subnormal
        t.w32(mover + o, vec)
    if kind < 4:
        t.wf32(mover + 0xD0, 1.)
        t.wf32(mover + 0x20, 0. if kind < 2 else 1.)
        t.wf32(mover + 0x24, 0.)
        t.wf32(mover + 0xF0, 0.)
        t.wf32(mover + 0xF4, 0.)
        # All zero velocity: both sides of stationary timer expiry.
        t.w8(mover + 0x85, 1)
        t.w8(mover + 0xE6, 1)
    if kind in (5, 6, 7):
        # Exactly below/equal/above the speed-squared threshold after adjustment.
        t.wf32(mover + 0xD0, 1.)
        t.wf32(mover + 0xD4, 0.)
        t.wf32(mover + 0xF0, 0.)
        t.wf32(mover + 0xF4, 0.)
        vec = t.alloc(16, "boundaryVelocity")
        for lane, value in enumerate((5. + (kind - 6) * 2**-20, 0., 0., 0.)):
            t.wf32(vec + lane * 4, value)
        t.w32(mover + 0xE8, vec)
        t.w32(mover + 0xEC, vec)
        t.wf32(mover + 0xD4, 1.)
        t.w8(mover + 0xE6, 1)
    t.args(r3=mover)
