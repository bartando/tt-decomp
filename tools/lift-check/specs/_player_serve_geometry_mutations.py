"""Behavioral proof for serve pose publication and bone matrix sampling."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_publish_serve_pose", [
        ("wrong output slot", "g_playerSlotPoseData + slot * 80", "g_playerSlotPoseData"),
        ("omit active flag", "output[0] = 1;", "output[0] = 0;"),
        ("wrong clip kind", "at<int32_t>(clip, 0x10) == 1", "at<int32_t>(clip, 0x10) != 0"),
        ("unsigned marker", "at<int32_t>(clip, 0x1C)", "at<uint32_t>(clip, 0x1C)"),
        ("omit duration", "markerSeconds / duration", "markerSeconds"),
        ("drop target w", "addVmx(origin._pad, target._pad)", "origin._pad"),
        ("drop root w", "addVmx(origin._pad, motion._pad)", "origin._pad"),
    ]),
    ("player_serve_bone_matrix", [
        ("wrong player slot", "const uint32_t playerSlot = at<uint32_t>(blender, 8);", "const uint32_t playerSlot = 0;"),
        ("wrong bone id", "at<uint32_t>(blender, 0x1C)", "0"),
        ("omit bone matrix", "phBoundCapsule_0880_g(skeleton, output, at<uint32_t>(blender, 0x1C));", "(void)skeleton;"),
        ("omit time fraction", "const float time = remaining * ballTime;", "const float time = ballTime;"),
        ("omit translation x", "addVmx(origin.x, multiplyVmx(motion.x, time))", "origin.x"),
        ("omit translation w", "addVmx(origin._pad, multiplyVmx(motion._pad, time))", "origin._pad"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_serve_hit_point.cpp").read_text()
    count = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, f"missing mutation anchor: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
