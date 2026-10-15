/**
 * dat_bit_buffer.cpp — datBitBuffer read primitives
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * The bit reader every network message deserialiser goes through. The game
 * has one template instance per destination width (u8, u16, u32) plus a
 * signed 16-bit reader built from two of them.
 *
 * Callers in the network code know these under several names; the
 * forwarders at the bottom give those names a definition.
 */

#include <cstdint>

namespace {

// Only the fields the readers touch.
struct datBitBufferView {
    uint8_t  m_pad00[0x04];
    uint8_t* m_pData;        // +0x04  byte buffer
    uint8_t  m_pad08[0x08];
    int32_t  m_bitLimit;     // +0x10  readable bits
    uint8_t  m_pad14[0x04];
    int32_t  m_bitOffset;    // +0x18  bit position of the buffer's first bit
    int32_t  m_cursor;       // +0x1C  bits read so far
};

// PowerPC slw/srw: the shift amount is the low 6 bits, and 32..63 gives 0.
inline uint32_t ppc_slw(uint32_t value, uint32_t amount) {
    amount &= 63;
    return amount >= 32 ? 0u : value << amount;
}

inline uint32_t ppc_srw(uint32_t value, uint32_t amount) {
    amount &= 63;
    return amount >= 32 ? 0u : value >> amount;
}

// datBitBuffer::ReadUnsigned<T>. Reads `bits` bits MSB first into *out,
// starting at the cursor, and advances the cursor. Fails (returns false,
// leaves *out alone) if bits is negative or runs past the limit.
template <typename T>
bool ReadUnsigned(datBitBufferView* bb, T* out, int32_t bits) {
    if (bits < 0 || static_cast<int32_t>(static_cast<uint32_t>(bb->m_cursor) + static_cast<uint32_t>(bits)) >
                        bb->m_bitLimit) {
        return false;
    }

    if (bb->m_pData == nullptr || bb->m_cursor >= bb->m_bitLimit) {
        // The original takes its byte pointer and shift from uninitialised
        // stack slots here (only reachable with no buffer, or bits == 0 at
        // the very end). Read nothing, but advance and succeed as it does.
        *out = 0;
        bb->m_cursor += bits;
        return true;
    }

    const int32_t bit = bb->m_bitOffset + bb->m_cursor;
    const uint32_t shift = static_cast<uint32_t>(bit) & 7;
    const uint8_t* src = bb->m_pData + (bit >> 3);

    *out = static_cast<T>(static_cast<uint8_t>(ppc_slw(*src++, shift)));
    if (bits > 8) {
        for (uint32_t n = (static_cast<uint32_t>(bits - 9) >> 3) + 1; n != 0; --n) {
            *out = static_cast<T>(ppc_slw(*src++, shift) | (static_cast<uint32_t>(*out) << 8));
        }
    }
    if (shift != 0) {
        *out = static_cast<T>(*out | (*src >> (8 - shift)));
    }

    // Drop the bits read past the end of the field, then mask to `bits`.
    const uint32_t rounded = static_cast<uint32_t>(bits + 7) & ~7u;
    *out = static_cast<T>(ppc_srw(*out, rounded - static_cast<uint32_t>(bits)));
    if ((bits & 7) != 0) {
        *out = static_cast<T>(*out & ~ppc_slw(static_cast<T>(~T(0)), static_cast<uint32_t>(bits)));
    }

    bb->m_cursor += bits;
    return true;
}

} // namespace

// @ 0x82238DF8 — datBitBuffer::ReadUnsigned<u32> (SinglesNetworkClient_8DF8_g)
bool datBitBuffer_ReadU32(void* bb, uint32_t* out, int32_t bits) {
    return ReadUnsigned(static_cast<datBitBufferView*>(bb), out, bits);
}

// @ 0x820D7830 — datBitBuffer::ReadUnsigned<u16> (util_7830)
bool datBitBuffer_ReadU16(void* bb, uint16_t* out, int32_t bits) {
    return ReadUnsigned(static_cast<datBitBufferView*>(bb), out, bits);
}

// @ 0x820D7A08 — datBitBuffer::ReadUnsigned<u8> (util_7A08)
bool datBitBuffer_ReadU8(void* bb, uint8_t* out, int32_t bits) {
    return ReadUnsigned(static_cast<datBitBufferView*>(bb), out, bits);
}

// @ 0x820D7970 — datBitBuffer::ReadSigned<s16> (util_7970)
// A sign bit, then 15 bits of magnitude, negated if the sign was set. The
// width is fixed: the asm overwrites r5 before looking at it.
bool datBitBuffer_ReadS16(void* bb, int16_t* out) {
    uint32_t sign;
    if (!datBitBuffer_ReadU32(bb, &sign, 1)) {
        return false;
    }
    if (!datBitBuffer_ReadU16(bb, reinterpret_cast<uint16_t*>(out), 15)) {
        return false;
    }
    if (sign != 0) {
        *out = static_cast<int16_t>(-*out);
    }
    return true;
}

// ── The names the network code calls these by ───────────────────────────────
// pong_network.cpp and pong_network_io.cpp each picked their own names for
// the readers (checked against the call sites: ServeStartedMessage's
// deserialiser at 0x823B8F68 and ReadBallHitDataFromNetwork at 0x821D5538).
// They declare them void, so the success flag is dropped.

void netStream_ReadFloat(void* bb, void* out, uint32_t bits) {
    datBitBuffer_ReadU32(bb, static_cast<uint32_t*>(out), static_cast<int32_t>(bits));
}

void snBitStream_ReadBits(void* bb, void* out, int bits) {
    datBitBuffer_ReadU32(bb, static_cast<uint32_t*>(out), bits);
}

void snBitStream_ReadUnsigned(void* bb, void* out, int bits) {
    datBitBuffer_ReadU16(bb, static_cast<uint16_t*>(out), bits);
}

void ReadBitsFromStream(void* bb, void* out, int bits) {
    datBitBuffer_ReadU8(bb, static_cast<uint8_t*>(out), bits);
}

void netStream_ReadBytes(void* bb, void* out, uint32_t bits) {
    datBitBuffer_ReadU8(bb, static_cast<uint8_t*>(out), static_cast<int32_t>(bits));
}

// The width argument callers pass (16) is ignored, as in the original.
void netStream_ReadS16(void* bb, void* out, uint32_t) {
    datBitBuffer_ReadS16(bb, static_cast<int16_t*>(out));
}
