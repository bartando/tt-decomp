"""Mutation proof for the creature teleport lifts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_teleport_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("creature_teleport", "src/game/creature/pong_creature.cpp",
     "void pongCreature_Teleport(", [
        ("empty lift", "    auto* self", "    return;\n    auto* self"),
        ("skip pre-pose update", "if (resetWorkers && haveWorkers && updatePoseFirst)", "if (false)"),
        ("ignore keep-matrix flag", "if (!keepInstanceMatrix)", "if (true)"),
        ("wrong worker pose destination", "pose + 0xB0 + row * 16", "pose + 0xA0 + row * 16"),
        ("drop worker translation w", "memcpy(pose + 0xF0, pose + 0xE0, 16)", "memcpy(pose + 0xF0, pose + 0xE0, 12)"),
        ("omit worker reset", "if (worker) pongCreatureWorker_Reset(worker, self->skeleton)", "if (worker) (void)worker"),
        ("wrong cache entry stride", "signals->entries[i][0x3E]", "signals->entries[0][0x3E]"),
        ("wrong secondary flag", "signals->secondary[0xA4]", "signals->secondary[0xA3]"),
        ("wrong frame cache flag", "g_phFrameIndex + 0x91", "g_phFrameIndex + 0x90"),
        ("omit frame index", "g_phFrameIndex + 0x91", "0x91"),
     ]),
    ("creature_inst_apply_teleport_matrix", "src/game/creature/pong_creature.cpp",
     "void pongCreatureInst_ApplyTeleportMatrix(", [
        ("empty lift", "    auto* bytes", "    return;\n    auto* bytes"),
        ("drop translation row", "row < 4", "row < 3"),
        ("omit last-matrix virtual", "dispatch->SetLastMatrix(matrix);", "(void)matrix;"),
        ("retain stale owner", "    owner = *reinterpret_cast<pongCreature**>(bytes + 0xD0);", "    (void)owner;"),
        ("omit bone sync", "dispatch->SyncBoneMatrices();", "(void)dispatch;"),
        ("skip level zero", "index != 0xFFFF", "index != 0xFFFF && index != 0"),
        ("wrong physics index", "UpdateObjectLocation(index)", "UpdateObjectLocation(0)"),
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
