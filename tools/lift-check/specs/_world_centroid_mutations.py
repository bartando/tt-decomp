"""Break the cache guard and output location; only behavioral FAILs count."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = Path(__file__).resolve().parents[3] / "src/physics/ph_physics.cpp"
CASES = [
    ("accept only enable value 1", "static_cast<const uint8_t*>(self)[7] != 0",
     "static_cast<const uint8_t*>(self)[7] == 1"),
    ("wrong enable byte", "static_cast<const uint8_t*>(self)[7] != 0",
     "static_cast<const uint8_t*>(self)[6] != 0"),
    ("overwrite local centroid", "reinterpret_cast<float*>(static_cast<char*>(self) + 0x40)",
     "reinterpret_cast<float*>(static_cast<char*>(self) + 0x30)"),
]


def main():
    source = SOURCE.read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, (name, source.count(old))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ph_bound_transform_world_centroid.py"),
                         Options(trials=600, seed=1, patches=((old, new),))).run()
        report = output.getvalue()
        caught = rc == 1 and "the lift faulted" not in report
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
        if not caught:
            print(report)
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
