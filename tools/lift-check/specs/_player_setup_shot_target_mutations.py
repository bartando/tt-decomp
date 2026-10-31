"""Cache-only setup mutants must produce a behavioral FAIL, not a build error."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("omit mutable x clamp", "position->x = clampCourt(position->x, lower.x, upper.x);", "(void)lower;"),
    ("omit mutable z clamp", "position->z = clampCourt(position->z, lower.z, upper.z);", "(void)upper;"),
    ("wrong timed activity", "!(at<float>(timing, 0x1C) >= at<float>(timing, 0x30))", "at<float>(timing, 0x1C) >= at<float>(timing, 0x30)"),
    ("omit recovery predicate", "if (!active) active = pongPlayer_D598_g(state);", "(void)state;"),
    ("drop copied fourth lane", "at<vec3>(target, 0x480) = *position;", "at<vec3>(target, 0x480) = {position->x, position->y, position->z, 0.0f};"),
    ("wrong stored y", "at<float>(target, 0x484) = 1.0f;", "at<float>(target, 0x484) = 0.0f;"),
    ("wrong stored contact scale", "at<float>(target, 0x494) = contactScale;", "at<float>(target, 0x494) = movementLimit;"),
    ("ignore active-player gate", "active && at<uint8_t>(at<void*>(target, 0x30), 0x19E0) == 0", "active"),
    ("wrong root slot", "[slot + 17]", "[17]"),
    ("wrong movement limit square", "movementLimit * movementLimit", "movementLimit"),
    ("wrong movement scale", "position->x, position->z, contactScale, speed", "position->x, position->z, movementLimit, speed"),
    ("wrong retained-root flag", "at<uint8_t>(target, 0x490) = 1;", "at<uint8_t>(target, 0x490) = 0;"),
    ("wrong normal return", "    return 1;", "    return 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_shot_target_setup.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_setup_shot_target.py"),
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
