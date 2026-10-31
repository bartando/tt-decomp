"""Mutation proof for the creature worker reset.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_worker_reset_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("creature_worker_reset", "src/game/creature/creature_pose.cpp",
     "void pongCreatureWorker_Reset(", [
        ("empty lift", "    void* geometry", "    return;\n    void* geometry"),
        ("retain stale geometry", "    geometry = workerField<void*>(worker, 0x3C);", "    (void)geometry;"),
        ("wrong mesh index", "0)[meshIndex]", "0)[0]"),
        ("wrong batch index", "uint32_t(batchIndex * 40)", "uint32_t(0)"),
        ("omit relative transform", "if (g_creatureWorkerRelativePose)", "if (false)"),
        ("wrong root bone", "matrices + rootBone * 16", "matrices"),
        ("omit last bone transform", "bone < boneCount", "bone + 1 < boneCount"),
        ("omit ring cursor", "? g_renderClearRingIdx : 0", "? 0 : 0"),
        ("wrong skinning flag", "skinMap, 0, vertexCount", "skinMap, 1, vertexCount"),
        ("cache stale vertex count", "vertex < workerField<int32_t>(buffer, 0)", "vertex < vertexCount"),
        ("omit map", "if (!workerField<uint8_t>(buffer, 0xDB)) pg_7578_g(buffer);", "(void)buffer;"),
        ("wrong vertex stride", "uint32_t(stride * vertex)", "uint32_t(16 * vertex)"),
        ("wrong output mapping", "0x28)[vertex]", "0x28)[0]"),
        ("omit first position array", "std::memcpy(workerField<uint8_t*>(part, 0x1C) + uint32_t(index * 16), position, 16);", "(void)part;"),
        ("omit source unmap", "grc_7628(buffer);", "(void)buffer;"),
        ("wrong bound type gate", "!= 9", "== 9"),
        ("omit parent bound", "    bound->vfn_1(1);", "    (void)bound;"),
        ("wrong parent flag", "    bound->vfn_1(1);", "    bound->vfn_1(0);"),
        ("wrong child index", "0x70)[index]", "0x70)[0]"),
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
