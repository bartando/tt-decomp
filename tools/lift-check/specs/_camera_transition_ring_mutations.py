import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("camera_condition_slice", "wrong integer value", "event.flag2 == required.flag2", "event.flag2 != required.flag2"),
    ("camera_condition_slice", "lose kind one", "event.flag1 >= 1", "event.flag1 > 1"),
    ("camera_condition_slice", "float bit equality", "return a == b;", "return event.flag2 == required.flag2;"),
    ("camera_condition_slice", "wrong event range", "entry->numConditions;", "entry->firstCondition;"),
    ("camera_condition_slice", "ignore missing conditions", "if (!found) return 0;", "if (!found) return 1;"),
    ("camera_transition_ring", "strict time comparison", "entries[cursor].key.value >= key->value", "entries[cursor].key.value > key->value"),
    ("camera_transition_ring", "wrong mode", "entry->mode == mode", "entry->mode != mode"),
    ("camera_transition_ring", "omit predicate", "requiredCount) != 0)", "requiredCount) == 0)"),
    ("camera_transition_ring", "overwrite metadata", "key->value = entry->key.value;", "*key = entry->key;"),
    ("camera_transition_clamp", "wrong default flags", "mode, nullptr, -1)", "mode, nullptr, 0)"),
    ("camera_transition_clamp", "wrong metadata", "__builtin_memcpy(&key, self, sizeof key);", "key.vtableOrState = 0;"),
    ("camera_transition_clamp", "lose NaN result", "key.value > upper", "!(key.value <= upper)"),
    ("camera_transition_clamp_flag0", "wrong flag zero", "flags = {3u, 0u}", "flags = {3u, 1u}"),
    ("camera_transition_clamp_flag1", "wrong flag one", "flags = {3u, 1u}", "flags = {3u, 0u}"),
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
