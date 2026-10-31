"""Mutation proof for C288 (weight ABI mutations are in _locomotion_weight_abi_mutations.py). Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_locomotion_lifts_mutations.py

Only build-cache copies are patched. Only behavioral FAIL (exit 1) counts;
BUILD, SPEC and UNSUPPORTED results fail the proof. Anchors are scoped to the
target function so identical code elsewhere in the TU cannot absorb a mutation.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = [
    ("transition_locomotion_state", "src/anim/locomotion.cpp",
     "void LocomotionStateAnim_TransitionLocomotionState(", [
         ("empty lift", "    (void)unusedR4;", "    return;\n    (void)unusedR4;"),
         ("skeleton in r4", "static_cast<uint8_t*>(skeleton)", "static_cast<uint8_t*>(unusedR4)"),
         ("apply non-root translations", "channel + 6) == 0", "channel + 6) != 0"),
         ("skip rotation lookup on failure", "if (!LocomotionStateAnim_04F0_g", "if (LocomotionStateAnim_04F0_g"),
         ("wrong rotation getter", "vtable[15](channel)", "vtable[14](channel)"),
         ("wrong bone stride", "index * 0x50", "index * 0x40"),
         ("omit translation w", "std::memcpy(records + 0x30, vector, sizeof(vector));",
          "std::memcpy(records + 0x30, vector, 12);"),
         ("wrong translation offset", "records + 0x30, vector", "records + 0x20, vector"),
     ]),

]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
