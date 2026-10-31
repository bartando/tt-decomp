#include "ball_audio_envelope.hpp"
#include "../../physics/ph_physics.hpp"
#include <stdint.h>

namespace {
struct Envelope {
    float threshold;
    uint8_t active;
    uint8_t _pad05[7];
};
}

// @ 0x8216EA00
bool AudioControl_IsWithinActiveEnvelope(void* object) {
    auto* bytes = static_cast<uint8_t*>(object);
    auto* envelope = reinterpret_cast<const Envelope*>(bytes + 0x20);
    if (envelope->active == 0) return false;
    const float threshold = envelope->threshold;
    auto* durations = reinterpret_cast<const rage::phBoundCapsule*>(bytes + 0x2C);
    const float first = durations->SumFloatArray(0);
    if (!(first < threshold)) return false;
    return threshold <= durations->SumFloatArray(4);
}
