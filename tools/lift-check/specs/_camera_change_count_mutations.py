import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("camera_shot_change_count", "wrong gate", "gate <= 0.0f && snapshot", "gate >= 0.0f && snapshot"),
    ("camera_shot_change_count", "drop interval length", "key.value += duration;", "key.value += 0.0f;"),
    ("camera_shot_change_count", "query local copy", "pg_6F68(evaluator, source, 5, nullptr, -1)", "pg_6F68(evaluator, &key, 5, nullptr, -1)"),
    ("camera_shot_change_count", "wrong predicate count", "pg_6F68(evaluator, source, 5, nullptr, -1)", "pg_6F68(evaluator, source, 5, nullptr, 0)"),
    ("camera_shot_change_count", "wrong clamp mode", "evaluator, 5)) return false;", "evaluator, 6)) return false;"),
    ("camera_shot_change_count", "live counter", "return snapshot == (!(distance", "return g_cameraLerpState == (!(distance"),
    ("camera_shot_change_count", "wrong near count", "requested - 2u : requested - 1u", "requested - 2u : requested"),
    ("camera_shot_change_count", "wrong far count", "requested - 2u : requested - 1u", "requested - 1u : requested - 1u"),
    ("camera_shot_change_count", "wrong distance boundary", "!(distance < g_cameraTransitionOffset)", "!(distance <= g_cameraTransitionOffset)"),
    ("camera_shot_change_count", "wrong NaN branch", "!(distance < g_cameraTransitionOffset)", "distance >= g_cameraTransitionOffset"),
]
CASES += [(f"camera_change_thunk_{i}", "wrong thunk count",
           f"return pg_7CD8_2h(this, gameState, 0, 0, {i});",
           f"return pg_7CD8_2h(this, gameState, 0, 0, {i + 1});") for i in range(1, 7)]

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
