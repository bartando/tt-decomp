// Serve animation hit positions, including the current ball's time offset.
#include "pong_player.hpp"

struct pongSwingAnimView;
extern "C" void** g_ppBallInst; // @ 0x8271A2F4
extern "C" float g_serveContactTimeBias; // @ 0x825D30BC
extern void phBoundCapsule_RotateAxisYZ(float*, float); // @ 0x8223AB70

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}

float addVmx(float a, float b) {
    return flushVmx(flushVmx(a) + flushVmx(b));
}

float multiplyVmx(float a, float b) {
    return flushVmx(flushVmx(a) * flushVmx(b));
}
}

// @ 0x820DD978 | size: 0x74
vec3* game_D978(vec3* output, void* clip, uint32_t hitIndex) {
    void* hit = at<void**>(clip, 0x2C)[hitIndex];
    const vec3 base = at<vec3>(hit, 0x30);
    *output = base;
    float ballTime = 0.0f;
    if (void* instance = *g_ppBallInst)
        ballTime = at<float>(at<void*>(at<void*>(instance, 4), 0x0C), 8);
    const vec3 velocity = at<vec3>(hit, 0x40);
    const float time = ballTime + g_serveContactTimeBias;
    *output = {addVmx(base.x, multiplyVmx(velocity.x, time)),
               addVmx(base.y, multiplyVmx(velocity.y, time)),
               addVmx(base.z, multiplyVmx(velocity.z, time)),
               addVmx(base._pad, multiplyVmx(velocity._pad, time))};
    return output;
}

// The optional half-turn depends on the position's z, not the sampled hit z.
// @ 0x820DD1C0 | size: 0x78
vec3* game_D1C0(vec3* output, pongSwingAnimView* animation) {
    game_D978(output, at<void*>(animation, 0x24), at<uint32_t>(animation, 0x28));
    if (at<float>(animation, 0x48) < 0.0f)
        phBoundCapsule_RotateAxisYZ(&output->x, 3.1415927410125732f);
    const vec3 sampled = *output;
    const vec3 origin = at<vec3>(animation, 0x40);
    *output = {addVmx(sampled.x, origin.x), addVmx(sampled.y, origin.y),
               addVmx(sampled.z, origin.z), addVmx(sampled._pad, origin._pad)};
    return output;
}
