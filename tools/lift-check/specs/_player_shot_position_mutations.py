import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_shot_target_position", "void* pongPlayer_ComputeTargetPosition(", [
        ("wrong cache gate", "entry[0xD8] != 0", "entry[0xD8] == 0"),
        ("full-word force", "static_cast<uint8_t>(force) == 0", "force == 0"),
        ("ignore force", "static_cast<uint8_t>(force) == 0", "true"),
        ("wrong cached vector", "entry + 0x120, sizeof result", "entry + 0x110, sizeof result"),
        ("wrong height", "table[5]", "table[4]"),
        ("wrong radius field", "shape[2]", "shape[1]"),
        ("drop radius", "height + radius", "height"),
        ("wrong side", "entry[0xD6] != 0", "entry[0xD6] == 0"),
        ("wrong factor", "deltaX * (factors[0] + 1.0f)", "deltaX * (factors[1] + 1.0f)"),
        ("wrong interpolation range", "__builtin_fmaf(x, 0.5f, baseX)", "__builtin_fmaf(x, 1.0f, baseX)"),
        ("wrong return", "return output;", "return object;"),
    ]),
    ("player_shot_position_two_offsets", "void playerShotEntry_UpdatePositionWithOffsets(", [
        ("drop force", "point, entry, force)", "point, entry, 0)"),
        ("wrong first offset", "entry + 0xE0, sizeof first", "entry + 0xF0, sizeof first"),
        ("drop second addition", "addVmxRows(result, partial, second);", "__builtin_memcpy(result, partial, sizeof result);"),
        ("cache offset before query",
         '    pongPlayer_ComputeTargetPosition(point, entry, force);\n    __builtin_memcpy(first, entry + 0xE0, sizeof first);',
         '    __builtin_memcpy(first, entry + 0xE0, sizeof first);\n    pongPlayer_ComputeTargetPosition(point, entry, force);'),
    ]),
    ("player_shot_position_one_offset", "void playerShotEntry_UpdatePositionWithOffset(", [
        ("force recomputation", "point, entry, 0)", "point, entry, 1)"),
        ("wrong destination", "entry + 0x20, result", "entry + 0x30, result"),
    ]),
    ("player_shot_position_one_offset", "void addVmxRows(", [
        ("omit VMX flushing", "rage::vmxAddFloat(first[lane], second[lane])", "first[lane] + second[lane]"),
        ("drop fourth lane", "lane < 4", "lane < 3"),
    ]),
]

def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_shot_position.cpp").read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        assert source.count(body) == 1, signature
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                    Options(seed=1, patches=((body, body.replace(old, new, 1)),))).run()
            first = output.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith("FAIL ")
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
