// Slot-state reset and face animation selection used by mode transitions.
#include "../creature/pong_creature.hpp"
#include <cstdint>
#include <cstring>

extern "C" const float lbl_825C5938; // @ 0x825C5938
extern "C" void* g_loop_obj_ptr; // @ 0x825EAB30
extern "C" uint32_t g_prngState[2]; // @ 0x825CA2C8
extern "C" uint32_t g_faceAnimationSelectionGuard[2]; // @ 0x825C9F00

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x820D6D48 | size: 0x110
void LocomotionStateAnim_6D48(void* object) {
    static_cast<LocomotionStateAnim*>(object)->ResetAccumulators();
    for (unsigned offset = 0x90; offset <= 0xB0; offset += 0x10)
        std::memset(static_cast<uint8_t*>(object) + offset, 0, 16);
    at<float>(object, 0xC0) = 0.0f;
    at<float>(object, 0xC4) = 0.0f;
    at<float>(object, 0xC8) = 0.0f;
    at<float>(object, 0xCC) = 1.0f;
    at<uint8_t>(object, 0x88) = 0;
    at<float>(object, 0x80) = 0.0f;
    at<uint8_t>(object, 0x89) = 0;
    at<float>(object, 0x84) = 0.0f;
    at<uint8_t>(object, 0x8A) = 0;
    std::memset(static_cast<uint8_t*>(object) + 0xD0, 0, 16);
    // The three basis w lanes are deliberately left untouched.
    for (unsigned row = 0; row < 3; ++row)
        for (unsigned lane = 0; lane < 3; ++lane)
            at<float>(object, 0xE0 + row * 16 + lane * 4) = row == lane ? 1.0f : 0.0f;
    std::memset(static_cast<uint8_t*>(object) + 0x110, 0, 16);
    at<uint16_t>(object, 0x130) = 0xFFFF;
    at<float>(object, 0x120) = lbl_825C5938;
    at<uint16_t>(object, 0x132) = 0xFFFF;
    at<float>(object, 0x124) = 0.0f;
    at<uint16_t>(object, 0x134) = 0xFFFF;
    at<float>(object, 0x128) = 0.0f;
    at<uint16_t>(object, 0x136) = 0xFFFF;
    at<float>(object, 0x12C) = 0.0f;
    at<uint8_t>(object, 0x138) = 0;
    at<uint8_t>(object, 0x139) = 0x13;
    at<uint8_t>(object, 0x13A) = 0;
}

// @ 0x820C2130 | size: 0x15C
void LocomotionStateAnim_2130_g(void* face) {
    const bool alternate = at<uint8_t>(g_loop_obj_ptr, 0x240) != 0;
    void* list = at<void*>(face, alternate ? 0x9C : 0x98);
    const uint32_t count = at<uint16_t>(list, 4);
    if (void* current = at<void*>(face, 0x4C)) at<float>(current, 0x14) = 0.0f;
    if (count == 1 || g_faceAnimationSelectionGuard[1] != 0 || count <= 1) return;
    const uint64_t next = uint64_t(g_prngState[0]) * 0x5CDCFAA7u + g_prngState[1];
    g_prngState[0] = static_cast<uint32_t>(next);
    g_prngState[1] = static_cast<uint32_t>(next >> 32);
    // Slot zero is the neutral animation; randomize only the remaining entries.
    const uint32_t index = (static_cast<uint32_t>(next) & 0x7FFFFFFF) % (count - 1) + 1;
    at<void*>(face, 0x4C) = at<void**>(list, 0)[index];
}
