"""Mutation proof for swf_script_array_get_member; patch build-cache copies only.

Run from the repo root with:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_script_array_mutations.py

Only a behavioral FAIL (exit 1) counts; build/spec/unsupported errors do not.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = (
    ("reject index zero", "index >= 0 &&", "index > 0 &&"),
    ("accept index equal to count", "index < *reinterpret_cast<const uint16_t*>(array + 20)",
     "index <= *reinterpret_cast<const uint16_t*>(array + 20)"),
    ("signed element count", "index < *reinterpret_cast<const uint16_t*>(array + 20)",
     "index < *reinterpret_cast<const int16_t*>(array + 20)"),
    ("wrong element stride", "elements + index * 2", "elements + index"),
    ("wrong second value word", "output[1] = element[1];", "output[1] = element[0];"),
    ("non-exact length match", 'strcmp(property, "length") == 0', "property[0] == 'l'"),
    ("wrong length source", "output[0] = *reinterpret_cast<const uint16_t*>(array + 20);",
     "output[0] = *reinterpret_cast<const uint16_t*>(array + 22);"),
    ("wrong length value tag", "output[1] = 3;", "output[1] = 4;"),
    ("omit base fallback", "return swfSCRIPTOBJECT::GetMember(name, result);", "return false;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    start = source.index("bool swfSCRIPTARRAY::GetMember(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    caught = 0
    # First reproduce the original incomplete lift, then alter distinct paths.
    mutations = [("base-only regression", body,
                  body[:body.index("{") + 1] + "\n    return swfSCRIPTOBJECT::GetMember(name, result);\n}")]
    for name, old, new in CASES:
        assert body.count(old) == 1, name
        mutations.append((name, body, body.replace(old, new)))
    for name, old, new in mutations:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("swf_script_array_get_member.py"),
                         Options(trials=1000, seed=1, patches=((old, new),))).run()
        lines = output.getvalue().splitlines()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} swf_script_array_get_member/{name}: "
              f"{lines[0] if lines else 'no result'}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"swf_script_array_get_member: caught {caught}/{len(mutations)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
