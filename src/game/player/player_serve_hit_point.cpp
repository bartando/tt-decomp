// Serve animation hit positions, including the current ball's time offset.
#include "pong_player.hpp"

struct pongSwingAnimView;
struct pongServeBlenderView;
struct alignas(16) pongMatrix34 { vec3 a, b, c, d; };
extern "C" void** g_ppBallInst; // @ 0x8271A2F4
extern "C" float g_serveContactTimeBias; // @ 0x825D30BC
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" void* g_pongMatchTiming; // @ 0x8271A2E8
extern "C" void* g_activeBallNode; // @ 0x82606570
extern "C" uint8_t g_playerSlotPoseData[160]; // @ 0x82619990
extern void phBoundCapsule_RotateAxisYZ(float*, float); // @ 0x8223AB70
extern vec3* LocomotionStateAnim_BBF8_g(vec3*, void*, float, float); // @ 0x820DBBF8
extern void game_0A30(void*, void*, void*); // @ 0x821D0A30
extern void phBoundCapsule_0880_g(void*, void*, void*); // @ 0x821D0880

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

// Publish the serve's timing and root positions to this player's pose slot.
// @ 0x820DD3E8 | size: 0x180
void game_D3E8(pongSwingAnimView* animation) {
    const uint32_t slot = at<uint32_t>(animation, 4);
    uint8_t* output = g_playerSlotPoseData + slot * 80;
    void* clip = at<void*>(animation, 0x24);
    output[1] = at<int32_t>(clip, 0x10) == 1;
    const float now = at<float>(g_pongMatchTiming, 0x30);
    const float duration = at<float>(at<void*>(clip, 0x24), 0x0C);
    output[0] = 1;
    at<float>(output, 8) = duration + now;
    const float markerSeconds = static_cast<float>(at<int32_t>(clip, 0x1C))
                              * 0.03333333507180214f;
    at<float>(output, 0x20) = at<float>(animation, 0x30) + markerSeconds;

    const uint32_t hitIndex = at<uint32_t>(animation, 0x28);
    void* hit = at<void**>(clip, 0x2C)[hitIndex];
    void* transform = static_cast<void**>(g_input_obj_ptr)[slot + 17];
    const vec3 origin = at<vec3>(transform, 0x30);
    const vec3 target = at<vec3>(hit, 0x60);
    at<vec3>(output, 0x10) = {addVmx(origin.x, target.x), addVmx(origin.y, target.y),
                            addVmx(origin.z, target.z), addVmx(origin._pad, target._pad)};
    const float endTime = duration > 0.0f ? markerSeconds / duration : 0.0f;
    alignas(16) vec3 motion;
    LocomotionStateAnim_BBF8_g(&motion, hit, 0.0f, endTime);
    at<vec3>(output, 0x30) = {addVmx(origin.x, motion.x), addVmx(origin.y, motion.y),
                            addVmx(origin.z, motion.z), addVmx(origin._pad, motion._pad)};
}

// A held ball follows the sampled bone, advanced by its current time fraction.
// @ 0x820CE090 | size: 0xDC
void game_E090(pongServeBlenderView* blender, pongMatrix34* output) {
    const uint32_t playerSlot = at<uint32_t>(blender, 8);
    void* character = pongMatch_GetCharacterForSlot(g_input_obj_ptr, playerSlot);
    void* skeleton = at<void*>(at<void*>(character, 0x2C), 0x148);
    // The original reads an uninitialized row if ID conversion fails.
    alignas(16) pongMatrix34 sampledBone = {};
    game_0A30(skeleton, &sampledBone, at<void*>(blender, 0x1C));
    character = pongMatch_GetCharacterForSlot(g_input_obj_ptr, at<uint32_t>(blender, 8));
    skeleton = at<void*>(at<void*>(character, 0x2C), 0x148);
    phBoundCapsule_0880_g(skeleton, output, at<void*>(blender, 0x1C));

    float ballTime = 0.0f;
    if (void* instance = *g_ppBallInst)
        ballTime = at<float>(at<void*>(at<void*>(instance, 4), 0x0C), 8);
    const float inverseRate = 1.0f / at<float>(g_activeBallNode, 0x8C);
    const float remaining = 1.0f - inverseRate;
    const float time = remaining * ballTime;
    const vec3 motion = sampledBone.a;
    const vec3 origin = output->d;
    output->d = {addVmx(origin.x, multiplyVmx(motion.x, time)),
                 addVmx(origin.y, multiplyVmx(motion.y, time)),
                 addVmx(origin.z, multiplyVmx(motion.z, time)),
                 addVmx(origin._pad, multiplyVmx(motion._pad, time))};
}
