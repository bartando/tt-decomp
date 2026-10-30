"""Run from the root with PYTHONPATH=tools/lift-check and the checker venv.

Only build-cache copies are patched; only behavioral FAIL (rc=1) counts.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("invert inner X test", "pos->x <= g_kCourtBoxInnerMax.x", "pos->x > g_kCourtBoxInnerMax.x"),
    ("exclude inner X face", "pos->x <= g_kCourtBoxInnerMax.x", "pos->x < g_kCourtBoxInnerMax.x"),
    ("invert outer X test", "pos->x <= g_kCourtBoxOuterMax.x", "pos->x > g_kCourtBoxOuterMax.x"),
    ("exclude outer Z face", "pos->z >= g_kCourtBoxOuterMin.z", "pos->z > g_kCourtBoxOuterMin.z"),
    ("use outer maximum as inner minimum", "pos->x >= g_kCourtBoxInnerMin.x", "pos->x >= g_kCourtBoxOuterMax.x"),
    ("interpolate along X", "const float offset = pos->z - g_kCourtBoxOuterMax.z;", "const float offset = pos->x - g_kCourtBoxOuterMax.z;"),
    ("reverse interpolation denominator", "g_kCourtBoxOuterMin.z - g_kCourtBoxOuterMax.z;", "g_kCourtBoxOuterMax.z - g_kCourtBoxOuterMin.z;"),
    ("scale slope by inner Y", "const float maxY = g_kCourtBoxOuterMax.y * fraction;", "const float maxY = g_kCourtBoxInnerMax.y * fraction;"),
    ("zero flat-depth fallback", "float fraction = g_kFloatConst_D108;", "float fraction = 0.0f;"),
    ("divide by flat depth", "if (g_kCourtBoxOuterMax.z != g_kCourtBoxOuterMin.z) {", "if (true) {"),
    ("exclude sloped face", "return pos->y <= maxY;", "return pos->y < maxY;"),
    ("let unordered X through outer box", "pos->x <= g_kCourtBoxOuterMax.x && pos->x >= g_kCourtBoxOuterMin.x", "!(pos->x > g_kCourtBoxOuterMax.x) && !(pos->x < g_kCourtBoxOuterMin.x)"),
]


def main():
    spec = Path(__file__).with_name("player_is_in_table_avoidance_volume.py")
    source = (spec.parents[3] / "src/game/player/pong_player.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
