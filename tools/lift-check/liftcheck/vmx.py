"""AltiVec + Xenon VMX128 in Python.

Unicorn has no vector registers it lets us read, and no VMX128 at all, so every
vector instruction (and the vector loads/stores in primary opcode 31) runs here
on a 128-register file of four big-endian u32 words each. Decoding follows the
binutils table the ReXGlue disassembler uses (thirdparty/disasm/ppc-dis.c).

Floats follow Xenon's VMX: non-Java mode, so denormal inputs and results are
flushed to zero. Estimate instructions (vrefp, vrsqrtefp, vexptefp, vlogefp)
return the exact value, not the hardware's 12-bit estimate.
"""
from __future__ import annotations

import math
import struct

M32 = 0xFFFFFFFF


class Unsupported(Exception):
    """An instruction lift-check can't run. str() is 'mnemonic' or 'opcode 0x...'."""


# ── float helpers ────────────────────────────────────────────────────────────

_pk_f, _upk_f = struct.Struct(">f").pack, struct.Struct(">f").unpack
_pk_I, _upk_I = struct.Struct(">I").pack, struct.Struct(">I").unpack


def u2f(u: int) -> float:
    if (u & 0x7F800000) == 0:          # denormal or zero: flush (keeps sign)
        return -0.0 if u & 0x80000000 else 0.0
    return _upk_f(_pk_I(u))[0]


def f2u(x: float) -> int:
    try:
        u = _upk_I(_pk_f(x))[0]
    except OverflowError:
        u = 0xFF800000 if x < 0 else 0x7F800000
    if (u & 0x7F800000) == 0:
        u &= 0x80000000
    return u


def _sat(v: int, lo: int, hi: int) -> tuple[int, bool]:
    if v < lo:
        return lo, True
    if v > hi:
        return hi, True
    return v, False


def _s32(u: int) -> int:
    return u - (1 << 32) if u & 0x80000000 else u


# ── lane views ───────────────────────────────────────────────────────────────

def to_bytes(v) -> bytes:
    return struct.pack(">4I", *v)


def from_bytes(b: bytes) -> list[int]:
    return list(struct.unpack(">4I", b))


def halves(v) -> list[int]:
    return list(struct.unpack(">8H", to_bytes(v)))


def from_halves(h) -> list[int]:
    return from_bytes(struct.pack(">8H", *[x & 0xFFFF for x in h]))


def bytes_of(v) -> list[int]:
    return list(to_bytes(v))


def from_byte_list(b) -> list[int]:
    return from_bytes(bytes(x & 0xFF for x in b))


def _signed(x: int, bits: int) -> int:
    return x - (1 << bits) if x & (1 << (bits - 1)) else x


# ── VMX128 operand fields (binutils extract_*) ───────────────────────────────

def vd128(i): return ((i << 3) & 0x60) | ((i >> 21) & 0x1F)
def va128(i): return ((i >> 4) & 0x40) | (i & 0x20) | ((i >> 16) & 0x1F)
def vb128(i): return ((i << 5) & 0x60) | ((i >> 11) & 0x1F)
def vc128(i): return (i >> 6) & 7
def vperm128(i): return ((i >> 1) & 0xE0) | ((i >> 16) & 0x1F)


# ── the unit ─────────────────────────────────────────────────────────────────

class VectorUnit:
    """Owns v0..v127 and VSCR. `cpu` gives GPR, CR and memory access."""

    def __init__(self, cpu):
        self.cpu = cpu
        self.v = [[0, 0, 0, 0] for _ in range(128)]
        self.vscr = 0x00010000  # NJ set

    # memory helpers ----------------------------------------------------------
    def _ea(self, i):
        ra, rb = (i >> 16) & 31, (i >> 11) & 31
        base = self.cpu.gpr(ra) if ra else 0
        return (base + self.cpu.gpr(rb)) & M32

    def _load16(self, addr):
        return from_bytes(self.cpu.read(addr & ~0xF, 16))

    def _store(self, addr, data: bytes):
        self.cpu.write(addr, data)

    # dispatch ----------------------------------------------------------------
    def execute(self, i: int, pc: int) -> str:
        """Runs one vector instruction; returns its mnemonic. Raises Unsupported."""
        op = i >> 26
        if op == 4:
            return self._op4(i)
        if op == 5:
            return self._op5(i)
        if op == 6:
            return self._op6(i)
        if op == 31:
            return self._op31(i)
        raise Unsupported(f"opcode 0x{i:08X}")

    # primary 31: AltiVec + Xenon vector loads/stores ------------------------
    _OP31 = {
        6: "lvsl", 38: "lvsr", 7: "lvebx", 39: "lvehx", 71: "lvewx",
        103: "lvx", 359: "lvxl", 135: "stvebx", 167: "stvehx", 199: "stvewx",
        231: "stvx", 487: "stvxl", 519: "lvlx", 551: "lvrx", 647: "stvlx",
        679: "stvrx", 775: "lvlxl", 807: "lvrxl", 903: "stvlxl", 935: "stvrxl",
    }

    def _op31(self, i):
        xo = (i >> 1) & 0x3FF
        name = self._OP31.get(xo)
        if name is None:
            raise Unsupported(f"opcode 0x{i:08X}")
        self._loadstore(name, (i >> 21) & 31, i)
        return name

    def _loadstore(self, name, vr, i):
        ea = self._ea(i)
        base = name[:-1] if name.endswith("xl") else name   # LRU hint only
        v = self.v
        if base == "lvsl":
            sh = ea & 0xF
            v[vr] = from_byte_list(range(sh, sh + 16))
        elif base == "lvsr":
            sh = ea & 0xF
            v[vr] = from_byte_list(range(16 - sh, 32 - sh))
        elif base in ("lvx", "lvebx", "lvehx", "lvewx"):
            v[vr] = self._load16(ea)
        elif base == "stvx":
            self._store(ea & ~0xF, to_bytes(v[vr]))
        elif base == "stvebx":
            self._store(ea, to_bytes(v[vr])[ea & 0xF:(ea & 0xF) + 1])
        elif base == "stvehx":
            a = ea & ~1
            self._store(a, to_bytes(v[vr])[a & 0xF:(a & 0xF) + 2])
        elif base == "stvewx":
            a = ea & ~3
            self._store(a, to_bytes(v[vr])[a & 0xF:(a & 0xF) + 4])
        elif base == "lvlx":
            sh = ea & 0xF
            blk = to_bytes(self._load16(ea))
            v[vr] = from_bytes(blk[sh:] + bytes(sh))
        elif base == "lvrx":
            sh = ea & 0xF
            if sh == 0:
                v[vr] = [0, 0, 0, 0]
            else:
                blk = to_bytes(self._load16(ea))
                v[vr] = from_bytes(bytes(16 - sh) + blk[:sh])
        elif base == "stvlx":
            sh = ea & 0xF
            self._store(ea, to_bytes(v[vr])[:16 - sh])
        elif base == "stvrx":
            sh = ea & 0xF
            if sh:
                self._store(ea & ~0xF, to_bytes(v[vr])[16 - sh:])
        else:
            raise Unsupported(name)

    # primary 4 ---------------------------------------------------------------
    _VMX128_LS = {
        3: "lvsl", 67: "lvsr", 131: "lvewx", 195: "lvx", 387: "stvewx",
        451: "stvx", 707: "lvxl", 963: "stvxl", 1027: "lvlx", 1091: "lvrx",
        1283: "stvlx", 1347: "stvrx", 1539: "lvlxl", 1603: "lvrxl",
        1795: "stvlxl", 1859: "stvrxl",
    }

    def _op4(self, i):
        xo6 = i & 0x3F
        if 32 <= xo6 <= 47:
            return self._va_form(i, xo6)
        if i & 0x10:
            # vsldoi128 vD, vA, vB, SHB
            shb = (i >> 6) & 0xF
            a, b = to_bytes(self.v[va128(i)]), to_bytes(self.v[vb128(i)])
            self.v[vd128(i)] = from_bytes((a + b)[shb:shb + 16])
            return "vsldoi128"
        if (i & 3) == 3:
            name = self._VMX128_LS.get(i & 0x7F3)
            if name is None:
                raise Unsupported(f"opcode 0x{i:08X}")
            self._loadstore(name, vd128(i), i)
            return name + "128"
        return self._vx_form(i)

    def _va_form(self, i, xo6):
        vd, va, vb, vc = (i >> 21) & 31, (i >> 16) & 31, (i >> 11) & 31, (i >> 6) & 31
        v = self.v
        if xo6 == 42:
            v[vd] = self._sel(v[va], v[vb], v[vc])
            return "vsel"
        if xo6 == 43:
            v[vd] = self._perm(v[va], v[vb], v[vc])
            return "vperm"
        if xo6 == 44:
            shb = vc & 0xF
            v[vd] = from_bytes((to_bytes(v[va]) + to_bytes(v[vb]))[shb:shb + 16])
            return "vsldoi"
        if xo6 == 46:
            v[vd] = self._fmap3(v[va], v[vc], v[vb], _madd)
            return "vmaddfp"
        if xo6 == 47:
            v[vd] = self._fmap3(v[va], v[vc], v[vb], _nmsub)
            return "vnmsubfp"
        raise Unsupported(f"AltiVec VA-form xo {xo6} (0x{i:08X})")

    # AltiVec VX/VXR ----------------------------------------------------------
    def _vx_form(self, i):
        vd, va, vb = (i >> 21) & 31, (i >> 16) & 31, (i >> 11) & 31
        xo = i & 0x7FF
        v = self.v
        A, B = v[va], v[vb]
        f = _VX.get(xo)
        if f is not None:
            name, fn = f
            v[vd] = fn(self, A, B, va)
            return name
        xr = i & 0x3FF
        c = _VXR.get(xr)
        if c is not None:
            name, fn = c
            res = fn(A, B)
            v[vd] = res
            if i & 0x400:
                self._cr6(res, name == "vcmpbfp")
                return name + "."
            return name
        if xo == 1540:      # mfvscr
            v[vd] = [0, 0, 0, self.vscr]
            return "mfvscr"
        if xo == 1604:      # mtvscr
            self.vscr = B[3]
            return "mtvscr"
        raise Unsupported(f"AltiVec VX xo {xo} (0x{i:08X})")

    def _cr6(self, res, bounds):
        if bounds:
            field = 0b0010 if all(w == 0 for w in res) else 0
        else:
            all_t = all(w == M32 for w in res)
            all_f = all(w == 0 for w in res)
            field = (0b1000 if all_t else 0) | (0b0010 if all_f else 0)
        self.cpu.set_cr_field(6, field)

    # primary 5 ---------------------------------------------------------------
    def _op5(self, i):
        v = self.v
        d, a, b = vd128(i), va128(i), vb128(i)
        if (i & 0x210) == 0:
            v[d] = self._perm(v[a], v[b], v[vc128(i)])
            return "vperm128"
        xo = i & 0x3D0
        D, A, B = v[d], v[a], v[b]
        if xo == 16:
            v[d] = self._fmap(A, B, lambda x, y: x + y); return "vaddfp128"
        if xo == 80:
            v[d] = self._fmap(A, B, lambda x, y: x - y); return "vsubfp128"
        if xo == 144:
            v[d] = self._fmap(A, B, lambda x, y: x * y); return "vmulfp128"
        if xo == 208:   # vD = vA*vB + vD
            v[d] = self._fmap3(A, B, D, _madd); return "vmaddfp128"
        if xo == 272:   # vD = vA*vD + vB
            v[d] = self._fmap3(A, D, B, _madd); return "vmaddcfp128"
        if xo == 336:   # vD = -(vA*vB - vD)
            v[d] = self._fmap3(A, B, D, _nmsub); return "vnmsubfp128"
        if xo == 400:
            s = self._dot(A, B, 3); v[d] = [s] * 4; return "vmsum3fp128"
        if xo == 464:
            s = self._dot(A, B, 4); v[d] = [s] * 4; return "vmsum4fp128"
        if xo == 528:
            v[d] = [x & y for x, y in zip(A, B)]; return "vand128"
        if xo == 592:
            v[d] = [x & ~y & M32 for x, y in zip(A, B)]; return "vandc128"
        if xo == 656:
            v[d] = [~(x | y) & M32 for x, y in zip(A, B)]; return "vnor128"
        if xo == 720:
            v[d] = [x | y for x, y in zip(A, B)]; return "vor128"
        if xo == 784:
            v[d] = [x ^ y for x, y in zip(A, B)]; return "vxor128"
        if xo == 848:   # vsel128 vD, vA, vB, vD
            v[d] = self._sel(A, B, D); return "vsel128"
        if xo == 912:
            v[d] = self._slo(A, B); return "vslo128"
        if xo == 976:
            v[d] = self._sro(A, B); return "vsro128"
        packs = {512: ("vpkshss128", _pk_shss), 576: ("vpkshus128", _pk_shus),
                 640: ("vpkswss128", _pk_swss), 704: ("vpkswus128", _pk_swus),
                 768: ("vpkuhum128", _pk_uhum), 832: ("vpkuhus128", _pk_uhus),
                 896: ("vpkuwum128", _pk_uwum), 960: ("vpkuwus128", _pk_uwus)}
        if xo in packs:
            name, fn = packs[xo]
            v[d] = fn(A, B)
            return name
        raise Unsupported(f"VMX128 opcode 0x{i:08X}")

    # primary 6 ---------------------------------------------------------------
    def _op6(self, i):
        v = self.v
        d, a, b = vd128(i), va128(i), vb128(i)
        D, A, B = v[d], v[a], v[b]
        uimm = (i >> 16) & 0x1F
        if (i & 0x630) == 0x210:
            p = vperm128(i)
            v[d] = [B[(p >> (6 - 2 * k)) & 3] for k in range(4)]
            return "vpermwi128"
        x3 = i & 0x7F0
        if x3 == 560:
            v[d] = [self._cvt_to_int(w, uimm, True) for w in B]; return "vcfpsxws128"
        if x3 == 624:
            v[d] = [self._cvt_to_int(w, uimm, False) for w in B]; return "vcfpuxws128"
        if x3 == 688:
            v[d] = [f2u(_s32(w) / (1 << uimm)) for w in B]; return "vcsxwfp128"
        if x3 == 752:
            v[d] = [f2u(w / (1 << uimm)) for w in B]; return "vcuxwfp128"
        if x3 == 816:
            v[d] = self._fmap1(B, math.floor); return "vrfim128"
        if x3 == 880:
            v[d] = self._fmap1(B, _round_even); return "vrfin128"
        if x3 == 944:
            v[d] = self._fmap1(B, math.ceil); return "vrfip128"
        if x3 == 1008:
            v[d] = self._fmap1(B, math.trunc); return "vrfiz128"
        if (i & 0x730) == 0x610:
            raise Unsupported("vpkd3d128")
        if x3 == 1584:
            v[d] = self._fmap1(B, _recip); return "vrefp128"
        if x3 == 1648:
            v[d] = self._fmap1(B, _rsqrt); return "vrsqrtefp128"
        if x3 == 1712:
            v[d] = self._fmap1(B, _exp2); return "vexptefp128"
        if x3 == 1776:
            v[d] = self._fmap1(B, _log2); return "vlogefp128"
        if (i & 0x730) == 0x710:
            z = (i >> 6) & 3
            rot = B[z:] + B[:z]
            v[d] = [rot[k] if (uimm >> (3 - k)) & 1 else D[k] for k in range(4)]
            return "vrlimi128"
        if x3 == 1840:
            v[d] = [B[uimm & 3]] * 4; return "vspltw128"
        if x3 == 1904:
            v[d] = [_signed(uimm, 5) & M32] * 4; return "vspltisw128"
        if x3 == 2032:
            raise Unsupported("vupkd3d128")
        xo = i & 0x3D0
        cmps = {0: ("vcmpeqfp128", _cmpeqfp), 128: ("vcmpgefp128", _cmpgefp),
                256: ("vcmpgtfp128", _cmpgtfp), 384: ("vcmpbfp128", _cmpbfp),
                512: ("vcmpequw128", _cmpequw)}
        base = xo & ~0x40
        if base in cmps:
            name, fn = cmps[base]
            res = fn(A, B)
            v[d] = res
            if xo & 0x40:
                self._cr6(res, base == 384)
                return name + "."
            return name
        if xo == 80:
            v[d] = [_rotl32(x, y & 31) for x, y in zip(A, B)]; return "vrlw128"
        if xo == 208:
            v[d] = [(x << (y & 31)) & M32 for x, y in zip(A, B)]; return "vslw128"
        if xo == 336:
            v[d] = [(_s32(x) >> (y & 31)) & M32 for x, y in zip(A, B)]; return "vsraw128"
        if xo == 464:
            v[d] = [x >> (y & 31) for x, y in zip(A, B)]; return "vsrw128"
        if xo == 640:
            v[d] = self._fmap(A, B, _fmax); return "vmaxfp128"
        if xo == 704:
            v[d] = self._fmap(A, B, _fmin); return "vminfp128"
        if xo == 768:
            v[d] = [A[0], B[0], A[1], B[1]]; return "vmrghw128"
        if xo == 832:
            v[d] = [A[2], B[2], A[3], B[3]]; return "vmrglw128"
        if xo == 896:   # vupkhsb128 vD, vB
            v[d] = _unpack_sb(B, high=True); return "vupkhsb128"
        if xo == 960:
            v[d] = _unpack_sb(B, high=False); return "vupklsb128"
        raise Unsupported(f"VMX128 opcode 0x{i:08X}")

    # shared ops --------------------------------------------------------------
    @staticmethod
    def _fmap(A, B, fn):
        out = []
        for x, y in zip(A, B):
            try:
                out.append(f2u(fn(u2f(x), u2f(y))))
            except (ValueError, OverflowError, ZeroDivisionError):
                out.append(0x7FC00000)
        return out

    @staticmethod
    def _fmap1(B, fn):
        out = []
        for x in B:
            try:
                out.append(f2u(fn(u2f(x))))
            except (ValueError, OverflowError, ZeroDivisionError):
                out.append(0x7FC00000)
        return out

    @staticmethod
    def _fmap3(A, B, C, fn):
        out = []
        for x, y, z in zip(A, B, C):
            try:
                out.append(f2u(fn(u2f(x), u2f(y), u2f(z))))
            except (ValueError, OverflowError):
                out.append(0x7FC00000)
        return out

    @staticmethod
    def _dot(A, B, n):
        s = 0.0
        try:
            for k in range(n):
                s += u2f(A[k]) * u2f(B[k])
            return f2u(s)
        except (ValueError, OverflowError):
            return 0x7FC00000

    @staticmethod
    def _sel(A, B, C):
        return [(a & ~c & M32) | (b & c) for a, b, c in zip(A, B, C)]

    @staticmethod
    def _perm(A, B, C):
        src = to_bytes(A) + to_bytes(B)
        return from_byte_list(src[c & 0x1F] for c in to_bytes(C))

    @staticmethod
    def _slo(A, B):
        sh = (B[3] >> 3) & 0xF
        return from_bytes(to_bytes(A)[sh:] + bytes(sh))

    @staticmethod
    def _sro(A, B):
        sh = (B[3] >> 3) & 0xF
        return from_bytes(bytes(sh) + to_bytes(A)[:16 - sh])

    def _cvt_to_int(self, w, scale, signed):
        x = u2f(w)
        if x != x:
            return 0x80000000 if signed else 0
        x = x * (1 << scale)
        lo, hi = ((-(1 << 31), (1 << 31) - 1) if signed else (0, M32))
        if x >= hi or x <= lo:
            r = hi if x >= hi else lo
            if x != r:
                self.vscr |= 1          # SAT
        else:
            r = int(x)                  # toward zero
        return r & M32


# ── element-wise tables ──────────────────────────────────────────────────────

def _r32(x):
    """Rounds to single precision (the product of a multiply-add is rounded on its own)."""
    return u2f(f2u(x))


def _madd(a, c, b):
    return _r32(a * c) + b


def _nmsub(a, c, b):
    return -(_r32(a * c) - b)


def _rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & M32 if n else x


def _round_even(x):
    return float(round(x))


def _recip(x):
    if x == 0:
        return math.copysign(math.inf, x)
    return 1.0 / x


def _rsqrt(x):
    if x == 0:
        return math.copysign(math.inf, x)
    if x < 0:
        return math.nan
    if math.isinf(x):
        return 0.0
    return 1.0 / math.sqrt(x)


def _exp2(x):
    try:
        return 2.0 ** x
    except OverflowError:
        return math.inf


def _log2(x):
    if x == 0:
        return -math.inf
    if x < 0:
        return math.nan
    return math.log2(x)


def _fmax(x, y):
    if x != x or y != y:
        return math.nan
    return x if x > y else y


def _fmin(x, y):
    if x != x or y != y:
        return math.nan
    return x if x < y else y


def _cmpf(fn):
    def go(A, B):
        return [M32 if fn(u2f(a), u2f(b)) else 0 for a, b in zip(A, B)]
    return go


_cmpeqfp = _cmpf(lambda a, b: a == b)
_cmpgefp = _cmpf(lambda a, b: a >= b)
_cmpgtfp = _cmpf(lambda a, b: a > b)


def _cmpbfp(A, B):
    out = []
    for a, b in zip(A, B):
        x, y = u2f(a), u2f(b)
        le = 0 if x <= y else 0x80000000
        ge = 0 if x >= -y else 0x40000000
        if x != x or y != y:
            le, ge = 0x80000000, 0x40000000
        out.append(le | ge)
    return out


def _cmpequw(A, B):
    return [M32 if a == b else 0 for a, b in zip(A, B)]


def _lanes(bits):
    if bits == 8:
        return bytes_of, from_byte_list
    if bits == 16:
        return halves, from_halves
    return list, list


def _int_op(bits, fn, signed=False):
    get, put = _lanes(bits)
    mask = (1 << bits) - 1

    def go(self, A, B, va):
        a, b = get(A), get(B)
        if signed:
            a = [_signed(x, bits) for x in a]
            b = [_signed(x, bits) for x in b]
        return put([fn(x, y, bits) & mask for x, y in zip(a, b)])
    return go


def _sat_op(bits, fn, signed):
    get, put = _lanes(bits)
    lo, hi = ((-(1 << (bits - 1)), (1 << (bits - 1)) - 1) if signed else (0, (1 << bits) - 1))

    def go(self, A, B, va):
        a, b = get(A), get(B)
        if signed:
            a = [_signed(x, bits) for x in a]
            b = [_signed(x, bits) for x in b]
        out = []
        for x, y in zip(a, b):
            r, sat = _sat(fn(x, y), lo, hi)
            if sat:
                self.vscr |= 1
            out.append(r & ((1 << bits) - 1))
        return put(out)
    return go


def _avg(bits, signed):
    return _int_op(bits, lambda x, y, b: (x + y + 1) >> 1, signed)


def _vsl(self, A, B, va):
    sh = B[3] & 7
    x = int.from_bytes(to_bytes(A), "big")
    return from_bytes(((x << sh) & ((1 << 128) - 1)).to_bytes(16, "big"))


def _vsr(self, A, B, va):
    sh = B[3] & 7
    x = int.from_bytes(to_bytes(A), "big")
    return from_bytes((x >> sh).to_bytes(16, "big"))


def _cmp_int(bits, fn, signed=False):
    get, put = _lanes(bits)
    mask = (1 << bits) - 1

    def go(A, B):
        a, b = get(A), get(B)
        if signed:
            a = [_signed(x, bits) for x in a]
            b = [_signed(x, bits) for x in b]
        return put([mask if fn(x, y) else 0 for x, y in zip(a, b)])
    return go


def _splat(bits):
    get, put = _lanes(bits)
    n = 128 // bits

    def go(self, A, B, uimm):
        return put([get(B)[uimm % n]] * n)
    return go


def _splat_imm(bits):
    get, put = _lanes(bits)
    n = 128 // bits

    def go(self, A, B, simm):
        return put([_signed(simm, 5) & ((1 << bits) - 1)] * n)
    return go


def _merge(bits, high):
    get, put = _lanes(bits)
    n = 128 // bits

    def go(self, A, B, va):
        a, b = get(A), get(B)
        half = range(0, n // 2) if high else range(n // 2, n)
        out = []
        for k in half:
            out += [a[k], b[k]]
        return put(out)
    return go


def _shift(bits, kind):
    get, put = _lanes(bits)
    mask = (1 << bits) - 1

    def go(self, A, B, va):
        out = []
        for x, y in zip(get(A), get(B)):
            s = y & (bits - 1)
            if kind == "l":
                r = x << s
            elif kind == "r":
                r = x >> s
            elif kind == "a":
                r = _signed(x, bits) >> s
            else:
                r = (x << s) | (x >> (bits - s)) if s else x
            out.append(r & mask)
        return put(out)
    return go


def _pack(src_bits, dst_bits, src_signed, dst_signed, saturate):
    get, _ = _lanes(src_bits)
    _, put = _lanes(dst_bits)
    lo = -(1 << (dst_bits - 1)) if dst_signed else 0
    hi = (1 << (dst_bits - 1)) - 1 if dst_signed else (1 << dst_bits) - 1

    def go(A, B):
        out = []
        for x in get(A) + get(B):
            if src_signed:
                x = _signed(x, src_bits)
            if saturate:
                x, _ = _sat(x, lo, hi)
            out.append(x & ((1 << dst_bits) - 1))
        return put(out)
    return go


_pk_shss = _pack(16, 8, True, True, True)
_pk_shus = _pack(16, 8, True, False, True)
_pk_swss = _pack(32, 16, True, True, True)
_pk_swus = _pack(32, 16, True, False, True)
_pk_uhum = _pack(16, 8, False, False, False)
_pk_uhus = _pack(16, 8, False, False, True)
_pk_uwum = _pack(32, 16, False, False, False)
_pk_uwus = _pack(32, 16, False, False, True)


def _unpack(src_bits, high, signed=True):
    get, _ = _lanes(src_bits)
    _, put = _lanes(src_bits * 2)
    n = 128 // src_bits

    def go(B):
        src = get(B)
        part = src[: n // 2] if high else src[n // 2:]
        return put([(_signed(x, src_bits) if signed else x) for x in part])
    return go


def _unpack_sb(B, high):
    return _unpack(8, high)(B)


def _vx_unary(fn):
    def go(self, A, B, va):
        return VectorUnit._fmap1(B, fn)
    return go


def _vx_bin(fn):
    def go(self, A, B, va):
        return VectorUnit._fmap(A, B, fn)
    return go


def _vx_cvt_from(signed):
    def go(self, A, B, uimm):
        return [f2u((_s32(w) if signed else w) / (1 << uimm)) for w in B]
    return go


def _vx_cvt_to(signed):
    def go(self, A, B, uimm):
        return [self._cvt_to_int(w, uimm, signed) for w in B]
    return go


def _wrap(fn):
    """Adapts a (A, B) -> v function to the VX signature."""
    def go(self, A, B, va):
        return fn(A, B)
    return go


def _maxmin(bits, signed, want_max):
    return _int_op(bits, (lambda x, y, b: max(x, y)) if want_max else (lambda x, y, b: min(x, y)), signed)


_VX = {
    0: ("vaddubm", _int_op(8, lambda x, y, b: x + y)),
    64: ("vadduhm", _int_op(16, lambda x, y, b: x + y)),
    128: ("vadduwm", _int_op(32, lambda x, y, b: x + y)),
    1024: ("vsububm", _int_op(8, lambda x, y, b: x - y)),
    1088: ("vsubuhm", _int_op(16, lambda x, y, b: x - y)),
    1152: ("vsubuwm", _int_op(32, lambda x, y, b: x - y)),
    10: ("vaddfp", _vx_bin(lambda x, y: x + y)),
    74: ("vsubfp", _vx_bin(lambda x, y: x - y)),
    1034: ("vmaxfp", _vx_bin(_fmax)),
    1098: ("vminfp", _vx_bin(_fmin)),
    266: ("vrefp", _vx_unary(_recip)),
    330: ("vrsqrtefp", _vx_unary(_rsqrt)),
    394: ("vexptefp", _vx_unary(_exp2)),
    458: ("vlogefp", _vx_unary(_log2)),
    522: ("vrfin", _vx_unary(_round_even)),
    586: ("vrfiz", _vx_unary(math.trunc)),
    650: ("vrfip", _vx_unary(math.ceil)),
    714: ("vrfim", _vx_unary(math.floor)),
    778: ("vcfux", _vx_cvt_from(False)),
    842: ("vcfsx", _vx_cvt_from(True)),
    906: ("vctuxs", _vx_cvt_to(False)),
    970: ("vctsxs", _vx_cvt_to(True)),
    1028: ("vand", _wrap(lambda A, B: [x & y for x, y in zip(A, B)])),
    1092: ("vandc", _wrap(lambda A, B: [x & ~y & M32 for x, y in zip(A, B)])),
    1156: ("vor", _wrap(lambda A, B: [x | y for x, y in zip(A, B)])),
    1220: ("vxor", _wrap(lambda A, B: [x ^ y for x, y in zip(A, B)])),
    1284: ("vnor", _wrap(lambda A, B: [~(x | y) & M32 for x, y in zip(A, B)])),
    12: ("vmrghb", _merge(8, True)),
    76: ("vmrghh", _merge(16, True)),
    140: ("vmrghw", _merge(32, True)),
    268: ("vmrglb", _merge(8, False)),
    332: ("vmrglh", _merge(16, False)),
    396: ("vmrglw", _merge(32, False)),
    524: ("vspltb", _splat(8)),
    588: ("vsplth", _splat(16)),
    652: ("vspltw", _splat(32)),
    780: ("vspltisb", _splat_imm(8)),
    844: ("vspltish", _splat_imm(16)),
    908: ("vspltisw", _splat_imm(32)),
    260: ("vslb", _shift(8, "l")),
    324: ("vslh", _shift(16, "l")),
    388: ("vslw", _shift(32, "l")),
    516: ("vsrb", _shift(8, "r")),
    580: ("vsrh", _shift(16, "r")),
    644: ("vsrw", _shift(32, "r")),
    772: ("vsrab", _shift(8, "a")),
    836: ("vsrah", _shift(16, "a")),
    900: ("vsraw", _shift(32, "a")),
    4: ("vrlb", _shift(8, "rot")),
    68: ("vrlh", _shift(16, "rot")),
    132: ("vrlw", _shift(32, "rot")),
    1036: ("vslo", _wrap(VectorUnit._slo)),
    452: ("vsl", _vsl),
    708: ("vsr", _vsr),
    512: ("vaddubs", _sat_op(8, lambda x, y: x + y, False)),
    576: ("vadduhs", _sat_op(16, lambda x, y: x + y, False)),
    640: ("vadduws", _sat_op(32, lambda x, y: x + y, False)),
    768: ("vaddsbs", _sat_op(8, lambda x, y: x + y, True)),
    832: ("vaddshs", _sat_op(16, lambda x, y: x + y, True)),
    896: ("vaddsws", _sat_op(32, lambda x, y: x + y, True)),
    1536: ("vsububs", _sat_op(8, lambda x, y: x - y, False)),
    1600: ("vsubuhs", _sat_op(16, lambda x, y: x - y, False)),
    1664: ("vsubuws", _sat_op(32, lambda x, y: x - y, False)),
    1792: ("vsubsbs", _sat_op(8, lambda x, y: x - y, True)),
    1856: ("vsubshs", _sat_op(16, lambda x, y: x - y, True)),
    1920: ("vsubsws", _sat_op(32, lambda x, y: x - y, True)),
    1026: ("vavgub", _avg(8, False)),
    1090: ("vavguh", _avg(16, False)),
    1154: ("vavguw", _avg(32, False)),
    1282: ("vavgsb", _avg(8, True)),
    1346: ("vavgsh", _avg(16, True)),
    1410: ("vavgsw", _avg(32, True)),
    1100: ("vsro", _wrap(VectorUnit._sro)),
    2: ("vmaxub", _maxmin(8, False, True)),
    66: ("vmaxuh", _maxmin(16, False, True)),
    130: ("vmaxuw", _maxmin(32, False, True)),
    258: ("vmaxsb", _maxmin(8, True, True)),
    322: ("vmaxsh", _maxmin(16, True, True)),
    386: ("vmaxsw", _maxmin(32, True, True)),
    514: ("vminub", _maxmin(8, False, False)),
    578: ("vminuh", _maxmin(16, False, False)),
    642: ("vminuw", _maxmin(32, False, False)),
    770: ("vminsb", _maxmin(8, True, False)),
    834: ("vminsh", _maxmin(16, True, False)),
    898: ("vminsw", _maxmin(32, True, False)),
    14: ("vpkuhum", _wrap(_pk_uhum)),
    78: ("vpkuwum", _wrap(_pk_uwum)),
    142: ("vpkuhus", _wrap(_pk_uhus)),
    206: ("vpkuwus", _wrap(_pk_uwus)),
    270: ("vpkshus", _wrap(_pk_shus)),
    334: ("vpkswus", _wrap(_pk_swus)),
    398: ("vpkshss", _wrap(_pk_shss)),
    462: ("vpkswss", _wrap(_pk_swss)),
    526: ("vupkhsb", _wrap(lambda A, B: _unpack(8, True)(B))),
    590: ("vupkhsh", _wrap(lambda A, B: _unpack(16, True)(B))),
    654: ("vupklsb", _wrap(lambda A, B: _unpack(8, False)(B))),
    718: ("vupklsh", _wrap(lambda A, B: _unpack(16, False)(B))),
}

_VXR = {
    6: ("vcmpequb", _cmp_int(8, lambda x, y: x == y)),
    70: ("vcmpequh", _cmp_int(16, lambda x, y: x == y)),
    134: ("vcmpequw", _cmp_int(32, lambda x, y: x == y)),
    198: ("vcmpeqfp", _cmpeqfp),
    454: ("vcmpgefp", _cmpgefp),
    710: ("vcmpgtfp", _cmpgtfp),
    966: ("vcmpbfp", _cmpbfp),
    518: ("vcmpgtub", _cmp_int(8, lambda x, y: x > y)),
    582: ("vcmpgtuh", _cmp_int(16, lambda x, y: x > y)),
    646: ("vcmpgtuw", _cmp_int(32, lambda x, y: x > y)),
    774: ("vcmpgtsb", _cmp_int(8, lambda x, y: x > y, True)),
    838: ("vcmpgtsh", _cmp_int(16, lambda x, y: x > y, True)),
    902: ("vcmpgtsw", _cmp_int(32, lambda x, y: x > y, True)),
}

# Primary-31 vector load/store extended opcodes, for the pre-scan.
OP31_VECTOR_XO = frozenset(VectorUnit._OP31)
