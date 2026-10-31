"""Reset ordering, default-name allocation, glyph cleanup and retained TLS root.

The glyph ownership callback changes both the current TLS root and the heap in
the retained old TLS block. Retail must free through that retained block's heap.
"""
from liftcheck.spec import *
from specs import _localized_font_lifecycle_inputs as common

FUNCTION = "localizedFontReset"
ADDRESS = 0x82409578
SOURCE = "src/rage/localized_font_lifecycle.cpp"
TRIALS = 500
EXTERNS = {"rage::Release(rage::grcTexture*)": 0x820C2E18}
_font = _sda = _thread = _new_thread = _new_heap = _glyphs = _name = _old_name = 0
_allocated = {}


def allocate(c):
    assert int.from_bytes(c.read(_font + 0x170, 4), "big") == _old_name
    _allocated[c.side] = True
    c.ret(r3=_name)


def ownership(c):
    if c.r(3) == _glyphs and _allocated[c.side]:
        c.write(_sda, _new_thread.to_bytes(4, "big"))
        c.write(_thread + 4, _new_heap.to_bytes(4, "big"))
    common.ownership(c)


CALLS = {**common.CLEAR_CALLS,
         0x820C0038: stub(ret="void", args=()),
         0x820F90D0: model(ownership, args=("r3",)),
         "heap.vfn_1": model(allocate, args=("r3", "r4", "r5")),
         "reboundHeap.vfn_2": stub(ret="void", args=("r3", "r4")),
         "wrongHeap.vfn_2": stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    global _font, _sda, _thread, _new_thread, _new_heap, _glyphs, _name, _old_name, _allocated
    _font, _sda, _thread, _ = common.clear_inputs(t)
    _allocated = {"orig": False, "lift": False}
    _old_name = t.alloc(16, "oldName", fill=b"old\0")
    common._owned[_old_name] = 0x100
    t.w32(_font + 0x170, _old_name)
    _glyphs = t.alloc(16, "glyphs")
    common._owned[_glyphs] = 0x100
    t.w32(_font + 0x64, _glyphs)
    _name = t.alloc(8, "defaultName")
    _new_thread = t.alloc(16, "newThread")
    wrong_heap = t.alloc(16, "wrongHeap")
    t.w32(wrong_heap, t.vtable("wrongHeap", 3))
    t.w32(_new_thread + 4, wrong_heap)
    _new_heap = t.alloc(16, "reboundHeap")
    t.w32(_new_heap, t.vtable("reboundHeap", 3))
    ignored_name = t.alloc(16, "ignoredName", fill=b"ignored\0")
    t.args(r3=_font, r4=t.rng.getrandbits(32), r5=ignored_name, r13=_sda)
