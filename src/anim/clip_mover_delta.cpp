// Express the current mover pose relative to its earlier sampled pose.
#include "mover_dof.hpp"
#include "rage/mat44.hpp"

extern bool LocomotionStateAnim_EvaluateChannel(void*, void*, void*, float); // @ 0x82248828
extern void LocomotionStateAnim_AD30_g(float*, const float*); // @ 0x8223AD30
extern void LocomotionStateAnim_B218_g(float*, const float*); // @ 0x8223B218
namespace rage {
extern bool mat44InverseAffineInPlace(float*); // @ 0x820D7B30
}
extern "C" void* const lbl_82027BF4[]; // @ 0x82027BF4
extern "C" void* const lbl_82027B9C[]; // @ 0x82027B9C

namespace {
// A view of the existing DOF virtual interface, not a concrete replacement.
// Getter/setter slots differ between quaternion and vector DOFs.
struct MoverDof {
    virtual void Reserved00() = 0;
    virtual void Reserved01() = 0;
    virtual void Reserved02() = 0;
    virtual void Reserved03() = 0;
    virtual void Reserved04() = 0;
    virtual void Reserved05() = 0;
    virtual void Reserved06() = 0;
    virtual void Reserved07() = 0;
    virtual void Reserved08() = 0;
    virtual void Reserved09() = 0;
    virtual void Reserved10() = 0;
    virtual void Reserved11() = 0;
    virtual void Reserved12() = 0;
    virtual void Reset() = 0;                         // 13
    virtual const float* GetVector() = 0;            // 14
    virtual const float* GetQuaternion() = 0;        // 15
    virtual void Reserved16() = 0;
    virtual void SetVector(const float*) = 0;        // 17
    virtual void SetQuaternion(const float*) = 0;    // 18
};
}

// r4/r5 are unused. Even the zero-step and missing-channel paths return 1;
// those paths reset the supplied DOFs instead of leaving stale motion behind.
// @ 0x82248DB0 | size: 0x1E8
uint32_t LocomotionStateAnim_8DB0_g(void* clip, void*, void*, void* rotationObject,
                                  void* translationObject, float time, float delta) {
    auto* rotation = static_cast<MoverDof*>(rotationObject);
    auto* translation = static_cast<MoverDof*>(translationObject);
    const float difference = time - delta;
    const float amount = difference >= 0.0f ? delta : time;
    if (amount > 0.0f) {
        // Padding lanes are unused by the affine math; initialize them on host.
        alignas(16) float current[16] = {};
        LocomotionStateAnim_AD30_g(current, rotation->GetQuaternion());
        __builtin_memcpy(current + 12, translation->GetVector(), 16);
        const float previousTime = time - amount;

        MoverDofStorage earlierRotation;
        earlierRotation.vtable = lbl_82027BF4;
        earlierRotation.flags = 1;
        earlierRotation.type = 6;
        earlierRotation.id = 0;
        MoverDofStorage earlierTranslation;
        earlierTranslation.vtable = lbl_82027B9C;
        earlierTranslation.flags = 0;
        earlierTranslation.type = 5;
        earlierTranslation.id = 0;
        if (LocomotionStateAnim_EvaluateChannel(clip, nullptr, &earlierRotation, previousTime)
            && LocomotionStateAnim_EvaluateChannel(clip, nullptr, &earlierTranslation, previousTime)) {
            alignas(16) float previous[16] = {};
            LocomotionStateAnim_AD30_g(previous, earlierRotation.value);
            __builtin_memcpy(previous + 12, earlierTranslation.value, 16);
            rage::mat44InverseAffineInPlace(previous);
            rage::mat44ComposeAffineInPlace(current, previous);
            alignas(16) float quaternion[4];
            LocomotionStateAnim_B218_g(quaternion, current);
            rotation->SetQuaternion(quaternion);
            translation->SetVector(current + 12);
            return 1;
        }
    }
    rotation->Reset();
    translation->Reset();
    return 1;
}
