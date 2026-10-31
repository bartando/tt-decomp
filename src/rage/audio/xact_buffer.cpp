#include "audio/xact_buffer.hpp"
#include "crt/crt_init.h"
#include "rage/ptr32.hpp"
#include <cstdint>
#include <cstring>

// @ 0x8245BF40 | size: 0x60
void* msgMsgSink_BF40_g(void* storage) {
    auto* bytes = static_cast<uint8_t*>(storage);
    std::memset(bytes, 0, 0x8C);
    *reinterpret_cast<rage::ptr32<uint8_t>*>(bytes + 0x84) = bytes + 0x6C;
    return storage;
}

// @ 0x8245BFA0 | size: 0x1C
void atSingleton_BFA0_g(void* buffer) {
    if (void* data = rage::load_ptr32<void>(buffer, 0x78))
        _locale_register(data, static_cast<int>(0xAB840003u));
}
