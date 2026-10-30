"""SWF event/hit-test tree walk (only pg_D078_g).

Exercise press/release/neither, optional callbacks, focus changes during dispatch,
definition replacement, zero/one/multiple children and nested sibling traversal.
Rectangle cases include every edge/corner, each rejection, negative dimensions,
signed coordinate conversion, general affine matrices, fused-rounding boundaries,
NaNs and infinities.

Limits: slot lookup, bounds calculation, transform rebuild and virtual bodies are
boundary models, not proofs of those callees. Original button-edge helpers run.
Models cover bounds helpers that leave outMin untouched (including the original
conversion-scratch initial value). Trees are finite/acyclic, at most seven nodes;
callbacks may replace definitions/focus, but do not delete nodes. No ignored
memory or float tolerance. This does not establish native rendering performance.
"""
import struct

from liftcheck.spec import *

FUNCTION = "pg_D078_g"
ADDRESS = 0x823FD078
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
# Other TUs also label a different CheckButtonPressed overload/address.
# This call is unambiguously 0x821DFFF8 in the original instruction stream.
EXTERNS = {"CheckButtonPressed": 0x821DFFF8}


def _u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def _lookup(ctx):
    assert ctx.r(4) in (13, 32)
    ctx.ret(r3=_u32(ctx, ctx.r(3) + 4 * ctx.r(4)))


def _callback(ctx):
    assert ctx.r(4) == ctx.r(5) == ctx.r(7) == 0
    node = ctx.r(6)
    replacement = _u32(ctx, ctx.r(3) + 4)
    if replacement:
        ctx.write(node + 4, struct.pack(">I", replacement))
    focus = _u32(ctx, ctx.r(3) + 8)
    if focus:
        ctx.write(0x8260281C, struct.pack(">I", node if focus == 1 else 0))


def _update(ctx):
    replacement = _u32(ctx, ctx.r(3) + 4)
    if replacement:
        ctx.write(ctx.r(4) + 4, struct.pack(">I", replacement))
    # Observable per-node write catches omitted/duplicated recursive visits.
    counter = ctx.r(4) + 0x104
    ctx.write(counter, struct.pack(">I", (_u32(ctx, counter) + 1) & 0xFFFFFFFF))


def _transition(ctx):
    assert (ctx.r(5), ctx.r(6)) in ((2, 3), (3, 2))
    ctx.write(ctx.r(4) + 0x108, struct.pack(">II", ctx.r(5), ctx.r(6)))


def _bounds(ctx, minimum_offset, size_offset, skip_bit):
    node = ctx.r(3)
    if not (_u32(ctx, node + 0xE4) & skip_bit):
        ctx.write(ctx.r(4), ctx.read(node + minimum_offset, 4))
    ctx.ret(f1=struct.unpack(">f", ctx.read(node + size_offset, 4))[0])


def _transform(ctx):
    # The helper's output must be reloaded before the comparisons.
    node = ctx.r(3) - 8
    ctx.write(ctx.r(3), ctx.read(node + 0xE8, 24))


CALLS = {
    0x823FB188: model(_lookup, args=("r3", "r4")),
    0x821DFFF8: run(),
    0x821E0068: run(),
    0x823FEF98: model(lambda c: _bounds(c, 0xD4, 0xD8, 1), args=("r3", "r4")),
    0x823FF0D8: model(lambda c: _bounds(c, 0xDC, 0xE0, 2), args=("r3", "r4")),
    0x823FB018: model(_transform, args=("r3",), deref={"r3": 24}),
    "callback.vfn_14": model(_callback, args=("r3", "r4", "r5", "r6", "r7")),
    "definition.vfn_2": model(_update, args=("r3", "r4")),
    "definition.vfn_3": model(_transition, args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    rng = t.rng
    slots = t.alloc(132, "inputSlots")
    t.w32(0x82604848, slots)
    for index in (13, 32):
        record = t.alloc(4, f"button{index}")
        t.w32(slots + 4 * index, record)
        # Four combinations of current/previous pressed state, arbitrary
        # released polarity and irrelevant low bits.
        released = rng.randrange(256)
        state, previous = rng.randrange(2), rng.randrange(2)
        t.w8(record, released ^ (state << 7) ^ rng.randrange(128))
        t.w8(record + 1, released ^ (previous << 7) ^ rng.randrange(128))
        t.w8(record + 3, released)

    definition_table = t.vtable("definition")
    callback_table = t.vtable("callback")
    count = rng.choice((1, 1, 2, 3, 7))
    nodes = [t.alloc(0x110, f"node{i}") for i in range(count)]
    pointer_x, pointer_y = rng.choice((
        (0, 0), (5, 5), (10, 10), (0, 10), (10, 0),
        (-1, 5), (11, 5), (5, -1), (5, 11),
        (-2147483648, 2147483647), (16777217, -16777217),
        (rng.randint(-100, 100), rng.randint(-100, 100)),
    ))
    rounding_case = rng.randrange(8)
    if rounding_case < 2:
        pointer_x = pointer_y = 0
    t.w32(0x825F312C, pointer_x)
    t.w32(0x825F3138, pointer_y)
    t.w32(0x8260281C, rng.choice((0, *nodes)))

    for i, node in enumerate(nodes):
        definition = t.alloc(8, f"definition{i}")
        replacement = t.alloc(8, f"replacement{i}")
        for d in (definition, replacement):
            t.w32(d, definition_table)
        t.w32(definition + 4, rng.choice((0, replacement)))
        t.w32(replacement + 4, 0)
        t.w32(node + 4, definition)
        for offset in (0xCC, 0xD0):
            callback = t.alloc(12, f"callback{i}_{offset:X}")
            t.w32(callback, callback_table)
            t.w32(callback + 4, rng.choice((0, replacement)))
            t.w32(callback + 8, rng.choice((0, 0, 0, 1, 2)))
            t.w32(node + offset, rng.choice((0, callback, callback)))

        t.w32(node + 0xB4, 0)
        t.w32(node + 0xB8, 0)
        t.floats(node + 8, 6)  # deliberately stale matrix
        mode = 6 + rounding_case if rounding_case < 2 else rng.randrange(6)
        matrix = (1, 0, 0, 1, 0, 0)
        bounds = (0, 10, 0, 10)  # minX, width, minY, height
        if mode == 1:
            matrix = tuple(rng.uniform(-4, 4) for _ in range(6))
            bounds = tuple(rng.uniform(-20, 20) for _ in range(4))
        elif mode == 2:
            matrix = tuple(rng.choice((0, -0.0, 1, -1, float("inf"), -float("inf"), float("nan")))
                           for _ in range(6))
        elif mode == 3:
            bounds = tuple(rng.choice((0, -0.0, 10, -10, float("inf"), -float("inf"), float("nan")))
                           for _ in range(4))
        elif mode == 4:
            # Near large integer conversion and inclusive rectangle edges.
            matrix = (1, 0, 0, 1, float(pointer_x), float(pointer_y))
            bounds = (0, rng.choice((0, 1, 32)), 0, rng.choice((0, 1, 32)))
        elif mode >= 6:
            # Exact fused residual is +/-2^-46; separate multiply/add gives
            # zero and incorrectly admits the origin on the left/right edge.
            ulp = 2 ** -23
            matrix = (-1 if mode == 6 else -(1 + 2 * ulp), 0, 1 + ulp, 0, 0, 0)
            bounds = (1, 0, 1 - ulp if mode == 6 else 1 + ulp, 0)
        for k, value in enumerate(bounds):
            t.wf32(node + 0xD4 + 4 * k, value)
        t.w32(node + 0xE4, rng.randrange(4) if mode == 5 else 0)
        for k, value in enumerate(matrix):
            t.wf32(node + 0xE8 + 4 * k, value)

    # Pick an earlier parent for each node: always acyclic, with both deep
    # chains and sibling lists. Preserve insertion order among siblings.
    last_child = {}
    for i in range(1, count):
        parent = rng.randrange(i)
        if parent in last_child:
            t.w32(nodes[last_child[parent]] + 0xB8, nodes[i])
        else:
            t.w32(nodes[parent] + 0xB4, nodes[i])
        last_child[parent] = i
    t.args(r3=nodes[0])
