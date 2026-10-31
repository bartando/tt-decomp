"""Behavioral checks: each deliberate regression must produce FAIL, not BUILD/SPEC."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

STREAM = 'src/rage/net/dat_bit_buffer.cpp'
CASES = {
    'network_player_id': ('src/game/network/pong_network_io.cpp', [
        ('target mask', 'client)[2] & 0x1F', 'client)[2] & 0x0F'),
        ('player mapping', 'if (player == 2) return 1;', 'if (player == 2) return 0;'),
        ('diagnostic byte', 'if (static_cast<uint8_t>(reportInvalid))', 'if (reportInvalid)'),
    ]),
    'network_read_u64': (STREAM, [
        ('word order', '(static_cast<uint64_t>(high) << 32) | low', '(static_cast<uint64_t>(low) << 32) | high'),
        ('second read', 'datBitBuffer_ReadU32(bb, &high, 32);', 'datBitBuffer_ReadU32(bb, &high, 31);'),
        ('failure result', 'return success;', 'return true;'),
    ]),
    'network_read_bytes': (STREAM, [
        ('clamp', 'if (count > available) count = available > 0 ? available : 0;', 'if (count > available) count = 0;'),
        ('shift', 'source[i + 1] >> (8 - shift)', 'source[i + 1] >> (7 - shift)'),
        ('cursor', 'bb->m_readCursor += count * 8;', 'bb->m_readCursor += count;'),
    ]),
    'network_read_short_string': (STREAM, [
        ('lookahead', 'snBitStream_ReadString(bb, destination, 16)', 'snBitStream_ReadString(bb, destination, 15)'),
        ('terminator', 'destination[count - 1] = 0;', 'destination[count] = 0;'),
        ('rewind', 'bb->m_readCursor = cursor;', 'bb->m_readCursor = cursor + 8;'),
    ]),
    'network_write_bytes': (STREAM, [
        ('first mask', '0xFFu << (8 - shift)', '0xFFu << (7 - shift)'),
        ('second mask', '0xFFu >> shift', '0xFFu >> (shift + 1)'),
        ('cursor', 'bb->m_writeCursor += count * 8;', 'bb->m_writeCursor += count;'),
    ]),
    'network_write_short_string': (STREAM, [
        ('limit', 'if (available >= 16) available = 16;', 'if (available >= 16) available = 15;'),
        ('terminator', 'datBitBuffer_WriteU32(bb, 0, 8);', 'datBitBuffer_WriteU32(bb, 1, 8);'),
        ('count', 'return count + 1;', 'return count;'),
    ]),
    'network_read_s8': (STREAM, [
        ('width', 'reinterpret_cast<uint8_t*>(out), 7)', 'reinterpret_cast<uint8_t*>(out), 6)'),
        ('sign', 'if (sign) *out = static_cast<int8_t>(-*out);', 'if (!sign) *out = static_cast<int8_t>(-*out);'),
        ('failure', 'if (!datBitBuffer_ReadU32(bb, &sign, 1)) return false;', 'if (!datBitBuffer_ReadU32(bb, &sign, 1)) return true;'),
    ]),
    'network_score_payload': ('src/game/network/score_payload.cpp', [
        ('first byte', 'bytes + 4, 8', 'bytes + 3, 8'),
        ('flags', 'offset <= 10', 'offset <= 9'),
        ('flag value', 'bytes[offset] = temporary != 0;', 'bytes[offset] = temporary == 0;'),
        ('float offset', 'bytes + 12, &temporary', 'bytes + 16, &temporary'),
    ]),
    'network_read_named_u64': ('src/game/network/pong_network.cpp', [
        ('destination name', 'datBitBuffer_ReadShortString(this, static_cast<char*>(outData))', 'datBitBuffer_ReadShortString(this, static_cast<char*>(outData) + 1)'),
        ('identifier offset', 'static_cast<uint8_t*>(outData) + 0x10', 'static_cast<uint8_t*>(outData) + 0x08'),
    ]),
    'network_score_message': ('src/game/network/pong_network.cpp', [
        ('score arguments', 'netScore_Deserialise(obj + 0x08, client);', 'netScore_Deserialise(client, obj + 0x08);'),
    ]),
    'network_match_score_message': ('src/game/network/pong_network.cpp', [
        ('byte count', 'snBitStream_ReadString(client, obj + 0x08, 88);', 'snBitStream_ReadString(client, obj + 0x08, 11);'),
    ]),
    'network_gamer_ready_message': ('src/game/network/pong_network.cpp', [
        ('byte count', 'snBitStream_ReadString(client, obj + 0x08, 24);', 'snBitStream_ReadString(client, obj + 0x08, 3);'),
    ]),
    'network_level_config_message': ('src/game/network/pong_network.cpp', [
        ('byte count', 'snBitStream_ReadString(client, obj + 0x08, 4);\n}\n\n//', 'snBitStream_ReadString(client, obj + 0x08, 1);\n}\n\n//'),
    ]),
    'network_forfeit_message': ('src/game/network/pong_network.cpp', [
        ('aux offset', 'snBitStream_ReadString(client, obj + 0x0C, 4);', 'snBitStream_ReadString(client, obj + 0x0D, 4);'),
    ]),
}

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, (path, mutations) in CASES.items():
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
