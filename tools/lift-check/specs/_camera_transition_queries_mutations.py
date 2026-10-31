import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("camera_offset_query", "wrong initial mode", "evaluator, 20)", "evaluator, 19)"),
    ("camera_offset_query", "stale source", "*static_cast<float*>(source) +", "copy.value +"),
    ("camera_offset_query", "lose offset", "+ g_cameraConstPool[0]", "+ 0.0f"),
    ("camera_offset_query", "wrong final mode", "evaluator, 3)", "evaluator, 2)"),
    ("camera_transition_mode6", "wrong flag", "flags = {5, 0}", "flags = {5, 1}"),
    ("camera_transition_mode6", "wrong mode", "&copy, 6,", "&copy, 7,"),
    ("camera_transition_mode6", "lose unordered acceptance", "copy.value > upper", "!(copy.value <= upper)"),
    ("camera_transition_mode6", "wrong bound", "copy.value > upper", "copy.value > lower"),
    ("camera_transition_mode6", "omit store", "*static_cast<float*>(source) = copy.value;", "/* store lost */"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        ok = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if ok else 'MISSED'} {spec}: {label}: {first}", flush=True)
        if not ok:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
