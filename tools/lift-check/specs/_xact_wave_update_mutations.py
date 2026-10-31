"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xact_wave_update_mutations.py

Only build-cache copies are patched. Only behavioral FAIL (exit 1) counts;
BUILD, SPEC and UNSUPPORTED errors do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("ignore flag 4", "self->flags & 0x14", "self->flags & 0x10"),
    ("ignore released flag", "self->flags & 0x14", "self->flags & 4"),
    ("consume stop value 2 instead of 1", "&self->stopRequested, 1u, 0u", "&self->stopRequested, 2u, 0u"),
    ("ignore noncanonical stop requests", "&self->stopRequested, 1u, 0u) != 0", "&self->stopRequested, 1u, 0u) == 1"),
    ("keep processing an already stopped wave", "if (self->state == 5) return;", "/* lost stopped guard */"),
    ("notify for negative state", "self->state >= 3 && self->state < 5", "static_cast<uint32_t>(self->state) >= 3"),
    ("skip state 4 notification", "self->state >= 3 && self->state < 5", "self->state == 3"),
    ("wrong stop notification", "atSingleton_A6C8(self, 13)", "atSingleton_A6C8(self, 12)"),
    ("notify before setting stopped state", "            self->state = 5;\n            atSingleton_A6C8", "            atSingleton_A6C8"),
    ("retain notification callback state", "        self->state = 5;\n    };", "        /* lost final state write */\n    };"),
    ("retain detached object pointer", "self->retainedObject = nullptr;", "/* lost retained clear */"),
    ("detach through wrong vtable slot", "(table[31])(instance, retained)", "(table[30])(instance, retained)"),
    ("destroy wrong retained object", "(table[2])(retained, 0, 0)", "(table[2])(retained, 1, 0)"),
    ("retain instance after detach", "            self->instance = nullptr;", "            /* lost instance clear */"),
    ("skip finalizer after detach", "            xactWave_Finalize(self);\n        } else if",
     "            /* lost finalizer */\n        } else if"),
    ("retire the voice instead of instance", "atSingleton_2378_g(instance);", "atSingleton_2378_g(self->voice);"),
    ("consume wrong update request value", "&self->updateRequested, 1u, 0u", "&self->updateRequested, 2u, 0u"),
    ("ignore noncanonical update requests", "&self->updateRequested, 1u, 0u) != 0", "&self->updateRequested, 1u, 0u) == 1"),
    ("skip instance update", "(table[8])(instance)", "(table[7])(instance)"),
    ("poll only state 3", "self->state != 3 && self->state != 4", "self->state != 3"),
    ("poll state 2", "self->state != 3 && self->state != 4", "self->state != 2 && self->state != 4"),
    ("reject successful nonzero HRESULT", "result < 0 ||", "result != 0 ||"),
    ("accept failed HRESULT", "result < 0 ||", "result > 0 ||"),
    ("require completion value 1", "completed == 0", "completed != 1"),
    ("ignore completion pause flag", " || (self->flags & 0x80)", ""),
    ("use wrong completion pause flag", "self->flags & 0x80", "self->flags & 0x40"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/audio/xact_sound.cpp").read_text()
    spec = Path(__file__).with_name("xact_wave_update.py")
    for name, old, new in MUTATIONS:
        # The retire call occurs on both the requested and completed paths;
        # Options.patches deliberately changes only its first occurrence.
        expected = 2 if name == "retire the voice instead of instance" else 1
        assert source.count(old) == expected, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        lines = output.getvalue().splitlines()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {lines[0] if lines else 'no output'}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
