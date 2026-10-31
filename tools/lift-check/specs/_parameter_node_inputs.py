"""Shared fixtures for the XML name/value nodes, with four-byte pointer fields."""
import math
from liftcheck.spec import *

_copy_result = 0
_slot = 0
_redirect = 0

def duplicate(c):
    c.ret(r3=_copy_result if c.r(3) else 0)

LEAF_CALLS = {
    'rage_free': stub(ret='void', args=('r3',)),
    'rage_strDuplicate': model(duplicate, args=('r3',)),
}

def node(t):
    global _copy_result
    p = t.alloc(48, 'nodeAndGuards') + 16
    name = t.alloc(16, 'oldName', fill=b'oldName\0' + bytes(8))
    text = t.alloc(16, 'oldText', fill=b'oldText\0' + bytes(8))
    kind = t.rng.choice([0, 0, 1, 2, 3, 255])
    t.w32(p, t.rng.choice([name, name, 0]))
    t.w32(p + 4, t.rng.choice([text, 0]) if kind == 0 else t.u32())
    t.w8(p + 8, kind)
    t.w8(p + 9, t.u32() & 255)
    _copy_result = t.alloc(24, 'duplicatedText')
    return p

def text(t):
    return t.rng.choice([0, t.alloc(16, 'newText', fill=b'newText\0' + bytes(8))])

def copy_flag(t):
    return t.rng.choice([0, 1, 2, 255, 256, 0xff00, t.u32()])

def real(t):
    return t.rng.choice([0., -0., 1., -1., math.inf, -math.inf, math.nan,
                         2.**-140, -2.**-140, t.rng.uniform(-1e6, 1e6)])

def slot_result(c):
    c.ret(r3=_slot)

def primary(c):
    if _redirect:
        c.write(_slot, _redirect.to_bytes(4, 'big'))
    c.ret()

WRAPPER_CALLS = {
    'rage_Alloc': run(transparent=True),
    0x820C0038: stub(ret='void', args=()),
    'heap.vfn_1': model(lambda c: c.ret(r3=int.from_bytes(c.read(c.r(3) + 4, 4), 'big')),
                        args=('r3', 'r4', 'r5')),
    'atFreeList_Alloc': model(slot_result, args=('r3', 'r4')),
    'cmOperator_SetPrimaryName': model(primary, args=('r3', 'r4', 'r5'), deref={'r3': 12}),
    'cmOperator_SetIntegerValue': stub(ret='void', args=('r3', 'r4'), deref={'r3': 12}),
    'cmOperator_SetRealValue': stub(ret='void', args=('r3', 'f1'), deref={'r3': 12}),
}

def wrapper(t):
    global _slot, _redirect
    _slot = t.alloc(16, 'childPointerSlot')
    _redirect = t.alloc(16, 'redirectedChild') if t.rng.randrange(4) == 0 else 0
    sda = t.alloc(16, 'sda')
    tls = t.alloc(16, 'tls')
    heap = t.alloc(16, 'heap')
    child = 0 if t.rng.randrange(5) == 0 else t.alloc(32, 'allocatedChild')
    t.w32(sda, tls)
    t.w32(tls + 4, heap)
    t.w32(heap, t.vtable('heap', 3))
    t.w32(heap + 4, child)
    t.w32(0x82600000, sda)
    t.args(r13=sda)
    return t.alloc(64, 'owner')
