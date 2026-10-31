#include "game/match_ai_array.hpp"
#include "rage/operator_new.hpp"

// Allocate initial pointer storage without constructing or copying entries.
// Count stays unchanged; failure still publishes the truncated capacity.
// @ 0x821EDB80 | size: 0x64
void game_DB80(gdaiNodeArray* array, uint32_t capacity) {
    const uint32_t bytes = capacity > 0x3FFFFFFFu ? UINT32_MAX : capacity * 4u;
    array->m_data = static_cast<rage::ptr32<gdaiNode>*>(rage_Alloc(bytes));
    array->m_capacity = static_cast<uint16_t>(capacity);
}
