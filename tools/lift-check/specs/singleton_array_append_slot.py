"""0x821A8588: append 12-byte entries, duplicate names, and return the new slot.

Growth across 0x5555 is valid (the asm limit is 0x15555555, above any u16).
Growth wrapping capacity below count and allocation failure with existing entries
are excluded: the original then copies out of bounds or through null. Empty
allocation failure and count wrap without growth are exercised.
"""
from liftcheck.spec import *

FUNCTION = "rage::InitializeSingleton"
ADDRESS = 0x821A8588
SOURCE = "src/rage/memory/singleton_array.cpp"
TRIALS = 1000
EXTERNS = {"g_sda_base": 0x82600000}


def allocate(ctx):
    sda = int.from_bytes(ctx.read(0x82600000, 4), "big")
    fail_first = int.from_bytes(ctx.read(sda + 8, 4), "big")
    if fail_first and len(ctx.m.calls) == 1:
        ctx.ret(r3=0)
        return
    size = ctx.r(3)
    block = ctx.alloc(size)
    # The original only initializes entry words +0 and +8, leaving +4 alone.
    ctx.write(block, ctx.rng.randbytes(size))
    ctx.ret(r3=block)


def duplicate(ctx):
    # The helper has its own spec (lf_rage_str_duplicate). Model it here so
    # large array cases don't time out executing thousands of nested run()s.
    text = ctx.r(3)
    if not text:
        ctx.ret(r3=0)
        return
    data = bytearray()
    while True:
        byte = ctx.read(text + len(data), 1)
        data += byte
        if byte == b"\0":
            break
    copy = ctx.alloc(len(data))
    ctx.write(copy, bytes(data))
    ctx.ret(r3=copy)


CALLS = {
    0x820DEC88: model(allocate, args=("r3",)),
    0x820C29E0: model(duplicate, args=("r3",)),
    0x820C2980: stub(ret="void", args=("r3",)),  # r4 is ignored by delete[]
    0x820F90D0: stub(ret=lambda c: c.rng.choice([0, 1, 0x100, 0x101])),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    sda = t.alloc(16, "sda", fill="zero")
    thread = t.alloc(8, "thread", fill="zero")
    heap = t.alloc(4, "heap")
    t.w32(sda, thread)
    t.w32(thread + 4, heap)
    t.w32(heap, t.vtable("heap"))
    t.w32(0x82600000, sda)

    # Most trials stay compact, with occasional large counts exposing the old
    # bogus 0x5555 clamp and the final u16 count increment.
    count = t.pick([21844, 21845, 21846, 65535]) if t.rng.randrange(100) == 0 else t.pick([0, 1, 2, 7, 16, 31])
    grow = count < 65520 and t.rng.choice([True, False])
    capacity = count if grow else t.pick([(count + 1) & 0xFFFF, count - 1 if count else 1])
    data = 0 if count == 0 and t.rng.choice([True, False]) else t.alloc(12 * (count + 1), "entries")
    # Reuse a few real strings; null names still call the duplicate helper.
    names = [0, t.alloc(1, "empty_name", fill=b"\0"),
             t.alloc(6, "name", fill=b"entry\0")]
    for i in range(count):
        t.w32(data + 12 * i, t.pick(names))
        t.w32(data + 12 * i + 4, t.u32())
        t.w32(data + 12 * i + 8, t.u32())
    array = t.alloc(8, "array")
    t.w32(array, data)
    t.w16(array + 4, count)
    t.w16(array + 6, capacity)
    t.w32(sda + 8, int(count == 0 and grow and t.rng.randrange(4) == 0))
    t.args(r3=array, r13=sda)
