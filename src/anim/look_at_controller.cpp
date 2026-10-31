#include "look_at_controller.hpp"
#include "rage/ptr32.hpp"

// @ 0x820D28F0
void game_28F0(pongLookAtController* controller, const float* target, int which) {
    if ((rage::load_ptr32<pongLookAtTargetOps>(controller, 0x34)->IsEnabled() & 0xffu) != 0)
        rage::load_ptr32<pongLookAtTargetOps>(controller, 0x34)->SetTarget(target, which);
}

// @ 0x820D2A40
void game_2A40(pongLookAtController* controller) {
    if ((rage::load_ptr32<pongLookAtTargetOps>(controller, 0x34)->IsEnabled() & 0xffu) != 0) {
        const float* target = reinterpret_cast<const float*>(
            reinterpret_cast<const uint8_t*>(controller) + 0x10);
        rage::load_ptr32<pongLookAtTargetOps>(controller, 0x34)->SaveTarget(target);
    }
}
