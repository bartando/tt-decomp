"""Shared inputs for the player_* specs (not a spec itself)."""
from liftcheck.spec import run, stub


class inlined(run):
    """Runs the original callee but leaves it out of the call trace: for a
    helper the lift calls and the original inlines."""
    transparent = True


def coin(ctx):
    return ctx.rng.choice([0, 1])


def player_state(t):
    """A pongPlayerState (pongCreature+0xBC) with each blender sub-state present
    or null and values near their thresholds, so every predicate goes both ways."""
    rng = t.rng
    st = t.alloc(0x200, "state", fill="zero")
    t.w8(st + 0x14, rng.choice([0, 1]))                       # m_bActive
    if rng.random() < 0.8:
        tm = t.alloc(0x90, "timing", fill="zero")
        t.floats(tm + 0x0C, 9, -2, 2)
        t.wf32(tm + 0x1C, rng.uniform(0, 2))                  # current time
        t.wf32(tm + 0x24, rng.uniform(0, 2))                  # peak time
        t.wf32(tm + 0x30, rng.uniform(0, 2))                  # target time
        t.w32(st + 0x7C, tm)
    if rng.random() < 0.8:
        rc = t.alloc(0xB0, "recovery", fill="zero")
        t.w8(rc + 0x2C, rng.random() < 0.3)                   # force block
        t.wf32(rc + 0xAC, rng.uniform(0, 2))                  # recovery timer vs 1.0
        t.w32(st + 0x80, rc)
    if rng.random() < 0.8:
        an = t.alloc(0x1B0, "anim", fill="zero")
        t.wf32(an + 0x19C, rng.uniform(-1, 1))
        t.wf32(an + 0x1A4, rng.uniform(-1, 1))                # phase vs 0.0
        t.w32(an + 0x1A0, rng.getrandbits(32) & rng.choice([0, 1, 0xFFFFFFFE]))
        t.w32(st + 0x88, an)
    cs = t.alloc(0x20, "cs", fill="zero")
    t.w32(cs, t.vtable("cs"))
    t.w32(st + 0x8C, cs)
    if rng.random() < 0.8:
        cs2 = t.alloc(0x20, "cs2", fill="zero")
        t.w32(cs2, t.vtable("cs2"))
        t.w32(st + 0x90, cs2)
    return st


PREDICATES = {
    0x820CD550: inlined(),   # IsSwingTimerActive (inlined everywhere in the original)
    0x820CD598: run(),       # IsRecovering
    0x820CD5F0: run(),       # IsSwingPhaseBlocked
    0x820CD660: run(),       # IsCreatureStateReady
    0x820CD6B8: run(),       # IsCreatureState2Active
    "cs.vfn_6": stub(ret=coin),
    "cs.vfn_7": stub(ret=coin),
    "cs2.vfn_6": stub(ret=coin),
    "cs2.vfn_7": stub(ret=coin),
}


def fill_vec_return_dest(ctx):
    """A callee that writes a vec3 (16 bytes) to r3 and returns r3."""
    import struct
    ctx.write(ctx.r(3), b"".join(struct.pack(">f", ctx.rng.uniform(-3, 3)) for _ in range(4)))
    ctx.ret(r3=ctx.r(3))


def timing_state(t, name="timing"):
    """A pongTimingState whose timer is running about half the time."""
    rng = t.rng
    tm = t.alloc(0x90, name, fill="zero")
    t.floats(tm + 0x0C, 9, -2, 2)
    t.wf32(tm + 0x1C, rng.uniform(0, 2))
    t.wf32(tm + 0x30, rng.uniform(0, 2))
    return tm


def match_settings(t):
    """The settings object behind 0x825EAB28 (g_pInputArrayTable)."""
    rng = t.rng
    s = t.alloc(0x160, "settings", fill="zero")
    t.w32(s + 0x14, rng.choice([0, 0, 1, -1]))
    for k in range(2):
        t.w32(s + 0x38 + 4 * k, rng.choice([0, 1, 2]))
        t.w8(s + 0x40 + k, rng.choice([0, 1]))
        t.wf32(s + 0x9C + 4 * k, rng.uniform(-1.5, 1.5))
    t.w8(s + 0x159, rng.choice([0, 1]))
    # what io_Input_poll_9D68 (0x821C9D68, run as is) reads
    t.w8(s + 0x14C, rng.random() < 0.3)
    t.w8(s + 0x14E, rng.random() < 0.3)
    t.w32(s + 0x154, rng.random() < 0.3)
    t.w32(0x825EAB28, s)
    return s


def physics(t, ball_index):
    """g_pPhysicsSim (0x825F5BD0) -> {vtable, level}; g_pPhysicsLevel
    (0x826065E4) -> the same level; the ball's state byte active or not."""
    level = t.alloc(0x20, "level", fill="zero")
    t.w32(level, t.vtable("level"))
    states = t.alloc(0x40, "objectStates", fill="zero")
    t.w8(states + ball_index, t.rng.choice([0, 0, 1, 8, 0x0F]))
    t.w32(level + 0x1C, states)
    sim = t.alloc(0x10, "sim", fill="zero")
    t.w32(sim + 4, level)
    t.w32(0x825F5BD0, sim)
    t.w32(0x826065E4, level)
    return sim, level


def ball_inst(t):
    """The ball's phInst (pongPlayer+0x1C0)."""
    inst = t.alloc(0xC0, "ballInst", ctype="phInstView")
    t.w32(inst, t.vtable("inst"))
    idx = t.rng.randrange(0, 0x40)
    t.w16(inst + 8, idx)
    t.floats(inst + 0x10, 4 * 4, -3, 3)
    t.floats(inst + 0xA0, 8, -3, 3)
    return inst, idx


SHOT_TABLE = 0x8261A3D0   # g_ballSplashArray: 0x1A0-byte entries, shot record at +0x30


def table_dims(t):
    """What 0x8271A304 points at: the table's dimensions in metres."""
    rng = t.rng
    d = t.alloc(0x30, "tableDims", fill="zero")
    t.wf32(d + 0x10, 1.5224)
    t.wf32(d + 0x14, 0.7628)
    t.wf32(d + 0x18, rng.choice([2.7439, rng.uniform(2.0, 3.0)]))
    t.wf32(d + 0x24, 0.325)
    t.wf32(d + 0x28, 0.481)
    t.w32(0x8271A304, d)
    return d


def shot_entry(t, index):
    """Fills the player's shot record in the image's table; returns its address."""
    rng = t.rng
    shot = SHOT_TABLE + index * 0x1A0 + 0x30
    t.floats(shot + 0x20, 4, -3, 3)             # targetPos
    t.floats(shot + 0x40, 4, -1, 1)             # vec40
    t.floats(shot + 0x60, 4, -3, 3)             # vec60
    t.wf32(shot + 0x94, rng.uniform(-12, -9))   # gravity
    t.w32(shot + 0x9C, rng.choice([3, 5, 9]))   # shotType
    t.floats(shot + 0xF0, 4, -1, 1)
    t.floats(shot + 0x100, 2, -1, 1)            # aimNorm
    t.wf32(shot + 0x154, rng.uniform(0, 1))
    return shot


def r32(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), "big")


def match_clock(t, now=None):
    """What 0x8271A2E8 (g_pongMatchTiming) points at: +0x30 is the match clock."""
    clock = t.alloc(0x40, "clock", fill="zero")
    t.wf32(clock + 0x30, t.rng.uniform(0, 500) if now is None else now)
    t.w32(0x8271A2E8, clock)
    return clock


def serve_creature(t, now):
    """pongPlayer+0x1C4 -> creature; +0xBC blender; +0x80 swing anim with a clip."""
    rng = t.rng
    creature = t.alloc(0xD0, "creature", fill="zero")
    blender = t.alloc(0x100, "blender", fill="zero")
    t.w32(creature + 0xBC, blender)
    swing = t.alloc(0xB0, "swingAnim", fill="zero")
    t.w32(blender + 0x80, swing)
    clip = t.alloc(0x20, "clip", fill="zero")
    t.w32(clip + 0x1C, rng.randrange(0, 60))
    t.w32(swing + 0x24, clip)
    t.wf32(swing + 0x30, now - rng.uniform(0, 1))
    return creature, blender, swing


BALL_SLOT = 0x1F8   # where the specs park the ball body for a stubbed getter
