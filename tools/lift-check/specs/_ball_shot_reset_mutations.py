import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("omit first vector", "shot->v10 = {};", ""),
    ("retain vector w", "shot->v50 = {};", "shot->v50.x = shot->v50.y = shot->v50.z = 0.0f;"),
    ("wrong vector pair row", "shot->v30[0] = {};", "shot->v30[1] = {};"),
    ("wrong index", "shot->i20 = 0;", "shot->i20 = 1;"),
    ("wrong weight", "shot->f70[3] = 1.0f;", "shot->f70[3] = 0.0f;"),
    ("wrong shot id", "shot->hB2 = 0xFFFF;", "shot->hB2 = 0;"),
    ("constant instead of data", "shot->f70[5] = g_floatConstant4;", "shot->f70[5] = 4.0f;"),
    ("clear scalar hole", "shot->f70[1] = 0.0f;", "shot->f70[1] = 0.0f; shot->f70[2] = 0.0f;"),
    ("clear padding", "shot->bB4 = 0;", "shot->bB4 = 0; shot->_padB5 = 0;"),
]

def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_shot_initialize.cpp").read_text()
    body = source[source.index("void bpShot_Reset("):]
    for label, old, new in CASES:
        assert body.count(old) == 1, label
        patch = (body, body.replace(old, new, 1))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_shot_reset.py"), Options(seed=1, patches=(patch,))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
