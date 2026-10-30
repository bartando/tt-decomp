"""Simple heap Allocate: best fit, unlink, split, physical backlinks and accounting.

Heads occupy +0x0C..+0x48, +0x54 is used bytes, +0x58..+0x94 are tag
totals, and +0x98 is free bytes (the scaffold names are misleading). Allocate
does not coalesce: it preserves/repairs +8 physical backlinks used by Free.
Inputs include heaps with previously coalesced blocks, adjacent free blocks,
allocated neighbors and end-of-heap splits. All heap and allocator writes,
return pointers and diagnostic arguments compare exactly. The debug-fill
callee runs the original code, including its address-byte fill mode.

Limits: finite acyclic lists, 16-byte heap alignment, readable live nodes;
no rounded sizes with bit 31 set (which produce invalid negative bucket indices).
Alignment is fixed at 16; r5 is ignored by the original. No host concurrency.
The exhaustion-only virtual slot 6 returns a fixed sentinel; its implementation
is outside this spec. Request round-up wrap to zero is covered separately.
Retail exhaustion logs then dereferences null; break-index equality traps
(Unicorn labels the original twui an exception; its exact PC/opcode is checked).
The normal runner rejects original faults, so run this spec directly to check
those expected faults and their preceding memory/call effects as well:

  PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
      tools/lift-check/specs/sysmem_simple_allocate.py --seed 1

Add --mutations to prove the spec rejects deliberately broken lifts. Patches
are applied only to build copies; the checked-in source is never mutated.
"""
from liftcheck.spec import *

FUNCTION = "rage::sysMemSimpleAllocator::Allocate"
ADDRESS = 0x82186E40
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
TRIALS = 2000
EXTERNS = {"rage_debugLog": 0x8240E6D0}


def diagnostic(ctx):
    # Only actual format arguments are defined. Capture them as compared bytes
    # instead of comparing arbitrary volatile registers on argumentless calls.
    text = bytearray()
    while True:
        ch = ctx.read(ctx.r(3) + len(text), 1)
        if ch == b"\0":
            break
        text.extend(ch)
    for i in range(text.count(b"%u") + text.count(b"%p")):
        reg = f"r{4 + i}"
        ctx.rec.derefs[reg] = (ctx.r(4 + i).to_bytes(4, "big"), None)


CALLS = {
    0x8240E6D0: model(diagnostic, args=("r3",)),
    0x821862A0: run(),
    "heap.vfn_6": stub(ret=0x12340, args=("r3",)),
}


def setup(t, sizes, request, *, order=None, count=None, broken_guard=False, at_end=False):
    rng = t.rng
    obj = t.alloc(0xC0, "allocator")
    t.w32(obj, t.vtable("heap", slots=21))
    # Include allocated neighbors so split must update a genuine physical node.
    sizes = list(sizes)
    physical = [(32, False)] + [(s, True) for s in sizes]
    if not at_end:
        physical.append((48, False))
    heap_size = sum(s + 16 for s, _ in physical)
    heap = t.alloc(heap_size, "heap")
    t.w32(obj + 4, heap)
    t.w32(obj + 0x4C, heap_size)
    for k in range(16):
        t.w32(obj + 0x0C + 4 * k, 0)
        t.w32(obj + 0x58 + 4 * k, t.u32())
    # Counters intentionally wrap too; comparisons must be unsigned arithmetic.
    t.w32(obj + 0x54, rng.choice([0, 16, 0xFFFFFFF0, t.u32()]))
    t.w32(obj + 0x98, sum(sizes))
    count = rng.choice([0, 1, 0x03FFFFFE, 0x03FFFFFF, 0xFFFFFFFF, t.u32()]) if count is None else count
    t.w32(obj + 0x9C, count)
    t.w32(obj + 0xA0, (count + 2) & 0xFFFFFFFF)
    t.w8(obj + 0xB9, rng.choice([0, 0, 1, 255]))
    t.w32(0x825EBCE4, t.u32())
    t.w8(0x8260642D, rng.choice([0, 1, 255]))

    nodes = []
    cursor, prev = heap, 0
    for size, free in physical:
        t.w32(cursor, cursor ^ (1 if broken_guard and free else 0))
        t.w32(cursor + 4, size)
        t.w32(cursor + 8, prev)
        t.w32(cursor + 12, (t.u32() & ~0x10) | (0 if free else 0x10))
        if free:
            nodes.append(cursor)
        prev = cursor
        cursor += size + 16
    order = list(range(len(sizes))) if order is None else order
    lists = [[] for _ in range(16)]
    for i in order:
        lists[min(sizes[i] // 16, 15)].append(nodes[i])
    for k, chain in enumerate(lists):
        if chain:
            t.w32(obj + 0x0C + k * 4, chain[0])
        for i, node in enumerate(chain):
            t.w32(node + 16, chain[i - 1] if i else 0)
            t.w32(node + 20, chain[i + 1] if i + 1 < len(chain) else 0)
    t.args(r3=obj, r4=request, r5=rng.choice([0, 1, 16, 64, 4096, t.u32()]))
    return obj


def inputs(t):
    rng = t.rng
    request = rng.choice([0, 1, 15, 16, 17, 31, 32, 33, 223, 224, 225, 239,
                          240, 241, 255, 256, 257, 511, 512, 0xFFFFFFF1, 0xFFFFFFFF,
                          rng.randrange(1, 1025)])
    if request >= 0xFFFFFFF1:
        # The original's unsigned round-up wraps to zero (bucket zero).
        setup(t, [16, 32, 256], request, at_end=rng.choice([False, True]))
        return
    aligned = ((request or 1) + 15) & ~15
    case = rng.randrange(8)
    if case == 0:
        sizes = [aligned]                           # exact single-node hit
    elif case == 1:
        sizes = [aligned + 16]                      # no room for free payload
    elif case == 2:
        sizes = [aligned + 32]                      # minimum split remainder
    elif case == 3:
        sizes = [aligned + rng.randrange(3, 80) * 16]  # already coalesced large block
    elif case == 4:
        sizes = [max(16, aligned - 16), aligned + 64, aligned + 32, aligned + 96]
    elif case == 5:
        sizes = [aligned + 64, aligned, aligned + 32, aligned]  # exact beats best fit; ties
    elif case == 6:
        sizes = [16, 32, 48, 128, 224, 240, 256, 1536]  # skip undersized/empty buckets
    else:
        sizes = [aligned + 64, aligned + 32, aligned + 32]  # first equal best wins
    order = list(range(len(sizes)))
    rng.shuffle(order)
    setup(t, sizes, request, order=order, broken_guard=rng.randrange(5) == 0,
          at_end=rng.choice([False, True]))


def failure_checks(checker):
    """Compare expected faults separately; never turn arbitrary faults into PASS."""
    saved = checker.spec.inputs
    for n, case in enumerate(("empty", "fragmented", "break")):
        def failure_input(t):
            obj = setup(t, [] if case == "empty" else [32, 48, 64], 96,
                        count=10 if case == "break" else 0)
            t.w8(obj + 0xB9, 0)
            if case == "break":
                t.w32(obj + 0xA0, 11)
        checker.spec.inputs = failure_input
        t, regs, vregs = checker.make_trial(n)
        orig = checker.run_side("orig", t, regs, vregs, n)
        lift = checker.run_side("lift", t, regs, vregs, n)
        expected = "trap" if case == "break" else "unmapped"
        if case == "break":
            assert orig.fault and orig.fault.kind == "exception" and orig.fault.pc == 0x82186E84
            assert "word 0x0FE00016" in orig.fault.detail, orig.fault
            assert lift.fault and lift.fault.kind == "trap", lift.fault
            assert not orig.calls and not lift.calls
        else:
            for side in (orig, lift):
                assert side.fault and side.fault.kind == expected, (case, side.side, side.fault)
                assert "read of 4 bytes at 0x0000000C" in side.fault.detail, side.fault
            assert orig.calls[-1].target == 0x8240E6D0
            assert t.fakes[orig.calls[-2].target] == "heap.vfn_6"
        oc, lc = orig.calls, lift.calls
        assert len(oc) == len(lc), (case, len(oc), len(lc))
        for k, (a, b) in enumerate(zip(oc, lc)):
            assert a.target == b.target, case
            checker.compare_args(k, a, b, oc, lc, t)
        assert orig.final == lift.final, (case, "writes before fault differ")
        print(f"PASS {checker.name}: expected {case} {expected}, writes and calls match")
    checker.spec.inputs = saved


MUTATIONS = [
    ("align to 32 bytes", [("+ 15) & ~15u;", "+ 31) & ~31u;")]),
    ("take the first larger block", [("node->size < bestSize", "chosen == nullptr")]),
    ("split an exact header-sized tail", [("chosen->size > alignedSize + 16", "chosen->size >= alignedSize + 16")]),
    ("leave the old bucket head linked", [("heads[bucket] = next;", "/* omitted unlink */")]),
    ("leave a stale successor backlink", [("nodeAt(following)->physicalPrev = remainderAddress;",
                                            "/* omitted physical backlink */")]),
    ("omit split header accounting", [("largestAvailBlock -= 16;", "/* omitted header accounting */")]),
    ("charge the wrong allocation tag", [("g_sysMemAllocationTag & 15u", "g_sysMemAllocationTag & 7u")]),
    ("return null on exhaustion", [("// Retail next reads null->flags", "return nullptr;\n        // Retail next reads null->flags")]),
]


def mutation_checks(seed):
    from pathlib import Path
    from liftcheck.runner import Checker, Options, Divergence

    for name, patches in MUTATIONS:
        checker = Checker(Path(__file__), Options(seed=seed, patches=tuple(patches)))
        if name == "return null on exhaustion":
            try:
                failure_checks(checker)
            except (AssertionError, Divergence):
                print(f"CAUGHT {name}")
                continue
            raise AssertionError(f"mutation survived: {name}")
        rc = checker.run()
        assert rc == 1, ("mutation must FAIL (not BUILD/SPEC/UNSUPPORTED)", name, rc)
        print(f"CAUGHT {name}")
    print(f"PASS sysmem_simple_allocate: {len(MUTATIONS)} mutations caught (seed {seed})")


def main():
    import argparse
    from pathlib import Path
    from liftcheck.runner import Checker, Options

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mutations", action="store_true")
    args = ap.parse_args()
    checker = Checker(Path(__file__), Options(seed=args.seed))
    rc = checker.run()
    if rc:
        return rc
    failure_checks(checker)
    if args.mutations:
        mutation_checks(args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
