"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this_file.

Only the build-cache copy is broken. A behavioral FAIL counts as caught;
BUILD, SPEC, UNSUPPORTED and crashes do not.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("ignore skip flag", "skipStateChanges == 0 &&", "true &&"),
    ("ignore global override", "g_pongControlGroupOverride == 0", "true"),
    ("lose player flag publication", "g_pongControlGroupPlayerFlag = playerFlag;",
     "g_pongControlGroupPlayerFlag = 0;"),
    ("omit first state selector", "        pg_6E58_wrh(this);", "        /* omitted selector */"),
    ("cache type before second selector", "        game_6B90(this);\n        // Reload the type after the helper; it may have changed the group.\n        const int32_t type = group->type;",
     "        const int32_t type = group->type;\n        game_6B90(this);"),
    ("wrong type-11 target", "setMaster(376, 380,", "setMaster(380, 380,"),
    ("omit type-7 event fade", "(type == 0 || type == 7)", "(type == 0)"),
    ("ignore type-14 event gate", "type == 14 && g_pongControlGroupEvent6473 != 0",
     "type == 14"),
    ("invert player gate", "playerFlag == 0 && master.overridden == 0",
     "playerFlag != 0 && master.overridden == 0"),
    ("wrong type-10 shared rate", "setMaster(400, 392,", "setMaster(400, 404,"),
    ("lose type-10 fallback rate", "setMaster(400, 392, g_pongControlGroupFallbackRate);",
     "setMaster(400, 392, 1.0f);"),
    ("overwrite earlier selector", "master.overridden == 0) {\n            setMaster(376,",
     "true) {\n            setMaster(376,"),
    ("swap default target and rate", "control.target = control.defaultTarget;",
     "control.target = control.defaultRate;"),
    ("retain override flags", "        control.overridden = 0;", "        /* missing clear */"),
    ("include epsilon equality", "__builtin_fabsf(control.current - control.target) > epsilon",
     "__builtin_fabsf(control.current - control.target) >= epsilon"),
    ("omit descending fades", "__builtin_fabsf(control.current - control.target) > epsilon",
     "(control.current - control.target) > epsilon"),
    ("omit effect channel", "i < 4; ++i", "i < 3; ++i"),
    ("wrong approach rate", "control.target, control.rate, g_pongControlGroupDeltaTime",
     "control.target, control.defaultRate, g_pongControlGroupDeltaTime"),
    ("omit debug logging", "reinterpret_cast<const uint8_t*>(this)[165] != 0",
     "false"),
    ("log target instead of current", "const double value = control.current;",
     "const double value = control.target;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/pong_game.cpp").read_text()
    spec = Path(__file__).with_name("pong_control_group_update.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        detected = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
        if not detected:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
