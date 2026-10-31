"""Mutation proof for the vertex buffer map/unmap/cursor.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_vertex_buffer_mapping_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("vertex_buffer_map", "src/graphics/grc_vertex_buffer.cpp", 'extern "C" uint8_t pg_7578_g(', [
        ("empty lift", "    auto* buffer", "    return 0;\n    auto* buffer"),
        ("remap active buffer", "!buffer->mapped && buffer->resourceAddress", "buffer->resourceAddress"),
        ("wrong data mask", "resource[3] & ~3u", "resource[3] & ~1u"),
        ("wrong fence word", "resource[1], 0x2E", "resource[0], 0x2E"),
        ("wrong size mask", "resource[4] & 0x03FFFFFCu", "resource[4]"),
        ("wrong stack flags", "0, 0x03000000u", "1, 0x03000000u"),
        ("wrong cache policy", "0x03000000u", "0x02000000u"),
        ("wrong mapped value", "buffer->mapped = 1", "buffer->mapped = 2"),
        ("omit thread ID", "buffer->mappingThread = xe_GetCurrentThreadId();", "(void)buffer;"),
    ]),
    ("vertex_buffer_unmap", "src/graphics/grc_vertex_buffer.cpp", 'extern "C" bool grc_7628(', [
        ("empty lift", "    auto* buffer", "    return true;\n    auto* buffer"),
        ("ignore dirty gate", "!rage::g_bTextureEndianDirty && g_grcUseResourceLocks", "g_grcUseResourceLocks"),
        ("ignore lock gate", "!rage::g_bTextureEndianDirty && g_grcUseResourceLocks", "!rage::g_bTextureEndianDirty"),
        ("wrong resource data mask", "resource[3] & ~3u", "resource[3] & ~1u"),
        ("retain mapped byte", "buffer->mapped = 0", "buffer->mapped = 1"),
        ("wrong return", "return buffer->mapped == 0", "return buffer->mapped != 0"),
    ]),
    ("vertex_buffer_begin_cursor", "src/graphics/grc_vertex_buffer.cpp", 'extern "C" void pg_54B0_g(', [
        ("empty lift", "    auto* buffer", "    return;\n    auto* buffer"),
        ("wrong map gate", "if (!buffer->mapped)", "if (buffer->mapped)"),
        ("wrong cursor source", "buffer->stagingAddress = buffer->dataAddress", "buffer->stagingAddress = buffer->resourceAddress"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip declarations: each definition begins at column zero.
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) >= 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            first = report.splitlines()[0] if report else "no checker output"
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
