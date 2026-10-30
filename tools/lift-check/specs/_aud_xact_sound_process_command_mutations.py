"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_aud_xact_sound_process_command_mutations.py

Only build-cache copies are patched. Each mutation must produce behavioral
FAIL (exit 1); BUILD, SPEC and UNSUPPORTED do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("dispatch upper command bits", "command & 0xffff", "command"),
    ("wrong pool for 2000 commands", "opcode < 0x4000 ?", "false ?"),
    ("wrong instance index", ")[params[0]];", ")[(params[0] + 1) % 16];"),
    ("turn load into an unknown command", "case 0x2002:", "case 0x2004:"),
    ("turn empty slot into an unknown command", "    case 0x2003:\n", ""),
    ("wrong play cue", "params[1], params[2], params[3], params[4],",
     "params[1], params[1], params[3], params[4],"),
    ("truncate play spatial flag", "params[7] != 0", "(params[7] & 1) != 0"),
    ("drop ninth play argument", "params[8], params[9]", "0, params[9]"),
    ("truncate tenth play argument", "params[9] != 0", "static_cast<uint8_t>(params[9])"),
    ("resume instead of pause", "aud_F5F0(getInstance());", "aud_F670(getInstance());"),
    ("wrong volume offset", "params[1] + 5000u", "params[1] + 5001u"),
    ("unsigned volume conversion", "static_cast<int32_t>(params[1] + 5000u)", "params[1] + 5000u"),
    ("skip volume backend update", "        audInstance_UpdateParameters(instance);", ""),
    ("unsigned parameter conversion", "aud_FD10(getInstance(), static_cast<float>(static_cast<int32_t>(params[1])))",
     "aud_FD10(getInstance(), static_cast<float>(params[1]))"),
    ("swap position coordinates", "position[1] = static_cast<float>(static_cast<int32_t>(params[2]))",
     "position[1] = static_cast<float>(static_cast<int32_t>(params[1]))"),
    ("drop position handedness conversion", "position[2] = -(static_cast<float>",
     "position[2] = (static_cast<float>"),
    ("skip control group write", "            instance->controlGroup = params[1];", ""),
    ("truncate control flag", "instance->controlEnabled = params[2] != 0;",
     "instance->controlEnabled = static_cast<uint8_t>(params[2]);"),
    ("wrong diagnostic opcode", "params[0], opcode);", "params[0], command);"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/audio/aud_instance_update.cpp").read_text()
    spec = Path(__file__).with_name("aud_xact_sound_process_command.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=256, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
