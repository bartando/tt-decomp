/**
 * ccal_ring_buffer.cpp — the movie player's sample ring buffer
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * A fixed ring of 0x3C-byte sample slots shared by the movie player's reader
 * and writer threads: separate read and write indices, and a free-slot count
 * both sides change atomically. pong_misc.cpp calls these by their map names
 * (CCalRingBuffer_* in its __asm__ labels).
 */

#include <cstdint>

namespace {

struct ccalSlotView {
    void (* const* m_pVtable)(ccalSlotView*);   // slot 1 resets the sample
};

struct ccalRingBufferView {
    uint8_t       m_pad00[0x30];
    uint8_t*      m_pSlots;      // +0x30  capacity slots of 0x3C bytes
    uint32_t      m_capacity;    // +0x34
    uint32_t      m_writeIndex;  // +0x38
    uint32_t      m_readIndex;   // +0x3C
    uint8_t       m_pad40[0x04];
    uint32_t      m_freeSlots;   // +0x44  changed with lwarx/stwcx.
};

ccalSlotView* ResetSlot(ccalRingBufferView* rb, uint32_t index) {
    ccalSlotView* slot = reinterpret_cast<ccalSlotView*>(rb->m_pSlots + index * 0x3C);
    slot->m_pVtable[1](slot);
    return slot;
}

}  // namespace

// @ 0x8248DBC8 — the free-slot count (atSingleton_vfn_28_DBC8_1)
extern "C" uint32_t atSingleton_vfn_28_DBC8_1(void* rb) {
    return static_cast<ccalRingBufferView*>(rb)->m_freeSlots;
}

// @ 0x8248DBD0 — the filled-slot count
extern "C" uint32_t CCalMoviePlayer_DBD0(void* rb) {
    const ccalRingBufferView* r = static_cast<ccalRingBufferView*>(rb);
    return r->m_capacity - r->m_freeSlots;
}

// @ 0x8248DBE0 — the slot at the write index, reset
extern "C" void* CCalMoviePlayer_DBE0(void* rb) {
    ccalRingBufferView* r = static_cast<ccalRingBufferView*>(rb);
    return ResetSlot(r, r->m_writeIndex);
}

// @ 0x8248DC30 — the slot at the read index, reset
extern "C" void* CCalMoviePlayer_DC30(void* rb) {
    ccalRingBufferView* r = static_cast<ccalRingBufferView*>(rb);
    return ResetSlot(r, r->m_readIndex);
}

// The commit/release pair (0x8248DCC8, 0x8248DD30) advance an index and
// change m_freeSlots with lwarx/stwcx. between mtmsrd's; lift-check can't run
// mtmsrd, so they aren't lifted here.
