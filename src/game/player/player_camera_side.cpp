// Resolve the active camera's data record and query its side flag.
#include <cstdint>

extern "C" void* g_input_obj_ptr; // @ 0x825EAB28
extern "C" void* g_pCourtState; // @ 0x8271A314
extern void* game_1700(void*); // @ 0x82101700

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// Both player modes must be 1 to select the alternate camera index.
// Missing indices, absent records and failed type checks all default to side 1.
// @ 0x821E7CC0 | size: 0xCC
uint8_t pongPlayer_7CC0_g(void* camera) {
    const bool alternate = at<int32_t>(g_input_obj_ptr, 0x38) == 1
                        && at<int32_t>(g_input_obj_ptr, 0x3C) == 1;
    const int32_t index = at<int32_t>(camera, alternate ? 0x0C : 0x08);
    if (index == -1) return 1;
    void* node = at<void**>(g_pCourtState, 0x2C)[index];
    if (!node) return 1;
    void* record = game_1700(node);
    if (!record) return 1;
    return at<uint32_t>(record, 0x30) == 0;
}
