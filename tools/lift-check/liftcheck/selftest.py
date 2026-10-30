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
    ("pg_6c00_w", "PASS", ()),
    ("strip_vertex_cache_access", "PASS", ()),
    ("stl_string_append", "PASS", ()),
    ("pong_player_toss_serve_ball", "PASS|FAIL:_pad", ()),
    ("pong_player_toss_serve_ball", "PASS", (TOSS_W_FIX,)),
    ("ccal_dispatch_color_constants", "UNSUPPORTED", ()),
    ("lc_drill_on_rally_end", "PASS", ()),
    ("lc_camviewcs_update_leaf", "PASS", ()),     # a stub keeps what its leaf callee keeps
    ("lc_xact_image_dtor_thunk", "PASS", ()),     # a call through `b X` is a call to X
    ("lc_drill_strings", "PASS", ()),             # const char* by content, any length
    ("lc_world_bound_static_init", "PASS", ()),   # the static initializers have run
    ("sysmem_simple_allocator_free", "PASS", ()),
    ("crt_asin", "PASS", ()),                    # original core on a Xenon caller frame
    ("crt_acos", "PASS", ()),
    ("rage_clip_polygon_to_frustum", "PASS", ()), # repeated run() calls stay in the trace
    ("misc_tristrip_join_strips", "PASS", ()),   # subclass's partial-cache deref survives
    ("player_cancel_swing", "PASS", ()),        # subclass's transparent flag survives
    ("grc_device_flush_dirty_register_group", "PASS", ()),
    ("grc_device_flush_dirty_six_register_groups", "PASS", ()),
    ("grc_device_flush_dirty_sixteen_register_groups", "PASS", ()),
    ("grc_device_flush_dirty_state", "PASS", ()),
]

MUTATIONS = [
    ("ph_segment_triangle_intersect", "reject a start on the plane",
     [("if (*startDistance < g_phZeroFloat) return 2;", "if (*startDistance <= g_phZeroFloat) return 2;")]),
    ("ph_segment_triangle_intersect", "omit end-distance output",
     [("*endDistance = dot3(endFromA, normal);", "/* omitted end distance */")]),
    ("ph_segment_triangle_intersect", "invert fraction denominator",
     [("*startDistance / (*startDistance - *endDistance)", "*startDistance / (*endDistance - *startDistance)")]),
    ("ph_segment_triangle_intersect", "accept small or back-facing triangles",
     [("if (area < g_segmentTriangleMinArea) return 1;", "if (false) return 1;")]),
    ("ph_segment_triangle_intersect", "skip first barycentric rejection",
     [("if (u < g_phZeroFloat || u > area) return 4;", "if (false) return 4;")]),
    ("ph_segment_triangle_intersect", "skip second barycentric rejection",
     [("if (v < g_phZeroFloat || v + u > area) return 5;", "if (false) return 5;")]),
    ("grc_device_flush_dirty_state", "lose upper bits of an outgoing uint64 argument",
     [("device, dirty(0x10), 0x4000,", "device, (uint32_t)dirty(0x10), 0x4000,")]),
    ("grc_device_flush_dirty_state", "change the integer following a uint64 argument",
     [("device, dirty(0x10), 0x4000,", "device, dirty(0x10), 0x4001,")]),
    ("rage_clip_polygon_to_frustum", "keep clipping after an empty result (extra run() calls)",
     [("        if (count == 0) {\n            return;\n        }", "/* omitted empty-result return */")]),
    ("sysmem_simple_allocator_free", "skip forward coalescing",
     [("if ((next->flags & 0x10) == 0) {", "if (false) {")]),
    ("sysmem_simple_allocator_free", "skip backward coalescing",
     [("if ((prev->flags & 0x10) == 0) {", "if (false) {")]),
    ("sysmem_simple_allocator_free", "unlink from the tag counters instead of the free-list heads",
     [("heap[index + 3] = node->freeNext;", "heap[index + 22] = node->freeNext;")]),
    ("sysmem_simple_allocator_free", "lose the successor's free-list backlink",
     [("nodeAt(node->freeNext)->freePrev = node->freePrev;", "/* lost free-list backlink */")]),
    ("sysmem_simple_allocator_free", "lose the physical backlink after a forward merge",
     [("nodeAt(afterNext)->physicalPrev = address;", "/* lost physical backlink */")]),
    ("sysmem_simple_allocator_free", "lose the previous head's backlink on insertion",
     [("nodeAt(heap[index + 3])->freePrev = address;", "/* lost insertion backlink */")]),
    ("sysmem_simple_allocator_free", "poison the last 16 payload bytes too",
     [("std::memset(ptr, 0xDD, node->size - 16);", "std::memset(ptr, 0xDD, node->size);")]),
    ("sysmem_simple_allocator_free", "return early on a double free",
     [("if ((node->flags & 0x10) == 0) {", "if ((node->flags & 0x10) == 0) { return;")]),
    ("sysmem_simple_allocator_free", "forget recovered header bytes in free accounting",
     [("heap[0x98 / 4] += 16;", "/* lost recovered header bytes */")]),
    ("sysmem_simple_allocator_free", "pass the allocator instead of the freed pointer to diagnostics",
     [('already marked free", ptr);', 'already marked free", self);')]),
    ("pg_6c00_w", "invert tangent handedness",
     [("lbl_82606750[k] > dot", "lbl_82606750[k] < dot")]),
    ("pg_6c00_w", "pack components at 9-bit intervals",
     [("<< (10 * k);", "<< (9 * k);")]),
    ("pg_6c00_w", "skip mapping refresh",
     [("        pg_7578_g(buffer);", "        /* omitted mapping */")]),
    ("pg_6c00_w", "keep VMX subnormals",
     [("        bits &= 0x80000000u;", "        /* omitted VMX flush */")]),
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
    ("lc_drill_strings", "change the tail of the 90-byte debug message",
     [('"something is wrong"', '"something is off"')]),
    ("lc_drill_strings", "post 2 instead of 1 (a variadic argument)",
     [('m_numSuccesses);\n    PostPageGroupMessageFmt(0x5008, 0x40, "i", 1);',
       'm_numSuccesses);\n    PostPageGroupMessageFmt(0x5008, 0x40, "i", 2);')]),
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


def _normpacked32() -> list[str]:
    """ReXGlue format=2/mask=1/shift=0, including reversed host lane placement.

    First three vectors are Xenia's uint_2101010_0..2 instruction tests. Extra
    cases pin NaN clamping, exact endpoints, aliasing and preserved lanes.
    """
    from .vmx import Unsupported, VectorUnit
    cases = [
        ([0xB8FF8000, 0xB8FF8000, 0xC04001FF, 0x4E9A5A5A], 0xE0180601),
        ([0x42C80000, 0xC2C80000, 0x40400000, 0x3F800000], 0x000805FF),
        ([0x3F000000, 0xBF000000, 0x3F800000, 0], 0x20180601),
        ([0x7FC00000, 0x7F800000, 0xFF800000, 0x7FC00000], 0x2017FE01),
        ([0x404001FF, 0x403FFE01, 0x40400000, 0x40400003], 0xC00805FF),
    ]
    errors = []
    for source, expected in cases:
        for alias in (False, True):
            v = VectorUnit(None)
            v.v[3] = source[:]
            v.v[4] = [0xCDCDCDCD] * 4
            # Actual instruction encoding: vpkd3d128 v4/v3,v3,2,1,0.
            word = 0x18891E10 if not alias else 0x18691E10
            v.execute(word, 0)
            want = (source[:3] if alias else [0xCDCDCDCD] * 3) + [expected]
            if v.v[3 if alias else 4] != want:
                errors.append(f"normpacked32 {source!r}, alias={alias}: wrong result")
    # Other forms must still fail explicitly, never silently use this model.
    for word in (0x18811E10, 0x188A1E10, 0x18891E50):
        try:
            VectorUnit(None).execute(word, 0)
            errors.append(f"normpacked32 accepted unsupported form 0x{word:08X}")
        except Unsupported:
            pass
    # vupkd3d128 v12,v12,8 (pg_5BD8_g): packed word in guest word 3.
    unpack_cases = [
        (0x000805FF, [0x404001FF, 0x403FFE01, 0x40400000, 0x3F800000]),
        (0xE0180601, [0x403FFE01, 0x403FFE01, 0x403FFE01, 0x3F800003]),
        (0x00000200, [0x7FC00000, 0x40400000, 0x40400000, 0x3F800000]),
        (0x7FFFFFFF, [0x403FFFFF, 0x403FFFFF, 0x403FFFFF, 0x3F800001]),
    ]
    for packed, expected in unpack_cases:
        v = VectorUnit(None)
        v.v[12] = [0xCDCDCDCD] * 3 + [packed]
        v.execute(0x198867F0, 0)
        if v.v[12] != expected:
            errors.append(f"vupkd3d128 0x{packed:08X}: got {[hex(w) for w in v.v[12]]}")
    try:
        VectorUnit(None).execute(0x198467F0, 0)
        errors.append("vupkd3d128 accepted unsupported type 1")
    except Unsupported:
        pass
    return errors


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

    from .calltests import regressions
    call_errors = regressions()
    print(f"{'ok  ' if not call_errors else 'FAIL'} run() repeat/nested/tail-call regressions")
    for line in call_errors:
        print(f"     {line}")
    bad += bool(call_errors)

    from .calltests import wide_regressions
    wide_errors = wide_regressions()
    print(f"{'ok  ' if not wide_errors else 'FAIL'} uint64 entry/call/return ABI regressions")
    for line in wide_errors:
        print(f"     {line}")
    bad += bool(wide_errors)

    packed_errors = _normpacked32()
    print(f"{'ok  ' if not packed_errors else 'FAIL'} vpkd3d128/vupkd3d128 NORMPACKED32 regression")
    for line in packed_errors:
        print(f"     {line}")
    bad += bool(packed_errors)

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
