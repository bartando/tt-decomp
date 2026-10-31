// Evaluate a clip's mover rotation and translation, then extract their delta.
#include <cstdint>
#include <cstddef>

extern bool LocomotionStateAnim_EvaluateChannel(void*, void*, void*, float); // @ 0x82248828
// r4/r5 are unused; the two sampled DOFs occupy r6 and r7.
extern uint32_t LocomotionStateAnim_8DB0_g(
    void*, void*, void*, void*, void*, float, float); // @ 0x82248DB0
extern "C" void* const lbl_82027BF4[]; // crAnimDofQuaternion vtable @ 0x82027BF4
extern "C" void* const lbl_82027B9C[]; // crAnimDofVector3 vtable @ 0x82027B9C

namespace {
// Compact construction view of the two stack DOFs. Only their metadata and
// value are used; dispatch remains inside the existing channel helpers.
struct alignas(16) MoverDof {
    const void* vtable;
    uint8_t flags;
    uint8_t type;
    uint16_t id;
    uint8_t reserved[12 - sizeof(void*)];
    float value[4];
};
static_assert(offsetof(MoverDof, value) == 0x10, "mover DOF value offset");
static_assert(sizeof(MoverDof) == 0x20, "mover DOF size");
#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(offsetof(MoverDof, flags) == 4, "mover DOF flags offset");
static_assert(offsetof(MoverDof, type) == 5, "mover DOF type offset");
static_assert(offsetof(MoverDof, id) == 6, "mover DOF id offset");
#endif

float clipDuration(void* clip) {
    return *reinterpret_cast<float*>(static_cast<uint8_t*>(clip) + 0x0C);
}
}

// r4/r5 carry no inputs. Output is a 32-byte rotation/translation pair and
// stays untouched unless both channel evaluations and delta extraction pass.
// @ 0x82248C58 | size: 0x158
uint32_t LocomotionStateAnim_ExtractDisplacement(
    void* clip, void*, void*, void* output, float time, float delta) {
    MoverDof rotation;
    rotation.vtable = lbl_82027BF4;
    // The original preserves an uninitialized high nibble; use zero there.
    rotation.flags = 1;
    rotation.type = 6;
    rotation.id = 0;
    MoverDof translation;
    translation.vtable = lbl_82027B9C;
    translation.flags = 0;
    translation.type = 5;
    translation.id = 0;

    if (!LocomotionStateAnim_EvaluateChannel(clip, nullptr, &rotation, time)) return 0;
    if (!LocomotionStateAnim_EvaluateChannel(clip, nullptr, &translation, time)) return 0;

    // fsel chooses zero for an unordered time, but retains an unordered delta.
    const double nonnegative = time >= 0.0f ? double(time) : 0.0;
    const float duration = clipDuration(clip);
    const float clampedTime = nonnegative - double(duration) >= 0.0
                            ? duration : float(nonnegative);
    const float forwardDelta = -double(delta) >= 0.0 ? 0.0f : delta;
    const uint32_t result = LocomotionStateAnim_8DB0_g(
        clip, nullptr, nullptr, &rotation, &translation, clampedTime, forwardDelta);
    if (!static_cast<uint8_t>(result)) return 0;

    __builtin_memcpy(output, rotation.value, sizeof rotation.value);
    __builtin_memcpy(static_cast<uint8_t*>(output) + 0x10,
                     translation.value, sizeof translation.value);
    return 1;
}
