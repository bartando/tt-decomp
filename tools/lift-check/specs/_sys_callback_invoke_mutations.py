"""All callback modes must reject their own cache-only broken dispatches."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("skip bound callbacks", "if (callback->target)", "if (false)"),
    ("skip free callbacks", "if (callback->target)", "if (true)"),
    ("bound no-argument target lost", "(callback->function)(callback->target);", "(callback->function)(callback->storedArgument);"),
    ("bound stored argument lost", "callback->target, callback->storedArgument);", "callback->target, argument);"),
    ("bound runtime argument lost", "callback->target, callback->storedArgument, argument);", "callback->target, callback->storedArgument, nullptr);"),
    ("bound two arguments swapped", "callback->target, callback->storedArgument, argument);", "callback->target, argument, callback->storedArgument);"),
    ("bound runtime uses stored", "callback->target, argument);", "callback->target, callback->storedArgument);"),
    ("skip free no-argument callback", "callback->function();", "(void)callback;"),
    ("free stored uses runtime", "(callback->function)(callback->storedArgument);", "(callback->function)(argument);"),
    ("free two arguments swapped", "callback->storedArgument, argument);", "argument, callback->storedArgument);"),
    ("free runtime uses stored", "(callback->function)(argument);", "(callback->function)(callback->storedArgument);"),
    ("call empty and unknown kinds", "switch (callback->kind) {", "switch (callback->kind) {\n        default: callback->function(); break;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/core/rage_core_utils.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("sys_callback_invoke.py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if caught else 'MISSED'} {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
