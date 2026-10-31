"""Font factory normalization, TLS allocation, fallback and failure cleanup.

Constructor/load/cleanup are call boundaries. Load may replace the stored name
and leave dirty status bits. Inputs are null or terminated within 80 bytes;
retail's unterminated >=80-byte names have no defined C-string contract.
"""
from liftcheck.spec import *

FUNCTION = "localizedFontCreate"
ADDRESS = 0x82409128
SOURCE = "src/rage/localized_font.cpp"
TRIALS = 600
_font = _copy = 0
_names = []
_results = []
_loads = {}


def allocate(c):
    c.ret(r3=_font)


def construct(c):
    c.write(c.r(3) + 0x170, _names[0].to_bytes(4, "big"))
    c.ret(r3=c.r(3))


def load(c):
    index = _loads[c.side]
    _loads[c.side] += 1
    if c.r(3):
        c.write(c.r(3) + 0x170, _names[index + 1].to_bytes(4, "big"))
    c.ret(r3=_results[index])


def duplicate(c):
    text = bytearray()
    while True:
        byte = c.read(c.r(3) + len(text), 1)
        text += byte
        if byte == b"\0":
            break
    c.write(_copy, text)
    c.ret(r3=_copy)


CALLS = {
    0x82430120: run(),
    0x820C0038: stub(ret="void", args=()),
    "heap.vfn_1": model(allocate, args=("r3", "r4", "r5")),
    0x82409338: model(construct, args=("r3",)),
    0x824098E8: model(load, args=("r3", "r4", "r5")),
    0x82409490: stub(ret="void", args=("r3",)),
    0x820C00C0: stub(ret="void", args=("r3",)),
    0x820C29E0: model(duplicate, args=("r3",)),
}


def inputs(t):
    global _font, _copy, _names, _results, _loads
    rng = t.rng
    sda = t.alloc(16, "sda")
    thread = t.alloc(16, "thread")
    heap = t.alloc(16, "heap")
    t.w32(sda, thread)
    t.w32(thread + 4, heap)
    t.w32(heap, t.vtable("heap", 2))
    t.w32(0x82600000, sda)
    _font = t.alloc(0x17C, "font") if t.index % 7 else 0
    _copy = t.alloc(80, "copiedName")
    _names = [t.alloc(16, "loadedName", fill=label) for label in (b"initial\0", b"first\0", b"fallback\0")]
    _results = [rng.choice((0, 0x100, 1, 0x101, 0xff, 0xffffffff)) for _ in range(2)]
    if not _font:
        _results = [0x100, 0]
    _loads = {"orig": 0, "lift": 0}
    text = rng.choice((None, b"", b"Arial12", b"HUD_Bold", b"MiXeD.Case", b"\xc0\xe0Az", b"A" * 79))
    name = 0 if text is None else t.alloc(len(text) + 1, "requestedName", fill=text + b"\0")
    t.args(r3=name, r13=sda)
