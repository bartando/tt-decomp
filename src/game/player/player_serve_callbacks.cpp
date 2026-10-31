// Serve-start query and the pending input-event reset that follows a serve.
#include <cstdint>
#include "rage/sys_callback.hpp"

struct pongSwingAnimView;

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x820DD388 | size: 0x60
bool game_D388(pongSwingAnimView* blender) {
    if (at<int32_t>(blender, 0x6C) == 0) return false;
    int32_t busy;
    sysCallback_Invoke(static_cast<uint8_t*>(static_cast<void*>(blender)) + 0x60, &busy);
    return busy != 0;
}

// The records retain their keys and payloads; only their queued state is reset.
// @ 0x821CE0F0 | size: 0xBC
void game_E0F0(void* object) {
    if (at<uint8_t>(object, 0x68CF9) == 0) return;
    at<uint32_t>(object, 0x68CF4) = 0;
    void* queue = at<void*>(object, 0x68D18);
    auto* records = at<uint8_t*>(queue, 0x0C);
    for (int32_t i = 0; i < at<int32_t>(queue, 0x08); ++i) {
        at<uint32_t>(records, i * 0x14 + 0x08) = 0;
        at<int32_t>(records, i * 0x14 + 0x0C) = -1;
        at<uint32_t>(records, i * 0x14 + 0x10) = 0;
    }
    at<uint32_t>(queue, 0x18) = at<uint32_t>(queue, 0x10);
    at<uint32_t>(queue, 0x20) = at<uint32_t>(queue, 0x10);
    void* slots = at<void*>(object, 0x68D1C);
    auto* entries = at<uint8_t*>(slots, 0x08);
    for (int32_t i = 0; i < at<int32_t>(slots, 0x04); ++i)
        at<uint32_t>(entries, i * 8) = 0;
}
