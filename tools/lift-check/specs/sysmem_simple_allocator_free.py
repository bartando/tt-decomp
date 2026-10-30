"""Free body: physical coalescing, intrusive size lists and retail bad frees.

Exercises neither/previous/next/both free neighbours, absent neighbours and
merges ending exactly at heapEnd; head/middle/tail unlinking (including both
neighbours in one bucket); empty/nonempty insertion; all tags, size-class
boundaries and overflow bucket 15. Random counter values exercise wrapping.
Whole-heap comparison includes poison bytes, unpoisoned payload tails, absorbed
headers, physical backlinks and every free-list link.

Retail diagnoses but continues for locked heaps, ownership rejection, corrupt
self guards and already-free headers. Already-free blocks may still be linked:
reinsertion can leave a self-link, and accounting is repeated. Those effects
are intentionally preserved, not treated as allocator invariants.

Limits: this isolates the unlocked body, not the locking thunk or Allocate.
Ownership is a scripted virtual call (including high-bit-only return values);
diagnostics return as in retail, comparing text and checking pointer varargs.
memset uses the checker's byte-accurate model. Addresses do not wrap; headers
and links stay mapped, with small positive sizes >=16. Null/unmapped pointers,
arbitrary corrupt links, and poison-length underflow may fault in the original
and are not claimed as tolerated inputs. Negative signed size classes and
32-bit address-wrap cases are outside this spec's coverage.
"""
from liftcheck.spec import *

FUNCTION = "sysMemSimpleAllocator_Free_body"
ADDRESS = 0x821871C0
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
TRIALS = 500

_expected_ptr = None


def _diagnostic(ctx):
    # The first two warnings have no initialized varargs in the original.
    prefix = b"sysMemSimpleAllocator::Free"
    if ctx.read(ctx.r(3), len(prefix)) == prefix:
        assert ctx.r(4) == _expected_ptr, "diagnostic lost the freed pointer"


CALLS = {
    "allocator.vfn_20": stub(
        ret=lambda ctx: int.from_bytes(ctx.read(ctx.r(3) + 0xC0, 4), "big"),
        args=("r3", "r4")),
    0x8240E6D0: model(_diagnostic, args=("r3",)),
}

SIZES = (16, 17, 31, 32, 47, 48, 208, 224, 239, 240, 255, 256, 512, 2048)


def inputs(t):
    global _expected_ptr
    rng = t.rng
    obj = t.alloc(0xC4, "allocator")
    t.w32(obj, t.vtable("allocator", slots=21))
    t.w8(obj + 0xB9, rng.choice((0, 0, 1, 255)))
    t.w32(obj + 0xC0, rng.choice((0, 1, 0x100, 0x101, 0xFFFFFF00, 0xFFFFFF01)))
    for i in range(16):
        t.w32(obj + 0x0C + 4 * i, 0)
        t.w32(obj + 0x58 + 4 * i, t.u32())
    t.w32(obj + 0x54, t.u32())
    t.w32(obj + 0x98, t.u32())

    position = rng.choice(("first", "middle", "last", "only"))
    prev_free, next_free = rng.choice(((False, False), (False, True), (True, False), (True, True)))
    double_free = rng.choice((False, False, False, True))
    bad_guard = rng.choice((False, False, False, True))
    # (role, payload size, allocated)
    layout = []
    if position in ("middle", "last"):
        layout.append(("previous", rng.choice(SIZES), not prev_free))
    target_size = rng.choice(SIZES)
    layout.append(("target", target_size, not double_free))
    if position in ("first", "middle"):
        layout.append(("next", rng.choice(SIZES), not next_free))
        if rng.choice((False, True)):
            layout.append(("after_next", rng.choice(SIZES), True))

    heap_size = sum(size + 16 for _, size, _ in layout)
    base = t.alloc(heap_size, "physical_heap")
    t.w32(obj + 0x04, base)
    t.w32(obj + 0x4C, heap_size)
    free_nodes = []

    def header(address, size, allocated, previous=0):
        t.w32(address, address)
        t.w32(address + 4, size)
        t.w32(address + 8, previous)
        t.w32(address + 12, (t.u32() & ~0x10) | (0x10 if allocated else 0))

    address, previous = base, 0
    merged_size = target_size
    for role, size, allocated in layout:
        header(address, size, allocated, previous)
        if role == "target":
            target = address
            if bad_guard:
                t.w32(address, address ^ 0x12345678)
            if double_free and rng.choice((False, True)):
                free_nodes.append((address, size))
        elif not allocated:
            free_nodes.append((address, size))
            merged_size += size + 16
        previous, address = address, address + size + 16

    # Also cover mapped pointers outside the advertised heap: warning-only.
    if rng.randrange(8) == 0:
        t.w32(obj + 0x4C, target - base)
        t.w32(obj + 0xC0, 0)

    # Detached list nodes give independent head/interior/tail unlink branches,
    # and an existing head in the eventual insertion bucket.
    for i in range(rng.randrange(5)):
        size = rng.choice((merged_size, *SIZES))
        address = t.alloc(size + 16, f"list_node_{i}")
        header(address, size, False)
        free_nodes.append((address, size))
    rng.shuffle(free_nodes)
    lists = {}
    for address, size in free_nodes:
        lists.setdefault(min(size // 16, 15), []).append(address)
    for index, nodes in lists.items():
        t.w32(obj + 0x0C + 4 * index, nodes[0])
        for i, address in enumerate(nodes):
            t.w32(address + 16, nodes[i - 1] if i else 0)
            t.w32(address + 20, nodes[i + 1] if i + 1 < len(nodes) else 0)

    _expected_ptr = target + 16
    t.args(r3=obj, r4=_expected_ptr)
