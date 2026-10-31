"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_gd_input_seq_update_mutations.py

Patch compiled build-cache copies only. Every mutation must produce behavioral
FAIL (exit 1); BUILD, SPEC and UNSUPPORTED do not count as detection.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("retain stale completion bit", "state->flags &= ~8u;", "/* omit completion clear */"),
    ("ignore active gate", "!(state->flags & 1)", "false"),
    ("ignore valid gate", "!(state->flags & 4)", "false"),
    ("miss enable transition", "if (enabled != ((state->flags & 2) != 0))",
     "if (false)"),
    ("normalize noncanonical enable byte", "const uint32_t enabled = data->enabled;",
     "const uint32_t enabled = data->enabled != 0;"),
    ("always read first step", "data->steps + stepIndex", "data->steps"),
    ("exclude latest boundary", "if (!(elapsed > step->latest))",
     "if (!(elapsed >= step->latest))"),
    ("time out on unordered latest", "if (!(elapsed > step->latest))",
     "if (elapsed <= step->latest)"),
    ("use unsigned button range", "button <= lastButton;",
     "static_cast<uint32_t>(button) <= static_cast<uint32_t>(lastButton);"),
    ("exclude final button", "button <= lastButton;", "button < lastButton;"),
    ("keep polling after unexpected input", "button == step->button || !otherPressed",
     "true"),
    ("skip expected button after unexpected input", "button == step->button || !otherPressed",
     "!otherPressed"),
    ("wrong button stride", "input->buttons + physical * 4", "input->buttons + physical * 3"),
    ("exclude earliest boundary", "if (elapsed >= step->earliest)",
     "if (elapsed > step->earliest)"),
    ("accept unordered earliest", "if (elapsed >= step->earliest)",
     "if (!(elapsed < step->earliest))"),
    ("accept simultaneous wrong button", "if (!otherPressed)", "if (true)"),
    ("advance two steps", "state->step = stepIndex + 1;", "state->step = stepIndex + 2;"),
    ("omit completion callback",
     "sysCallback_Invoke(callback, const_cast<InputSequenceData*>(state->data));",
     "/* omit callback */"),
    ("publish completion bit after callback",
     "state->flags |= 8;\n                sysCallback_Invoke(callback, const_cast<InputSequenceData*>(state->data));",
     "sysCallback_Invoke(callback, const_cast<InputSequenceData*>(state->data));\n                state->flags |= 8;"),
    ("reset index before callback",
     "state->flags |= 8;", "state->flags |= 8;\n                state->step = 0;"),
    ("leave final index set", "    state->step = 0;\n}", "    /* omit final index reset */\n}"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/input/input_sequence.cpp").read_text()
    spec = Path(__file__).with_name("gd_input_seq_update.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
