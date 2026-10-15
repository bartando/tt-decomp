/**
 * dat_bit_buffer.cpp — datBitBuffer, the network messages' bit stream
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Readers: one template instance per destination width (u8, u16, u32) plus
 * a signed 16-bit reader built from two of them. Writers: the u32 and s32
 * writes, the copy-on-write buffer growth they go through, the packet header
 * and the wrappers the messages call, which patch the packet length after
 * every field.
 *
 * Callers in the network code know these under several names; the
 * forwarders at the bottom give those names a definition.
 */

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

// datBitBuffer::Allocator, with its slots in the original's order.
struct datBitBufferAllocatorView {
    virtual void ScalarDtor(int flags) = 0;
    virtual bool CanAllocate(uint32_t bytes) const = 0;
    virtual void* Allocate(uint32_t bytes) = 0;   // slot 2
    virtual void Free(void* block) = 0;           // slot 3
};

struct datBitBufferView {
    int32_t* m_pShared;                       // +0x00  refcounted block: [0] = refcount, the bits follow
    uint8_t* m_pReadData;                     // +0x04
    uint8_t* m_pWriteData;                    // +0x08
    int32_t  m_capacityBits;                  // +0x0C
    int32_t  m_sizeBits;                      // +0x10  bits written so far (what readers may read)
    int32_t  m_maxBits;                       // +0x14
    int32_t  m_bitOffset;                     // +0x18  bit position of the buffer's first bit
    int32_t  m_readCursor;                    // +0x1C
    int32_t  m_writeCursor;                   // +0x20
    datBitBufferAllocatorView* m_pAllocator;  // +0x24
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
    if (bits < 0 || static_cast<int32_t>(static_cast<uint32_t>(bb->m_readCursor) + static_cast<uint32_t>(bits)) >
                        bb->m_sizeBits) {
        return false;
    }

    if (bb->m_pReadData == nullptr || bb->m_readCursor >= bb->m_sizeBits) {
        // The original takes its byte pointer and shift from uninitialised
        // stack slots here (only reachable with no buffer, or bits == 0 at
        // the very end). Read nothing, but advance and succeed as it does.
        *out = 0;
        bb->m_readCursor += bits;
        return true;
    }

    const int32_t bit = bb->m_bitOffset + bb->m_readCursor;
    const uint32_t shift = static_cast<uint32_t>(bit) & 7;
    const uint8_t* src = bb->m_pReadData + (bit >> 3);

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

    bb->m_readCursor += bits;
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

// @ 0x82260E18 — datBitBuffer::ReadSigned<s32> (SinglesNetworkClient_0E18_g)
// A sign bit, then bits - 1 bits of magnitude, negated if the sign was set.
bool datBitBuffer_ReadS32(void* bb, int32_t* out, int32_t bits) {
    uint32_t sign;
    if (!datBitBuffer_ReadU32(bb, &sign, 1)) {
        return false;
    }
    if (!datBitBuffer_ReadU32(bb, reinterpret_cast<uint32_t*>(out), bits - 1)) {
        return false;
    }
    if (sign != 0) {
        *out = static_cast<int32_t>(0u - static_cast<uint32_t>(*out));
    }
    return true;
}

// @ 0x823CEA98 — a network timestamp, a signed 32-bit count and a float
// (SinglesNetworkClient_EA98_g). Note the stream is the second argument.
void netTimestamp_Deserialise(void* timestamp, void* bb) {
    uint8_t* ts = static_cast<uint8_t*>(timestamp);
    datBitBuffer_ReadS32(bb, reinterpret_cast<int32_t*>(ts), 32);
    uint32_t bits;
    datBitBuffer_ReadU32(bb, &bits, 32);
    __builtin_memcpy(ts + 4, &bits, sizeof bits);
}

// @ 0x82260CE8 — datBitBuffer::Grow (SinglesNetworkClient_0CE8_g)
// Makes room for `bits` bits: false if that is past m_maxBits. A buffer
// whose block is shared (refcount > 1) is copied even when it is big enough.
// The new block is the bytes rounded up to 64 with the refcount word in front.
bool datBitBuffer_Grow(void* bbp, int32_t bits) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    if (bits > bb->m_maxBits) {
        return false;
    }
    int32_t want;
    if (bb->m_pShared != nullptr && bb->m_pShared[0] > 1) {
        want = bits <= bb->m_sizeBits ? bb->m_sizeBits : bits;
    } else {
        if (bits <= bb->m_capacityBits) {
            return true;
        }
        want = bits;
    }
    if (want == 0) {
        return true;
    }

    const uint32_t blockBytes = ((static_cast<uint32_t>(want + 7) >> 3) + 0x43) & ~0x3Fu;
    int32_t* block = static_cast<int32_t*>(bb->m_pAllocator->Allocate(blockBytes));
    if (block == nullptr) {
        return false;
    }
    block[0] = 1;
    if (bb->m_pShared != nullptr) {
        std::memcpy(block + 1, bb->m_pShared + 1, static_cast<size_t>((bb->m_sizeBits + 7) >> 3));
        if (--bb->m_pShared[0] == 0) {
            bb->m_pAllocator->Free(bb->m_pShared);
        }
    }

    uint8_t* data = reinterpret_cast<uint8_t*>(block + 1);
    bb->m_pShared = block;
    bb->m_pWriteData = data;
    bb->m_pReadData = data;
    const int32_t capacity = static_cast<int32_t>((blockBytes - 4) << 3);
    bb->m_capacityBits = capacity > bb->m_maxBits ? bb->m_maxBits : capacity;
    return true;
}

// @ 0x82260448 — datBitBuffer::WriteUnsigned<u32> (SinglesNetworkClient_0448_g)
// Writes the low `bits` bits of value MSB first at the write cursor, keeping
// the bits around them, and advances the cursor (and the size with it).
bool datBitBuffer_WriteU32(void* bbp, uint32_t value, int32_t bits) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    if (!datBitBuffer_Grow(bb, bits + bb->m_writeCursor)) {
        return false;
    }

    if (bb->m_pWriteData != nullptr && bb->m_writeCursor < bb->m_maxBits) {
        const int32_t bit = bb->m_bitOffset + bb->m_writeCursor;
        const uint32_t shift = static_cast<uint32_t>(bit) & 7;
        uint8_t* dst = bb->m_pWriteData + (bit >> 3);

        // value and its mask, left-aligned in a word, then shifted so the
        // first byte lines up with the bit position
        const uint32_t align = static_cast<uint32_t>(32 - bits);
        uint32_t mask = ppc_slw(0xFFFFFFFFu, align);
        uint32_t data = ppc_slw(value, align);
        const int32_t firstBits = 8 - static_cast<int32_t>(shift);
        *dst = static_cast<uint8_t>((*dst & ~((mask >> 24) >> shift)) | ((data >> 24) >> shift));
        ++dst;
        mask = ppc_slw(mask, static_cast<uint32_t>(firstBits));
        data = ppc_slw(data, static_cast<uint32_t>(firstBits));
        if (firstBits < bits) {
            for (uint32_t n = (static_cast<uint32_t>(bits - firstBits - 1) >> 3) + 1; n != 0; --n) {
                *dst = static_cast<uint8_t>((*dst & ~(mask >> 24)) | (data >> 24));
                ++dst;
                data <<= 8;
                mask <<= 8;
            }
        }
    }
    // else: the original writes through a pointer from an uninitialised stack
    // slot (no buffer, or the cursor at the limit); write nothing.

    bb->m_writeCursor += bits;
    if (bb->m_writeCursor > bb->m_sizeBits) {
        bb->m_sizeBits = bb->m_writeCursor;
    }
    return true;
}

// @ 0x822605F0 — datBitBuffer::WriteSigned<s32> (atSingleton_05F0_g)
// A sign bit, then the magnitude in bits - 1 bits.
bool datBitBuffer_WriteS32(void* bb, int32_t value, int32_t bits) {
    if (value < 0) {
        return datBitBuffer_WriteU32(bb, 1, 1) &&
               datBitBuffer_WriteU32(bb, static_cast<uint32_t>(-value), bits - 1);
    }
    return datBitBuffer_WriteU32(bb, 0, 1) && datBitBuffer_WriteU32(bb, static_cast<uint32_t>(value), bits - 1);
}

// @ 0x82238AE0 — the packet header (SinglesNetworkClient_8AE0_g)
// On an empty buffer that may hold anything, writes three 16-bit fields
// (0, the length, filled in later, and 6) and starts reading after them.
void datBitBuffer_BeginPacket(void* bbp) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    if (bb->m_maxBits > 0 && ((bb->m_sizeBits + 7) & ~7) == 0) {
        datBitBuffer_WriteU32(bb, 0, 16);
        datBitBuffer_WriteU32(bb, 0x3FFF, 16);
        datBitBuffer_WriteU32(bb, 6, 16);
        if (bb->m_sizeBits >= 48) {
            bb->m_readCursor = 48;
        }
    }
}

// The header's second field is the packet length in bytes; every field
// write below rewrites it.
static void PatchPacketLength(datBitBufferView* bb) {
    const int32_t sizeBits = bb->m_sizeBits;
    datBitBuffer_BeginPacket(bb);
    const int32_t cursor = bb->m_writeCursor;
    bb->m_writeCursor = 32;
    datBitBuffer_WriteU32(bb, static_cast<uint32_t>((sizeBits + 7) >> 3), 16);
    bb->m_writeCursor = cursor;
}

// @ 0x820D6838 — write an unsigned field (SinglesNetworkClient_6838_g)
bool datBitBuffer_WriteFieldU32(void* bbp, uint32_t value, int32_t bits) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    datBitBuffer_BeginPacket(bb);
    const bool ok = datBitBuffer_WriteU32(bb, value, bits);
    PatchPacketLength(bb);
    return ok;
}

// @ 0x820D68A8 — write a signed field (SinglesNetworkClient_68A8_g)
bool datBitBuffer_WriteFieldS32(void* bbp, int32_t value, int32_t bits) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    datBitBuffer_BeginPacket(bb);
    const bool ok = datBitBuffer_WriteS32(bb, value, bits);
    PatchPacketLength(bb);
    return ok;
}

// @ 0x820D6918 — write a bool field, one bit (SinglesNetworkClient_6918_g)
// Only the low byte of the argument counts.
bool datBitBuffer_WriteFieldBool(void* bbp, uint32_t value) {
    datBitBufferView* bb = static_cast<datBitBufferView*>(bbp);
    datBitBuffer_BeginPacket(bb);
    const bool ok = datBitBuffer_WriteU32(bb, (value & 0xFF) != 0 ? 1u : 0u, 1);
    PatchPacketLength(bb);
    return ok;
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

// pong_network_io.cpp calls the raw u32 write ReadBitsFromStream (0x82260448
// is what WriteFloatToNetworkStream at 0x820D6990 calls); pong_network.cpp
// calls it snBitStream_WriteBits.
uint32_t ReadBitsFromStream(void* bb, uint32_t value, int bits) {
    return datBitBuffer_WriteU32(bb, value, bits) ? 1u : 0u;
}

uint32_t snBitStream_WriteBits(void* bb, uint32_t value, int bits) {
    return datBitBuffer_WriteU32(bb, value, bits) ? 1u : 0u;
}

void BeginNetworkWrite(void* bb) {
    datBitBuffer_BeginPacket(bb);
}

void snBitStream_ValidateWrite(void* bb) {
    datBitBuffer_BeginPacket(bb);
}

// The field writers, by the callers' names. They pass the value in its own
// width; the original takes the whole register.
void netStream_WriteByte(void* bb, uint8_t value, int bits) {
    datBitBuffer_WriteFieldU32(bb, value, bits);
}

void WriteUInt8Bits(void* bb, uint8_t value, int bits) {
    datBitBuffer_WriteFieldU32(bb, value, bits);
}

void WriteInt8Bits(void* bb, int8_t value, int bits) {
    datBitBuffer_WriteFieldS32(bb, value, bits);
}

void WriteInt8Bits(void* bb, int16_t value, int bits) {
    datBitBuffer_WriteFieldS32(bb, value, bits);
}

void netStream_WriteS16(void* bb, int16_t value, int bits) {
    datBitBuffer_WriteFieldS32(bb, value, bits);
}

void netStream_WriteBool(void* bb, uint8_t value) {
    datBitBuffer_WriteFieldBool(bb, value);
}

// pong_network.cpp's name for the timestamp read (MatchTimeSyncMessage and
// two other deserialisers call 0x823CEA98 with the destination first).
void netStream_ReadU64(void* timestamp, void* bb) {
    netTimestamp_Deserialise(timestamp, bb);
}
