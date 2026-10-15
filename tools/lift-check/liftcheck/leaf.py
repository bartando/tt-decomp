"""Which volatile registers a leaf function can write.

MSVC's link-time code generation lets a caller keep values in volatile registers
across a call to a leaf it knows leaves them alone (r8 across pg_C2A0_g, f1 and r7
across io_Input_poll_9D68, r3 = this after a reset). A stub standing in for such a
callee must leave them alone too, so the dispatcher only clobbers what the
original callee could write. Over-approximates: any field that may be a
destination counts.
"""
from __future__ import annotations

_STORES = {36, 38, 44, 47, 52, 54}                 # stw stb sth stmw stfs stfd
_STORE_UPDATE = {37, 39, 45, 53, 55}               # stwu stbu sthu stfsu stfdu: write RA
_FP_LOADS = {48, 49, 50, 51}                       # lfs lfsu lfd lfdu
_OP31_NO_GPR = {0, 32, 4, 54, 86, 246, 278, 470, 982, 598, 854, 1014,      # cmp tw dcb* sync
                144, 146, 178, 467,                                        # mtcrf mtmsr(d) mtspr
                151, 215, 407, 662, 918, 149, 150, 214, 663, 727, 725, 661,  # stores
                6, 38, 7, 39, 71, 103, 359, 519, 551, 775, 807,            # vector loads
                135, 167, 199, 231, 487, 647, 679, 903, 935}               # vector stores
_OP31_FP = {535, 567, 599, 631}                    # lfsx lfsux lfdx lfdux: write FRT


def written(words: list[int], lo: int, hi: int) -> tuple[set[int], set[int]] | None:
    """(GPRs, FPRs) the code in [lo, hi) may write, or None if it isn't a leaf (calls,
    branches out of its range, jumps through CTR)."""
    gprs: set[int] = set()
    fprs: set[int] = set()
    data: set[int] = set()
    for k, w in enumerate(words):
        pc = lo + 4 * k
        if pc in data:
            continue
        op = w >> 26
        rt, ra = (w >> 21) & 31, (w >> 16) & 31
        if op == 18:
            if w & 1:
                return None
            li = w & 0x03FFFFFC
            li = li - 0x04000000 if li & 0x02000000 else li
            dest = li if w & 2 else pc + li
            if not lo <= dest < hi:
                return None             # a tail call
        elif op == 16:
            if w & 1:
                return None
            bd = w & 0xFFFC
            bd = bd - 0x10000 if bd & 0x8000 else bd
            dest = bd if w & 2 else pc + bd
            if not lo <= dest < hi:
                return None
        elif op == 19:
            xo = (w >> 1) & 0x3FF
            if xo in (16, 528) and w & 1:
                return None             # bclrl / bcctrl
            if xo == 528:               # bcctr: fine if it's a jump table into this function
                table = _jump_table(words, k, lo)
                if table is None or not lo <= table < hi:
                    return None
                a = table
                while lo <= a < hi and lo <= words[(a - lo) // 4] < hi:
                    data.add(a)
                    a += 4
        elif op == 17:
            return None
        elif op in (2, 3, 10, 11, 4, 5, 6):
            pass                        # traps, compares, vector
        elif op in _STORES:
            pass
        elif op in _STORE_UPDATE:
            gprs.add(ra)
        elif op in _FP_LOADS:
            fprs.add(rt)
            if op & 1:
                gprs.add(ra)
        elif op in (24, 25, 26, 27, 28, 29, 20, 21, 23, 30):
            gprs.add(ra)
        elif op in (7, 8, 12, 13, 14, 15, 32, 34, 40, 42):
            gprs.add(rt)
        elif op in (33, 35, 41, 43):
            gprs.update((rt, ra))
        elif op == 46:                  # lmw
            gprs.update(range(rt, 32))
        elif op in (59, 63):
            xo = (w >> 1) & 0x3FF
            if not (op == 63 and xo in (0, 32, 64, 38, 70, 134, 711)):   # fcmp*, mcrfs, mtfs*
                fprs.add(rt)
        elif op == 62:
            if w & 3 == 1:
                gprs.add(ra)
        elif op == 31:
            xo = (w >> 1) & 0x3FF
            if xo in _OP31_FP:
                fprs.add(rt)
                if xo in (567, 631):
                    gprs.add(ra)
            elif xo in (695, 759, 983):     # stfsux stfdux: RA; stfiwx: nothing
                if xo != 983:
                    gprs.add(ra)
            elif xo not in _OP31_NO_GPR:
                gprs.update((rt, ra))
        else:
            gprs.update((rt, ra))
            fprs.add(rt)
    return gprs, fprs


def _jump_table(words, k, lo) -> int | None:
    """MSVC's switch: lis rB,hi; addi rB,rB,lo; ...; lwzx rA,rB,rX; mtctr rA; bctr.
    -> the table's address, or None."""
    if k < 2 or (words[k - 1] & 0xFC1FFFFF) != 0x7C0903A6:          # mtctr rA
        return None
    ra = (words[k - 1] >> 21) & 31
    lw = words[k - 2]
    if lw >> 26 != 31 or (lw >> 1) & 0x3FF != 23 or (lw >> 21) & 31 != ra:   # lwzx rA, rB, rX
        return None
    rb = (lw >> 16) & 31
    base = None
    for j in range(k - 3, max(k - 10, -1), -1):
        w = words[j]
        if w >> 26 == 14 and (w >> 21) & 31 == rb and (w >> 16) & 31 == rb and base is None:
            base = w & 0xFFFF
            base = base - 0x10000 if base & 0x8000 else base
        elif w >> 26 == 15 and (w >> 21) & 31 == rb and (w >> 16) & 31 == 0 and base is not None:
            return ((w & 0xFFFF) << 16) + base & 0xFFFFFFFF
    return None
