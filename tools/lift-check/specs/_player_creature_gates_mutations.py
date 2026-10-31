"""Require behavioral failures for broken primary and secondary state gates."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_is_creature_state_ready", "IsCreatureStateReady", "ignore active byte",
     "if (!m_bActive)", "if (false)"),
    ("player_is_creature_state_ready", "IsCreatureStateReady", "invert readiness",
     "m_pCreatureState->IsReady() != 0", "m_pCreatureState->IsReady() == 0"),
    ("player_is_creature_state_ready", "IsCreatureStateReady", "accept only canonical true",
     "m_pCreatureState->IsReady() != 0", "m_pCreatureState->IsReady() == 1"),
    ("player_is_creature_state2_active", "IsCreatureState2Active", "accept missing state",
     "if (!m_pCreatureState2) {\n        return false;", "if (!m_pCreatureState2) {\n        return true;"),
    ("player_is_creature_state2_active", "IsCreatureState2Active", "old reversed slot 6",
     "m_pCreatureState2->IsActive() != 0", "m_pCreatureState2->IsActive() == 0"),
    ("player_is_creature_state2_active", "IsCreatureState2Active", "skip slot 7",
     "return m_pCreatureState2->IsReady() != 0;", "return true;"),
    ("player_is_creature_state2_active", "IsCreatureState2Active", "cache secondary across callback",
     "    if (!m_pCreatureState2)", "    auto* cached = m_pCreatureState2;\n    if (!cached)"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/game/player/pong_player.cpp").read_text()
    for spec, member, label, old, new in CASES:
        start = source.index(f"bool pongPlayer::{member}() const {{")
        end = source.index("\n}", start) + 2
        body = source[start:end]
        assert body.count(old) == 1, label
        changed = body.replace(old, new)
        if label == "cache secondary across callback":
            changed = changed.replace("return m_pCreatureState2->IsReady()", "return cached->IsReady()")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((body, changed),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
