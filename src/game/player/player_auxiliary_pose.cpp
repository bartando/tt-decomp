// Auxiliary facial pose update at the end of player pose assembly.
#include "../../rage/animation/rage_anim.hpp"
#include "game/game_message.hpp"
#include "../../anim/locomotion.hpp"
#include <cstdint>
#include <cstring>

extern "C" uint8_t g_matMgrGuard[20]; // @ 0x825C9EB0
extern "C" uint32_t g_auxiliaryPoseBlendGuard[2]; // @ 0x825C9F14
extern "C" void* g_pongMatchTiming; // @ 0x8271A2E8
extern void LocomotionStateAnim_1CE8_g(void*); // @ 0x820C1CE8
extern void LocomotionStateAnim_1B90(void*); // @ 0x820C1B90
extern void LocomotionStateAnim_1978(void*); // @ 0x820C1978
// The callback's full register contract matches crAnimDofFilter.
extern uint32_t LocomotionStateAnim_81A8(void*, uint32_t, uint32_t, void*, float*); // @ 0x822481A8

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x820C1E68 | size: 0x184
void LocomotionStateAnim_1E68_g(void* auxiliary, void* destination) {
    if (!at<uint8_t>(auxiliary, 4) || at<uint32_t>(g_matMgrGuard, 4) != 0) return;
    LocomotionStateAnim_1CE8_g(auxiliary);
    void* active = at<void*>(auxiliary, 0x44);
    if (active && g_auxiliaryPoseBlendGuard[1] == 0) {
        const float deadline = at<float>(auxiliary, 0x18);
        if (at<float>(g_pongMatchTiming, 0x30) >= deadline) {
            if (deadline != 0.0f) {
                char* name = at<char*>(active, 0x18);
                const int mask = at<int32_t>(auxiliary, 8) == 0 ? 1 : 2;
                const uint8_t words = static_cast<uint8_t>((std::strlen(name) + 4) >> 2);
                PostGameMessage(0x5810, mask, words, name);
                at<float>(auxiliary, 0x18) = 0.0f;
            }
            LocomotionStateAnim_1B90(auxiliary);
        }
    } else {
        LocomotionStateAnim_1978(auxiliary);
    }
    rage::crAnimFrame_ApplyMatchingDofs(
        static_cast<rage::crAnimFrame*>(destination),
        at<const rage::crAnimFrame*>(auxiliary, 0x34), nullptr,
        LocomotionStateAnim_81A8, at<void*>(auxiliary, 0x54),
        1.0f, nullptr, LocomotionStateAnim_BB98);
}
