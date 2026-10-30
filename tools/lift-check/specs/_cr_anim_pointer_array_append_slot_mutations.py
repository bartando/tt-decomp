"""Run with PYTHONPATH=tools/lift-check and the lift-check venv Python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("grow by one", "array->capacity + static_cast<uint16_t>(growth)", "array->capacity + 1"),
    ("wrong allocation size", "uint32_t(array->capacity) * 4", "uint32_t(array->capacity) * 8"),
    ("skip construction", "crAnimPointer_Construct(data + i);", ";"),
    ("skip copy", "data[i] = array->data[i];", ";"),
    ("free tracked storage", "& 0xFF) == 0", "& 0xFF) != 0"),
    ("test whole tracking result", "(rage_FindSingleton(old) & 0xFF)",
     "rage_FindSingleton(old)"),
    ("return next slot", "array->data + array->count;", "array->data + array->count + 1;"),
    ("omit count increment", "array->count = static_cast<uint16_t>(array->count + 1);", ";"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/animation/rage_anim.cpp").read_text()
    spec = Path(__file__).with_name("cr_anim_pointer_array_append_slot.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f'{"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
