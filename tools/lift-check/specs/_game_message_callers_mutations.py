"""Require behavioral FAIL for broken message payloads and callback byte reloads."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_notify_slot_change", "src/game/player/pong_player.cpp", [
        ("send column as address", "PostGameMessage(4130, slotMask, 1, &columnIndex);", "PostGameMessage(4130, slotMask, 1, reinterpret_cast<const void*>(static_cast<uintptr_t>(columnIndex)));"),
        ("omit dirty sync", "SyncByteField(dirtyAddr, syncBuf);", "(void)syncBuf;"),
    ]),
    ("player_reset_slot_tracking", "src/game/player/pong_player.cpp", [
        ("drop reset payload", "PostGameMessage(4131, static_cast<int>(bitMask), 1, &slotResult);", "PostGameMessage(4131, static_cast<int>(bitMask), 1, nullptr);"),
    ]),
    ("player_sync_byte_field", "src/game/player/pong_player.cpp", [
        ("cache source across callback", "tgt[0] = *static_cast<uint8_t*>(source);", "tgt[0] = newVal;"),
    ]),
    ("message_signal_ready_use", "src/game/message.cpp", [
        ("drop negative-one payload", "PostGameMessage(10244, 64, 1, &negOne);", "PostGameMessage(10244, 64, 1, nullptr);"),
        ("wrong formatted event type", 'const_cast<char*>("i")', 'const_cast<char*>("f")'),
        ("wrong spectator mode", "} else if (lbl_825C9A2C == 2) {", "} else if (lbl_825C9A2C == 1) {"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, path, mutations in CASES:
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert old in source, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
