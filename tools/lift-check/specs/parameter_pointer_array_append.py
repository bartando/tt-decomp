"""Fixed 16-slot growth, raw four-byte entries, singleton ownership and TLS free.
Compare complete old/new storage, array counters, return slot and calls. The
allocator boundary returns fresh zeroed storage; no ignored writes or bytes.
"""
from liftcheck.spec import *
FUNCTION = 'atFreeList_Alloc'
ADDRESS = 0x822665C0
SOURCE = 'src/rage/data/parameter_node.cpp'
TRIALS = 800
_owned = 0
CALLS = {
    'rage_Alloc': alloc(size_reg='r3'),
    'rage_FindSingleton': stub(ret=lambda c: _owned, args=('r3',)),
    'heap.vfn_2': stub(ret='void', args=('r3', 'r4')),
}

def inputs(t):
    global _owned
    r = t.rng
    _owned = r.choice([0, 0, 1, 255, 256, 0xffffff00])
    array = t.alloc(32, 'pointerArrayAndGuards') + 8
    count = r.randrange(33)
    capacity = count + r.choice([0, 0, 1, 16])
    entries = t.alloc(max(capacity, 1) * 4, 'oldEntries') if capacity else 0
    t.w32(array, entries)
    t.w16(array + 4, count)
    t.w16(array + 6, capacity)
    sda, tls, heap = (t.alloc(16, n) for n in ['sda', 'tls', 'heap'])
    t.w32(sda, tls)
    t.w32(tls + 4, heap)
    t.w32(heap, t.vtable('heap', 3))
    t.w32(0x82600000, sda)
    t.args(r3=array, r4=t.u32(), r13=sda)
