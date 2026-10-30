"""Run from the checkout root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_four_hot_match_lifts_mutations.py

Patch build-cache copies only, scoped to each lift (or its inlined shared
command writer). Use default trial counts, seed 1. Only behavioral FAIL (1)
counts: PASS, BUILD, SPEC, or UNSUPPORTED makes this proof fail.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("fx_crowd_apply_animation_frame", "src/graphics/fx_crowd.cpp",
     "void fxCrowd_ApplyAnimationFrame(", [
         ("empty lift", "    auto* self", "    return;\n    auto* self"),
         ("wrong callback", "data + 20) & 1", "data + 20) & 2"),
         ("signed count", "const unsigned count =", "const int16_t count ="),
         ("cache entry array across callbacks", "    for (unsigned i", "    auto* cached = *reinterpret_cast<void* const* const*>(list + 8);\n    for (unsigned i"),
         ("use cached final skeleton", "LocomotionStateAnim_C8F8_g(*reinterpret_cast<void**>(self + 0x24))", "LocomotionStateAnim_C8F8_g(skeleton)"),
         ("wrong weight", "skeleton, 0.0f", "skeleton, 1.0f"),
     ]),
    ("rage_mat33_from_euler", "src/rage/math/mat33.cpp",
     "void mat33FromEuler(", [
         ("empty lift", "    float sx", "    return;\n    float sx"),
         ("swap sine/cosine", "ph_SinCos(&cx, &sx", "ph_SinCos(&sx, &cx"),
         ("skip negative X", "angles[0] != 0.0f", "angles[0] > 0.0f"),
         ("wrong row stride", "out[6] =", "out[7] ="),
         ("lose fused rounding", "__builtin_fmaf(czsy, sx, -szcx)", "czsy * sx - szcx"),
         ("overwrite aliased angles", "    float sx", "    out[0] = 0.0f;\n    float sx"),
     ]),
    ("grc_device_set_depth_stencil_clear", "src/graphics/grc_device.cpp",
     'extern "C" void grcDevice_SetDepthStencilClear(', [
         ("empty lift", "    (void)unusedR4;", "    return;\n    (void)unusedR4;"),
         ("wrong depth scale", "16777215.0f", "16777216.0f"),
         ("shift fixed-point mode", "mode = convert(depth * 2047.0f);", "mode = convert(depth * 2047.0f) >> 21;"),
         ("lose negative float clamp", "bits & 0x80000000u", "bits & 0x40000000u"),
         ("32-bit shift wrap", "resultShift = shift & 63", "resultShift = shift & 31"),
         ("truncate full stencil", "| stencil;", "| (stencil & 0xFF);"),
         ("overwrite dirty flags", "*reinterpret_cast<uint64_t*>(dev + 48) |=", "*reinterpret_cast<uint64_t*>(dev + 48) ="),
     ]),
    ("aud_command_enqueue", "src/rage/audio/rage_audio.cpp",
     "void PushAudioCommand(", [
         ("empty writer", "    uint32_t idx", "    return;\n    uint32_t idx"),
         ("wrong class byte", "hdr[0] = cmdClass", "hdr[0] = cmdClass ^ 1"),
         ("missing header count", "hdr[1] = paramCount + 1", "hdr[1] = paramCount"),
         ("wrong command id", "hdr + 2) = cmdId", "hdr + 2) = cmdId ^ 1"),
         ("signed payload count", "if (paramCount > 0)", "if (static_cast<int8_t>(paramCount) > 0)"),
         ("reverse payload", "dst[i] = params[i]", "dst[i] = params[paramCount - 1 - i]"),
         ("wrong write index", "g_audCommandWriteIndex = idx + paramCount;", "g_audCommandWriteIndex = idx + paramCount + 1;"),
         ("publish write index after copy", "g_audCommandWriteIndex = idx + paramCount;", ""),
     ]),
    ("aud_command_enqueue", "src/rage/audio/rage_audio.cpp",
     "void audCommand_Enqueue(", [
         ("lose byte truncation", "static_cast<uint8_t>(paramCount)", "static_cast<uint8_t>(paramCount >> 8)"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {name}: {label}"
            mutated = body.replace(old, new)
            if label == "signed count":
                mutated = mutated.replace("for (unsigned i", "for (int i")
            if label == "cache entry array across callbacks":
                mutated = mutated.replace("apply(entries[i]", "apply(cached[i]")
            if label == "publish write index after copy":
                mutated = mutated.replace("        }\n    }", "        }\n        g_audCommandWriteIndex = idx + paramCount;\n    }")
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(name + ".py"),
                                 Options(seed=1, patches=((body, mutated),))).run()
            except BuildError as exc:
                print(f"MISSED {name}: {label}: BUILD {exc}", flush=True)
                return 1
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} behavioral mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
