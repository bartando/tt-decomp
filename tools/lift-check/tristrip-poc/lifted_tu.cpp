#include <stdint.h>
#include <stddef.h>
#include <string.h>
void* cmOperatorCtor_Allocate(uint32_t size);
// rage's inlined operator new[] for an element type without a constructor:
// MSVC saturates the byte count to 0xFFFFFFFF when count * size overflows,
// then asks the current allocator for it at 16-byte alignment.
template <typename T>
static T* RageNewArray(uint32_t count) {
    const uint32_t elemSize = (uint32_t)sizeof(T);
    const uint32_t bytes = count > 0xFFFFFFFFu / elemSize ? 0xFFFFFFFFu : count * elemSize;
    return static_cast<T*>(cmOperatorCtor_Allocate(bytes));
}

// Neighbours of one triangle; LinkEdge fills both sides of a shared edge.
struct TriNeighbors {
    int32_t tri[3];     // +0x00  triangle across edge e, -1 if none
    int32_t edge[3];    // +0x0C  which edge of that triangle is the shared one
};
static_assert(sizeof(TriNeighbors) == 0x18, "the ctor allocates numTris * 24 bytes");

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
    // and closes the gap. It matches the slot's address, not the strip;
    // pong_network.cpp lifts it as pongNetMessageHolder::RemoveElementByPointer.
    void       Erase(TriStrip** slot);
    TriStrip** TakeBest(const StripVertexCache* cache);
};

// The driver's stack object, 16 bytes. The driver frees m_triFlags and then
// m_neighbors itself; there is no destructor function.
struct TriStripper {
    int32_t       m_numTris;      // +0x00
    uint16_t*     m_indices;      // +0x04  three per triangle; not owned
    TriNeighbors* m_neighbors;    // +0x08  one per triangle
    uint32_t*     m_triFlags;     // +0x0C  per triangle. While the ctor links edges, bit e
                                  //        means edge e is linked; 0x82135138 then reuses
                                  //        the words as "triangle is in a strip"

    TriStripper(int32_t numTris, uint16_t* indices);
    void LinkEdge(int32_t tri, int32_t edge);
    int  JoinStrips(TriStripList* strips, uint16_t** outIndices);
};

// ─────────────────────────────────────────────────────────────────────────────
// TriStrip::TriStrip @ 0x821342A0 | size: 0xB0   (symbol map: cmOperatorCtor_42A0_w)
// Allocates the triangle and index arrays; the caller (0x82135138) sets
// m_startsEven and copies the data in.
// ─────────────────────────────────────────────────────────────────────────────
TriStrip::TriStrip(uint32_t numTris, uint32_t numIndices) {
    m_numTris    = numTris;
    m_tris       = RageNewArray<int32_t>(numTris);
    m_numIndices = numIndices;
    m_indices    = RageNewArray<uint16_t>(numIndices);
}

// ─────────────────────────────────────────────────────────────────────────────
// TriStripList::TakeBest @ 0x82134C10 | size: 0x280   (symbol map: cmOperatorCtor_4C10_wrh)
// Picks the strip JoinStrips appends next. Only strips with the winding and
// index-count parity of the one in slot 0 compete; each is replayed on a copy
// of `cache` (even-length ones backwards too) and scored by how many vertices
// the cache already held. The winner is reversed in place if backwards scored
// higher, swapped into slot 0, and slot 0 is returned (null if empty).
// ─────────────────────────────────────────────────────────────────────────────
TriStrip** TriStripList::TakeBest(const StripVertexCache* cache) {
    if (m_count == 0) {
        return nullptr;
    }

    TriStrip** best         = m_items;
    bool       bestReversed = false;
    int32_t    bestScore    = -1;
    // The original re-reads the parity from the current best, which always
    // shares slot 0's.
    const uint32_t parity     = m_items[0]->m_numIndices & 1;
    const int32_t  startsEven = m_items[0]->m_startsEven;

    for (uint32_t i = 0; i < m_count; ++i) {
        TriStrip* strip = m_items[i];
        const uint32_t numIndices = strip->m_numIndices;
        if (strip->m_startsEven != startsEven || (numIndices & 1) != parity) {
            continue;
        }

        bool reversed = false;
        StripVertexCache trial = *cache;
        for (uint32_t j = 0; j < numIndices; ++j) {
            trial.Access(StripVertexCache::kPassTrial, strip->m_indices[j]);
        }
        // Reversing an even-length strip keeps its winding.
        if ((numIndices & 1) == 0) {
            StripVertexCache backwards = *cache;
            for (int32_t j = (int32_t)strip->m_numIndices - 1; j >= 0; --j) {
                backwards.Access(StripVertexCache::kPassTrial, strip->m_indices[j]);
            }
            if (backwards.m_hits > trial.m_hits) {
                trial = backwards;
                reversed = true;
            }
        }

        const int32_t score = trial.m_hits - cache->m_hits;
        if (score > bestScore) {
            bestScore    = score;
            best         = &m_items[i];
            bestReversed = reversed;
        }
    }

    if (bestReversed) {
        TriStrip* strip = *best;
        for (int32_t lo = 0, hi = (int32_t)strip->m_numIndices - 1; lo < hi; ++lo, --hi) {
            const uint16_t index = strip->m_indices[hi];
            strip->m_indices[hi] = strip->m_indices[lo];
            strip->m_indices[lo] = index;
        }
    }

    if (best != Begin()) {
        TriStrip* winner = *best;
        *best    = *Begin();
        *Begin() = winner;
    }
    return Begin();
}

// ─────────────────────────────────────────────────────────────────────────────
// TriStripper::JoinStrips @ 0x82134E90 | size: 0x228   (symbol map: cmOperatorCtor_4E90_w)
// Concatenates every strip into one new index list and empties `strips`. The
// first strip goes in as it is; after that TakeBest picks the strip that reuses
// the most cached vertices. Strips are stitched with degenerate triangles.
// Returns the index count. Doesn't touch the stripper itself.
// ─────────────────────────────────────────────────────────────────────────────
int TriStripper::JoinStrips(TriStripList* strips, uint16_t** outIndices) {
    // Room for every strip plus up to three stitching indices each.
    uint32_t capacity = strips->m_count * 3 + 2;
    for (uint32_t i = 0; i < strips->m_count; ++i) {
        capacity += strips->m_items[i]->m_numIndices;
    }
    uint16_t* out = RageNewArray<uint16_t>(capacity);
    int count = 0;

    // Only these fields are reset; m_pass and m_setByHit start as stack garbage.
    StripVertexCache cache;
    cache.m_hits = 0;
    for (int i = 0; i < StripVertexCache::kSlots; ++i) {
        cache.m_verts[i] = StripVertexCache::kEmptySlot;
    }
    cache.m_next = 0;

    // The original dereferences slot 0 even for an empty list; the driver
    // never passes one.
    TriStrip** slot = strips->Begin();
    TriStrip* strip = *slot;
    for (uint32_t i = 0; i < strip->m_numIndices; ++i) {
        out[count++] = strip->m_indices[i];
        cache.Access(StripVertexCache::kPassJoined, strip->m_indices[i]);
    }
    strips->Erase(slot);

    while (strips->m_count != 0) {
        slot  = strips->TakeBest(&cache);
        strip = *slot;

        // Repeat the last index and the new first one (two degenerate
        // triangles), then once more if the strip would start on the wrong
        // winding.
        const uint16_t last  = out[count - 1];
        const uint16_t first = strip->m_indices[0];
        if (first != last) {
            out[count]     = last;
            out[count + 1] = first;
            count += 2;
        }
        if (strip->m_startsEven != ((count & 1) == 0)) {
            out[count++] = first;
        }

        for (uint32_t i = 0; i < strip->m_numIndices; ++i) {
            out[count++] = strip->m_indices[i];
            cache.Access(StripVertexCache::kPassJoined, strip->m_indices[i]);
        }
        strips->Erase(slot);
    }

    *outIndices = out;
    return count;
}

// ─────────────────────────────────────────────────────────────────────────────
// TriStripper::LinkEdge @ 0x821354D0 | size: 0x178   (symbol map: cmOperatorCtor_54D0_wrh)
// Finds the first later triangle that has edge `edge` of `tri` running the
// other way and records the pair on both sides. Triangles with all three
// edges linked are skipped; a single linked edge of the candidate isn't
// checked.
// ─────────────────────────────────────────────────────────────────────────────
void TriStripper::LinkEdge(int32_t tri, int32_t edge) {
    const int32_t  numTris = m_numTris;
    const uint16_t from    = m_indices[tri * 3 + edge];
    const uint16_t to      = m_indices[tri * 3 + (edge + 1) % 3];

    for (int32_t other = tri + 1; other < numTris; ++other) {
        if (m_triFlags[other] == 7) {
            continue;
        }
        const uint16_t* corners = &m_indices[other * 3];
        for (int32_t otherEdge = 0; otherEdge < 3; ++otherEdge) {
            if (corners[otherEdge] == to && corners[(otherEdge + 1) % 3] == from) {
                m_neighbors[tri].tri[edge]         = other;
                m_neighbors[tri].edge[edge]        = otherEdge;
                m_triFlags[tri]                   |= 1u << edge;
                m_neighbors[other].tri[otherEdge]  = tri;
                m_neighbors[other].edge[otherEdge] = edge;
                m_triFlags[other]                 |= 1u << otherEdge;
                return;
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// TriStripper::TriStripper @ 0x82135648 | size: 0x170   (symbol map: cmOperatorCtor_5648_w)
// Builds the edge adjacency of the triangle list. m_neighbors[].edge stays
// uninitialised for edges without a neighbour.
// ─────────────────────────────────────────────────────────────────────────────
TriStripper::TriStripper(int32_t numTris, uint16_t* indices) {
    m_numTris   = numTris;
    m_indices   = indices;
    m_triFlags  = RageNewArray<uint32_t>(numTris);
    m_neighbors = RageNewArray<TriNeighbors>(numTris);
    for (int32_t i = 0; i < numTris; ++i) {
        m_neighbors[i].tri[0] = -1;
        m_neighbors[i].tri[1] = -1;
        m_neighbors[i].tri[2] = -1;
    }

    memset(m_triFlags, 0, m_numTris * sizeof(uint32_t));
    for (int32_t tri = 0; tri < numTris; ++tri) {
        for (int32_t edge = 0; edge < 3; ++edge) {
            if ((m_triFlags[tri] & (1u << edge)) == 0) {
                LinkEdge(tri, edge);
            }
        }
    }
    memset(m_triFlags, 0, m_numTris * sizeof(uint32_t));
}

// ─────────────────────────────────────────────────────────────────────────────
// StripVertexCache::Access @ 0x821357B8 | size: 0x100   (symbol map: cmOperatorCtor_57B8_w)
// Feeds one vertex through the cache. Returns 0 on a hit, 1 on a miss, 2 on a
// miss that pushed out a vertex this same pass had inserted (neither caller
// reads it). A hit on a slot from another pass counts in m_hits and moves the
// slot to this pass.
// ─────────────────────────────────────────────────────────────────────────────
int StripVertexCache::Access(int32_t pass, uint16_t vertex) {
    for (int i = 0; i < kSlots; ++i) {
        if (m_verts[i] == vertex) {
            if (m_pass[i] != pass) {
                ++m_hits;
                m_pass[i]     = pass;
                m_setByHit[i] = 1;
            }
            return 0;
        }
    }

    int result = 1;
    const int32_t slot = m_next;
    if (m_verts[slot] != kEmptySlot && m_pass[slot] == pass && m_setByHit[slot] == 0) {
        result = 2;
    }
    m_verts[slot]    = vertex;
    m_pass[slot]     = pass;
    m_setByHit[slot] = 0;
    m_next = (m_next + 1) % kSlots;
    return result;
}
