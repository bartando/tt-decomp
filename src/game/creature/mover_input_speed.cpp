// Movement speed selected from the active gameplay mode and character tuning.
#include "pong_creature.hpp"

extern "C" void* g_gameDataMgr; // @ 0x8271A2E4
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern void* pongMatch_GetCharacterForSlot(void*, uint32_t); // @ 0x821C9C00

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x820CB4D0 | size: 0xC8
float pongMover_GetInputSpeed(pongMover* mover) {
    if (mover->m_flags & 4)
        return at<float>(at<void*>(g_gameDataMgr, 0x14), 0x64);
    const uint32_t slot = mover->m_creatureIndex;
    void* settings = g_input_obj_ptr;
    if (at<uint8_t>(settings, slot * 36 + 0xC4))
        return at<float>(at<void*>(g_gameDataMgr, 0x14), 0x58);
    void* character = pongMatch_GetCharacterForSlot(settings, slot);
    const float scale = at<float>(at<void*>(character, 0x28), 0x64);
    // The character lookup may replace the game-data manager: reload it here.
    return scale * at<float>(at<void*>(g_gameDataMgr, 0x14), 0x58);
}
