#include "rage/swf_text.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>
#include <cstring>

extern void* g_swfTextPool; // @ 0x82602844
extern "C" char g_swfInternedText[8192]; // @ 0x82602848

namespace {
struct TextChunk {
    char bytes[12];
    rage::ptr32<TextChunk> next;
};
struct TextPool {
    uint8_t _pad00[6];
    uint16_t freeCount;
    uint8_t _pad08[4];
    rage::ptr32<TextChunk> freeList;
};
static_assert(sizeof(TextChunk) == 16);
static_assert(sizeof(TextPool) == 16);
}

// @ 0x823FABC0
extern "C" void* swfCopyString(const char* text) {
    auto* pool = static_cast<TextPool*>(g_swfTextPool);
    const size_t count = std::strlen(text) / 12 + 1;
    rage::ptr32<TextChunk> head;
    rage::ptr32<TextChunk>* link = &head;
    for (size_t i = 0; i < count; ++i) {
        TextChunk* chunk = pool->freeList.get();
        --pool->freeCount;
        // Active chunks use the first word as text; free chunks use it as the
        // free-list link. It remains a four-byte game pointer in either state.
        pool->freeList = rage::load_ptr32<TextChunk>(chunk, 0);
        chunk->next = nullptr;
        std::memset(chunk->bytes, 0, sizeof(chunk->bytes));
        *link = chunk;
        std::memcpy(chunk->bytes, text, sizeof(chunk->bytes));
        text += sizeof(chunk->bytes);
        link = &chunk->next;
    }
    *link = nullptr;
    return head.get();
}

// The flags argument is unused, including in the recursive release.
// @ 0x823F8A38
extern "C" void* swfReleaseText(void* text, int /*freeStorage*/) {
    auto* chunk = static_cast<TextChunk*>(text);
    if (chunk->next) swfReleaseText(chunk->next.get(), 1);
    // Reload after recursion, as retail does.
    auto* pool = static_cast<TextPool*>(g_swfTextPool);
    const rage::ptr32<TextChunk> nextFree = pool->freeList;
    std::memcpy(chunk->bytes, &nextFree, sizeof(nextFree));
    pool->freeList = chunk;
    ++pool->freeCount;
    return chunk;
}

// @ 0x823F9FB0
extern "C" const char* swfInternText(const char* text) {
    int freeSlot = -1;
    for (int i = 0; i < 128; ++i) {
        char* slot = g_swfInternedText + i * 64;
        if (freeSlot == -1 && slot[0] == '\0') freeSlot = i;
        if (slot[0] != '\0' && std::strcmp(slot, text) == 0) return slot;
    }
    if (freeSlot < 0) return nullptr;
    char* slot = g_swfInternedText + freeSlot * 64;
    // Retail uses strncpy's exact bound: a 64-byte input need not terminate.
    std::strncpy(slot, text, 64);
    return slot;
}
