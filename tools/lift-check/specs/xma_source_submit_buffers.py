"""ke_7278: XAudio XMA input queue submission and completion, 0x82467278.

Uses the original decoder callees, including the two input slots, loop/read
position packing and both live/cached query modes. Only physical translation,
IRQL/spinlocks and completion callbacks are models. No memory is ignored.
Checks empty/mixed queues, 0..6 streams, full slots, loop-count truncation,
retained final buffers, detached entries, pending positions and recursive locks.
Callbacks unlink and poison the retired buffer and can change source state.
The source lock is held on entry, as in XmaSource_Render. r13 is represented by
its existing host equivalent g_sda_base. Byte 11 of the loop descriptor is ABI
padding: the real callee reads exactly bytes 0..10, which are compared at calls.

Mutation checks:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xma_source_submit_buffers_mutations.py
"""
import struct

from liftcheck.spec import *

FUNCTION = "XmaSource_SubmitBuffers"
ADDRESS = 0x82467278
SOURCE = "src/rage/audio/xma_source.cpp"
TRIALS = 1000
EXTERNS = {"g_sda_base": 0x82600000}


def u32(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), "big")


def w32(ctx, addr, value):
    ctx.write(addr, struct.pack(">I", value & 0xFFFFFFFF))


def physical_address(ctx):
    ctx.ret(r3=ctx.r(3) ^ 0x10000000)


def complete(ctx):
    source, buffer = ctx.r(3) - 16, ctx.r(4)
    decoder = u32(ctx, source + 180)
    assert ctx.r(5) == 0
    assert ctx.read(buffer + 96, 1) == b"\x04"
    assert u32(ctx, source + 268) == u32(ctx, decoder + 16) - 1
    assert u32(ctx, 0x825E7874) == u32(ctx, decoder + 20)
    for lock in (source + 264, 0x825E7870):
        assert u32(ctx, lock + 8) == (u32(ctx, decoder + 24) if u32(ctx, lock + 4) else 0)
    link = buffer + u32(ctx, source + 28)
    next_link, previous_link = u32(ctx, link), u32(ctx, link + 4)
    w32(ctx, previous_link, next_link)
    w32(ctx, next_link + 4, previous_link)
    # Accessing current after callback is invalid; next must already be saved.
    ctx.write(buffer, b"\xDD" * 144)
    mode = u32(ctx, decoder + 28)
    if mode & 1:
        ctx.write(source + 168, bytes([ctx.rng.choice([0, 1, 16, 17, 255])]))
    if mode & 2:
        ctx.write(source + 52, bytes([ctx.rng.randrange(7)]))
    if mode & 4:
        w32(ctx, source + 116, ctx.rng.choice([0, 32, 16384, 0xFFFFFFFF]))


CALLS = {
    "KeRaiseIrqlToDpcLevel": stub(ret=lambda ctx: ctx.rng.randrange(4), args=()),
    "KeAcquireSpinLockAtRaisedIrql": stub(ret="void", deref={"r3": 16}),
    "KeReleaseSpinLockFromRaisedIrql": stub(ret="void", deref={"r3": 16}),
    "KfLowerIrql": stub(ret="void"),
    "XmaDecoder_HasInputSpace": run(),
    "XmaDecoder_IsBufferPending": run(),
    "XmaDecoder_GetStreamStatus": run(),
    "XmaDecoder_IsInputEmpty": run(),
    "XmaDecoder_SubmitData": run(),
    "XmaDecoder_SetReadPosition": run(),
    "XmaDecoder_SetLoopRegion": run(deref={"r5": 11}),
    0x8246B618: run(),  # inline XMA packet header -> initial read position
    0x8258630C: model(physical_address, args=("r3",)),
    "interface.vfn_19": model(complete, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    source = t.alloc(280, "source")
    decoder = t.alloc(32, "decoder")
    contexts = t.alloc(6 * 96, "decoderContexts")
    thread = t.alloc(16, "thread")
    mode = rng.randrange(12)
    count = rng.choice([0, 1, 1, 2, 3, 6])
    if mode in (0, 1, 2):
        count = rng.choice([1, 2, 6])
    t.w8(source + 52, count)
    t.w8(source + 168, rng.choice([0, 1, 1, 3, 16, 17, 255]))
    t.w32(source + 16, t.vtable("interface", slots=20))
    t.w32(source + 180, decoder)
    t.w32(decoder, 6)
    t.w32(decoder + 4, rng.choice([0, 0x20000]))
    t.w32(decoder + 8, contexts)
    t.w32(decoder + 28, rng.randrange(8))

    buffers = [t.alloc(144, f"buffer{i}") for i in range(rng.randrange(7))]
    data = [t.alloc(32, f"packet{i}") for i in range(max(1, len(buffers)))]
    offset = rng.choice([0, 100, 112, 128])
    t.w32(source + 28, offset)
    links = [source + 20] + [buffer + offset for buffer in buffers]
    for i, link in enumerate(links):
        t.w32(link, links[(i + 1) % len(links)])
        t.w32(link + 4, links[(i - 1) % len(links)])
    for i, buffer in enumerate(buffers):
        if offset:
            t.w32(buffer, buffer if mode == 8 and i == rng.randrange(len(buffers)) else buffer + offset)
        t.w32(buffer + 8, data[i])
        t.w32(buffer + 12, rng.choice([0, 2048, 4096, 65536, 0xFFFFFFFF]))
        t.w32(buffer + 16, rng.choice([0, 0, 1, 8, 31, 255, 256, 257, 0xFFFFFFFF]))
        for stream in range(6):
            t.w32(buffer + 20 + stream * 12, t.u32())
            t.w32(buffer + 24 + stream * 12, t.u32())
            t.w8(buffer + 28 + stream * 12, rng.randrange(4))
            t.w8(buffer + 29 + stream * 12, rng.randrange(8))
        state = 0 if mode in (0, 1, 2) else rng.choice([0, 0, 1, 2, 3, 4, 5, 255])
        t.w8(buffer + 96, state)
    for i in range(6):
        context = contexts + i * 96
        slots = 0 if mode in (0, 1, 2) else rng.randrange(4)
        t.w32(context, (t.u32() & ~0x300000) | (slots << 20))
        t.w32(context + 80, rng.choice(data))
        t.w32(context + 84, rng.choice(data))
        # Cached queries can see the live context or an independent snapshot.
        cached = context if mode != 9 else t.alloc(12, f"snapshot{i}")
        t.w32(context + 64, cached)
        t.w32(source + 116 + i * 8, rng.choice([0, 1, 32, 0x3FFFFFF, 0xFFFFFFFF]))
        t.w16(source + 120 + i * 8, rng.choice([0, 1, 127, 128, 255, 256, 65535]))
    if mode in (0, 3):
        t.w32(source + 116, 0)
    for lock, depth, saved in [
        (source + 264, rng.choice([1, 1, 2, 7]), decoder + 16),
        (0x825E7870, rng.choice([0, 0, 1, 2, 7]), decoder + 20),
    ]:
        t.w32(lock, t.u32())
        t.w32(lock + 4, depth)
        t.w32(lock + 8, thread if depth else 0)
        t.w8(lock + 12, rng.randrange(4))
        t.w32(saved, depth)
    t.w32(decoder + 24, thread)
    t.w32(0x82600000, thread)
    t.args(r3=source, r13=thread)
