"""Require behavioral failures for ABI, payload and callback-lifetime mistakes."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
 ('network_tournament_complete_process', 'src/game/network/pong_network.cpp', [
  ('wrong byte', 'reinterpret_cast<const int8_t*>(this)[8]', 'reinterpret_cast<const int8_t*>(this)[4]'),
  ('unsigned payload', 'reinterpret_cast<const int8_t*>(this)[8]', 'reinterpret_cast<const uint8_t*>(this)[8]'),
  ('drop flag path', 'loop[0x242] != 0 ||', 'false ||'),
  ('payload in wrong register', 'PostGameMessage(14386, 128, 1, &tournament);', 'PostGameMessage(14386, 128, 0, &tournament);'),
 ]),
 ('player_check_button_input', 'src/game/player/pong_player.cpp', [
  ('wrong clock root', 'static_cast<const uint8_t*>(g_loop_obj_ptr) + 12', 'static_cast<const uint8_t*>(g_input_obj_ptr) + 12'),
  ('drop input query', 'if (enabled != 0 && CheckButtonPressed', 'if (CheckButtonPressed'),
  ('full query result', 'const uint8_t enabled = static_cast<uint8_t>(reinterpret_cast<PlayerInputQuery*>(this)->IsInputEnabled());', 'const uint32_t enabled = reinterpret_cast<PlayerInputQuery*>(this)->IsInputEnabled();'),
  ('cache input before callback', 'const uint8_t enabled =', 'const auto* cachedInput = static_cast<const int32_t*>(g_input_obj_ptr);\n    const uint8_t enabled ='),
  ('wrong press target', 'rage::load_ptr32<uint8_t>(record, 0x31C) + 8', 'record + 0x31C'),
  ('reverse mirror gate', 'input[15 - playerSlot] == 0', 'input[15 - playerSlot] != 0'),
  ('do not reload slot', 'const uint32_t playerSlot = slot();', 'const uint32_t playerSlot = AFTER_INVALID;'),
  ('drop saved slot gate', '*reinterpret_cast<const uint32_t*>(replay + 0x68D00) == playerSlot', 'false'),
  ('skip charge after query false', 'if (replay[0x68CFA] == 0', 'if (enabled == 0 || replay[0x68CFA] == 0'),
  ('wrong charge destination', 'replay + 0x68CEC', 'replay + 0x68CE8'),
  ('wrong negative blend', 'std::fma(delta, g_kPowerBlend, 1.0f)', 'delta + 1.0f'),
 ])]


def main():
 root = Path(__file__).resolve().parents[3]
 count = 0
 for spec, path, cases in CASES:
  source = (root/path).read_text()
  for label, old, new in cases:
   patches = [(old,new)]
   if label == 'cache input before callback':
    patches.append(('const auto* input = static_cast<const int32_t*>(g_input_obj_ptr);', 'const auto* input = cachedInput;'))
   if label == 'do not reload slot':
    patches = [('const uint8_t enabled =', 'const uint32_t cachedSlot = slot();\n    const uint8_t enabled ='),
               (old, 'const uint32_t playerSlot = cachedSlot;')]
   for before, after in patches:
    assert before in source, (spec,label,before)
   out = io.StringIO()
   with contextlib.redirect_stdout(out):
    rc = Checker(Path(__file__).with_name(spec+'.py'), Options(seed=1,patches=tuple(patches))).run()
   print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}",flush=True)
   if rc != 1: return 1
   count += 1
 print(f'Caught {count}/{count} mutations',flush=True)
 return 0

if __name__ == '__main__':
 raise SystemExit(main())
