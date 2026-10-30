"""Run from the root with PYTHONPATH=tools/lift-check and the checker venv.

Only build-cache copies are patched; only behavioral FAIL (rc=1) counts.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("normalize direct byte", "return *(uint8_t*)pData;", "return *(uint8_t*)pData != 0;"),
    ("normalize virtual byte", "return tmp;", "return tmp != 0;"),
    ("read adjacent direct byte", "return *(uint8_t*)pData;", "return *((uint8_t*)pData + 1);"),
    ("dispatch wrong virtual slot", "((VFn_GetBool)vtbl[3])(pNode, &tmp);", "((VFn_GetBool)vtbl[4])(pNode, &tmp);"),
    ("pass port instead of node", "((VFn_GetBool)vtbl[3])(pNode, &tmp);", "((VFn_GetBool)vtbl[3])(port, &tmp);"),
    ("accept truncated tag", "if (port->m_type == 1) {\n        // DIRECT: read bool", "if ((port->m_type & 0xff) == 1) {\n        // DIRECT: read bool"),
    ("nonzero disconnected result", "return tmp;\n    }\n\n    return false;", "return tmp;\n    }\n\n    return 1;"),
]


def main():
    spec = Path(__file__).with_name("cm_port_get_bool.py")
    source = (spec.parents[3] / "src/game/misc/cm_operators.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
