"""The game's C++ static initializers, run once over the boot image.

The image is a memory dump from before `_cinit`, so globals that MSVC fills at
startup (`static const Vec4 kUp(0, 0, 0, 1)`, copies of other globals) are zero
in it. Each initializer in the `__xc_a..__xc_z` table runs here on its own, with
every call it makes returning 0 (so a global set from a factory stays null, as
it was), and what it writes is patched into the image the checks start from.
They run in table order, each seeing what the earlier ones wrote; one that faults
leaves nothing behind. Cached in build/.
"""
from __future__ import annotations

import hashlib
import os
import pickle
import struct
from pathlib import Path

from unicorn import ppc_const as P

from .machine import IMAGE_BASE, STACK_TOP, TLS_BASE, Machine

XC_TABLE = (0x825B0010, 0x825B09F0)     # __xc_a..__xc_z, walked by _initterm_e2 (0x8242BFC0)
CACHE = Path(__file__).resolve().parent.parent / "build"


def _runs(patch: dict[int, int]) -> list[tuple[int, bytes]]:
    out, addrs, k = [], sorted(patch), 0
    while k < len(addrs):
        start = addrs[k]
        buf = bytearray()
        while k < len(addrs) and addrs[k] == start + len(buf):
            buf.append(patch[addrs[k]])
            k += 1
        out.append((start, bytes(buf)))
    return out


def patch(image: bytes, m: Machine, syms) -> list[tuple[int, bytes]]:
    """[(address, bytes)] the initializers write into the image."""
    h = hashlib.sha1(image)
    for f in ("staticinit.py", "assist.py", "machine.py", "vmx.py"):
        h.update((Path(__file__).parent / f).read_bytes())
    cache = CACHE / f"static-init-{h.hexdigest()[:16]}.pickle"
    try:
        return pickle.loads(cache.read_bytes())
    except (OSError, pickle.PickleError, EOFError, ValueError):
        pass

    lo, hi = XC_TABLE
    fns = [f for f in struct.unpack(f">{(hi - lo) // 4}I", image[lo - IMAGE_BASE: hi - IMAGE_BASE]) if f]
    written: dict[int, int] = {}

    def returns_zero(mm: Machine, addr: int):
        mm.set_gpr(3, 0)
        mm.set_fpr(1, 0.0)
        mm.uc.reg_write(P.UC_PPC_REG_PC, mm.uc.reg_read(P.UC_PPC_REG_LR) & 0xFFFFFFFF)

    regs = {"gpr": [0] * 32, "fpr": [0.0] * 32, "ctr": 0, "cr": 0, "gpr64": {}}
    regs["gpr"][1], regs["gpr"][13] = STACK_TOP, TLS_BASE
    vregs = [[0, 0, 0, 0] for _ in range(128)]
    for fn in fns:
        r = syms.func_range(fn)
        if r is None:
            continue
        m.prescan(*r)
        res = m.run("init", fn, [r], returns_zero, regs, vregs, max_insns=200_000, timeout_us=2_000_000)
        if res.fault is None:           # later initializers see what earlier ones wrote
            for a in res.writes:
                if IMAGE_BASE <= a < IMAGE_BASE + len(image):
                    written[a] = m.uc.mem_read(a, 1)[0]
            continue
        for a in res.writes:            # a faulting one leaves nothing behind
            m.uc.mem_write(a, bytes([written.get(a, image[a - IMAGE_BASE])])
                           if IMAGE_BASE <= a < IMAGE_BASE + len(image) else b"\0")
    for a in written:                   # back to the boot image; the caller applies the patch
        m.uc.mem_write(a, bytes([image[a - IMAGE_BASE]]))
    out = [(a, d) for a, d in _runs(written) if d != image[a - IMAGE_BASE: a - IMAGE_BASE + len(d)]]
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_bytes(pickle.dumps(out))
        os.replace(tmp, cache)
    except OSError:
        pass
    return out
