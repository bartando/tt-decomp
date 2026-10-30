"""Small real-PPC programs pin call dispatch without relying on game lift details."""
from __future__ import annotations

import random
import struct
from types import SimpleNamespace

from .build import LIFT_BASE
from .dwarf import Signature, TypeInfo
from .machine import ARENA_BASE, IMAGE_BASE, STACK_TOP, TLS_BASE, Machine
from .runner import Checker, Divergence, Options, repo_root
from .spec import Trial, model, run, stub


def _branch(pc, target, link=False):
    return 0x48000000 | ((target - pc) & 0x03FFFFFC) | int(link)


def _caller(addr, targets, frame=0x80, setup=()):
    # mflr r0; stwu r1,-frame(r1); stw r0,frame+4(r1); bl ...;
    # lwz r0,frame+4(r1); addi r1,r1,frame; mtlr r0; blr
    words = [0x7C0802A6, 0x94210000 | (-frame & 0xFFFF), 0x90010000 | (frame + 4)]
    words.extend(setup)
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
                           target=SimpleNamespace(addr=LIFT_BASE),
                           sections=[SimpleNamespace(addr=LIFT_BASE, data=data, size=len(data))],
                           symbolize=lambda addr: f'caller+0x{addr - LIFT_BASE:X}')
    syms = SimpleNamespace(func_range=ranges.get, name_at=lambda a: '', describe=lambda a: hex(a))
    c = Checker.__new__(Checker)
    c.repo = repo_root()
    c.lift, c.syms, c.image = lift, syms, bytes(image)
    c.spec = SimpleNamespace(FUNCTION='caller')
    c.opts, c.ftol, c.ignore = Options(), 0, []
    c.policies = policies or {addr: run() for addr in callees}
    c.fake_policies, c._canon, c._leaf, c.host = {}, {}, {}, {}
    c.helpers = []
    c.disasm_cache = {}
    c.orig_range = ranges[IMAGE_BASE]
    c.addr, c.lift_home = IMAGE_BASE, [(lift.lo, lift.hi)]
    c.machine = Machine(c.image, lift, syms, [])
    c.machine.prescan(*c.orig_range)
    c.machine.prescan(lift.lo, lift.hi)
    return c


def _sides(c, args=None):
    t = Trial(random.Random(1), c.syms)
    t.alloc(16, 'output', fill='zero')
    t.stack_fill = bytes(0x9000)
    regs = {'gpr': [0] * 32, 'fpr': [0.] * 32, 'ctr': 0, 'cr': 0}
    regs['gpr'][1], regs['gpr'][13] = STACK_TOP, TLS_BASE
    regs['gpr64'] = args or {}
    for n, value in (args or {}).items():
        regs['gpr'][n] = value & 0xFFFFFFFF
    results = []
    for side in ('orig', 'lift'):
        res = c.run_side(side, t, regs, [[0] * 4 for _ in range(128)], 0)
        assert res.fault is None, f'{side}: {res.fault}'
        assert not c.machine.run_frames, f'{side}: leaked run() frames'
        results.append(res)
    return t, regs, results


def msr_regressions():
    """Run native mfmsr around assisted mtmsrd, including an atomic store."""
    errors = []
    # mfmsr r6; mtmsrd r3,1; mfmsr r7; lwarx r8,0,r4;
    # mtmsrd r6,1; stwcx. r5,0,r4; mfcr r9; mfmsr r10; blr
    words = [0x7CC000A6, 0x7C610164, 0x7CE000A6, 0x7D002028,
             0x7CC10164, 0x7CA0212D, 0x7D200026, 0x7D4000A6, 0x4E800020]
    for source in (0, 2, 0x8000, 0x8002, 0xffffffff):
        try:
            c = _fixture(words, words, {})
            _, _, results = _sides(c, {3: source, 4: ARENA_BASE, 5: 0x12345678})
            for result in results:
                before, after, restored = (result.gpr[n] for n in (6, 7, 10))
                assert after == (before & ~0x8002) | (source & 0x8002), "wrong EE/RI mask"
                assert restored == before, "saved MSR did not restore"
                assert result.gpr[9] & 0x20000000, "stwcx lost its reservation"
                assert all(ARENA_BASE + i in result.writes for i in range(4)), "missing atomic write"
                assert bytes(result.final[ARENA_BASE + i] for i in range(4)) == bytes.fromhex('12345678'), "wrong atomic value"
        except Exception as e:
            errors.append(f'mtmsrd source {source:#x}: {e}')
    try:
        c = _fixture([0x7C600164, 0x4E800020], [0x4E800020], {})
        t = Trial(random.Random(1), c.syms)
        t.stack_fill = bytes(0x9000)
        regs = {'gpr': [0] * 32, 'fpr': [0.] * 32, 'ctr': 0, 'cr': 0}
        result = c.run_side('orig', t, regs, [[0] * 4 for _ in range(128)], 0)
        assert result.fault and result.fault.kind == 'unsupported', "L=0 silently accepted"
    except Exception as e:
        errors.append(f'mtmsrd L=0: {e}')
    return errors


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
    try:
        class Inlined(run):
            transparent = True

        c = _fixture(_caller(IMAGE_BASE, [b]), _caller(LIFT_BASE, [a, b], 16),
                     {a: [0x4E800020], b: leaf}, {a: Inlined(), b: run()})
        t, regs, (o, l) = _sides(c)
        c.compare(t, regs, o, l)
    except Exception as e:
        errors.append(f'run() subclass transparent policy: {e}')
    try:
        from .dwarf import Param

        class CacheHead(run):
            args = ('r4',)
            deref = {'r4': 4}

        # Each caller passes a stack struct with equal heads and differing tails;
        # its unused r3 differs too. The subclass explicitly excludes both.
        def setup(value):
            return [0x7C240B78, 0x38600007, 0x90640000, 0x38600000 | value, 0x90640004]

        c = _fixture(_caller(IMAGE_BASE, [a], setup=setup(1)),
                     _caller(LIFT_BASE, [a], 16, setup(2)), {a: [0x4E800020]}, {a: CacheHead()})
        word = TypeInfo('int', 4)
        cache = TypeInfo('struct', 8, fields=[(0, word, 'head'), (4, word, 'tail')])
        ptr = TypeInfo('ptr', 4, const_pointee=True, pointee=cache)
        c.lift.signatures[a] = Signature('cache', [Param('unused', word), Param('cache', ptr)],
                                          TypeInfo('void', 0))
        t, regs, (o, l) = _sides(c)
        c.compare(t, regs, o, l)
    except Exception as e:
        errors.append(f'run() subclass args/deref policy: {e}')
    errors.extend(_mapped_memory_regressions())
    return errors


def _mapped_memory_regressions():
    errors = []
    # lwz r5,0(r4); addi r5,r5,1; stw r5,0(r4); stw r5,0(r3); blr.
    words = [0x80a40000, 0x38a50001, 0x90a40000, 0x90a30000, 0x4e800020]
    for broken in (False, True):
        lift_words = words[:] if not broken else [words[0], 0x60000000, *words[2:]]
        c = _fixture(words, lift_words, {})
        try:
            for initial in (0x12345678, 0x7fffffff):
                t = Trial(random.Random(1), c.syms)
                output = t.alloc(16, "output", fill="zero")
                t.map(0x7fea1000, 0x1000, "device", fill="zero")
                t.w32(0x7fea1818, initial)
                t.stack_fill = bytes(0x9000)
                regs = {"gpr": [0] * 32, "fpr": [0.] * 32, "ctr": 0, "cr": 0}
                regs["gpr"][1], regs["gpr"][3], regs["gpr"][4] = STACK_TOP, output, 0x7fea1818
                results = []
                for side in ("orig", "lift"):
                    result = c.run_side(side, t, regs, [[0] * 4 for _ in range(128)], 0)
                    assert result.fault is None, result.fault
                    expected = initial + (1 if side == "orig" or not broken else 0)
                    actual = bytes(result.final[0x7fea1818 + i] for i in range(4))
                    assert int.from_bytes(actual, "big") == expected
                    assert c.machine.u32(0x7fea1818) == initial, "mapped writes not restored"
                    results.append(result)
                try:
                    c.compare(t, regs, *results)
                except Divergence:
                    assert broken, "equal mapped memory failed comparison"
                else:
                    assert not broken, "different mapped writes passed comparison"
            # Fixed maps must not make arbitrary unmapped reads legal.
            regs["gpr"][4] = 0x7fea2818
            result = c.run_side("orig", t, regs, [[0] * 4 for _ in range(128)], 0)
            assert result.fault and result.fault.kind == "unmapped"
            # Nor may a spec overwrite code/arena/stack via a map.
            t = Trial(random.Random(1), c.syms)
            t.map(IMAGE_BASE, 0x1000, fill="zero")
            try:
                c.run_side("orig", t, regs, [[0] * 4 for _ in range(128)], 0)
            except ValueError:
                pass
            else:
                raise AssertionError("accepted map overlapping image")
        except Exception as e:
            errors.append(f"fixed mapped memory broken={broken}: {e}")
    return errors


def wide_regressions():
    from .abi import argument_moves, to_lift, to_xenon
    from .build import BuildError
    from .dwarf import Param

    a = IMAGE_BASE + 0x100
    u32, u64, ptr = TypeInfo('int', 4), TypeInfo('int', 8), TypeInfo('ptr', 4)
    sig = Signature('wide', [Param('tag', u32), Param('mask', u64),
                             Param('register', u32), Param('output', ptr)], u64)
    # std r4,0(r6); stw r5,8(r6); mr r3,r4; blr
    leaf = [0xF8860000, 0x90A60008, 0x7C832378, 0x4E800020]
    errors = []

    def echo(ctx):
        assert ctx.r(3) == 17 and ctx.r(5) == 0x1234 and ctx.r(6) == ARENA_BASE
        ctx.write(ctx.r(6), ctx.r64(4).to_bytes(8, 'big'))
        ctx.ret(r3=ctx.r64(4))

    for value in (0, 0x8000000000000000, 0x1234567887654321, 0xFFFFFFFFFFFFFFFF):
        for policy in (run(), model(echo), stub(ret=value)):
            for tail in (False, True):
                label = f'uint64 entry/call/return {type(policy).__name__}, tail={tail}, 0x{value:016X}'
                try:
                    lift_words = [_branch(LIFT_BASE, a)] if tail else _caller(LIFT_BASE, [a], 16)
                    c = _fixture(_caller(IMAGE_BASE, [a]), lift_words,
                                 {a: leaf}, {a: policy})
                    c.lift.target_sig = sig
                    c.lift.signatures[a] = sig
                    t, regs, (o, l) = _sides(c, {3: 17, 4: value, 5: 0x1234, 6: ARENA_BASE})
                    c.compare(t, regs, o, l)
                    # Flip only an upper-half bit: the built-in call comparison must catch it.
                    l.calls[0].gpr64[1] ^= 1 << 63
                    try:
                        c.compare(t, regs, o, l)
                    except Divergence as e:
                        assert '64-bit' in e.title, str(e)
                    else:
                        raise AssertionError('upper-half corruption passed')
                except Exception as e:
                    errors.append(f'{label}: {e}')
    try:
        # Two wide args, pair alignment gaps, a following pointer and an FP arg.
        mixed = Signature('mixed', [Param('a', u64), Param('b', u32), Param('c', u64),
                                    Param('p', ptr), Param('f', TypeInfo('float', 8))], u32)
        g = list(range(32))
        wide = {n: n for n in range(32)}
        wide[3], wide[5] = 0x1122334455667788, 0x8877665544332211
        updates = to_lift(mixed, g, wide)
        assert updates == {3: 0x11223344, 4: 0x55667788, 5: 4,
                           7: 0x88776655, 8: 0x44332211, 9: 6}, updates
        for n, v in updates.items():
            g[n] = wide[n] = v
        assert to_xenon(mixed, g, wide) == {3: 0x1122334455667788, 4: 4,
                                           5: 0x8877665544332211, 6: 6}
        overflow = Signature('overflow', [Param(str(n), u64) for n in range(5)], u32)
        try:
            list(argument_moves(overflow))
        except BuildError:
            pass
        else:
            raise AssertionError('stack-spanning uint64 signature accepted')
    except Exception as e:
        errors.append(f'uint64 register layout: {e}')
    return errors
