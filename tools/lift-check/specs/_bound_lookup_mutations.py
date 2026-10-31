"""Behavioral mutation proof for recursive bound counting and articulated lookup.

Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python.
Only checker build-cache copies change; build/spec errors and lift faults fail.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/bound_lookup.cpp"
CASES = {
    "ph_composite_count_bounds": [
        ("omit direct slots", "uint32_t count = compositeChildCount(bound);", "uint32_t count = 0;"),
        ("count only one descendant", "count += phBoundComposite_E750(child);", "count += 1;"),
    ],
    "ph_composite_resolve_bound_index": [
        ("unsigned direct index check", "if (index < count)",
         "if (static_cast<uint32_t>(index) < static_cast<uint32_t>(count))"),
        ("include subtree boundary", "static_cast<int32_t>(remaining) < static_cast<int32_t>(descendants)",
         "static_cast<int32_t>(remaining) <= static_cast<int32_t>(descendants)"),
        ("subtract wrong subtree size", "remaining -= descendants;", "remaining -= descendants + 1;"),
        ("return flattened index", "return i;", "return index;"),
    ],
    "ph_articulated_get_joint_index": [
        ("wrong body map offset", " + 0x204 + child * 4,", " + 0x200 + child * 4,"),
        ("wrong RTTI target", "&g_typeDescriptor_phBoundComposite, 0);", "&g_typeDescriptor_phBound, 0);"),
        ("ignore bone index", "ResolveBoundIndex(composite, boneIndex);", "ResolveBoundIndex(composite, 0);"),
        ("return child instead of body", "return bodyIndex;", "return child;"),
    ],
}


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, mutations in CASES.items():
        for name, old, new in mutations:
            assert source.count(old) == 1, (spec, name, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=400, seed=1, patches=((old, new),))).run()
            report = output.getvalue()
            caught = rc == 1 and "the lift faulted" not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
