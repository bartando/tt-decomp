"""Small real-PPC programs pin call dispatch without relying on game lift details."""
from __future__ import annotations

import random
import struct
from types import SimpleNamespace

from .build import LIFT_BASE
from .dwarf import Signature, TypeInfo
from .machine import IMAGE_BASE, STACK_TOP, TLS_BASE, Machine
from .runner import Checker, Divergence, Options
from .spec import Trial, run


def _branch(pc, target, link=False):
    return 0x48000000 | ((target - pc) & 0x03FFFFFC) | int(link)


def _caller(addr, targets, frame=0x80):
    # mflr r0; stwu r1,-frame(r1); stw r0,frame+4(r1); bl ...;
    # lwz r0,frame+4(r1); addi r1,r1,frame; mtlr r0; blr
    words = [0x7C0802A6, 0x94210000 | (-frame & 0xFFFF), 0x90010000 | (frame + 4)]
    for target in targets:
        words.append(_branch(addr + len(words) * 4, target, True))
    return words + [0x80010000 | (frame + 4), 0x38210000 | frame, 0x7C0803A6, 0x4E800020]


def _fixture(orig_words, lift_words, callees, policies=None):
    image = bytearray(0x1000)
    ranges = {}
    for addr, words in {IMAGE_BASE: orig_words, **callees}.items():
        data = struct.pack(f'>{len(words)}I', *words)
        image[addr - IMAGE_BASE:addr - IMAGE_BASE + len(data)] = data
        ranges[addr] = (addr, addr + len(data))
    data = struct.pack(f'>{len(lift_words)}I', *lift_words)
    void = TypeInfo('void', 0)
    lift = SimpleNamespace(lo=LIFT_BASE, hi=LIFT_BASE + len(data), call_map={}, signatures={},
                           target_sig=Signature('caller', [], void),
                           sections=[SimpleNamespace(addr=LIFT_BASE, data=data)],
                           symbolize=lambda addr: f'caller+0x{addr - LIFT_BASE:X}')
    syms = SimpleNamespace(func_range=ranges.get, name_at=lambda a: '', describe=lambda a: hex(a))
    c = Checker.__new__(Checker)
    c.lift, c.syms, c.image = lift, syms, bytes(image)
    c.spec = SimpleNamespace(FUNCTION='caller')
    c.opts, c.ftol, c.ignore = Options(), 0, []
    c.policies = policies or {addr: run() for addr in callees}
    c.fake_policies, c._canon, c._leaf, c.host = {}, {}, {}, {}
    c.helpers = []
    c.orig_range = ranges[IMAGE_BASE]
    c.machine = Machine(c.image, lift, syms, [])
    c.machine.prescan(*c.orig_range)
    c.machine.prescan(lift.lo, lift.hi)
    return c


def _sides(c):
    t = Trial(random.Random(1), c.syms)
    regs = {'gpr': [0] * 32, 'fpr': [0.] * 32, 'ctr': 0, 'cr': 0}
    regs['gpr'][1], regs['gpr'][13] = STACK_TOP, TLS_BASE
    results = []
    for side, entry, home in (('orig', IMAGE_BASE, [c.orig_range]),
                              ('lift', c.lift.lo, [(c.lift.lo, c.lift.hi)])):
        c.machine.uc.mem_write(STACK_TOP - 0x1000, bytes(0x2000))
        res = c.machine.run(side, entry, home, c._dispatcher(side, t, {}, 1, 0), regs,
                            [[0] * 4 for _ in range(128)], max_insns=10000, timeout_us=1000000)
        assert res.fault is None, f'{side}: {res.fault}'
        assert not c.machine.run_frames, f'{side}: leaked run() frames'
        res.final = {}
        results.append(res)
    return t, regs, results


def regressions():
    a, b = IMAGE_BASE + 0x100, IMAGE_BASE + 0x200
    # The stack store intentionally overlaps a SysV caller's saved LR unless
    # run() supplies the Xenon caller argument area.
    leaf = [0x38600007, 0x90610014, 0x4E800020]  # li r3,7; stw r3,20(r1); blr
    errors = []
    for count in (1, 2, 3):
        label = f'run() repeat calls: original 2, lift {count}'
        try:
            c = _fixture(_caller(IMAGE_BASE, [a] * 2), _caller(LIFT_BASE, [a] * count, 16), {a: leaf})
            t, regs, (o, l) = _sides(c)
            assert len(o.calls) == 2 and len(l.calls) == count, 'repeat call missing from trace'
            try:
                c.compare(t, regs, o, l)
            except Divergence as e:
                assert count != 2 and 'only the' in e.title, str(e)
            else:
                assert count == 2, 'missing/extra repeat call passed comparison'
        except Exception as e:
            errors.append(f'{label}: {e}')
    for tail in (False, True):
        label = 'run() nested calls' if not tail else 'run() tail calls'
        try:
            parent = (_caller(a, [b, b]) if not tail else
                      [0x60000000, _branch(a + 4, b)])  # nop; b child
            # A compiled lift's bare `b` must keep the caller's return address.
            lift_words = _caller(LIFT_BASE, [a, a], 16) if not tail else [_branch(LIFT_BASE, a)]
            targets = [a, a] if not tail else [a]
            c = _fixture(_caller(IMAGE_BASE, targets), lift_words, {a: parent, b: leaf})
            t, regs, (o, l) = _sides(c)
            want = [a, b, b, a, b, b] if not tail else [a, b]
            assert [x.target for x in o.calls] == want, 'wrong original trace'
            assert [x.target for x in l.calls] == want, 'wrong lift trace'
            c.compare(t, regs, o, l)
        except Exception as e:
            errors.append(f'{label}: {e}')
    return errors
