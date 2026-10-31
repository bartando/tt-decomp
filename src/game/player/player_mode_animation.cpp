// Animation resets used when the inner player state changes movement mode.
#include <cstdint>
#include <cstring>
#include "link/tt_alias.h"

// Isolated declaration of the member's recovered ABI while the creature
// thread owns its implementation. Bind directly to that member's native symbol.
extern bool SetupAnimationPair(void* animations, uint32_t first, uint32_t second,
                               void* unusedR6, const void* parameters)
    __asm__(TT_ASM_SYMBOL("_ZN19LocomotionStateAnim18SetupAnimationPairEjjPvPKv")); // @ 0x8224C418

extern "C" uint8_t g_swingInFlightFlag; // @ 0x8260633C
extern "C" uint32_t g_swingCountFlag; // @ 0x82606340
extern void crAnimBlenderState_Init(void*); // @ 0x8224C810
extern void LocomotionStateAnim_6D48(void*); // @ 0x820D6D48
extern void LocomotionStateAnim_2130_g(void*); // @ 0x820C2130
extern void game_CD20(void*); // @ 0x820DCD20
extern void LocomotionStateAnim_BlendLocomotionAnims(uint32_t, void*, void*, float); // @ 0x8224C128
extern void LocomotionStateAnim_TransitionLocomotionState(uint32_t, void*, void*, float); // @ 0x8224C288
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" uint32_t g_prngState[2]; // @ 0x825CA2C8
extern "C" uint8_t g_faceAnimDirty; // @ 0x82606324
extern "C" float g_kPowerBlend; // @ 0x825C2EA0
extern "C" const float lbl_825C5938; // @ 0x825C5938
extern "C" uint8_t g_playerModeAnimationBytes[28]; // @ 0x825EAB48
extern "C" const float g_playerModeAnimationPairParams[8]; // @ 0x825CB850

namespace {
struct ModeLocomotion {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Start(uint32_t, const void*, uint32_t) = 0;
};
struct ModeAnimation {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Reset() = 0;
};
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

void clearSwingTiming(void* timing) {
    const unsigned zeroFields[] = {0x0C, 0x10, 0x14, 0x20, 0x24,
                                   0x40, 0x44, 0x48, 0x50, 0x54, 0x58};
    for (unsigned offset : zeroFields) at<float>(timing, offset) = 0.0f;
    at<float>(timing, 0x18) = 1.0f;
    at<float>(timing, 0x1C) = 1.0f;
    at<uint8_t>(timing, 0x8D) = 0;
    g_swingInFlightFlag = 0;
    g_swingCountFlag = 0;
}
}

// @ 0x820CE2B8 | size: 0xC8
void game_E2B8(void* state) {
    at<uint8_t>(state, 0x13) = 1;
    at<ModeLocomotion*>(state, 0x94)->Start(0, nullptr, 0);
    void* phase = at<void*>(state, 0x88);
    crAnimBlenderState_Init(static_cast<uint8_t*>(phase) + 0x10);
    at<float>(phase, 0x19C) = 0.0f;
    clearSwingTiming(at<void*>(state, 0x7C));
}

// @ 0x820CBBC8 | size: 0x34C
extern "C" void LocomotionStateAnim_BBC8_g(void* state) {
    at<void*>(state, 0x78) = nullptr;
    at<uint8_t>(state, 0x14) = 0;
    for (unsigned offset = 0x64; offset <= 0x74; offset += 4) {
        if (void* record = at<void*>(state, offset)) {
            LocomotionStateAnim_6D48(static_cast<uint8_t*>(record) + 0x20);
            std::memset(static_cast<uint8_t*>(record) + 0x180, 0, 16);
        }
    }
    if (void* timing = at<void*>(state, 0x7C)) clearSwingTiming(timing);
    if (void* recovery = at<void*>(state, 0x80)) game_CD20(recovery);
    if (void* phase = at<void*>(state, 0x88)) {
        crAnimBlenderState_Init(static_cast<uint8_t*>(phase) + 0x10);
        at<float>(phase, 0x19C) = 0.0f;
    }
    if (auto* secondary = at<ModeAnimation*>(state, 0x90)) secondary->Reset();
    if (void* face = at<void*>(state, 0x84)) {
        at<float>(face, 0x0C) = 0.0f;
        at<float>(face, 0x10) = 0.0f;
        at<float>(face, 0x18) = 0.0f;
        if (void* active = at<void*>(face, 0x44)) at<float>(active, 0x14) = 0.0f;
        at<void*>(face, 0x44) = nullptr;
        g_faceAnimDirty = 0;
        LocomotionStateAnim_2130_g(face);
        const uint64_t next = uint64_t(g_prngState[0]) * 0x5CDCFAA7u + g_prngState[1];
        g_prngState[0] = static_cast<uint32_t>(next);
        g_prngState[1] = static_cast<uint32_t>(next >> 32);
        const float sample = static_cast<float>(static_cast<uint32_t>(next) & 0x7FFFFF);
        at<float>(face, 0x14) = __builtin_fmaf(sample, 8.344650268554688e-7f, g_kPowerBlend);
    }
    at<ModeAnimation*>(state, 0x8C)->Reset();
    if (auto* locomotion = at<ModeLocomotion*>(state, 0x94)) {
        const uint32_t slot = at<uint32_t>(state, 8);
        const void* transform = at<void*>(g_input_obj_ptr, (slot + 17) * 4);
        locomotion->Start(1, transform, 0);
    }
    void* skeleton = at<void*>(state, 0x1C);
    at<float>(state, 0xB0) = lbl_825C5938;
    at<uint8_t>(state, 0x13) = 0;
    using Apply = void (*)(uint32_t, void*, void*, float);
    const Apply apply = at<uint32_t>(at<void*>(skeleton, 4), 0x14) & 1
        ? LocomotionStateAnim_TransitionLocomotionState : LocomotionStateAnim_BlendLocomotionAnims;
    // The original snapshots the list length, but reloads the entry pointer.
    const uint16_t count = at<uint16_t>(state, 0x4C);
    for (uint32_t i = 0; i < count; ++i)
        apply(at<uint32_t*>(state, 0x48)[i], nullptr, skeleton, 0.0f);
    SetupAnimationPair(static_cast<uint8_t*>(state) + 0x40, 5, 6, nullptr,
                       g_playerModeAnimationPairParams);
    at<uint32_t>(state, 0xAC) = 1;
    const uint32_t slot = at<uint32_t>(state, 8);
    std::memset(g_playerModeAnimationBytes + slot * 14, 0, 14);
}
