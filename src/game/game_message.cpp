// Queue or immediately dispatch packed gameplay events.
#include "game/game_message.hpp"
#include <cstring>

extern "C" void RtlEnterCriticalSection(void*); // @ 0x82585E0C
extern "C" void RtlLeaveCriticalSection(void*); // @ 0x82585DFC
extern "C" uint8_t g_gameMessageQueueLock[32]; // @ 0x82619DA0
extern "C" uint32_t g_gameMessageQueueWords; // @ 0x825F3860
extern "C" uint8_t g_gameMessageQueueBank; // @ 0x825EE297
extern "C" uint8_t g_gameMessageQueue[8192]; // @ 0x825F3AA8
extern "C" uint32_t g_ui_state_counter; // @ 0x825F3864
extern "C" void* g_ui_object_ptrs[64]; // @ 0x825F3868
extern "C" uint32_t g_ui_object_types[64]; // @ 0x825F3968
extern "C" uint8_t g_ui_object_flags[64]; // @ 0x825F3A68

struct GameMessageGuard {
    uint8_t entered;
    void* lock;
};

// @ 0x821880D0 | size: 0x60
void GameMessageGuard_Enter(GameMessageGuard* guard) {
    if (guard->entered == 0) RtlEnterCriticalSection(guard->lock);
    guard->entered = 1;
}

// @ 0x82188130 | size: 0x60
void GameMessageGuard_Leave(GameMessageGuard* guard) {
    if (guard->entered == 1) RtlLeaveCriticalSection(guard->lock);
    guard->entered = 0;
}

namespace {
struct MessageSink {
    virtual void Destroy() = 0;
    virtual void OnMessage(GameEventHeader*) = 0;
};
struct InlineMessage {
    GameEventHeader header;
    uint32_t payload[255];
};
}

// Callbacks can change the registry count, receiver pointers and message flags.
// The category mask is taken once from the original message id.
// @ 0x8225E7F8 | size: 0xC4
void DispatchGameMessage(GameEventHeader* message) {
    const uint32_t category = 1u << (message->id >> 11);
    uint32_t count = g_ui_state_counter;
    for (uint32_t i = 0; i < count; ++i) {
        if ((g_ui_object_types[i] & category) == 0) continue;
        const uint8_t flags = message->flags;
        const uint8_t receiverFlags = g_ui_object_flags[i];
        if ((flags & 0x80) == 0 && ((receiverFlags | flags) & 0x1F) == 0
            && (receiverFlags & 0x80) == 0) continue;
        static_cast<MessageSink*>(g_ui_object_ptrs[i])->OnMessage(message);
        count = g_ui_state_counter;
    }
}

// Queue capacity/bank selection are maintained by the queue pump. A queued
// null payload preserves the existing words, as in the original.
// @ 0x8225E6E0 | size: 0x118
void PostGameMessage(uint32_t id, uint32_t flags, uint32_t payloadWords, const void* payload) {
    GameMessageGuard guard;
    guard.entered = 0;
    guard.lock = g_gameMessageQueueLock;
    GameMessageGuard_Enter(&guard);
    const uint32_t initialWords = g_gameMessageQueueWords;
    const uint32_t words = static_cast<uint8_t>(payloadWords);
    const bool immediate = (flags & 0x40) != 0;
    alignas(16) InlineMessage local;
    auto* message = immediate ? &local.header : reinterpret_cast<GameEventHeader*>(
        g_gameMessageQueue + (uint32_t(g_gameMessageQueueBank) * 1024 + initialWords) * 4);
    message->id = static_cast<uint16_t>(id);
    message->flags = static_cast<uint8_t>(flags);
    message->payloadWords = static_cast<uint8_t>(payloadWords);
    if (words != 0 && payload != nullptr)
        std::memcpy(reinterpret_cast<uint8_t*>(message) + 4, payload, words * 4);
    else if (immediate && words != 0)
        std::memset(reinterpret_cast<uint8_t*>(message) + 4, 0, words * 4);
    if (immediate) DispatchGameMessage(message);
    else g_gameMessageQueueWords = initialWords + words + 1;
    if (guard.entered != 0) GameMessageGuard_Leave(&guard);
}
