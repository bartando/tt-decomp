"""Each broken lifecycle contract must yield behavioral FAIL."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("anim_blender_reset", "wrong phase", "state->phase = 0.0f;", "state->phase = 1.0f;"),
    ("anim_blender_reset", "lost slot sentinel", "state->slots[2] = 0xFFFF;", "state->slots[2] = 0;"),
    ("anim_blender_reset", "lost notification lane", "i < 4; ++i", "i < 3; ++i"),
    ("anim_blender_stop", "ignore inactive state", "if (state->status == 0) return;", "if (false) return;"),
    ("anim_blender_stop", "lose notification", "state->flags & 0x800u", "state->flags & 0x80u"),
    ("anim_blender_stop", "keep running flag", "state->flags &= ~1u;", "state->flags |= 1u;"),
    ("anim_blender_start_clip", "wrong protection bit", "state->flags & 0x100u", "state->flags & 0x200u"),
    ("anim_blender_start_clip", "lose clip", "state->clip = clip;", "state->clip = nullptr;"),
    ("anim_blender_start_clip", "full-word loop flag", "static_cast<uint8_t>(flags) != 0", "flags != 0"),
    ("callback_destroy", "wrong callback object", "cleanup(callback);", "cleanup(nullptr);"),
]


def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
