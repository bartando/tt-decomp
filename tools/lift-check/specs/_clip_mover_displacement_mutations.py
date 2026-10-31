"""Only behavioral FAIL counts for these cache-only ExtractDisplacement mutants."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong rotation vtable", "rotation.vtable = lbl_82027BF4;", "rotation.vtable = lbl_82027B9C;"),
    ("wrong rotation flags", "rotation.flags = 1;", "rotation.flags = 0;"),
    ("wrong rotation type", "rotation.type = 6;", "rotation.type = 5;"),
    ("wrong translation type", "translation.type = 5;", "translation.type = 6;"),
    ("wrong mover id", "rotation.id = 0;", "rotation.id = 1;"),
    ("ignore rotation failure", "if (!LocomotionStateAnim_EvaluateChannel(clip, nullptr, &rotation, time)) return 0;", "LocomotionStateAnim_EvaluateChannel(clip, nullptr, &rotation, time);"),
    ("ignore translation failure", "if (!LocomotionStateAnim_EvaluateChannel(clip, nullptr, &translation, time)) return 0;", "LocomotionStateAnim_EvaluateChannel(clip, nullptr, &translation, time);"),
    ("wrong channel sample time", "&rotation, time)", "&rotation, 0.0f)"),
    ("omit time floor", "time >= 0.0f ? double(time) : 0.0", "double(time)"),
    ("omit time cap", "? duration : float(nonnegative)", "? float(nonnegative) : float(nonnegative)"),
    ("retain negative delta", "-double(delta) >= 0.0 ? 0.0f : delta", "delta"),
    ("ignore low-byte delta status", "if (!static_cast<uint8_t>(result))", "if (!result)"),
    ("copy translation as rotation", "__builtin_memcpy(output, rotation.value, sizeof rotation.value);", "__builtin_memcpy(output, translation.value, sizeof rotation.value);"),
    ("drop second result vector", "translation.value, sizeof translation.value);", "translation.value, 0);"),
    ("wrong successful return", "    return 1;", "    return 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/anim/clip_mover_displacement.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("clip_mover_displacement.py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
