#include "stream_configuration.hpp"
#include "rage/ptr32.hpp"

extern "C" const float g_phStreamInitialInterval; // @ 0x82003DA8

// @ 0x824662F8
int32_t phStream_Configure(void* stream, const uint32_t* configuration, uint32_t mode) {
    auto* bytes = static_cast<uint8_t*>(stream);
    if (bytes[0x98] & 1) return static_cast<int32_t>(0x8000ffffu);
    auto* first = rage::load_ptr32<uint8_t>(stream, 4);
    if (first != bytes + 4 && first != rage::load_ptr32<uint8_t>(stream, 0x0c))
        return static_cast<int32_t>(0x8000ffffu);
    auto* output = reinterpret_cast<uint32_t*>(bytes + 0x20);
    // Retail's forward word loop is observable when the records overlap.
    for (unsigned i = 0; i < 14; ++i) output[i] = configuration[i];
    bytes[0x99] = static_cast<uint8_t>(mode);
    return static_cast<phStreamConfigurationOps*>(stream)->SetInterval(g_phStreamInitialInterval);
}

// @ 0x82466A50
int32_t phStream_ConfigurePrimary(void* owner, const uint32_t* configuration, uint32_t mode) {
    auto* bytes = static_cast<uint8_t*>(owner);
    const int32_t result = phStream_Configure(bytes + 0x10, configuration, mode);
    if (result >= 0) {
        *reinterpret_cast<uint16_t*>(bytes + 0x68) = 1;
        *reinterpret_cast<uint16_t*>(bytes + 0x6a) = 1;
    }
    return result;
}

extern "C" const uint32_t g_phStreamFormatWidths[3]; // @ 0x82005C78

// @ 0x824668D8
int32_t phStream_GetRecordField(void* owner, uint32_t* output) {
    auto* stream = reinterpret_cast<phStreamConfigurationOps*>(static_cast<uint8_t*>(owner) + 0x10);
    rage::ptr32<uint8_t> record;
    const int32_t result = stream->GetRecord(&record);
    if (result >= 0)
        *output = *reinterpret_cast<uint32_t*>(record.get() + 0x10);
    return result;
}

// @ 0x82468AA0
int32_t phStream_ConfigurePacked(void* owner, const uint32_t* configuration, uint32_t mode) {
    auto* bytes = static_cast<uint8_t*>(owner);
    const int32_t result = phStream_Configure(bytes + 0x10, configuration, mode);
    if (result >= 0) {
        const uint32_t width = g_phStreamFormatWidths[bytes[0xc0]];
        const uint32_t channels = bytes[0xc1];
        *reinterpret_cast<uint16_t*>(bytes + 0x6a) = 1;
        *reinterpret_cast<uint16_t*>(bytes + 0x68) = static_cast<uint16_t>(width * channels);
    }
    return result;
}
