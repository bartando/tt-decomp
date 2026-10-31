// Inner-creature mode transitions used by the outer-player movement controller.
#include "../creature/pong_creature.hpp"
#include <cstdint>

struct pongPlayer;
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" void* g_sceneRenderObj; // @ 0x82606430
extern "C" uint32_t g_selectionKillSignal[2]; // @ 0x825C9F28
extern "C" uint8_t g_playerModeTransitionFlag; // @ 0x82606327
extern "C" uint8_t g_playerModeTransform[64]; // @ 0x82606910
extern "C" void pongPlayer_7C78_g(pongPlayer*, uint8_t); // @ 0x820C7C78
extern uint8_t game_C690(pongPlayer*); // @ 0x8218C690
extern void game_E2B8(void*); // @ 0x820CE2B8
extern "C" void LocomotionStateAnim_BBC8_g(void*); // @ 0x820CBBC8
extern float pongMover_GetInputSpeed(pongMover*); // @ 0x820CB4D0
extern int io_Input_poll_9D68(void*); // @ 0x821C9D68
extern void pg_E6E0(int, uint8_t, int, int); // @ 0x8225E6E0
extern void PostPageGroupMessageFmt(uint32_t, uint32_t, const char*, ...); // @ 0x8225E480

namespace {
struct ModeAnimation {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void ChangeMode() = 0;
};
struct ModeLocomotion {
    virtual void Reserved0() = 0;
    virtual void Reserved1() = 0;
    virtual void Reserved2() = 0;
    virtual void Start(uint32_t, const void*, uint32_t) = 0;
};
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
float clampVelocity(float value, float speed) {
    const float delta = value - (-speed);
    const float raised = delta >= 0.0f ? value : -speed;
    return double(raised) - double(speed) >= 0.0 ? speed : raised;
}
}

// @ 0x820C6CF8 | size: 0x340
void pg_6CF8(void* creature, int32_t mode) {
    int32_t previous = at<int32_t>(creature, 0xC8);
    if (previous == mode) {
        void* state = at<void*>(creature, 0xBC);
        if (!at<uint8_t>(state, 0x14) && mode == 7) {
            at<uint8_t>(state, 0x14) = 1;
            at<ModeAnimation*>(state, 0x8C)->ChangeMode();
        }
        return;
    }

    if (previous == 3 && mode == 4) {
        void* state = at<void*>(creature, 0xBC);
        at<uint8_t>(state, 0x13) = 0;
        at<ModeLocomotion*>(state, 0x94)->Start(1, nullptr, 0);
        at<uint8_t>(at<void*>(creature, 0xA8), 0x40) &= 0xFB;
    } else if (previous == 7) {
        at<uint8_t>(creature, 0xD4) = g_selectionKillSignal[1] == 0;
        void* state = at<void*>(creature, 0xBC);
        at<uint8_t>(state, 0x14) = 0;
        at<ModeAnimation*>(state, 0x8C)->ChangeMode();
        const uint32_t slot = at<uint32_t>(creature, 0xCC);
        const uint32_t index = at<uint32_t>(g_sceneRenderObj, (slot + 0x21) * 4);
        auto* player = at<pongPlayer*>(g_sceneRenderObj, (index + 0x1D) * 4);
        const bool flip = game_C690(player) != 0;
        static_cast<pongMover*>(at<void*>(creature, 0xA8))->Reset(flip);
    }

    previous = at<int32_t>(creature, 0xC8);
    if (previous == 1) at<uint8_t>(creature, 0xC4) = 0;
    if (previous != 3 && mode == 2) {
        game_E2B8(at<void*>(creature, 0xBC));
        auto* mover = static_cast<pongMover*>(at<void*>(creature, 0xA8));
        at<uint8_t>(mover, 0x40) |= 4;
        const float speed = pongMover_GetInputSpeed(mover);
        g_playerModeTransitionFlag = 0;
        at<float>(mover, 0x30) = clampVelocity(at<float>(mover, 0x30), speed);
        at<float>(mover, 0x34) = clampVelocity(at<float>(mover, 0x34), speed);
    } else if (mode == 7) {
        LocomotionStateAnim_BBC8_g(at<void*>(creature, 0xBC));
        void* state = at<void*>(creature, 0xBC);
        at<uint8_t>(state, 0x14) = 1;
        at<ModeAnimation*>(state, 0x8C)->ChangeMode();
    } else if (mode == 3) {
        void* mover = at<void*>(creature, 0xA8);
        void* settings = g_input_obj_ptr;
        const uint32_t slot = at<uint32_t>(mover, 0x44);
        const void* transform = at<void*>(settings, (slot + 0x11) * 4);
        __builtin_memcpy(g_playerModeTransform, transform, 64);
        if (static_cast<uint8_t>(io_Input_poll_9D68(settings))) {
            const uint32_t player = at<uint32_t>(creature, 0xCC);
            if (at<int32_t>(settings, (player + 14) * 4) == 1)
                pg_E6E0(0x3809, static_cast<uint8_t>((player == 0 ? 1 : 2) | 0x40), 0, 0);
        }
    } else if (mode == 1) {
        at<uint8_t>(creature, 0xC4) = 1;
    }

    if (at<int32_t>(creature, 0xC8) == 3) {
        const uint32_t slot = at<uint32_t>(creature, 0xCC);
        const uint32_t bit = (slot & 0x20) ? 0 : (1u << (slot & 31));
        PostPageGroupMessageFmt(0x101C, 0x80 | (bit & 0x7F), "i", mode == 2 ? 1 : 0);
    }
    if (mode != 7 && mode != 0) {
        at<uint8_t>(creature, 0xE6) = 0;
        at<uint8_t>(creature, 0xE7) = 0;
    }
    pongPlayer_7C78_g(static_cast<pongPlayer*>(creature), 0);
    at<int32_t>(creature, 0xC8) = mode;
}
