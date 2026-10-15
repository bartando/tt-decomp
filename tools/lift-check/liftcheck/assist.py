"""Instructions Unicorn's 32-bit G4 can't run, done in Python.

Unicorn's PPC64 mode is unusable (every 64-bit, FP or vector instruction raises
exception 96, and on the 970 models stores vanish), so lift-check runs a 7400 in
32-bit mode and steps in for the rest of Xenon's set:

- 64-bit integer ops (ld/std, rld*, sld/srd/srad*, extsw, mulld, divd, cmpd, ...).
  GPRs are 32 bits wide in the emulator, so the upper halves live in a shadow:
  a value written here keeps its upper half while the low half is unchanged;
  anything else reads as the sign extension of its low half.
- In code that uses those, every 32-bit integer instruction that writes a GPR
  (add, addi, ori, rlwinm, lwz, ...) still runs natively, but `predict` first
  works out its full 64-bit result and records the upper half, so `mulld` then
  `add` carries into the upper word and `lwz` zero-extends, as on Xenon.
- fsqrt(s), fcfid, fctid(z), dcbz/dcbz128, lwsync/eieio variants.
- every vector instruction (vmx.py), because Unicorn doesn't expose VRs.

`needs_assist(word)` is the pre-scan: lift-check hooks exactly those addresses
and runs them here, skipping the native instruction.
"""
from __future__ import annotations

import math
import struct

from .vmx import OP31_VECTOR_XO, Unsupported, VectorUnit

M32 = 0xFFFFFFFF
M64 = (1 << 64) - 1

_OP31_ASSIST = {
    21: "ldx", 53: "ldux", 149: "stdx", 181: "stdux", 341: "lwax", 373: "lwaux",
    27: "sld", 539: "srd", 794: "srad", 986: "extsw", 58: "cntlzd",
    233: "mulld", 745: "mulldo", 73: "mulhd", 9: "mulhdu",
    489: "divd", 1001: "divdo", 457: "divdu", 969: "divduo",
    68: "td", 84: "ldarx", 214: "stdcx.", 1014: "dcbz",
}


_OP31_WIDE = frozenset(k for k, v in _OP31_ASSIST.items() if v != "dcbz")


def is_wide(w: int) -> bool:
    """A 64-bit integer instruction: code containing one gets `predict` hooks."""
    op = w >> 26
    if op in (30, 58, 62, 2):
        return True
    if op == 31:
        xo10 = (w >> 1) & 0x3FF
        return (xo10 in _OP31_WIDE or ((w >> 2) & 0x1FF) == 413
                or (xo10 in (0, 32) and (w >> 21) & 1))
    return op in (10, 11) and bool((w >> 21) & 1)


# 32-bit instructions that write a GPR, run natively.
_D_PREDICT = frozenset({7, 8, 12, 13, 14, 15, 20, 21, 23, 24, 25, 26, 27, 28, 29, 32, 33, 34, 35,
                        37, 39, 40, 41, 42, 43, 45, 46, 49, 51, 53, 55})
_XO_ARITH = {266: "add", 10: "addc", 138: "adde", 202: "addze", 234: "addme", 40: "subf",
             8: "subfc", 136: "subfe", 200: "subfze", 232: "subfme", 104: "neg", 235: "mullw",
             75: "mulhw", 11: "mulhwu", 491: "divw", 459: "divwu"}
_X_LOGIC = {28: "and", 60: "andc", 444: "or", 412: "orc", 316: "xor", 124: "nor", 476: "nand",
            284: "eqv", 24: "slw", 536: "srw", 792: "sraw", 824: "srawi", 26: "cntlzw",
            954: "extsb", 922: "extsh"}
# X-form loads: xo10 -> (size, signed, update)
_X_LOAD = {23: (4, False, False), 55: (4, False, True), 87: (1, False, False),
           119: (1, False, True), 279: (2, False, False), 311: (2, False, True),
           343: (2, True, False), 375: (2, True, True), 534: (4, False, False),
           790: (2, False, False), 20: (4, False, False)}
_X_UPDATE = frozenset({183, 247, 439, 567, 631, 695, 759})   # st*ux, lf*ux, stf*ux: RA = EA
_X_CLEAR = frozenset({19, 83, 339, 371, 533, 597})            # mfcr mfmsr mfspr mftb lswx lswi
_D_LOAD = {32: (4, False), 33: (4, False), 34: (1, False), 35: (1, False), 40: (2, False),
           41: (2, False), 42: (2, True), 43: (2, True)}


def needs_predict(w: int) -> bool:
    op = w >> 26
    if op in _D_PREDICT:
        return True
    if op != 31 or needs_assist(w):
        return False
    xo10 = (w >> 1) & 0x3FF
    return ((xo10 & 0x1FF) in _XO_ARITH or xo10 in _X_LOGIC or xo10 in _X_LOAD
            or xo10 in _X_UPDATE or xo10 in _X_CLEAR)


def sext32(x: int) -> int:
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def s64(x: int) -> int:
    x &= M64
    return x - (1 << 64) if x >> 63 else x


def _mask64(mb: int, me: int) -> int:
    """IBM-numbered mask: bits mb..me set, bit 0 being the MSB; wraps if mb > me."""
    def upto(n):  # bits 0..n
        return (M64 << (63 - n)) & M64
    if mb <= me:
        return upto(me) & ~upto(mb - 1) & M64 if mb else upto(me)
    return (upto(me) | (~upto(mb - 1) & M64)) & M64


def _rotl64(x: int, n: int) -> int:
    n &= 63
    return ((x << n) | (x >> (64 - n))) & M64 if n else x & M64


def needs_assist(w: int) -> bool:
    op = w >> 26
    if op in (4, 5, 6, 30, 58, 62, 2):
        return True
    if op == 31:
        xo10 = (w >> 1) & 0x3FF
        xo9 = (w >> 2) & 0x1FF
        if xo10 in OP31_VECTOR_XO or xo10 in _OP31_ASSIST or xo9 == 413:
            return True
        if xo10 in (0, 32) and (w >> 21) & 1:      # cmpd / cmpld
            return True
        if xo10 == 598:                             # sync (L=1 lwsync, L=2 ptesync)
            return True
        if xo10 in (19, 144) and (w >> 20) & 1:     # mfocrf / mtocrf
            return True
        return False
    if op in (10, 11) and (w >> 21) & 1:            # cmpldi / cmpdi
        return True
    if op == 59 and ((w >> 1) & 0x1F) == 22:        # fsqrts
        return True
    if op == 63:
        if ((w >> 1) & 0x1F) == 22:                 # fsqrt
            return True
        if ((w >> 1) & 0x3FF) in (846, 814, 815, 14, 15):   # fcfid fctid fctidz fctiw fctiwz
            return True
    return False


class Trap(Exception):
    """A tw/td trap that fired (assert or __debugbreak)."""


class Assist:
    def __init__(self, cpu):
        self.cpu = cpu
        self.vmx = VectorUnit(cpu)

    def execute(self, w: int, pc: int) -> str:
        op = w >> 26
        if op in (4, 5, 6):
            return self.vmx.execute(w, pc)
        if op == 31:
            xo10 = (w >> 1) & 0x3FF
            if xo10 in OP31_VECTOR_XO:
                return self.vmx.execute(w, pc)
            return self._op31(w, xo10)
        if op == 30:
            return self._rld(w)
        if op == 58:
            return self._ld(w)
        if op == 62:
            return self._std(w)
        if op in (10, 11):
            return self._cmpi(w, op == 11)
        if op == 2:
            return self._tdi(w)
        if op in (59, 63):
            return self._fp(w, op)
        raise Unsupported(f"opcode 0x{w:08X}")

    # 64-bit results of native 32-bit instructions --------------------------
    def predict(self, w: int) -> list:
        """[(reg, values)] for the instruction about to run natively: the full 64-bit
        results it can produce (two when it reads the CA bit, which Python can't see),
        or None where the sign extension of the native result is right."""
        cpu = self.cpu
        op = w >> 26
        rt, ra, rb = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
        simm = (w & 0xFFFF) - 0x10000 if w & 0x8000 else w & 0xFFFF

        def g(n):
            return cpu.gpr64(n) & M64

        def ea_d():
            return ((cpu.gpr(ra) if ra else 0) + simm) & M32

        def load(ea, size, signed):
            try:
                v = int.from_bytes(cpu.uc.mem_read(ea, size), "big")
            except Exception:
                return None
            if signed and v >> (8 * size - 1):
                v -= 1 << (8 * size)
            return [v]

        if op == 31:
            xo10 = (w >> 1) & 0x3FF
            name = _XO_ARITH.get(xo10 & 0x1FF)
            if name is not None:
                a, b = g(ra), g(rb)
                if name in ("add", "addc"):
                    return [(rt, [a + b])]
                if name in ("subf", "subfc"):
                    return [(rt, [b - a])]
                if name == "neg":
                    return [(rt, [-a])]
                if name == "adde":
                    return [(rt, [a + b, a + b + 1])]
                if name == "addze":
                    return [(rt, [a, a + 1])]
                if name == "addme":
                    return [(rt, [a - 1, a])]
                if name == "subfe":
                    return [(rt, [~a + b, ~a + b + 1])]
                if name == "subfze":
                    return [(rt, [~a, ~a + 1])]
                if name == "subfme":
                    return [(rt, [~a - 1, ~a])]
                if name == "mullw":
                    return [(rt, [sext32(a) * sext32(b)])]
                # upper half undefined in the ISA; Xenon (per Xenia's tests) zero-extends
                # all but mulhw
                la, lb = a & M32, b & M32
                if name == "mulhwu":
                    return [(rt, [(la * lb) >> 32])]
                if name == "divwu":
                    return [(rt, [la // lb] if lb else None)]
                if name == "divw":
                    sa, sb = sext32(la), sext32(lb)
                    if sb == 0 or (sa == -(1 << 31) and sb == -1):
                        return [(rt, None)]
                    q = abs(sa) // abs(sb)
                    return [(rt, [(q if (sa < 0) == (sb < 0) else -q) & M32])]
                return [(rt, None)]
            name = _X_LOGIC.get(xo10)
            if name is not None:
                s, b = g(rt), g(rb)
                if name in ("slw", "srw"):
                    n, lo = cpu.gpr(rb) & 63, s & M32
                    r = 0 if n > 31 else (lo << n) & M32 if name == "slw" else lo >> n
                    return [(ra, [r])]
                r = {"and": lambda: s & b, "andc": lambda: s & ~b, "or": lambda: s | b,
                     "orc": lambda: s | ~b, "xor": lambda: s ^ b, "nor": lambda: ~(s | b),
                     "nand": lambda: ~(s & b), "eqv": lambda: ~(s ^ b)}.get(name)
                return [(ra, [r()] if r else None)]
            if xo10 in _X_LOAD:
                size, signed, update = _X_LOAD[xo10]
                ea = ((cpu.gpr(ra) if ra else 0) + cpu.gpr(rb)) & M32
                v = load(ea, size, signed)
                if xo10 == 534 and v:
                    v = [int.from_bytes(v[0].to_bytes(4, "big"), "little")]
                elif xo10 == 790 and v:
                    v = [int.from_bytes(v[0].to_bytes(2, "big"), "little")]
                return [(rt, v)] + ([(ra, [ea])] if update else [])
            if xo10 in _X_UPDATE:
                return [(ra, [(cpu.gpr(ra) + cpu.gpr(rb)) & M32])]
            if xo10 == 19:
                return [(rt, [cpu.cr()])]
            if xo10 == 339 and (((w >> 16) & 0x1F) | ((w >> 6) & 0x3E0)) in (8, 9):
                return [(rt, [cpu.spr_lr_ctr((w >> 16) & 0x1F)])]
            return [(rt, None)]
        if op in _D_LOAD:
            size, signed = _D_LOAD[op]
            ea = ea_d()
            return [(rt, load(ea, size, signed))] + ([(ra, [ea])] if op & 1 else [])
        if op in (37, 39, 45, 49, 51, 53, 55):      # stores and FP loads with update
            return [(ra, [ea_d()])]
        if op == 46:                                # lmw
            return [(n, None) for n in range(rt, 32)]
        if op in (14, 15):
            base = g(ra) if ra else 0
            return [(rt, [base + (simm << 16 if op == 15 else simm)])]
        if op in (12, 13):
            return [(rt, [g(ra) + simm])]
        if op == 8:
            return [(rt, [simm - g(ra)])]
        if op == 7:
            return [(rt, [s64(g(ra)) * simm])]
        if op in (24, 25, 26, 27, 28, 29):
            imm = (w & 0xFFFF) << (16 if op & 1 else 0)
            s = g(rt)
            return [(ra, [s | imm if op < 26 else s ^ imm if op < 28 else s & imm])]
        if op in (20, 21, 23):
            sh = cpu.gpr(rb) & 31 if op == 23 else rb
            mb, me = (w >> 6) & 31, (w >> 1) & 31
            lo = g(rt) & M32
            r = _rotl64(lo | (lo << 32), sh)
            m = _mask64(mb + 32, me + 32)
            return [(ra, [(r & m) | (g(ra) & ~m if op == 20 else 0)])]
        return []

    # helpers -----------------------------------------------------------------
    def _cr0(self, v64: int, rc: bool):
        # Titles run with MSR[SF]=0, so record forms compare the low word even for
        # 64-bit instructions (Xenia's divdu. test: 0xFFFFFFFF sets LT).
        if not rc:
            return
        v = sext32(v64)
        so = (self.cpu.xer() >> 31) & 1
        self.cpu.set_cr_field(0, (8 if v < 0 else 4 if v > 0 else 2) | so)

    def _ea_d(self, w, ds=False):
        ra = (w >> 16) & 31
        d = w & 0xFFFC if ds else w & 0xFFFF
        d = d - 0x10000 if d & 0x8000 else d
        base = self.cpu.gpr(ra) if ra else 0
        return (base + d) & M32, ra

    def _ea_x(self, w):
        ra, rb = (w >> 16) & 31, (w >> 11) & 31
        base = self.cpu.gpr(ra) if ra else 0
        return (base + self.cpu.gpr(rb)) & M32, ra

    def _load64(self, ea):
        return int.from_bytes(self.cpu.read(ea, 8), "big")

    # loads/stores ------------------------------------------------------------
    def _ld(self, w):
        rt, kind = (w >> 21) & 31, w & 3
        ea, ra = self._ea_d(w, ds=True)
        if kind == 2:   # lwa
            self.cpu.set_gpr64(rt, sext32(int.from_bytes(self.cpu.read(ea, 4), "big")))
            return "lwa"
        self.cpu.set_gpr64(rt, self._load64(ea))
        if kind == 1:
            self.cpu.set_gpr(ra, ea)
            return "ldu"
        return "ld"

    def _std(self, w):
        rs, kind = (w >> 21) & 31, w & 3
        ea, ra = self._ea_d(w, ds=True)
        self.cpu.write(ea, (self.cpu.gpr64(rs) & M64).to_bytes(8, "big"))
        if kind == 1:
            self.cpu.set_gpr(ra, ea)
            return "stdu"
        return "std"

    # rotates -----------------------------------------------------------------
    def _rld(self, w):
        rs, ra = (w >> 21) & 31, (w >> 16) & 31
        rc = bool(w & 1)
        x = self.cpu.gpr64(rs) & M64
        mb = ((w >> 6) & 0x1F) | (w & 0x20)
        xo = (w >> 2) & 7
        if xo < 4:
            sh = ((w >> 11) & 0x1F) | ((w << 4) & 0x20)
            r = _rotl64(x, sh)
            if xo == 0:
                res, name = r & _mask64(mb, 63), "rldicl"
            elif xo == 1:
                res, name = r & _mask64(0, mb), "rldicr"
            elif xo == 2:
                res, name = r & _mask64(mb, 63 - sh), "rldic"
            else:
                m = _mask64(mb, 63 - sh)
                res, name = (r & m) | (self.cpu.gpr64(ra) & ~m & M64), "rldimi"
        else:
            xo4 = (w >> 1) & 0xF
            n = self.cpu.gpr((w >> 11) & 31) & 63
            r = _rotl64(x, n)
            if xo4 == 8:
                res, name = r & _mask64(mb, 63), "rldcl"
            elif xo4 == 9:
                res, name = r & _mask64(0, mb), "rldcr"
            else:
                raise Unsupported(f"opcode 0x{w:08X}")
        self.cpu.set_gpr64(ra, res)
        self._cr0(res, rc)
        return name + ("." if rc else "")

    # compares ----------------------------------------------------------------
    def _set_cmp(self, crf, a, b):
        so = (self.cpu.xer() >> 31) & 1
        self.cpu.set_cr_field(crf, (8 if a < b else 4 if a > b else 2) | so)

    def _cmpi(self, w, signed):
        crf, ra = (w >> 23) & 7, (w >> 16) & 31
        imm = w & 0xFFFF
        a = self.cpu.gpr64(ra) & M64
        if signed:
            self._set_cmp(crf, s64(a), imm - 0x10000 if imm & 0x8000 else imm)
            return "cmpdi"
        self._set_cmp(crf, a, imm)
        return "cmpldi"

    # primary 31 --------------------------------------------------------------
    def _op31(self, w, xo10):
        cpu = self.cpu
        rt, ra, rb = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
        rc = bool(w & 1)
        if xo10 in (0, 32):
            crf = (w >> 23) & 7
            a, b = cpu.gpr64(ra) & M64, cpu.gpr64(rb) & M64
            if xo10 == 0:
                self._set_cmp(crf, s64(a), s64(b))
                return "cmpd"
            self._set_cmp(crf, a, b)
            return "cmpld"
        if xo10 == 598:
            return "sync"
        if xo10 == 19:      # mfocrf
            cpu.set_gpr64(rt, cpu.cr())
            return "mfocrf"
        if xo10 == 144:     # mtocrf
            fxm = (w >> 12) & 0xFF
            mask = 0
            for k in range(8):
                if fxm & (0x80 >> k):
                    mask |= 0xF << (28 - 4 * k)
            cpu.set_cr((cpu.cr() & ~mask) | (cpu.gpr(rt) & mask))
            return "mtocrf"
        if ((w >> 2) & 0x1FF) == 413:    # sradi
            sh = ((w >> 11) & 0x1F) | ((w << 4) & 0x20)
            x = s64(cpu.gpr64(rt))
            res = x >> sh
            ca = 1 if x < 0 and (x & ((1 << sh) - 1)) else 0
            cpu.set_xer_ca(ca)
            cpu.set_gpr64(ra, res & M64)
            self._cr0(res, rc)
            return "sradi"
        name = _OP31_ASSIST.get(xo10)
        if name is None:
            raise Unsupported(f"opcode 0x{w:08X}")
        if name in ("ldx", "ldux", "ldarx"):
            ea, _ = self._ea_x(w)
            cpu.set_gpr64(rt, self._load64(ea))
            if name == "ldux":
                cpu.set_gpr(ra, ea)
            return name
        if name in ("lwax", "lwaux"):
            ea, _ = self._ea_x(w)
            cpu.set_gpr64(rt, sext32(int.from_bytes(cpu.read(ea, 4), "big")))
            if name == "lwaux":
                cpu.set_gpr(ra, ea)
            return name
        if name in ("stdx", "stdux", "stdcx."):
            ea, _ = self._ea_x(w)
            cpu.write(ea, (cpu.gpr64(rt) & M64).to_bytes(8, "big"))
            if name == "stdux":
                cpu.set_gpr(ra, ea)
            if name == "stdcx.":
                cpu.set_cr_field(0, 2 | ((cpu.xer() >> 31) & 1))
            return name
        if name == "dcbz":
            ea, _ = self._ea_x(w)
            size = 128 if (w >> 21) & 1 else 32
            cpu.write(ea & ~(size - 1), bytes(size))
            return "dcbz128" if size == 128 else "dcbz"
        if name == "td":
            self._trap((w >> 21) & 31, cpu.gpr64(ra), cpu.gpr64(rb))
            return "td"
        if name in ("sld", "srd", "srad"):
            n = cpu.gpr(rb) & 0x7F
            v = cpu.gpr64(rt) & M64
            if name == "sld":
                res = (v << n) & M64 if n < 64 else 0
            elif name == "srd":
                res = v >> n if n < 64 else 0
            else:
                sv = s64(v)
                res = sv >> min(n, 63)
                cpu.set_xer_ca(1 if sv < 0 and (n > 63 or (sv & ((1 << n) - 1))) else 0)
            cpu.set_gpr64(ra, res & M64)
            self._cr0(res, rc)
            return name
        if name == "extsw":
            res = sext32(cpu.gpr(rt))
            cpu.set_gpr64(ra, res & M64)
            self._cr0(res, rc)
            return "extsw"
        if name == "cntlzd":
            v = cpu.gpr64(rt) & M64
            res = 64 - v.bit_length()
            cpu.set_gpr64(ra, res)
            self._cr0(res, rc)
            return "cntlzd"
        a, b = cpu.gpr64(ra), cpu.gpr64(rb)
        if name in ("mulld", "mulldo"):
            res = (s64(a) * s64(b)) & M64
        elif name == "mulhd":
            res = ((s64(a) * s64(b)) >> 64) & M64
        elif name == "mulhdu":
            res = (((a & M64) * (b & M64)) >> 64) & M64
        elif name in ("divd", "divdo"):
            sa, sb = s64(a), s64(b)
            if sb == 0 or (sa == -(1 << 63) and sb == -1):
                res = 0
            else:
                q = abs(sa) // abs(sb)
                res = (q if (sa < 0) == (sb < 0) else -q) & M64
        elif name in ("divdu", "divduo"):
            res = 0 if (b & M64) == 0 else ((a & M64) // (b & M64))
        else:
            raise Unsupported(name)
        cpu.set_gpr64(rt, res)
        self._cr0(res, rc)
        return name

    def _tdi(self, w):
        to, ra = (w >> 21) & 31, (w >> 16) & 31
        imm = w & 0xFFFF
        imm = imm - 0x10000 if imm & 0x8000 else imm
        self._trap(to, self.cpu.gpr64(ra), imm & M64)
        return "tdi"

    def _trap(self, to, a, b):
        sa, sb, ua, ub = s64(a), s64(b), a & M64, b & M64
        if ((to & 16 and sa < sb) or (to & 8 and sa > sb) or (to & 4 and sa == sb)
                or (to & 2 and ua < ub) or (to & 1 and ua > ub)):
            raise Trap()

    # floating point ----------------------------------------------------------
    def _fp(self, w, op):
        cpu = self.cpu
        frt, frb = (w >> 21) & 31, (w >> 11) & 31
        b = struct.unpack(">d", cpu.fpr_raw(frb).to_bytes(8, "big"))[0]
        if ((w >> 1) & 0x1F) == 22:
            r = math.sqrt(b) if b >= 0 else (b if b == 0 else math.nan)
            if op == 59:
                r = struct.unpack(">f", struct.pack(">f", r))[0] if math.isfinite(r) else r
            cpu.set_fpr_raw(frt, int.from_bytes(struct.pack(">d", r), "big"))
            return "fsqrts" if op == 59 else "fsqrt"
        xo = (w >> 1) & 0x3FF
        if xo == 846:   # fcfid
            r = float(s64(cpu.fpr_raw(frb)))
            cpu.set_fpr_raw(frt, int.from_bytes(struct.pack(">d", r), "big"))
            return "fcfid"
        if xo in (14, 15):  # fctiw / fctiwz: QEMU's G4 gets the overflow cases wrong
            if b != b or b <= -(2.0 ** 31):
                r = -(1 << 31)
            elif b >= 2.0 ** 31 - 1:
                r = (1 << 31) - 1
            elif xo == 15:
                r = math.trunc(b)
            else:
                rn = cpu.fpscr() & 3
                r = int(round(b) if rn == 0 else math.trunc(b) if rn == 1
                        else math.ceil(b) if rn == 2 else math.floor(b))
                r = max(-(1 << 31), min((1 << 31) - 1, r))
            cpu.set_fpr_raw(frt, r & M64)
            return "fctiwz" if xo == 15 else "fctiw"
        # fctid / fctidz
        if b != b:
            r = 0x8000000000000000
        elif b >= 2.0 ** 63:
            r = 0x7FFFFFFFFFFFFFFF
        elif b < -(2.0 ** 63):
            r = 0x8000000000000000
        else:
            if xo == 815:
                iv = math.trunc(b)
            else:
                rn = cpu.fpscr() & 3
                iv = (round(b) if rn == 0 else math.trunc(b) if rn == 1
                      else math.ceil(b) if rn == 2 else math.floor(b))
            r = int(iv) & M64
        cpu.set_fpr_raw(frt, r)
        return "fctidz" if xo == 815 else "fctid"
