"""Require behavioral FAIL for deliberately broken Y-axis rotations."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("rotate Y row instead of Z", "matrix[8 + lane]", "matrix[4 + lane]"),
    ("lose final difference negation", "matrix[lane] = -flushRotationVmx", "matrix[lane] = flushRotationVmx"),
    ("drop row padding lanes", "lane < 4", "lane < 3"),
    ("round double input angle", "cosSin(&cosine, &sine, angle);", "cosSin(&cosine, &sine, static_cast<float>(angle));"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/mat33.cpp").read_text()
    start = source.index("void mat33RotateY(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    count = 0
    for label, old, new in CASES:
        assert old in body, f"missing anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("rage_mat33_rotate_y.py"),
                         Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            return 1
        count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
