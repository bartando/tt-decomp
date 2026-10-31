#include "pong_match.hpp"
#include "rage/operator_new.hpp"

// Initialize the index pool, then shuffle it using the existing forward shuffle.
// Heap callbacks can change capacity; the fill loop rereads it like the PPC.
// @ 0x821B2A58 | size: 0xD0
void gmPracticeTargetWordArray_Init(gmPracticeTargetWordArray* array, int32_t capacity,
                                     bool flag6, bool flag7) {
    const uint32_t unsignedCapacity = static_cast<uint32_t>(capacity);
    const uint32_t bytes = unsignedCapacity > 0x3FFFFFFFu ? UINT32_MAX : unsignedCapacity * 4u;
    array->m_count = capacity;
    array->m_capacity = capacity;
    array->m_flags = static_cast<uint8_t>((array->m_flags & 0x3Fu)
                       | (uint32_t(flag6) << 6) | (uint32_t(flag7) << 7));
    array->m_data = static_cast<uint32_t*>(rage_Alloc(bytes));
    for (int32_t i = 0; i < array->m_capacity; ++i)
        array->m_data.get()[i] = static_cast<uint32_t>(i);
    gmPracticeTargetWordArray_Shuffle(array);
}
