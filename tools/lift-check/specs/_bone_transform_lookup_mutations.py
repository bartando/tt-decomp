"""Require behavioral FAIL for deliberately broken bone transform lookups."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/anim/bone_transform_lookup.cpp"
CASES = [
    ("lose reference fallback", "__builtin_memcpy(sampled, g_identityMatrixRef, sizeof sampled);", "__builtin_memset(sampled, 0, sizeof sampled);"),
    ("clear preserved row w", "matrix[0] = 1.0f;", "matrix[3] = 0.0f; matrix[0] = 1.0f;"),
    ("omit Y rotation", "rage::mat33RotateY(matrix, at<float>(bone, 0x24));", "(void)matrix;"),
    ("drop translation w", "translated.lane[lane] = translateLane(basis.lane[lane], amount, position.lane[lane]);", "translated.lane[lane] = lane == 3 ? position.lane[3] : translateLane(basis.lane[lane], amount, position.lane[lane]);"),
    ("lose authored translation", "at<MatrixRow>(output, 0x30) = at<MatrixRow>(bone, 0x30);", "at<MatrixRow>(output, 0x30) = {};"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    count = 0
    for label, old, new in CASES:
        assert old in source, f"missing anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("bone_transform_lookup.py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            return 1
        count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
