"""The checked-cast spec must reject incorrect arguments and return gates."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong type token", "IsType(g_cameraNodeType)", "IsType(0)"),
    ("ignore low byte", "static_cast<uint8_t>(matches) != 0", "matches != 0"),
    ("reverse type result", "!= 0 ? object : nullptr", "== 0 ? object : nullptr"),
]


def main():
    for label, old, new in MUTATIONS:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("camera_node_checked_cast.py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
