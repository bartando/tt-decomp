"""Ambient scene selection, all seven lazy lookups, six scaled faces and falloff.

State 8, both key sources (including negative/missing keys), null lookup result,
cached/failing handles, each face missing independently, counter wrap, arbitrary
colour w bits, zero/subnormal scales and explicit FMA-sensitive finite values.
Model only registry lookup and handle interning; all argument traces and defined
memory are compared. Falloff descriptors cover all 1..4 component counts: the
original actually copies a full reused staging vector regardless. When X+ is
absent, only the final falloff z/w (uninitialized original stack) are ignored;
the lift zero-initializes those undefined words. Falloff has a distinct slot.
"""
from liftcheck.spec import model

FUNCTION = 'pongLighting_ApplyAmbientCube'
ADDRESS = 0x820FFF78
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'
# Another declaration describes this address as base+116; pin the actual lfs.
EXTERNS = {'kFastTurnMul': 0x8202D184}


def word(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), 'big')


def resolve(ctx):
    root = ctx.r(3)
    ctx.ret(r3=word(ctx, root))


def intern(ctx):
    name = ctx.r(3)
    assert (name - 0x82030048) % 8 == 0
    index = (name - 0x82030048) // 8
    assert 0 <= index < 7 and ctx.r(4) == 1
    root = word(ctx, 0x8271A310)
    ctx.ret(r3=word(ctx, root + 40 + index * 4))


CALLS = {0x821DC2A0: model(resolve, args=('r3', 'r4')),
         0x8215A2F8: model(intern, args=('r3', 'r4'), deref={'r3': 8})}


def inputs(t):
    loop = t.alloc(0x250, 'game loop')
    root = t.alloc(80, 'lighting registry and lookup handles')
    scene = t.alloc(32, 'active scene')
    lighting = t.alloc(0x1700, 'lighting record')
    table = t.alloc(0x120, 'shader table')
    entries = t.alloc(0x100, 'shader descriptors')
    bank = t.alloc(0x200, 'shader values')
    t.w32(0x825EAB30, loop)
    t.w32(0x8271A310, root)
    t.w32(0x82606564, scene)
    t.w32(0x825EBC40, table)
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, bank)
    state = t.pick([0, 3, 8, 8, 9])
    override = t.pick([0, 0, 1, 255])
    registry_key = t.pick([-2, -1, 0, 12])
    scene_key = t.pick([-2, -1, 0, 9])
    resolved = t.pick([lighting, lighting, 0])
    t.w32(loop + 12, state)
    t.w8(loop + 0x240, override)
    t.w32(root + 32, registry_key)
    t.w32(scene + 20, scene_key)
    t.w32(root, resolved)
    t.w32(0x825EBC54, t.pick([0, 0xFFFFFFFF, t.u32()]))
    cached = t.index % 2
    handles = []
    for face in range(7):
        bit = t.rng.randrange(128)
        handle = ((face + 1) << 18) | (bit << 1) | t.rng.randrange(2)
        if t.rng.randrange(4) == 0:
            handle = 0
        if face == 0 and cached:
            handle |= 1 << 18
        handles.append(handle)
        t.w32(0x82606380 + face * 4, handle if cached else 0)
        t.w32(root + 40 + face * 4, handle)
        t.w32(entries + (face + 1) * 8, (t.u32() & ~0x600) | t.rng.randrange(4) << 9)
        t.w32(entries + (face + 1) * 8 + 4, (t.u32() & 0xFFFF0000) | (15 if face == 6 else t.rng.randrange(15)))
    selected_key = registry_key if override else scene_key
    if state != 8 and selected_key >= 0 and resolved and handles[0] == 0 and handles[6] != 0:
        t.ignore(bank + 15 * 16 + 8, 8)
    light = t.rng.randrange(5)
    for i in range(5):
        t.wf32(lighting + 0x1660 + i * 4, t.pick([0.0, -1.0, 1e-40, t.f32(-4, 4)]))
        for face in range(6):
            color = lighting + 0xA10 + i * 0x120 + face * 16
            for lane in range(3):
                t.wf32(color + lane * 4, t.pick([0.0, -0.0, 1e-40, t.f32(-8, 8)]))
            t.w32(color + 12, t.u32())
    t.wf32(lighting + 0x1674, t.pick([0.0, 1.0, 1e-30, t.f32(-4, 4)]))
    t.args(r3=light)
