import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("math_index_wrap", "equal bounds", "if (maximum == minimum) return minimum;", "if (maximum == minimum) return value;"),
    ("math_index_wrap", "negative origin", "value < minimum ? last + 1u : first", "value < minimum ? last : first"),
    ("math_index_wrap", "inclusive length", "last - first + 1u", "last - first"),
    ("camera_cursor_next", "wrong forward step", "static_cast<uint32_t>(*cursor) + 1u", "static_cast<uint32_t>(*cursor) + 2u"),
    ("camera_cursor_next", "wrapped high boundary", "if (*cursor > high) *cursor = low;", "if (*cursor >= high) *cursor = low;"),
    ("camera_cursor_previous", "wrapped low boundary", "if (*cursor < low) *cursor = high;", "if (*cursor <= low) *cursor = high;"),
    ("camera_cursor_previous", "wrong capacity", "static_cast<uint32_t>(cursor[1]) - 1u", "static_cast<uint32_t>(cursor[1]) - 2u"),
    ("camera_interval_search", "exclusive lower", "entry.key.value >= key->value", "entry.key.value > key->value"),
    ("camera_interval_search", "inclusive upper", "entry.key.value < upper", "entry.key.value <= upper"),
    ("camera_interval_search", "allow mode zero", "return entry.mode != 0 &&", "return true &&"),
    ("camera_interval_search", "wrong count", "if (visited >= ring->count) return false;", "if (visited >= ring->count - 1) return false;"),
    ("camera_interval_search", "skip rewind", "do {\n        retreat();", "do {\n        break;\n        retreat();"),
    ("camera_interval_search", "wrong requested mode", "candidate->mode == mode", "candidate->mode != mode"),
    ("camera_interval_search", "overwrite duration", "if (matches(entry)) {\n        key->value = entry->key.value;", "if (matches(entry)) {\n        *key = entry->key;"),
    ("camera_interval_flag1", "wrong flag", "TransitionFlags flags = {3, 1};", "TransitionFlags flags = {3, 0};"),
    ("camera_shot_condition_counter", "wrong first flag", "TransitionFlags flags = {3, 0};", "TransitionFlags flags = {3, 1};"),
    ("camera_shot_condition_counter", "wrong mode", "pg_6F68(evaluator, &key, 5,", "pg_6F68(evaluator, &key, 6,"),
    ("camera_shot_condition_counter", "increment twice", "++g_cameraLerpState;", "g_cameraLerpState += 2;"),
    ("camera_transition_two_stage", "wrong forward mode", "&key, 7, &flags, 1)", "&key, 8, &flags, 1)"),
    ("camera_transition_two_stage", "wrong interval mode", "&key, 16, &flags.flag1, 1)", "&key, 17, &flags.flag1, 1)"),
    ("camera_transition_two_stage", "skip second bound", "if (!pg_6F68(evaluator, &key, 16, &flags.flag1, 1) || key.value > upper)", "if (!pg_6F68(evaluator, &key, 16, &flags.flag1, 1))"),
    ("camera_transition_two_stage", "lose NaN", "if (pongCameraMgr_6E08(evaluator, &key, 7, &flags, 1) == 0 || key.value > upper)", "if (pongCameraMgr_6E08(evaluator, &key, 7, &flags, 1) == 0 || !(key.value <= upper))"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"), Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
