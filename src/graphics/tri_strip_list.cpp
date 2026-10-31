#include "graphics/tri_strip.hpp"
#include "rage/memory.h"

// @ 0x82134350 | size: 0xB8
void TriStripList::Erase(TriStrip** target) {
    uint32_t index = 0;
    if (m_count == 0) return;
    for (TriStrip** slot = m_items; slot != target; ++slot) {
        if (++index >= m_count) return;
    }

    TriStrip* strip = m_items[index];
    if (strip != nullptr) {
        rage_free(strip->m_tris);
        rage_free(strip->m_indices);
        rage_free(strip);
    }
    --m_count;
    for (; index < m_count; ++index) {
        m_items[index] = m_items[index + 1];
    }
}
