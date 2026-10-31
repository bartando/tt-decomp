"""Raw integer/float slots, padded strings, two-pass parsing, and full queue counts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES=[
 ('reverse inline flag','const bool immediate = (flags & 0x40) != 0;','const bool immediate = (flags & 0x40) == 0;'),
 ('do not consume float bits',"*type == 'i' || *type == 'f'","*type == 'i'"),
 ('wrong numeric payload','payload[written++] = va_arg(arguments, uint32_t);','payload[written++] = va_arg(arguments, uint32_t) + 1;'),
 ('omit string terminator word',' + 4u) >> 2',' + 3u) >> 2'),
 ('drop padded string bytes','std::memcpy(payload + written, text, length * 4u);','std::memcpy(payload + written, text, std::strlen(text) + 1);'),
 ('truncate queued count','initialWords + words + 1','initialWords + static_cast<uint8_t>(words) + 1'),
 ('reuse advanced varargs','va_copy(countArguments, arguments);','va_copy(countArguments, arguments);\n    (void)va_arg(arguments, uint32_t);'),
 ('drop queue header word','initialWords + words + 1','initialWords + words'),
 ('omit payload header count','message->payloadWords = static_cast<uint8_t>(words);','message->payloadWords = 0;'),
 ('wrong bank stride','uint32_t(g_gameMessageQueueBank) * 1024','uint32_t(g_gameMessageQueueBank) * 512'),
]

def main():
 source=(Path(__file__).resolve().parents[3]/'src/game/game_message.cpp').read_text()
 start=source.index('void PostGameMessageFmt(')
 body=source[start:source.index('\n}',start)+2]
 for label,old,new in CASES:
  assert old in body,label
  out=io.StringIO()
  with contextlib.redirect_stdout(out):
   rc=Checker(Path(__file__).with_name('game_message_post_formatted.py'),Options(seed=1,patches=((body,body.replace(old,new)),))).run()
  print(f"{'CAUGHT' if rc==1 else 'MISSED'} {label}: {out.getvalue().splitlines()[0]}",flush=True)
  if rc!=1:return 1
 print(f'Caught {len(CASES)}/{len(CASES)} mutations')
 return 0
if __name__=='__main__':raise SystemExit(main())
