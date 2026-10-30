"""XACT sound worker: readiness/stop transitions, parameter/track updates,
expired and lookahead events, blocking events, and active-event retirement.

Callees are isolated except the real clock accessor and event-duration decoder.
Destruction/retirement callbacks poison detached links; track callbacks change
the traversal; cue/control callbacks can change sound state and flags.
"""
import struct

from liftcheck.spec import *

FUNCTION = "xactSound_Update"
ADDRESS = 0x82455148
SOURCE = "src/rage/audio/xact_sound.cpp"
TRIALS = 1000
RET = None


def u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def put(ctx, addr, value):
    ctx.write(addr, struct.pack(">I", value & 0xffffffff))


def owns_transitions(ctx):
    cue = ctx.r(3)
    sound = u32(ctx, cue + 8)
    # The readiness path must reread the flags after calling into the cue.
    ctx.write(sound + 0x34, bytes([ctx.read(sound + 0x34, 1)[0] ^ ctx.read(cue + 16, 1)[0]]))
    return u32(ctx, cue + 4)


def control_result(ctx):
    return u32(ctx, ctx.r(3))


def process_control(ctx):
    sound = ctx.r(3)
    put(ctx, sound + 0x50, u32(ctx, sound + 8))


def count_parameters(ctx):
    return u32(ctx, ctx.r(3) + 0x68)


def start_result(ctx):
    return u32(ctx, ctx.r(3) + 0x6c)


def update_track(ctx):
    track = ctx.r(3)
    replacement = u32(ctx, track + 0x20)
    if replacement:
        put(ctx, track + 4, replacement)


def retire(ctx):
    node = ctx.r(3)
    assert u32(ctx, node + 4) == node, "callback needs a detached next link"
    assert u32(ctx, node + 8) == node, "callback needs a detached previous link"
    # Check the live ring before poisoning this node. A missed neighbor write
    # must fail here, rather than cascading into an unrelated emulator fault.
    sentinel = u32(ctx, node + 0x38)
    current = sentinel
    seen = set()
    while current not in seen:
        seen.add(current)
        following, previous = u32(ctx, current + 4), u32(ctx, current + 8)
        assert following and previous, "null link in a circular event list"
        assert u32(ctx, following + 8) == current, "broken next.previous link"
        assert u32(ctx, previous + 4) == current, "broken previous.next link"
        current = following
    assert current == sentinel, "event list does not return to its sentinel"
    # A real callback can free or recycle this object. Cached successors are
    # required for active events; expired events must reload the queue head.
    put(ctx, node + 4, 0)
    put(ctx, node + 8, 0)
    put(ctx, node + 0x3c, 0xdec0de01)


def blocking_result(ctx):
    return u32(ctx, ctx.r(3) + 0x30)


CALLS = {
    "cue.vfn_31": stub(ret=owns_transitions, args=("r3",)),
    "cue.vfn_27": stub(ret="void", args=("r3",)),
    "event.vfn_1": model(retire, args=("r3",)),
    "msgMsgSink_3B48_g": stub(ret=control_result),
    "msgMsgSink_3DC8_g": model(process_control),
    "msgMsgSink_DC40_g": stub(ret="void"),
    "msgMsgSink_4EB8_g": stub(ret=start_result),
    "rage_4318": stub(ret=count_parameters),
    "atSingleton_3078_p39": stub(ret="void"),
    "atSingleton_A5A0_h": model(update_track),
    "atSingleton_6F98_g": run(),
    "game_A758_h": stub(ret=blocking_result),
    # Deliberately trace cancellation without emulating its downstream virtual
    # calls/queues: this checks the worker's saved-next order even for repeats.
    "atSingleton_27C0": stub(ret="void"),
    "game_2880_h": run(),
    "atSingleton_28A8_g_28A8_1": model(retire),
    "msgMsgSink_8B90_g": stub(ret="void"),
}


def chain(t, sentinel, nodes):
    linked = [sentinel, *nodes]
    for i, node in enumerate(linked):
        t.w32(node + 4, linked[(i + 1) % len(linked)])
        t.w32(node + 8, linked[i - 1])


def signed(word):
    return (word + 0x80000000) % 0x100000000 - 0x80000000


def inputs(t):
    rng = t.rng
    sound = t.alloc(0x80, "XACT sound")
    record = t.alloc(8, "packed sound record")
    engine = t.alloc(0x30, "XACT engine clock")
    cue = t.alloc(32, "cue callback controls")
    clock = t.alloc(0x20, "SDK clock")
    t.w32(0x8200084c, clock)

    state = rng.choice((0, 1, 2, 2, 2, 3, 4, 4, 5, 5, 6, 0x80000000))
    flags = rng.getrandbits(8) & ~0x20
    if rng.randrange(12) == 0:
        flags |= 0x20
    t.w32(sound + 4, rng.choice((0, 0, 1, 0xffffffff)))
    t.w32(sound + 8, rng.choice((state, state, 4, 5, 6, 7, 0x80000000)))
    t.w32(sound + 0x1c, record)
    t.w32(sound + 0x20, engine)
    t.w32(sound + 0x30, cue)
    t.w8(sound + 0x34, flags)
    t.w32(sound + 0x50, state)
    t.w32(sound + 0x54, rng.choice((0, 1, 0x100, 0xffffffff)))
    t.w8(record, rng.getrandbits(8))
    t.w16(record + 1, rng.choice((0, 1, 255, 256, 0x8000, 0xffff)))
    t.w32(cue, t.vtable("cue", 32))
    t.w32(cue + 4, rng.choice((0, 0, 1, 0x100, 0x80000000)))
    t.w32(cue + 8, sound)
    t.w8(cue + 16, rng.choice((0, 0, 0x40)))

    count = rng.choice((0, 1, 2, 3, 5, 7, 0x100, 0x101, 0x103, 0x1ff))
    parameters = t.alloc(48 * max(1, count & 255), "48-byte parameter blocks")
    t.w32(sound + 0x60, parameters)
    t.w32(sound + 0x68, count)
    t.w32(sound + 0x6c, rng.choice((0, 1, 0x7fffffff, 0x80000000, 0xffffffff)))

    tracks = []
    readiness = rng.choice((None, 3, 3, 4, 5))
    for i in range(rng.choice((0, 1, 2, 4))):
        track = t.alloc(0x38, f"track {i}")
        voice = t.alloc(0x30, f"track {i} voice")
        voice_state = readiness if readiness is not None else rng.choice((0, 2, 3, 4, 5, 6))
        t.w32(voice + 0x28, voice_state)
        t.w32(track + 0x18, 0 if readiness is None and rng.randrange(3) == 0 else voice)
        t.w32(track + 0x20, 0)
        tracks.append(track)
    chain(t, sound + 0x24, tracks)
    if len(tracks) >= 2 and rng.randrange(3) == 0:
        # The original reloads the successor after track work.
        t.w32(tracks[0] + 0x20, tracks[-1])

    engine_time = rng.choice((0, 1, 100, 0x7fffffff, 0x80000000, 0xffffffff, t.u32()))
    now = rng.choice((0, 1, 1000, 0x7fffffff, 0x80000000, 0xffffffff, t.u32()))
    lookahead = rng.choice((0, 1, 100, 0x7fffffff, 0xffffffff, t.u32()))
    horizon = signed(now + lookahead)
    t.w32(engine + 0x18, engine_time)
    t.w32(engine + 0x28, lookahead)
    t.w32(clock + 0x10, now)

    def event_node(label, time, sentinel):
        node = t.alloc(0x40, label)
        event_record = t.alloc(9, label + " packed record") + 1
        event_state = t.alloc(0x30, label + " state")
        context = t.alloc(0x18, label + " context")
        owner = t.alloc(0x30, label + " owner")
        t.w32(node, t.vtable("event", 5))
        t.w32(node + 0x10, event_record)
        t.w32(node + 0x14, time)
        t.w32(node + 0x24, event_state)
        t.w32(node + 0x2c, context)
        t.w32(context + 0x10, owner)
        t.w32(node + 0x30, rng.choice((0, 0, 1, 0xffffffff)))
        t.w32(node + 0x38, sentinel)
        return node, event_record, event_state

    # Include equality, signed boundaries, wraparound, and ordered lists whose
    # first future node must prevent looking at any later nodes.
    times = [signed(engine_time - 1), signed(engine_time), signed(engine_time + 1),
             signed(horizon - 1), horizon, signed(horizon + 1), -0x80000000, 0x7fffffff]
    pending = []
    for i, time in enumerate(sorted(rng.choices(times, k=rng.choice((0, 1, 2, 4, 6))))):
        node, event_record, _ = event_node(f"pending event {i}", time, sound + 0x38)
        event_type = rng.choice((0, 9, 10, 10, 11, 11, 12, 31))
        t.w32(event_record, (t.u32() & ~31) | event_type)
        pending.append(node)
    chain(t, sound + 0x38, pending)

    active = []
    for i in range(rng.choice((0, 1, 2, 4, 6))):
        node, event_record, event_state = event_node(f"active event {i}", t.u32(), sound + 0x44)
        duration = rng.choice((0, 1, 2, 17, 100, 0x7fffff, 0xffffff))
        word = (duration << 5) | rng.randrange(32) | rng.choice((0, 0x40000000))
        t.w32(event_record, word)
        t.w8(event_state + 0x28, rng.choice((0, 0x40, 0x7f, 0x80, 0x81, 0xc0, 0xff)))
        for off in (0x14, 0x18, 0x1c):
            elapsed = rng.choice((duration - 1, duration, duration + 1,
                                  -1, 0, 0x7fffffff, 0x80000000, t.u32()))
            t.w32(event_state + off, engine_time - elapsed)
        active.append(node)
    chain(t, sound + 0x44, active)
    t.args(r3=sound)
