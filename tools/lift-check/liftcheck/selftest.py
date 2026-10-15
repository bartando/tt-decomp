"""lift-check selftest: the checker must pass good lifts and catch broken ones.

1. Xenia's instruction tests through the Python half of the emulator (isatest).
2. The example specs, with their expected outcome.
3. Mutated copies of those lifts (a flipped comparison, a moved struct field, a
   dropped call, ...): every one has to fail. Mutations are applied to a copy of
   the source in the build dir; src/ is never touched.
"""
from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path

from .build import BuildError
from .cli import find_spec
from .runner import Checker, Options

# The pongPlayer_TossServeBall lift computes the impulse's w lane; the original's
# 1/t comes from a (1,1,1,0) constant, so its w lane is 0. Patch it for mutations.
TOSS_W_FIX = ("velocity._pad = (hitPoint._pad - ball->position._pad) * invTime;",
              "velocity._pad = 0.0f;")

EXPECT = [
    ("strip_vertex_cache_access", "PASS", ()),
    ("stl_string_append", "PASS", ()),
    ("pong_player_toss_serve_ball", "PASS|FAIL:_pad", ()),
    ("pong_player_toss_serve_ball", "PASS", (TOSS_W_FIX,)),
    ("ccal_dispatch_color_constants", "UNSUPPORTED", ()),
    ("lc_drill_on_rally_end", "PASS", ()),
]

MUTATIONS = [
    ("strip_vertex_cache_access", "flip the pass comparison",
     [("if (m_pass[i] != pass) {", "if (m_pass[i] == pass) {")]),
    ("strip_vertex_cache_access", "wrap m_next at 17 instead of 18",
     [("m_next = (m_next + 1) % kSlots;", "m_next = (m_next + 1) % 17;")]),
    ("strip_vertex_cache_access", "result 2 when the slot was set by a hit",
     [("&& m_setByHit[slot] == 0)", "&& m_setByHit[slot] != 0)")]),
    ("stl_string_append", "swap m_finish and m_endOfStorage (struct offsets)",
     [("    char* m_finish;\n    char* m_endOfStorage;", "    char* m_endOfStorage;\n    char* m_finish;")]),
    ("stl_string_append", "grow by one byte too many",
     [("const uint32_t newCapacity = oldSize + std::max(oldSize, n) + 1;",
       "const uint32_t newCapacity = oldSize + std::max(oldSize, n) + 2;")]),
    ("stl_string_append", "free the inline buffer too",
     [("if (!UsingStaticBuf() && m_dynamicBuf != nullptr) {", "if (m_dynamicBuf != nullptr) {")]),
    ("pong_player_toss_serve_ball", "add gravity instead of subtracting",
     [TOSS_W_FIX, ("velocity.y = velocity.y - halfGravity * flightTime;",
                   "velocity.y = velocity.y + halfGravity * flightTime;")]),
    ("pong_player_toss_serve_ball", "drop the vfn_1 call",
     [TOSS_W_FIX, ("    ball->vfn_1();\n    phSimulator_CBB8_g", "    phSimulator_CBB8_g")]),
    ("pong_player_toss_serve_ball", "pongBallBody padding 4 bytes short (mass at +0x60)",
     [TOSS_W_FIX, ("    uint8_t     _pad14[0x50];", "    uint8_t     _pad14[0x4C];")]),
    # what lift-check itself computed before it tracked native ops' upper halves
    ("lc_drill_on_rally_end", "carry = the sum's sign (a 32-bit add's upper half)",
     [("uint32_t nNewCarry = (uint32_t)(nNext >> 32);",
       "uint32_t nNewCarry = (uint32_t)((int32_t)nNewSeed >> 31);")]),
]


# The marker scan, on a made-up TU: (demangled name, expected address or None).
MARKER_TU = """
// @ 0x82000010 (some_map_name) -- a comment block above a declaration ending in ';'
extern "C" float lcst_AboveDecl(float value, float lo, float hi);
extern "C" void* lcst_TwoLines(void* object, int delta,
                               int isReference);  // @ 0x82000020
// =====================================================================
// lcst section banner, Vtable @ 0x82000030
// =====================================================================

extern "C" {
    void lcst_InBlock(void* self, int param);  // @ 0x82000040
}
void lcst_Shared(int);                          // @ 0x82000050
void lcst_Caller() {
    lcst_Shared(1);  // @ 0x82000058  (a string the call prints)
}
namespace rage {
void lcst_InNamespace(int x);  // @ 0x82000060
}
struct lcstHolder {
    // @ 0x82000070 -- an in-class declaration under a comment
    int Method();
};
extern void (*lcst_FnPtr)();  // @ 0x82000080
"""
MARKER_EXPECT = [
    ("lcst_AboveDecl", 0x82000010),
    ("lcst_TwoLines", 0x82000020),
    ("lcst_InBlock", 0x82000040),
    ("lcst_Shared(int)", 0x82000050),
    ("rage::lcst_InNamespace(int)", 0x82000060),
    ("lcstHolder::Method()", 0x82000070),
    ("lcst_FnPtr", 0x82000080),
    ("lcst_Caller()::$_0::operator()() const", None),
    ("void", None),
]


def _markers() -> list[str]:
    import tempfile

    from .runner import repo_root
    from .symbols import Symbols
    syms = Symbols(repo_root())
    with tempfile.TemporaryDirectory() as d:
        tu = Path(d) / "markers.cpp"
        tu.write_text(MARKER_TU)
        syms.include(tu)
        bad = []
        for name, want in MARKER_EXPECT:
            got = syms.resolve(name, name)
            if got != want:
                bad.append(f"{name}: {f'0x{got:08X}' if got is not None else None}, "
                           f"want {f'0x{want:08X}' if want is not None else None}")
    return bad


def _run(spec: str, patches, trials=None):
    """-> (status, first output line)"""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = Checker(find_spec(spec), Options(patches=tuple(patches), trials=trials)).run()
    except BuildError as e:
        msg = str(e)
        if "patch text not found" in msg:
            return "SKIP", msg
        return "BUILD", msg.splitlines()[0]
    first = buf.getvalue().strip().splitlines()[0] if buf.getvalue().strip() else ""
    return {0: "PASS", 1: "FAIL", 2: "SPEC", 3: "UNSUPPORTED"}.get(rc, f"rc{rc}"), first


def _matches(status, line, expect):
    for alt in expect.split("|"):
        want, _, needle = alt.partition(":")
        if status == want and (not needle or needle in line):
            return True
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lift-check selftest")
    ap.add_argument("--isa", action="store_true", help="only the instruction tests")
    ap.add_argument("--no-isa", action="store_true", help="skip the instruction tests")
    ap.add_argument("--rexglue", type=Path, help="ReXGlue tests/ppc/asm directory")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv or [])
    bad = 0

    if not args.no_isa:
        from .isatest import DEFAULT_TESTS
        from .isatest import main as isa
        tests = args.rexglue or DEFAULT_TESTS
        if tests.exists():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = isa(tests, args.verbose)
            out = buf.getvalue().strip().splitlines()
            print(f"{'ok  ' if rc == 0 else 'FAIL'} {out[-1] if out else 'isa'}")
            if rc:
                print("\n".join("     " + ln for ln in out[:-1][:30]))
                bad += 1
        else:
            print(f"skip isa: no instruction tests at {tests} (pass --rexglue)")
        if args.isa:
            return 1 if bad else 0

    bad_markers = _markers()
    print(f"{'ok  ' if not bad_markers else 'FAIL'} markers: {len(MARKER_EXPECT) - len(bad_markers)}"
          f"/{len(MARKER_EXPECT)} resolve as expected")
    for line in bad_markers:
        print(f"     {line}")
    bad += 1 if bad_markers else 0

    for spec, expect, patches in EXPECT:
        status, line = _run(spec, patches)
        ok = _matches(status, line, expect)
        label = spec + (" (w lane fixed)" if patches else "")
        print(f"{'ok  ' if ok else 'FAIL'} {label}: {status}" + ("" if ok else f" (expected {expect})"))
        if not ok or args.verbose:
            print(f"     {line}")
        bad += 0 if ok else 1

    for spec, what, patches in MUTATIONS:
        status, line = _run(spec, patches)
        if status == "SKIP":
            print(f"skip mutation {spec}: {what}: the source changed ({line})")
            continue
        ok = status == "FAIL"
        print(f"{'ok  ' if ok else 'MISS'} mutation {spec}: {what} -> "
              + ("caught" if ok else f"{status}, not caught"))
        if ok and args.verbose or not ok:
            print(f"     {line}")
        bad += 0 if ok else 1

    print("selftest: " + ("all good" if not bad else f"{bad} problem(s)"))
    return 1 if bad else 0
