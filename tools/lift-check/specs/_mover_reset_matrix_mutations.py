"""Mutation checks for the shared mover reset and rest-matrix corrections."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("mover_reset", [
        ("wrong table stride", "table[m_creatureIndex + 0x21]", "table[(m_creatureIndex + 0x21) * 4]"),
        ("wrong horizontal axis", "m_posY = initMatrix[14]", "m_posY = initMatrix[13]"),
        ("teleport missing player", "table[index + 0x1D] != 0", "table[index + 0x1D] == 0"),
        ("clear unrelated flag", "m_flags &= 0xF9", "m_flags = 0"),
        ("drop motion buffer reset", "memset(m_unk60, 0, sizeof(m_unk60))", "(void)m_unk60"),
    ]),
    ("mover_calc_init_matrix", [
        ("ignore saved alternate", "static_cast<uint8_t>(alternate) && g_playerModeTransitionFlag", "false"),
        ("test full alternate word", "static_cast<uint8_t>(alternate)", "alternate"),
        ("choose wrong court edge", "side ? lower[2] : upper[2]", "side ? upper[2] : lower[2]"),
        ("ignore character mirror", "if (side != moverAt<uint8_t>(moverAt<void*>(character, 0x2C), 0x104))", "if (false)"),
        ("lose returned destination", "return outMatrix;", "return nullptr;"),
        ("leave mirror w lane", "lane < 4", "lane < 3"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/creature/pong_creature.cpp").read_text()
    total = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, label
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, trials=1000,
                                     patches=((source, source.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
