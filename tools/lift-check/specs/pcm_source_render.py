"""0x824691C0: software PCM source renderer, formerly ph_vt5B98_36_91C0.

Runs the real descriptor getter/resizer (including capacity failures). DSP is a
bounded model: this verifies orchestration, not the resampler/filter algorithm.
Exact comparison, no ignored memory. Covers 0..6 planar channels, empty/multiple
buffers, nonzero intrusive-link offsets, clamped positions, finite/infinite and
zero-length finite loops, exact output boundaries, callback queue/state changes,
fade wraparound, recursive/contended locks, underruns and stop/ending flags.
Callbacks assert lock depth, unlink and poison completed buffers, and may enqueue
one replacement. Data left beyond the output block is a random canary.
The real getter always succeeds; its defensive error exit is unreachable here.
Only valid non-null output interfaces are supplied. r13 uses g_sda_base as in
XmaSource_Render. Run the companion _pcm_source_render_mutations.py for mutations.
"""
import struct

from liftcheck.spec import *

FUNCTION = "PcmSource_Render"
ADDRESS = 0x824691C0
SOURCE = "src/rage/audio/xma_source.cpp"
FP_CONTRACT = "off"
TRIALS = 1000
EXTERNS = {"g_sda_base": 0x82600000}
LOCK = 0x825E7870


def u32(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), "big")


def w32(ctx, addr, value):
    ctx.write(addr, struct.pack(">I", value & 0xFFFFFFFF))


def state(ctx, source):
    return u32(ctx, source + 12)


def check_lock(ctx, source, held):
    config = state(ctx, source)
    assert u32(ctx, LOCK + 4) == u32(ctx, config + 4) + held
    assert u32(ctx, LOCK + 8) == (u32(ctx, config + 8) if u32(ctx, LOCK + 4) else 0)


def acquire(ctx):
    assert ctx.r(3) == LOCK
    # A contending thread finishes releasing before acquisition returns.
    w32(ctx, LOCK, 1)
    w32(ctx, LOCK + 4, 0)


def release(ctx):
    assert ctx.r(3) == LOCK
    assert ctx.read(LOCK + 4, 9) == bytes(9)
    w32(ctx, LOCK, 0)


def process(ctx):
    stream = ctx.r(3)
    source = stream - 180
    check_lock(ctx, source, 0)
    available = u32(ctx, stream + 4) - u32(ctx, stream + 8)
    remaining = u32(ctx, stream + 24) - u32(ctx, stream + 28)
    assert available <= 2048 and remaining <= 256
    n = min(available, remaining, ctx.rng.choice([1, 31, 64, 128, 256]))
    offset = u32(ctx, stream + 28)
    input_offset = u32(ctx, stream + 8)
    # Include input address/position in sample values, so caller mistakes have
    # observable output effects as well as descriptor/call-trace differences.
    tag = (u32(ctx, stream) & 255) / 256 + input_offset / 4096
    for channel in range(ctx.read(stream + 13, 1)[0]):
        sample = struct.pack(">f", 0.25 + channel + tag)
        ctx.write(u32(ctx, stream + 20) + channel * 1024 + offset * 4, sample * n)
    w32(ctx, stream + 8, input_offset + n)
    w32(ctx, stream + 28, offset + n)
    ctx.ret(r3=n)


def set_flags(ctx):
    source = ctx.r(3) - 16
    check_lock(ctx, source, 1)
    assert (ctx.r(4), ctx.r(5)) in [(2, 0), (16, 16)]
    flags = ctx.read(source + 168, 1)[0]
    ctx.write(source + 168, bytes([(flags & ~ctx.r(4)) | ctx.r(5)]))
    if ctx.r(4) == 2 and u32(ctx, state(ctx, source) + 12) & 1:
        # The virtual setter is allowed to change state while the lock is held.
        ctx.write(source + 168, bytes([ctx.rng.choice([1, 5, 9, 17])]))


def stop(ctx):
    source = ctx.r(3)
    check_lock(ctx, source, 1)
    assert ctx.r(4) == 1
    flags = ctx.read(source + 168, 1)[0]
    ctx.write(source + 168, bytes([(flags & ~1) | 16]))


def loop(ctx):
    event = ctx.r(3)
    config = u32(ctx, event)
    source = u32(ctx, config)
    check_lock(ctx, source, 0)
    assert u32(ctx, event + 8) == 0
    if u32(ctx, config + 12) & 2:
        ctx.write(source + 168, bytes([ctx.rng.choice([1, 5, 9, 13, 17])]))
        w32(ctx, source + 176, 0)  # must reload the callback on later loop wraps


def complete(ctx):
    source, buffer = ctx.r(3) - 16, ctx.r(4)
    config = state(ctx, source)
    check_lock(ctx, source, 0)
    assert ctx.r(5) == 0
    assert u32(ctx, buffer + 16) == 0
    link = buffer + u32(ctx, source + 28)
    next_link, previous_link = u32(ctx, link), u32(ctx, link + 4)
    w32(ctx, previous_link, next_link)
    w32(ctx, next_link + 4, previous_link)
    ctx.write(buffer, b"\xDD" * 112)
    w32(ctx, source + 116, ctx.rng.choice([0, 0, 1, 32, 2048]))
    mode = u32(ctx, config + 12)
    if mode & 4:
        ctx.write(source + 168, bytes([ctx.rng.choice([1, 5, 9, 13, 17])]))
    spare = u32(ctx, config + 16)
    if spare:
        # Insert once at the head: the caller must query the queue again.
        head = source + 20
        first = u32(ctx, head)
        link = spare + u32(ctx, source + 28)
        w32(ctx, link, first)
        w32(ctx, link + 4, head)
        w32(ctx, first + 4, link)
        w32(ctx, head, link)
        w32(ctx, config + 16, 0)


CALLS = {
    "KeRaiseIrqlToDpcLevel": stub(ret=lambda ctx: ctx.rng.randrange(4), args=()),
    "KeAcquireSpinLockAtRaisedIrql": model(acquire, deref={"r3": 16}),
    "KeReleaseSpinLockFromRaisedIrql": model(release, deref={"r3": 16}),
    "KfLowerIrql": stub(ret="void"),
    "PcmFrame_Get": run(),
    "PcmFrame_Resize": run(deref={"r4": 12}),
    "XmaRenderStream_Process": model(process, deref={"r3": 88}),
    "pcm.vfn_11": model(stop, args=("r3", "r4")),
    "pcmInterface.vfn_17": model(set_flags, args=("r3", "r4", "r5")),
    "pcmInterface.vfn_19": model(complete, args=("r3", "r4", "r5")),
    "loopCallback": model(loop, args=("r3",), deref={"r3": 12}),
}


def inputs(t):
    rng = t.rng
    source = t.alloc(268, "source", ctype="PcmSourceLayout")
    config = t.alloc(20, "callbackState")
    thread = t.alloc(16, "thread")
    output = t.alloc(6 * 1024 + 64, "planarOutputWithCanary")
    owner = t.alloc(36, "outputOwner")
    mode = rng.randrange(12)
    channels = rng.choice([0, 1, 1, 2, 3, 6])
    t.w32(source, t.vtable("pcm", slots=12))
    t.w32(source + 12, config)
    t.w32(source + 16, t.vtable("pcmInterface", slots=20))
    t.w8(source + 52, channels)
    t.wf32(source + 108, rng.choice([-0.0, 0.0, 0.5, 1.0, -2.0, rng.uniform(-4, 4)]))
    t.w32(source + 116, rng.choice([0, 0, 1, 31, 255, 256, 1024, 0xFFFFFFFF]))
    t.w32(source + 164, rng.choice([0, 0xFFFFFFF0, t.u32()]))
    flags = rng.choice([1, 1, 3, 5, 7, 9, 11, 13, 15, 0, 16, 17, 255])
    if mode in (0, 1, 2, 3):
        flags = [1, 3, 5, 9][mode]
    t.w8(source + 168, flags)
    t.w16(source + 170, rng.choice([0, 1, 2, 3, 65535]))
    t.w32(source + 176, t.fake_fn("loopCallback") if mode % 3 else 0)
    stream = source + 180
    t.w8(stream + 13, channels)
    for off in (36, 40, 48):
        t.wf32(stream + off, rng.choice([-0.0, 0.0, 0.5, 1.0, -2.0, rng.uniform(-4, 4)]))
    t.w8(owner + 13, rng.randrange(7) if mode == 4 else 6)
    t.w32(owner + 16, 48000)
    t.w8(owner + 20, 0)
    t.w8(owner + 21, rng.randrange(7))
    t.w32(owner + 24, 48000)
    t.w32(owner + 28, output)

    offset = rng.choice([0, 28, 32, 100])
    t.w32(source + 28, offset)
    buffers = [t.alloc(112, f"buffer{i}") for i in range(0 if mode == 5 else rng.randrange(1, 6))]
    spare = t.alloc(112, "replacementBuffer")
    links = [source + 20] + [buffer + offset for buffer in buffers]
    for i, link in enumerate(links):
        t.w32(link, links[(i + 1) % len(links)])
        t.w32(link + 4, links[(i - 1) % len(links)])
    for i, buffer in enumerate(buffers + [spare]):
        frames = rng.choice([0, 1, 31, 64, 128, 255, 256, 257, 512, 1024])
        start = rng.randrange(frames + 1)
        length = rng.randrange(frames - start + 1)
        loops = rng.choice([0, 0, 1, 2, 3, 0xFFFFFFFF])
        if loops == 0xFFFFFFFF and length == 0:
            loops = 2  # zero-length infinite loops make no forward progress
        if mode == 6:
            frames, start, length, loops = 256, 0, 256, 1
            t.w32(source + 116, 0)  # loop callback on the exact output boundary
        elif mode == 7:
            frames, loops = 256, 0
            t.w32(source + 116, 0)  # completion on the exact output boundary
        t.w32(buffer + 8, t.alloc(16, f"samples{i}"))
        t.w32(buffer + 12, frames)
        t.w32(buffer + 16, loops)
        t.w32(buffer + 20, start)
        t.w32(buffer + 24, length)
        t.w32(buffer + 92, t.u32())
    depth = rng.choice([0, 0, 1, 2, 7])
    contended = depth and mode == 8
    t.w32(LOCK, 1 if depth else 0)
    t.w32(LOCK + 4, depth)
    t.w32(LOCK + 8, 0x12345678 if contended else thread if depth else 0)
    t.w8(LOCK + 12, rng.randrange(4))
    t.w32(config, source)
    t.w32(config + 4, 0 if contended else depth)
    t.w32(config + 8, thread)
    t.w32(config + 12, rng.randrange(8))
    t.w32(config + 16, spare if mode == 9 else 0)
    t.w32(0x82600000, thread)
    t.args(r3=source, r4=t.u32(), r5=owner + 8, r13=thread)
