// Facial animation progression and pose composition used by the auxiliary layer.
#include "../creature/pong_creature.hpp"
#include "../../rage/animation/rage_anim.hpp"
#include "../../anim/locomotion.hpp"
#include "game/game_message.hpp"
#include <cstdint>

extern "C" uint32_t g_prngState[2]; // @ 0x825CA2C8
extern "C" float g_kPowerBlend; // @ 0x825C2EA0
extern "C" uint8_t g_faceAnimDirty; // @ 0x82606324
extern "C" uint32_t g_auxiliaryRandomBlendGuard[2]; // @ 0x825C9EC4
extern "C" uint32_t g_auxiliaryPoseBlendGuard[2]; // @ 0x825C9F14
struct AuxiliaryTimeManager {
    void* vtable;
    uint32_t reserved;
    float frameSeconds;
};
extern "C" AuxiliaryTimeManager g_sysTimeManager; // @ 0x825CAEB8
extern float LocomotionStateAnim_2858(void*, void*, uint32_t); // @ 0x820C2858
extern void LocomotionStateAnim_28B0_w(void*); // @ 0x820C28B0
extern void LocomotionStateAnim_2130_g(void*); // @ 0x820C2130
extern uint32_t LocomotionStateAnim_81A8(void*, uint32_t, uint32_t, void*, float*); // @ 0x822481A8
void playerPose_CopyDof(void*, void*, float, uint32_t, uint32_t); // @ 0x82378450

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
float clampWeight(float raw) {
    const float nonnegative = raw >= 0.0f ? raw : 0.0f;
    return double(nonnegative) - 1.0 >= 0.0 ? 1.0f : nonnegative;
}
uint32_t nextRandom() {
    const uint64_t next = uint64_t(g_prngState[0]) * 0x5CDCFAA7u + g_prngState[1];
    g_prngState[0] = static_cast<uint32_t>(next);
    g_prngState[1] = static_cast<uint32_t>(next >> 32);
    return static_cast<uint32_t>(next);
}
uint32_t recipient(void* state) {
    const uint32_t shift = at<uint32_t>(state, 8) & 63;
    const uint32_t bit = shift < 32 ? 1u << shift : 0;
    return (bit & 0xFF) | 0x40;
}
float blendFactor(void* state, void* entry) {
    return static_cast<LocomotionStateAnim*>(state)->CalculateBlendFactor(entry);
}
void blendFrame(void* state, unsigned sourceOffset, rage::crAnimDofFilter filter,
                void* userData, float weight, unsigned destinationOffset = 0x34) {
    rage::crAnimFrame_ApplyMatchingDofs(at<rage::crAnimFrame*>(state, destinationOffset),
        at<const rage::crAnimFrame*>(state, sourceOffset), nullptr,
        filter, userData, clampWeight(weight), nullptr, LocomotionStateAnim_BB98);
}
struct CopyTarget {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Reserved3() = 0;
    virtual void Reserved4() = 0;
    virtual void Reserved5() = 0;
    virtual void CopyFrom(void*) = 0;
};
}

// @ 0x82378450 | size: 0x10
void playerPose_CopyDof(void* destination, void* source, float, uint32_t, uint32_t) {
    static_cast<CopyTarget*>(destination)->CopyFrom(source);
}

// @ 0x820C1978 | size: 0x214
void LocomotionStateAnim_1978(void* state) {
    const float timer = at<float>(state, 0x14) - g_sysTimeManager.frameSeconds;
    at<float>(state, 0x14) = timer;
    if (timer < 0.0f) {
        const float sample = static_cast<float>(nextRandom() & 0x7FFFFF);
        at<float>(state, 0x14) = __builtin_fmaf(sample, 8.344650268554688e-7f, g_kPowerBlend);
        if (at<uint8_t>(state, 4) && !at<void*>(state, 0x50)) {
            void* list = at<void*>(state, 0x94);
            const uint32_t count = at<uint16_t>(list, 4);
            if (count != 0) {
                const uint32_t index = (nextRandom() & 0x7FFFFFFF) % count;
                at<void*>(state, 0x50) = at<void**>(at<void*>(state, 0x94), 0)[index];
            }
        }
    }
    if (void* entry = at<void*>(state, 0x50)) {
        if (g_auxiliaryRandomBlendGuard[1] == 0 && g_auxiliaryPoseBlendGuard[1] == 0) {
            LocomotionStateAnim_2858(entry, at<void*>(state, 0x38), 1);
            const float weight = blendFactor(state, at<void*>(state, 0x50));
            blendFrame(state, 0x38, LocomotionStateAnim_81A8, at<void*>(state, 0x58), weight);
            if (at<float>(at<void*>(state, 0x50), 0x14) == 0.0f)
                at<void*>(state, 0x50) = nullptr;
        }
    }
}

// @ 0x820C1B90 | size: 0x154
void LocomotionStateAnim_1B90(void* state) {
    void* active = at<void*>(state, 0x44);
    if (!at<void*>(active, 0x1C)) return;
    LocomotionStateAnim_2858(active, at<void*>(state, 0x38), 1);
    active = at<void*>(state, 0x44);
    const float duration = at<float>(at<void*>(active, 0x1C), 0x0C);
    const float seconds = at<float>(active, 0x14) * duration;
    const float elapsedFrames = seconds * 30.0f;
    const float exitFrame = __builtin_fmaf(duration, 30.0f, -g_kPowerBlend);
    if (elapsedFrames >= exitFrame && !g_faceAnimDirty) {
        PostGameMessage(0x580F, recipient(state), 0, nullptr);
        g_faceAnimDirty = 1;
    }
    const float weight = blendFactor(state, at<void*>(state, 0x44));
    blendFrame(state, 0x38, nullptr, nullptr, weight);
    if (at<float>(at<void*>(state, 0x44), 0x14) == 0.0f) {
        at<void*>(state, 0x44) = nullptr;
        PostGameMessage(0x580E, recipient(state), 0, nullptr);
        g_faceAnimDirty = 0;
    }
}

// @ 0x820C1CE8 | size: 0x180
void LocomotionStateAnim_1CE8_g(void* state) {
    void* base = at<void*>(state, 0x48);
    void* bundle = at<void*>(base, 0x1C);
    const float time = at<float>(bundle, 0x0C) * at<float>(base, 0x14);
    LocomotionStateAnim_88E0_g(bundle, nullptr, at<void*>(state, 0x38), 0, 1, time);
    LocomotionStateAnim_28B0_w(base);
    if (void* selected = at<void*>(state, 0x4C)) {
        if (g_auxiliaryPoseBlendGuard[1] == 0) {
            LocomotionStateAnim_2858(selected, at<void*>(state, 0x3C), 1);
            float weight;
            if (void* active = at<void*>(state, 0x44)) weight = 1.0f - blendFactor(state, active);
            else if (void* queued = at<void*>(state, 0x50)) weight = 1.0f - blendFactor(state, queued);
            else weight = blendFactor(state, at<void*>(state, 0x4C));
            // PPC ble skips unordered weights as well as nonpositive ones.
            if (weight > 0.0f) blendFrame(state, 0x3C, nullptr, nullptr, weight, 0x38);
            if (at<float>(at<void*>(state, 0x4C), 0x14) == 0.0f)
                LocomotionStateAnim_2130_g(state);
        }
    }
    rage::crAnimFrame_ApplyMatchingDofs(at<rage::crAnimFrame*>(state, 0x34),
        at<const rage::crAnimFrame*>(state, 0x38), nullptr, nullptr, nullptr,
        0.0f, nullptr, playerPose_CopyDof);
}
