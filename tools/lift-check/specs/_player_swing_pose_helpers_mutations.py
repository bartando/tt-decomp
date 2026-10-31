"""Require behavioral FAIL for deliberately broken swing pose helpers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/player/player_swing_pose_helpers.cpp"
CASES = [
    ("player_swing_marker_events", [
        ("ignore in-flight suppression", "if (g_swingInFlightFlag) return;", "if (false) return;"),
        ("lose completion event", "pg_E6E0(0x100B,", "pg_E6E0(0x100A,"),
        ("unsigned marker frames", "at<int16_t>(record, offset)", "at<uint16_t>(record, offset)"),
        ("lose broadcast recipient bit", "swingRecipient(at<uint32_t>(swing, 0x88), 0x40)", "swingRecipient(at<uint32_t>(swing, 0x88), 0)"),
        ("swap clip weights", "at<float>(swing, 0x18), at<float>(swing, 0x1C));", "at<float>(swing, 0x1C), at<float>(swing, 0x18));"),
    ]),
    ("player_advance_swing_phase", [
        ("skip triggered flag clear", "at<uint8_t>(swing, 0x8D) = 0;", "at<uint8_t>(swing, 0x8D) = 1;"),
        ("swap phase update paths", "if (at<uint8_t>(swing, 0x8C))", "if (!at<uint8_t>(swing, 0x8C))"),
        ("lose empty completion", "at<float>(swing, 0x1C) = 1.0f;", "at<float>(swing, 0x1C) = 0.0f;"),
        ("omit frozen phase retreat", "at<float>(swing, 0x1C) -= 9.999999747378752e-05f;", "at<float>(swing, 0x1C) -= 0.0f;"),
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
