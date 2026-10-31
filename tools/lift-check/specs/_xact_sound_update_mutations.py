"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xact_sound_update_mutations.py

Only build-cache copies are changed. A behavioral FAIL (exit 1) counts;
BUILD, SPEC and UNSUPPORTED errors do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("wrong suspended flag", "if (self->flags & 0x20) return;", "if (self->flags & 0x10) return;"),
    ("accept an unready voice", "voice->state != 3", "voice->state != 2"),
    ("wrong ready state", "self->state = 3;", "self->state = 2;"),
    ("wrong ready notification", "msgMsgSink_DC40_g(self->cue, 1)", "msgMsgSink_DC40_g(self->cue, 0)"),
    ("retain deferred start flag", "self->flags &= 0xbf;", "self->flags |= 0x40;"),
    ("continue after failed start", "if (static_cast<int32_t>(msgMsgSink_4EB8_g(self)) < 0) return;",
     "if (static_cast<int32_t>(msgMsgSink_4EB8_g(self)) > 0) return;"),
    ("ignore stopping voices", "voice->state == 4 || voice->state == 5", "voice->state == 4"),
    ("ignore control queue", "if (rage::xactFade_Update(reinterpret_cast<rage::XactFade*>(self->control)))", "if (!rage::xactFade_Update(reinterpret_cast<rage::XactFade*>(self->control)))"),
    ("wrong completed state", "self->state = 6;", "self->state = 5;"),
    ("leave instance counted", "self->countedInstance = 0;", "self->countedInstance = 1;"),
    ("truncate packed category", "msgMsgSink_8B90_g(self->engine, category);",
     "msgMsgSink_8B90_g(self->engine, static_cast<uint8_t>(category));"),
    ("wrong completion vtable slot", "table[27]", "table[26]"),
    ("wrong parameter flag", "self->record[0] & 2", "self->record[0] & 1"),
    ("omit count byte truncation", "uint8_t count = static_cast<uint8_t>(rage_4318(self));",
     "uint32_t count = rage_4318(self);"),
    ("wrong parameter stride", "self->parameters + i * 48", "self->parameters + i * 32"),
    ("cache track successor before callback",
     "    for (auto link = self->tracks.next; link != &self->tracks; link = link->next) {\n"
     "        atSingleton_A5A0_h(link);\n    }",
     "    for (auto link = self->tracks.next; link != &self->tracks;) {\n"
     "        auto next = link->next;\n        atSingleton_A5A0_h(link);\n        link = next;\n    }"),
    ("expire equality too late", "event->time > static_cast<int32_t>(self->engine->time)",
     "event->time >= static_cast<int32_t>(self->engine->time)"),
    ("unsigned expiry comparison", "event->time > static_cast<int32_t>(self->engine->time)",
     "static_cast<uint32_t>(event->time) > self->engine->time"),
    ("leave next neighbor linked", "node->next->previous = node->previous;", "/* lost neighbor write */"),
    ("leave previous neighbor linked", "node->previous->next = node->next;", "/* lost neighbor write */"),
    ("do not self-link detached node", "node->next = node;", "/* lost self-link */"),
    ("wrong lookahead arithmetic", "self->engine->lookahead + now", "self->engine->lookahead - now"),
    ("exclude lookahead equality", "if (event->time > horizon) break;", "if (event->time >= horizon) break;"),
    ("skip type 11 events", "type == 10 || type == 11", "type == 10"),
    ("omit blocking event ownership", "event->context->owner->blockingEvent = event;",
     "/* lost blocking event */"),
    ("omit cancellation of following events", "auto remaining = link->next;",
     "auto remaining = &self->pending;"),
    ("wrong active event flag", "state->flags & 0x80", "state->flags & 0x40"),
    ("wrong clock for absolute events", "? state->startTime", "? state->stopTime"),
    ("wrong clock for released events", "? state->releaseTime : state->stopTime",
     "? state->startTime : state->stopTime"),
    ("retire equality too late", "static_cast<int32_t>(clock - start) >= duration",
     "static_cast<int32_t>(clock - start) > duration"),
    ("unsigned elapsed comparison", "static_cast<int32_t>(clock - start) >= duration",
     "clock - start >= static_cast<uint32_t>(duration)"),
    ("reload active successor after retirement", "        link = next;\n    }\n}",
     "        link = link->next;\n    }\n}"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/audio/xact_sound.cpp").read_text()
    spec = Path(__file__).with_name("xact_sound_update.py")
    for name, old, new in MUTATIONS:
        # Two completion paths intentionally have the same state assignment;
        # Options.patches changes the first occurrence, the notifying path.
        expected = 2 if name == "wrong completed state" else 1
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
