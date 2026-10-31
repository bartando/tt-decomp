"""Reject broken registry lookups; only behavioral FAIL (exit 1) is a catch."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/core/indexed_registry.cpp").read_text()
    start = source.index('extern "C" void* pg_C2A0_g(')
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    mutants = [
        ("always miss", "    RegistryNode* node =", "    return nullptr;\n    RegistryNode* node ="),
        ("off-by-one key", "while (node != nullptr", "++index;\n    while (node != nullptr"),
        ("do not walk", "node != nullptr && index != 0", "false"),
        ("reject high-bit keys before walking", "    while (node != nullptr", "    if (index > 0x7FFFFFFFu) return node;\n    while (node != nullptr"),
    ]
    for label, old, new in mutants:
        assert old in body, label
        for seed in (1, 2):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name("registry_get_child.py"),
                             Options(trials=128, seed=seed,
                                     patches=((body, body.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: seed {seed}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
    print(f"Caught {len(mutants) * 2}/{len(mutants) * 2} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
