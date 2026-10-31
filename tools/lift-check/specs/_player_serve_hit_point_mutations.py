"""Cache-only mutants must fail the hit-point behavioral comparisons."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_sample_serve_hit", [
        ("wrong hit index", "0x2C)[hitIndex]", "0x2C)[0]"),
        ("ignore current ball time", "if (void* instance = *g_ppBallInst)", "if (void* instance = nullptr)"),
        ("ignore contact lead time", "ballTime + g_serveContactTimeBias", "ballTime"),
        ("scale position instead of velocity", "const vec3 velocity = at<vec3>(hit, 0x40);", "const vec3 velocity = at<vec3>(hit, 0x30);"),
        ("drop vector w", "addVmx(base._pad, multiplyVmx(velocity._pad, time))", "base._pad"),
        ("lose output return", "    return output;", "    return nullptr;"),
    ]),
    ("player_serve_world_hit_point", [
        ("wrong sample index", "at<uint32_t>(animation, 0x28)", "0"),
        ("omit half-turn", "if (at<float>(animation, 0x48) < 0.0f)", "if (false)"),
        ("rotate unordered position", "at<float>(animation, 0x48) < 0.0f", "!(at<float>(animation, 0x48) >= 0.0f)"),
        ("wrong half-turn angle", "3.1415927410125732f", "1.5707963705062866f"),
        ("omit origin addition", "addVmx(sampled.x, origin.x)", "sampled.x"),
        ("drop origin w", "addVmx(sampled._pad, origin._pad)", "sampled._pad"),
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
