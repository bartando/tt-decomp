"""Break queue and delivery contracts; only behavioral FAIL is accepted."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("game_message_guard_enter", "lock twice", "guard->entered == 0", "true"),
    ("game_message_guard_leave", "unlock noncanonical flags", "guard->entered == 1", "guard->entered != 0"),
    ("game_message_dispatch", "resnapshot category", "g_ui_object_types[i] & category", "g_ui_object_types[i] & (1u << (message->id >> 11))"),
    ("game_message_dispatch", "lose wildcard", "(flags & 0x80) == 0", "true"),
    ("game_message_dispatch", "lose active receiver", "(receiverFlags & 0x80) == 0", "true"),
    ("game_message_dispatch", "cache registry count", "count = g_ui_state_counter;\n    }", "/* stale count */\n    }"),
    ("game_message_post", "use whole count", "static_cast<uint8_t>(payloadWords);", "payloadWords;"),
    ("game_message_post", "wrong queue bank", "uint32_t(g_gameMessageQueueBank) * 1024", "uint32_t(g_gameMessageQueueBank) * 512"),
    ("game_message_post", "wrong payload size", "payload, words * 4", "payload, words"),
    ("game_message_post", "wrong immediate flag", "flags & 0x40", "flags & 0x80"),
    ("game_message_post", "forget header word", "initialWords + words + 1", "initialWords + words"),
    ("game_message_post", "omit dispatch", "if (immediate) DispatchGameMessage(message);", "if (immediate) {}"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/game/game_message.cpp").read_text()
    for spec, label, old, new in CASES:
        assert old in source, label
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
