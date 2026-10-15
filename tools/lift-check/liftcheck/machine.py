"""The emulator: one Unicorn PPC32 with the game image, the compiled lift and the inputs.

Each trial runs the original at its address and the lift at its symbol on the
same register file and memory. Calls that leave the function under test are
caught at the first block of the callee and handled in Python (see policies.py);
the original's stack save/restore helpers just run.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from unicorn import (UC_ARCH_PPC, UC_HOOK_BLOCK, UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_MEM_UNMAPPED,
                     UC_HOOK_MEM_WRITE, UC_MEM_FETCH_UNMAPPED, UC_MEM_WRITE_UNMAPPED,
                     UC_MODE_BIG_ENDIAN, UC_MODE_PPC32, Uc, UcError)
from unicorn import ppc_const as P

from .assist import Assist, Trap, is_wide, needs_assist, needs_predict
from .vmx import Unsupported

M32 = 0xFFFFFFFF

IMAGE_BASE = 0x82000000
ARENA_BASE, ARENA_SIZE = 0x40000000, 0x01000000
HEAP_BASE, HEAP_SIZE = 0x48000000, 0x01000000
TLS_BASE, TLS_SIZE = 0x7D000000, 0x10000
STACK_LO, STACK_HI = 0x70000000, 0x70100000
STACK_TOP = 0x700F0000            # r1 at entry; the space above is the caller's frame
FAKE_BASE, FAKE_SIZE = 0x7E000000, 0x10000
SENTINEL = FAKE_BASE + FAKE_SIZE - 0x10
# Unicorn's XER register ignores QEMU's separate CA bit, so a CA computed in Python
# goes in through `mtxer` in this trampoline (r0 parked in the scratch page).
TRAMP = FAKE_BASE
SCRATCH = 0xFFFF0000
_TRAMP_CODE = [0x90008000,      # stw   r0, -0x8000(0)
               0x80008004,      # lwz   r0, -0x7FFC(0)
               0x7C0103A6,      # mtxer r0
               0x80008000]      # lwz   r0, -0x8000(0)
TRAMP_END = TRAMP + 4 * len(_TRAMP_CODE)

GPR = [getattr(P, f"UC_PPC_REG_{n}") for n in range(32)]
FPR = [getattr(P, f"UC_PPC_REG_FPR{n}") for n in range(32)]
MSR_FP, MSR_VEC = 1 << 13, 1 << 25

_pd, _ud = struct.Struct(">d").pack, struct.Struct(">d").unpack


def d2bits(x: float) -> int:
    return int.from_bytes(_pd(x), "big")


def bits2d(b: int) -> float:
    return _ud(b.to_bytes(8, "big"))[0]


class Stop(Exception):
    pass


@dataclass
class Fault:
    kind: str            # 'unmapped' | 'unsupported' | 'trap' | 'exception' | 'timeout'
    pc: int
    detail: str


@dataclass
class CallRecord:
    target: int
    gpr: list            # r3..r10, low 32 bits
    gpr64: list          # r3..r10 with the upper-half shadow
    fpr: list            # f1..f8 as doubles
    lr: int
    ret: dict = field(default_factory=dict)
    derefs: dict = field(default_factory=dict)   # reg -> bytes read at call time
    strings: dict = field(default_factory=dict)  # r3.. index -> const char* text at call time
    transparent: bool = False
    note: str = ""


@dataclass
class SideResult:
    side: str
    fault: Fault | None
    writes: dict          # addr -> (byte, pc) for every non-stack byte written
    calls: list
    gpr: list
    gpr64: list
    fpr: list
    instructions: int = 0


class Machine:
    def __init__(self, image: bytes, lift, symbols, helper_ranges):
        self.image = image
        self.lift = lift
        self.syms = symbols
        uc = Uc(UC_ARCH_PPC, UC_MODE_PPC32 | UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(P.UC_CPU_PPC32_7400_V2_9)
        self.uc = uc
        size = (len(image) + 0xFFFF) & ~0xFFFF
        uc.mem_map(IMAGE_BASE, size)
        uc.mem_write(IMAGE_BASE, image)
        self.image_end = IMAGE_BASE + len(image)
        llo = lift.lo & ~0xFFFF
        if lift.hi > lift.lo:
            uc.mem_map(llo, ((lift.hi - llo) + 0xFFFF) & ~0xFFFF)
        for s in lift.sections:
            uc.mem_write(s.addr, s.data)
        uc.mem_map(ARENA_BASE, ARENA_SIZE)
        uc.mem_map(HEAP_BASE, HEAP_SIZE)
        uc.mem_map(TLS_BASE, TLS_SIZE)
        uc.mem_map(STACK_LO, STACK_HI - STACK_LO)
        uc.mem_map(FAKE_BASE, FAKE_SIZE)
        uc.mem_write(FAKE_BASE, struct.pack(">I", 0x7FE00008) * (FAKE_SIZE // 4))   # trap
        uc.mem_write(TRAMP, b"".join(struct.pack(">I", w) for w in _TRAMP_CODE))
        uc.mem_map(SCRATCH, 0x10000)
        uc.hook_add(UC_HOOK_CODE, self._on_tramp_end, begin=TRAMP_END, end=TRAMP_END)
        self.pending_xer = None
        self.tramp_ret = 0
        self.helpers = helper_ranges
        self.assist = Assist(self)
        self.hi_shadow: list = [None] * 32      # per GPR: {low word: upper word} or None
        self._hooked: set[int] = set()

        uc.hook_add(UC_HOOK_BLOCK, self._on_block)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._on_write)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._on_unmapped)
        uc.hook_add(UC_HOOK_INTR, self._on_intr)

        # filled per run
        self.side = ""
        self.home: list[tuple[int, int]] = []
        self.dispatch = None
        self.writes: dict = {}
        self.calls: list = []
        self.fault: Fault | None = None
        self.heap_next = HEAP_BASE

    # ── pre-scan: hook the instructions Python has to run ──────────────────
    def prescan(self, lo: int, hi: int, wide: bool | None = None):
        """Hooks what Python has to run. `wide`: also track the upper halves of native
        32-bit results (default: when the range has a 64-bit integer instruction)."""
        data = self.uc.mem_read(lo, hi - lo)
        words = [int.from_bytes(data[off:off + 4], "big") for off in range(0, hi - lo, 4)]
        if wide is None:
            wide = any(is_wide(w) for w in words)
        added = False
        for k, w in enumerate(words):
            a = lo + 4 * k
            if a in self._hooked:
                continue
            if needs_assist(w) or wide and needs_predict(w):
                self._hooked.add(a)
                self.uc.hook_add(UC_HOOK_CODE, self._on_assist, begin=a, end=a)
                added = True
        if added:
            self.uc.ctl_flush_tb()       # blocks translated before the hook existed

    # ── register/memory interface used by assist, vmx and policies ────────
    def gpr(self, n):
        return self.uc.reg_read(GPR[n]) & M32

    def set_gpr(self, n, v):
        self.uc.reg_write(GPR[n], v & M32)
        self.hi_shadow[n] = None

    def gpr64(self, n):
        lo = self.uc.reg_read(GPR[n]) & M32
        sh = self.hi_shadow[n]
        if sh is not None and lo in sh:
            return (sh[lo] << 32) | lo
        return (lo | 0xFFFFFFFF00000000) if lo & 0x80000000 else lo

    def has_upper(self, n):
        """Whether r<n>'s upper half is known rather than assumed sign-extended."""
        sh = self.hi_shadow[n]
        return sh is not None and (self.uc.reg_read(GPR[n]) & M32) in sh

    def set_gpr64(self, n, v):
        v &= (1 << 64) - 1
        lo = v & M32
        self.uc.reg_write(GPR[n], lo)
        self.hi_shadow[n] = {lo: v >> 32}

    def spr_lr_ctr(self, spr):
        return self.uc.reg_read(P.UC_PPC_REG_LR if spr == 8 else P.UC_PPC_REG_CTR) & M32

    def fpr_raw(self, n):
        return self.uc.reg_read(FPR[n])

    def set_fpr_raw(self, n, v):
        self.uc.reg_write(FPR[n], v)

    def fpr(self, n):
        return bits2d(self.fpr_raw(n))

    def set_fpr(self, n, x):
        self.set_fpr_raw(n, d2bits(x))

    def cr(self):
        return self.uc.reg_read(P.UC_PPC_REG_CR) & M32

    def set_cr(self, v):
        self.uc.reg_write(P.UC_PPC_REG_CR, v & M32)

    def set_cr_field(self, n, v4):
        sh = 28 - 4 * n
        self.set_cr((self.cr() & ~(0xF << sh)) | ((v4 & 0xF) << sh))

    def xer(self):
        return self.uc.reg_read(P.UC_PPC_REG_XER) & M32

    def set_xer_ca(self, ca):
        x = self.xer()
        self.pending_xer = (x | 0x20000000) if ca else (x & ~0x20000000)

    def _on_tramp_end(self, uc, addr, size, _):
        uc.reg_write(P.UC_PPC_REG_PC, self.tramp_ret)

    def fpscr(self):
        return self.uc.reg_read(P.UC_PPC_REG_FPSCR) & M32

    def pc(self):
        return self.uc.reg_read(P.UC_PPC_REG_PC) & M32

    def read(self, addr, n) -> bytes:
        try:
            return bytes(self.uc.mem_read(addr & M32, n))
        except UcError:
            self.fault = Fault("unmapped", self.pc(), f"read of {n} bytes at 0x{addr:08X}")
            raise Stop()

    def write(self, addr, data: bytes, pc=None):
        addr &= M32
        try:
            self.uc.mem_write(addr, bytes(data))
        except UcError:
            self.fault = Fault("unmapped", self.pc(), f"write of {len(data)} bytes at 0x{addr:08X}")
            raise Stop()
        if not (STACK_LO <= addr < STACK_HI):
            pc = self.pc() if pc is None else pc
            for k in range(len(data)):
                self.writes[addr + k] = pc

    def u32(self, addr):
        return int.from_bytes(self.read(addr, 4), "big")

    def alloc(self, n, align=16) -> int:
        a = (self.heap_next + align - 1) & ~(align - 1)
        if a + n > HEAP_BASE + HEAP_SIZE:
            raise RuntimeError("lift-check heap exhausted")
        self.heap_next = a + n
        return a

    # ── hooks ──────────────────────────────────────────────────────────────
    def _on_write(self, uc, access, addr, size, value, _):
        if STACK_LO <= addr < STACK_HI:
            return
        pc = uc.reg_read(P.UC_PPC_REG_PC) & M32
        for k in range(size):
            self.writes[addr + k] = pc

    def _on_unmapped(self, uc, access, addr, size, value, _):
        kind = {UC_MEM_WRITE_UNMAPPED: "write", UC_MEM_FETCH_UNMAPPED: "fetch"}.get(access, "read")
        self.fault = Fault("unmapped", self.pc(), f"{kind} of {size} bytes at 0x{addr:08X}")
        return False

    def _on_intr(self, uc, intno, _):
        pc = self.pc()
        if self.fault is None:
            word = None
            for a in (pc - 4, pc):
                try:
                    word = int.from_bytes(uc.mem_read(a, 4), "big")
                    if word == 0x7FE00008 or (word >> 26) == 31 and ((word >> 1) & 0x3FF) == 4:
                        self.fault = Fault("trap", a, "trap instruction")
                        break
                except UcError:
                    pass
            if self.fault is None:
                w = int.from_bytes(uc.mem_read(pc - 4, 4), "big") if pc >= 4 else 0
                self.fault = Fault("exception", pc - 4,
                                   f"CPU exception {intno} near 0x{pc - 4:08X} (word 0x{w:08X}); "
                                   f"unsupported instruction?")
        uc.emu_stop()

    def _on_assist(self, uc, addr, size, _):
        w = int.from_bytes(uc.mem_read(addr, 4), "big")
        if not needs_assist(w):
            if needs_predict(w):
                for n, values in self.assist.predict(w):
                    self.hi_shadow[n] = None if values is None else \
                        {v & M32: (v >> 32) & M32 for v in values}
            return              # runs natively
        try:
            self.assist.execute(w, addr)
        except Unsupported as e:
            self.fault = Fault("unsupported", addr, f"{e} (word 0x{w:08X})")
            uc.emu_stop()
            return
        except Trap:
            self.fault = Fault("trap", addr, "td/tdi trap")
            uc.emu_stop()
            return
        except Stop:
            uc.emu_stop()
            return
        if self.pending_xer is not None:
            uc.mem_write(SCRATCH + 0x8004, struct.pack(">I", self.pending_xer & M32))
            self.pending_xer = None
            self.tramp_ret = addr + 4
            uc.reg_write(P.UC_PPC_REG_PC, TRAMP)
            return
        uc.reg_write(P.UC_PPC_REG_PC, addr + 4)

    def _in_home(self, addr):
        for lo, hi in self.home:
            if lo <= addr < hi:
                return True
        return False

    def _on_block(self, uc, addr, size, _):
        if self._in_home(addr) or TRAMP <= addr <= TRAMP_END:
            return
        if addr == SENTINEL:
            uc.emu_stop()
            return
        for lo, hi in self.helpers:
            if lo <= addr < hi:
                return
        try:
            self.dispatch(self, addr)
        except Stop:
            uc.emu_stop()

    # ── running one side ────────────────────────────────────────────────────
    def run(self, side, entry, home, dispatch, regs: dict, vregs, max_insns=20_000_000,
            timeout_us=20_000_000) -> SideResult:
        uc = self.uc
        self.side = side
        self.home = list(home)
        self.dispatch = dispatch
        self.writes = {}
        self.calls = []
        self.fault = None
        self.hi_shadow = [None] * 32
        self.assist.vmx.v = [list(v) for v in vregs]
        self.assist.vmx.vscr = 0x00010000
        for n in range(32):
            uc.reg_write(GPR[n], regs["gpr"][n] & M32)
            uc.reg_write(FPR[n], d2bits(regs["fpr"][n]))
        for n, v in regs.get("gpr64", {}).items():
            self.set_gpr64(n, v)
        uc.reg_write(P.UC_PPC_REG_LR, SENTINEL)
        uc.reg_write(P.UC_PPC_REG_CTR, regs["ctr"])
        uc.reg_write(P.UC_PPC_REG_CR, regs["cr"])
        uc.reg_write(P.UC_PPC_REG_XER, 0)
        uc.reg_write(P.UC_PPC_REG_FPSCR, 0)
        uc.reg_write(P.UC_PPC_REG_MSR, uc.reg_read(P.UC_PPC_REG_MSR) | MSR_FP | MSR_VEC)
        try:
            uc.emu_start(entry, SENTINEL, timeout=timeout_us, count=max_insns)
        except UcError as e:
            if self.fault is None:
                self.fault = Fault("exception", self.pc(), str(e))
        except Stop:
            pass
        if self.fault is None and self.pc() != SENTINEL:
            self.fault = Fault("timeout", self.pc(), "didn't return (instruction or time limit)")
        return SideResult(side, self.fault, self.writes, self.calls,
                          [self.gpr(n) for n in range(32)],
                          [self.gpr64(n) for n in range(32)],
                          [self.fpr(n) for n in range(32)])

    def restore(self, addrs, initial):
        """Puts back the initial bytes at every address a side wrote."""
        runs = sorted(addrs)
        k = 0
        while k < len(runs):
            start = runs[k]
            end = start + 1
            k += 1
            while k < len(runs) and runs[k] == end:
                end += 1
                k += 1
            self.uc.mem_write(start, initial(start, end - start))

    def snapshot(self, addrs) -> dict:
        out = {}
        for a in addrs:
            out[a] = self.uc.mem_read(a, 1)[0]
        return out
