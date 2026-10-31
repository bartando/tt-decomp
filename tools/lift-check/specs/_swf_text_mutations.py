"""Behavioral mutation checks for the three pooled-text entry points."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "swf_copy_string": [
        ("omit terminator chunk", "std::strlen(text) / 12 + 1", "(std::strlen(text) + 11) / 12"),
        ("wrong count direction", "--pool->freeCount;", "++pool->freeCount;"),
        ("lose list advance", "pool->freeList = rage::load_ptr32<TextChunk>(chunk, 0);", "/* lost free link */"),
        ("truncate chunk bytes", "std::memcpy(chunk->bytes, text, sizeof(chunk->bytes));",
         "std::memcpy(chunk->bytes, text, sizeof(chunk->bytes) - 1);"),
    ],
    "swf_release_text": [
        ("omit recursive release", "if (chunk->next) swfReleaseText(chunk->next.get(), 1);", "/* lost tail release */"),
        ("wrong count direction", "++pool->freeCount;", "--pool->freeCount;"),
        ("lose free-list head", "pool->freeList = chunk;", "/* lost head */"),
        ("clear data beyond free link", "std::memcpy(chunk->bytes, &nextFree, sizeof(nextFree));",
         "std::memset(chunk->bytes, 0, 12); std::memcpy(chunk->bytes, &nextFree, sizeof(nextFree));"),
    ],
    "swf_intern_text": [
        ("last hole instead of first", "freeSlot == -1 && slot[0] == '\\0'", "slot[0] == '\\0'"),
        ("skip table tail", "i < 128", "i < 64"),
        ("reject existing strings", "std::strcmp(slot, text) == 0", "false"),
        ("short copy bound", "std::strncpy(slot, text, 64);", "std::strncpy(slot, text, 63);"),
    ],
}


def main():
    for spec, cases in CASES.items():
        for label, old, new in cases:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith("FAIL ")
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(output.getvalue())
                return 1
    print(f"Caught {sum(map(len, CASES.values()))} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
