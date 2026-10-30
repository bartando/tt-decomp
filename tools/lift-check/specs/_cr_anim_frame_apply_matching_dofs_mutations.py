"""From repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_cr_anim_frame_apply_matching_dofs_mutations.py

Only build-cache copies are mutated. A caught mutation must produce behavioral
FAIL (exit 1); BUILD/SPEC/UNSUPPORTED are failures of this mutation test itself.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("ignore destination channel type", "(type << 16) | id", "id"),
    ("truncate destination ID", "(type << 16) | id", "(type << 16) | (id & 0xFF)"),
    ("stop on equal source key", "if (srcKey > dstKey)", "if (srcKey >= dstKey)"),
    ("reverse source scan", "if (srcKey > dstKey)", "if (srcKey < dstKey)"),
    ("reuse source after match", "                ++srcIndex;\n                break;",
     "                break;"),
    ("restart source scan for each destination", "        void* dstDof = dst->m_dofs[dstIndex];",
     "        srcIndex = 0;\n        void* dstDof = dst->m_dofs[dstIndex];"),
    ("treat source count as signed", "if (srcIndex >= srcCount)",
     "if (static_cast<int>(srcIndex) >= static_cast<int16_t>(srcCount))"),
    ("zero initial filter weight", "float channelWeight = 1.0f;", "float channelWeight = 0.0f;"),
    ("test whole filter return", "&channelWeight) & 0xFF)", "&channelWeight))"),
    ("ignore filter rejection", "&channelWeight) & 0xFF) != 0", "&channelWeight) & 0xFF) >= 0"),
    ("drop per-channel weight", "channelWeight * weight", "weight"),
    ("add weights instead of multiplying", "channelWeight * weight", "channelWeight + weight"),
    ("swap operation receivers", "operation(dstDof, srcDof,", "operation(srcDof, dstDof,"),
    ("change operation flags", "operation(dstDof, srcDof, weight, 0, 0);",
     "operation(dstDof, srcDof, weight, 0, 1);"),
    ("forward wrong filter user data", "filter(context, type, id, userData,",
     "filter(context, type, id, context,"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/animation/rage_anim.cpp").read_text()
    spec = Path(__file__).with_name("cr_anim_frame_apply_matching_dofs.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) >= 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
