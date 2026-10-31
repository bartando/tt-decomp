"""Mutation proof for the creature teleport lifts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_teleport_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [('vtn_gd_player_mgr_dtor',
  'src/game/data/gd_data.cpp',
  'plrPlayerMgr::~plrPlayerMgr(',
  [('retain manager singleton', 'g_plrPlayerMgr_state = nullptr;', '(void)g_plrPlayerMgr_state;')]),
 ('pong_match_get_character_for_slot',
  'src/game/player/pong_player.cpp',
  'void* pongMatch_GetCharacterForSlot(',
  [('reject odd slots', 'if (!g_plrPlayerMgr_state)', 'if (!g_plrPlayerMgr_state || (playerSlot & 1))'),
   ('read character zero', 'characterIndex * 4u', '0u')])]

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip declarations: each definition begins at column zero.
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) >= 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            first = report.splitlines()[0] if report else "no checker output"
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
