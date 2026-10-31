#include "rage/localized_font.hpp"
#include "rage/operator_new.hpp"
#include <cstring>

// @ 0x8240A250
void localizedFontResizeArray(void* array, uint32_t count) {
    auto* bytes = static_cast<uint8_t*>(array);
    uint16_t capacity;
    std::memcpy(&capacity, bytes + 6, sizeof(capacity));
    const uint16_t storedCount = static_cast<uint16_t>(count);
    if (capacity == 0) {
        // The capacity store truncates, but allocation still uses the full word.
        std::memcpy(bytes + 6, &storedCount, sizeof(storedCount));
        void* data = count ? rage_Alloc(count > 0x3FFFFFFFu ? UINT32_MAX : count * 4) : nullptr;
        const rage::ptr32<void> pointer(data);
        std::memcpy(bytes, &pointer, sizeof(pointer));
    }
    std::memcpy(bytes + 4, &storedCount, sizeof(storedCount));
}
