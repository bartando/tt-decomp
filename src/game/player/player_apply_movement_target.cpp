// Apply a court target to the player's mover, respecting serve-input gates.
#include <cstdint>

struct pongPlayer;
extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern bool pongPlayer_CheckServeInput(pongPlayer*); // @ 0x82195B60

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
void* mover(void* player) {
    return at<void*>(at<void*>(player, 0x1C4), 0xA8);
}
}

// Coordinates/contact are f1/f2/f3; the speed in f4 survives the input query.
// The original's fsel chain stores a constant one at mover+1C.
// @ 0x82195DF0 | size: 0xE4
void io_5DF0(pongPlayer* player, float x, float z, float contact, float speed) {
    const uint32_t slot = at<uint32_t>(player, 0x1D0);
    if (at<int32_t>(g_input_obj_ptr, (slot + 14) * 4) != 0
        && !pongPlayer_CheckServeInput(player)) return;

    const float speedSquared = speed * speed;
    at<float>(mover(player), 0x1C) = 1.0f;
    void* bound = mover(player);
    at<float>(bound, 0x48) = speed;
    at<float>(bound, 0x4C) = speedSquared;
    bound = mover(player);
    if (at<uint8_t>(bound, 0x40) & 2) return;
    at<float>(bound, 0x14) = z;
    at<float>(bound, 0x18) = contact;
    at<float>(bound, 0x10) = x;
    at<uint8_t>(bound, 0x40) &= 0xF7;
}
