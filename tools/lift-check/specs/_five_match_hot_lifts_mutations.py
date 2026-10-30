"""Mutation proof for five match-hot lifts; only behavioral FAIL counts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_five_match_hot_lifts_mutations.py

Patches apply only to build-cache copies. Each check uses its spec's default
1000 trials, seed 1; BUILD/SPEC/UNSUPPORTED and passing mutants fail the proof.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

QUERIES = "src/game/player/pong_gameplay_queries.cpp"
PHYSICS = "src/physics/ph_update_object.cpp"
CASES = [
    ("anim_clip_is_playback_ready", QUERIES, 'extern "C" bool pongAnimClip_IsPlaybackReady(', [
        ("empty lift", "    const auto* bytes", "    return false;\n    const auto* bytes"),
        ("accept zero progress", "values[32] > 0.0f", "values[32] >= 0.0f"),
        ("accept unordered progress", "values[32] > 0.0f", "!(values[32] <= 0.0f)"),
        ("accept unordered position", "values[72] >= 0.0f", "!(values[72] < 0.0f)"),
        ("old reversed stop byte", "bytes[136] == 0", "bytes[136] != 0"),
        ("omit active byte", "bytes[138] != 0", "true"),
        ("old combined flag exclusion", "(flags & 4) == 0\n        && (flags & 8) == 0", "(flags & 12) != 12"),
        ("omit primary flag", "(flags & 1) != 0", "true"),
    ]),
    ("match_settings_get_court_bounds", QUERIES, 'extern "C" void pongMatchSettings_GetCourtBounds(', [
        ("empty lift", "    auto* values", "    return;\n    auto* values"),
        ("old wrong negative half", "values[32] * -0.5f", "values[32] * 0.5f"),
        ("old missing chained sum", "hi[2] = values[33] + nearZ;", "hi[2] = values[33] + halfDepth;"),
        ("wrong side index", "[64 + sideIndex]", "[64]"),
        ("invert court side", "if (side)", "if (!side)"),
        ("overwrite w", "    lo[1] = 0.0f;", "    lo[3] = 0.0f;\n    lo[1] = 0.0f;"),
        ("wrong table dimension", "g_pTableDims)[6]", "g_pTableDims)[5]"),
    ]),
    ("input_poll_predicate", "src/rage/core/io_input.cpp", "int io_Input_poll_9D68(", [
        ("empty lift", "    if (!inputObj)", "    return 0;\n    if (!inputObj)"),
        ("AND instead of OR", "(held != 0) || (rep != 0)", "(held != 0) && (rep != 0)"),
        ("ignore pressed gate", "return pressed ? 1 : 0;", "return 1;"),
        ("test only low counter byte", "(rep != 0)", "((rep & 255) != 0)"),
        ("require canonical held byte", "(held != 0)", "(held == 1)"),
        ("return unnormalized byte", "return pressed ? 1 : 0;", "return pressed;"),
    ]),
    ("ph_update_object_commit_transform", PHYSICS, "void phUpdateObject::CommitTransform(", [
        ("empty lift", "    const auto* src", "    return;\n    const auto* src"),
        ("wrong frame cursor", "g_phFrameIndex * 64", "g_phFrameCounter * 64"),
        ("old ignored external source", "const auto* src = m_pTransformSrc", "const auto* src = false"),
        ("omit translation row", "row < 4", "row < 3"),
        ("old missing scaling", "row < 3", "row < 0"),
        ("scale translation", "row < 3", "row < 4"),
        ("omit w scale", "lane < 4", "lane < 3"),
        ("omit VMX input flushing", "flushTransformVmx(values[lane]) * flushTransformVmx(scale[lane])", "values[lane] * scale[lane]"),
        ("omit VMX result flushing", "values[lane] = flushTransformVmx(flushTransformVmx(values[lane]) * flushTransformVmx(scale[lane]));", "values[lane] = flushTransformVmx(values[lane]) * flushTransformVmx(scale[lane]);"),
    ]),
    ("ph_update_object_render_shadow", PHYSICS, "void phUpdateObject::RenderShadow(", [
        ("empty lift", "    if (!m_pDrawable)", "    return;\n    if (!m_pDrawable)"),
        ("wrong frame cursor", "g_phFrameCounter * 64", "g_phFrameIndex * 64"),
        ("scale translation", "i < 12", "i < 16"),
        ("omit third basis row", "i < 12", "i < 8"),
        ("drop caller context", "localMatrix, context);", "localMatrix, nullptr);"),
        ("omit scale rounding", "const float scale = storedScale;", "const float scale = shadowScale;"),
        ("omit VMX input flushing", "flushTransformVmx(localMatrix[i]) * flushTransformVmx(scale)", "localMatrix[i] * scale"),
        ("omit VMX result flushing", "localMatrix[i] = flushTransformVmx(flushTransformVmx(localMatrix[i]) * flushTransformVmx(scale));", "localMatrix[i] = flushTransformVmx(localMatrix[i]) * flushTransformVmx(scale);"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
        print(f"{spec}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
