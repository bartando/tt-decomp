// Sample and blend the mover channels of up to three locomotion clips.
#include "../game/player/pong_player.hpp"
#include "../game/creature/pong_creature.hpp"

extern float LocomotionStateAnim_BB48_g(void*, int); // @ 0x820DBB48
// r4/r5 are unused; r6 receives a 32-byte rotation/translation pair.
extern uint32_t LocomotionStateAnim_ExtractDisplacement(
    void*, void*, void*, void*, float, float); // @ 0x82248C58
extern void rage_debugLog(const char*, ...); // @ 0x8240E6D0
extern "C" const char g_rootMotionMissingChannels[]; // @ 0x820289F4
extern "C" const float lbl_82606750[4]; // @ 0x82606750

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
struct alignas(16) MotionSample { vec3 rotation, translation; };

float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
float subtractVmx(float a, float b) {
    return flushVmx(flushVmx(a) - flushVmx(b));
}
float blendLane(float old, float sampled, float weight) {
    const float delta = subtractVmx(sampled, old);
    const float weighted = flushVmx(flushVmx(delta) * flushVmx(weight));
    return flushVmx(flushVmx(old) + flushVmx(weighted));
}

bool sample(void* layers, int index, float end, float delta, MotionSample* output) {
    void* clip = at<void*>(layers, 0x10 + index * 4);
    const float duration = at<float>(clip, 0x0C);
    const uint32_t result = LocomotionStateAnim_ExtractDisplacement(
        clip, nullptr, nullptr, output, duration * end, delta * duration);
    if (static_cast<uint8_t>(result)) return true;
    rage_debugLog(g_rootMotionMissingChannels, at<const char*>(clip, 0x20));
    return false;
}
}

// The first successful sample replaces all four lanes. A failed first sample
// leaves the destination's w lane alone; subsequent failures retain the blend.
// @ 0x820DBBF8 | size: 0x1F8
vec3* LocomotionStateAnim_BBF8_g(vec3* output, void* layers, float start, float end) {
    output->x = output->y = output->z = 0.0f;
    if (start > end) {
        // A failed reverse sample leaves the original temporary's w undefined.
        // Give that error-only lane a defined value on the host.
        alignas(16) vec3 reversed = {};
        LocomotionStateAnim_BBF8_g(&reversed, layers, end, start);
        *output = {subtractVmx(lbl_82606750[0], reversed.x),
                   subtractVmx(lbl_82606750[1], reversed.y),
                   subtractVmx(lbl_82606750[2], reversed.z),
                   subtractVmx(lbl_82606750[3], reversed._pad)};
        return output;
    }

    auto* animation = static_cast<LocomotionStateAnim*>(layers);
    int index = 0;
    const int count = animation->CountActiveAnimLayers();
    while (index < count && !(LocomotionStateAnim_BB48_g(layers, index) > 0.0f)) ++index;
    const float delta = end - start;
    MotionSample sampled;
    if (!sample(layers, index, end, delta, &sampled)) return output;
    *output = sampled.translation;
    ++index;
    if (index >= animation->CountActiveAnimLayers()) return output;
    do {
        const float weight = LocomotionStateAnim_BB48_g(layers, index);
        if (weight > 0.0f) {
            if (!sample(layers, index, end, delta, &sampled)) return output;
            const vec3 old = *output;
            *output = {blendLane(old.x, sampled.translation.x, weight),
                       blendLane(old.y, sampled.translation.y, weight),
                       blendLane(old.z, sampled.translation.z, weight),
                       blendLane(old._pad, sampled.translation._pad, weight)};
        }
        ++index;
    } while (index < animation->CountActiveAnimLayers());
    return output;
}
