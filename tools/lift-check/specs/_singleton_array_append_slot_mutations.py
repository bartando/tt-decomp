"""Check that the array spec rejects the old lift's main mistakes."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("grow when count exceeds capacity", "array->count == array->capacity", "array->count >= array->capacity"),
    ("wrong entry stride", "capacity * sizeof(SingletonEntry) + 4", "capacity * 16 + 4"),
    ("zero the untouched middle word", "entries[i].instance = nullptr;", "entries[i].instance = nullptr; entries[i].hash = 0;"),
    ("reuse names instead of duplicating", "static_cast<char*>(rage_strDuplicate(array->entries[i].name))", "const_cast<char*>(array->entries[i].name)"),
    ("lose the payload", "entries[i].instance = array->entries[i].instance;", "entries[i].instance = nullptr;"),
    ("skip old array destruction", "xmlTreeEntry_DeleteArray(reinterpret_cast<xmlTreeEntry*>(array->entries));", ";"),
    ("return the next slot", "array->entries + array->count;", "array->entries + array->count + 1;"),
    ("omit count increment", "array->count = static_cast<uint16_t>(array->count + 1);", ";"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/memory/singleton_array.cpp").read_text()
    spec = Path(__file__).with_name("singleton_array_append_slot.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f'{"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
