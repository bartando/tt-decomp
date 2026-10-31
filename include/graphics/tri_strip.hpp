#pragma once
#include <cstddef>
#include <cstdint>

// One strip, 0x18 bytes (0x82135138 allocates it and fills the arrays).
struct TriStrip {
    int32_t   m_startsEven;   // +0x00  1: the strip's first index has to land on an even
                              //        position of the joined list (JoinStrips pads it
                              //        otherwise); set by 0x82135138
    uint32_t  m_numTris;      // +0x04
    int32_t*  m_tris;         // +0x08  triangles the strip covers
    uint32_t  m_numIndices;   // +0x0C
    uint16_t* m_indices;      // +0x10
    uint32_t  field_0x14;     // +0x14  not touched by anything lifted here

    TriStrip(uint32_t numTris, uint32_t numIndices);
};

// FIFO model of the GPU's post-transform vertex cache, 0x88 bytes (TakeBest
// copies it as 0x22 words). JoinStrips feeds it the joined list as pass 1;
// TakeBest replays candidate strips on copies as pass 2.
struct StripVertexCache {
    enum {
        kSlots      = 18,
        kEmptySlot  = 0xFFFF,
        kPassJoined = 1,
        kPassTrial  = 2,
    };

    int32_t  m_hits;               // +0x00  hits on slots another pass filled or hit
    uint16_t m_verts[kSlots];      // +0x04  kEmptySlot when unused
    int32_t  m_pass[kSlots];       // +0x28  pass that last inserted or hit the slot
    int32_t  m_next;               // +0x70  slot the next miss replaces
    uint8_t  m_setByHit[kSlots];   // +0x74  1 if m_pass was set by a hit, 0 if by an insert

    int Access(int32_t pass, uint16_t vertex);
};
static_assert(offsetof(StripVertexCache, m_verts) == 0x04, "StripVertexCache layout");
static_assert(offsetof(StripVertexCache, m_pass) == 0x28, "StripVertexCache layout");
static_assert(offsetof(StripVertexCache, m_next) == 0x70, "StripVertexCache layout");
static_assert(offsetof(StripVertexCache, m_setByHit) == 0x74, "StripVertexCache layout");
static_assert(sizeof(StripVertexCache) == 0x88, "TakeBest copies 0x22 words");

// Strips grown by 0x82135138 (ctor 0x82134408 allocates numTris slots).
struct TriStripList {
    TriStrip** m_items;       // +0x00
    uint32_t   m_count;       // +0x04

    // Slot 0 is always read through an accessor that yields null when empty.
    TriStrip** Begin() { return m_count != 0 ? m_items : nullptr; }

    // @ 0x82134350 — deletes the strip in `slot` (its two arrays, then itself)
    // and closes the gap. It matches the slot's address, not the strip.
    void       Erase(TriStrip** slot);                  // @ 0x82134350
    TriStrip** TakeBest(const StripVertexCache* cache);  // @ 0x82134C10
};
