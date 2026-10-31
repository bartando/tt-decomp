"""Require behavioral FAIL for deliberately broken phase/clip selection helpers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/player/player_swing_pose_helpers.cpp"
CASES = [
    ("player_select_dominant_clip", [
        ("ignore third clip", "index < 3", "index < 2"),
        ("allow later ties", "> at<float>(record, 0x1C + unsigned(selected) * 4)", ">= at<float>(record, 0x1C + unsigned(selected) * 4)"),
        ("use previous weight column", "0x1C + unsigned(index) * 4", "0x18 + unsigned(index) * 4"),
    ]),
    ("player_interpolate_swing_markers", [
        ("use exit marker for first interval", "markerTime(record, 0x130) * ratio", "markerTime(record, 0x132) * ratio"),
        ("reverse marker interval", "difference = exit - entry", "difference = entry - exit"),
        ("discard elapsed clock fraction", "ratio = elapsed / interval", "ratio = 0.0f"),
        ("multiply free phase span", "advance = g_sysTimeManager.frameSeconds / phaseFrameSpan(duration)", "advance = g_sysTimeManager.frameSeconds * phaseFrameSpan(duration)"),
    ]),
    ("player_interpolate_swing_followthrough", [
        ("use entry marker for planned exit", "markerTime(record, 0x132) * ratio", "markerTime(record, 0x130) * ratio"),
        ("reverse follow-through slope", "difference = finalRate - initialRate", "difference = initialRate - finalRate"),
        ("omit phase blend clamp", "blend = nonnegative - 1.0 >= 0.0 ? 1.0f : static_cast<float>(nonnegative)", "blend = static_cast<float>(nonnegative)"),
        ("unsigned follow-through marker", "static_cast<float>(at<int16_t>(record, 0x132))", "static_cast<float>(at<uint16_t>(record, 0x132))"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    count = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
