import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "player_court_profile_bounds": ("src/game/player/player_court.cpp", "void* pongPlayer_GetCourtBounds(", [
        ("full-word side", "static_cast<uint8_t>(side) != 0", "side != 0"),
        ("full-word profile", "static_cast<uint8_t>(useProfiles) == 0", "useProfiles == 0"),
        ("wrong base profile", "== 0 ? 8", "== 0 ? 11"),
        ("wrong center scale", "table[6] * g_phCapsuleShapeK", "table[6] * 0.25f"),
        ("positive lower width", "lo[0] = negateFloatWord(positiveWidth);", "lo[0] = positiveWidth;"),
        ("swap depth extents", "profile + (flipped ? 1 : 2)", "profile + (flipped ? 2 : 1)"),
        ("wrong subtract center", "table[lowDepth], halfLength, -center", "table[lowDepth], halfLength, center"),
        ("wrong return", "return object;", "return lower;"),
    ]),
    "player_court_cell_position": ("src/game/player/player_court.cpp", 'extern "C" void* pongPlayer_E7B0_g(', [
        ("wrong profile flag", "target[1], 1)", "target[1], 0)"),
        ("wrong factors", "target + 4, sizeof factors", "target + 8, sizeof factors"),
        ("wrong side after bounds", "factors, target[0], result", "factors, target[1], result"),
        ("wrong embedded result", "target + 0x10", "target + 0x14"),
        ("cache factors before bounds",
         '    pongPlayer_GetCourtBounds(g_pTableDims, target[0], lower, upper, target[1], 1);\n    float factors[2];\n    __builtin_memcpy(factors, target + 4, sizeof factors);',
         '    float factors[2];\n    __builtin_memcpy(factors, target + 4, sizeof factors);\n    pongPlayer_GetCourtBounds(g_pTableDims, target[0], lower, upper, target[1], 1);'),
    ]),
    "player_court_build_grid": ("src/game/player/player_court.cpp", "void pongPlayer_E008_g(", [
        ("extra outer row", "row < 3", "row < 4"),
        ("extra inner column", "column < 3", "column < 4"),
        ("missing corner", "corner < 4", "corner < 3"),
        ("wrong corner radius", "1.0f / 6.0f", "1.0f / 8.0f"),
        ("wrong row scale", "const float rowCenter = ((float(row) + float(row + 1)) * scale) * 0.5f;", "const float rowCenter = ((float(row) + float(row + 1)) * scale) * 0.25f;"),
        ("wrong second grid offset", "cell + 0x380 + corner * 16", "cell + 0x390 + corner * 16"),
        ("wrong side metadata", "cell[0] = static_cast<uint8_t>(side);", "cell[0] = 0;"),
        ("wrong mirrored variant", "cell[0x361] = target[0x3B0];", "cell[0x361] = 0;"),
    ]),
    "player_court_apply_cell_position": ("src/game/player/pong_player.cpp", "vec3* pongPlayer::UpdatePositionFromSwingTarget(", [
        ("wrong row stride", "row * 3u + column", "row * 2u + column"),
        ("wrong cell base", "+ 0x3D0u", "+ 0x3E0u"),
        ("wrong live offset", "self + 0x370, sizeof offset", "self + 0x360, sizeof offset"),
        ("wrong output", "self + 0x340, result", "self + 0x350, result"),
        ("drop fourth lane", "lane < 4", "lane < 3"),
        ("omit VMX flushing", "rage::vmxAddFloat(point[lane], offset[lane])", "point[lane] + offset[lane]"),
        ("wrong return pointer", "return reinterpret_cast<vec3*>(self + 0x340);", "return reinterpret_cast<vec3*>(self + 0x350);"),
    ]),
}

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, (path, signature, mutations) in CASES.items():
        source = (root / path).read_text()
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        assert source.count(body) == 1, spec
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
