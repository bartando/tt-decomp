// Clamp the requested shot position and choose the creature's movement target.
#include "pong_player.hpp"
#include "pong_gameplay_queries.hpp"

extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" bool pongPlayer_D598_g(void*); // @ 0x820CD598
extern float pongPlayer_C7A8_g(pongPlayer*); // @ 0x8218C7A8
extern void io_5DF0(pongPlayer*, float, float, float, float); // @ 0x82195DF0

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}

// The lower comparison rounds to float; the upper subtraction stays double.
float clampCourt(float value, float lower, float upper) {
    const float delta = value - lower;
    const float raised = delta >= 0.0f ? value : lower;
    return double(raised) - double(upper) >= 0.0 ? upper : raised;
}
}

// Returns 0 when an active opponent makes us retain the player's current root;
// otherwise writes the opponent's movement limit and returns 1.
// @ 0x821A5DF8 | size: 0x1D0
uint32_t pongPlayer_SetupShotTarget(void* target, vec3* position,
                                  float contactScale, float movementLimit) {
    pongPlayer* owner = at<pongPlayer*>(target, 0x30);
    vec3 lower, upper;
    pongMatchSettings_GetCourtBounds(g_input_obj_ptr, at<int32_t>(owner, 0x1D0), &lower, &upper);
    position->x = clampCourt(position->x, lower.x, upper.x);
    position->z = clampCourt(position->z, lower.z, upper.z);

    owner = at<pongPlayer*>(target, 0x30);
    void* opponent = at<void*>(owner, 0x1C4);
    void* state = at<void*>(opponent, 0xBC);
    void* timing = at<void*>(state, 0x7C);
    bool active = timing && !(at<float>(timing, 0x1C) >= at<float>(timing, 0x30));
    if (!active) active = pongPlayer_D598_g(state);
    const float speed = pongPlayer_C7A8_g(owner);
    at<float>(target, 0x494) = contactScale;
    at<vec3>(target, 0x480) = *position;
    at<float>(target, 0x484) = 1.0f;

    if (active && at<uint8_t>(at<void*>(target, 0x30), 0x19E0) == 0) {
        owner = at<pongPlayer*>(target, 0x30);
        const uint32_t slot = at<uint32_t>(owner, 0x1D0);
        const vec3 root = at<vec3>(static_cast<void**>(g_input_obj_ptr)[slot + 17], 0x30);
        io_5DF0(owner, root.x, root.z, contactScale, speed);
        at<uint8_t>(target, 0x490) = 1;
        return 0;
    }

    owner = at<pongPlayer*>(target, 0x30);
    void* bound = at<void*>(at<void*>(owner, 0x1C4), 0xA8);
    at<float>(bound, 0x50) = movementLimit;
    at<float>(bound, 0x54) = movementLimit * movementLimit;
    io_5DF0(at<pongPlayer*>(target, 0x30), position->x, position->z, contactScale, speed);
    at<uint8_t>(target, 0x490) = 0;
    return 1;
}
