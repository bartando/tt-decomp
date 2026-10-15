/**
 * xact_sink_forwards.cpp — two XACT sink helpers pong_network_io.cpp calls
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * The msgMsgSink_* functions are the XACT runtime (KNOWN_WRONG_LIFTS, "Not
 * game code"). msg_msg_sink.cpp defines these two with one argument and
 * drops the slot the original passes through in r4; pong_network_io.cpp
 * declares the two-argument form, which is what the asm takes.
 */

#include <cstdint>

void msgMsgSink_D168_sp(void* self, uint16_t slotIndex);   // @ 0x8244D168
void msgMsgSink_D1D8_sp(void* self, uint16_t slotIndex);   // @ 0x8244D1D8

// @ 0x82448B78 — msgMsgSink_8B78_g: if the object at +0x7C exists, walk its
// message chain from `slot` (tail call, r4 unchanged).
void msgMsgSink_8B78_g(void* self, uint16_t slot) {
    void* chain = *reinterpret_cast<void**>(static_cast<uint8_t*>(self) + 0x7C);
    if (chain == nullptr) {
        return;
    }
    msgMsgSink_D168_sp(chain, slot);
}

// @ 0x82448B90 — msgMsgSink_8B90_g: the same for msgMsgSink_D1D8_sp.
void msgMsgSink_8B90_g(void* self, uint16_t slot) {
    void* chain = *reinterpret_cast<void**>(static_cast<uint8_t*>(self) + 0x7C);
    if (chain == nullptr) {
        return;
    }
    msgMsgSink_D1D8_sp(chain, slot);
}
