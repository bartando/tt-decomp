#include "audio/xact_wave_acquire.hpp"
#include "../../game/misc/pong_misc.hpp"
#include "xam/kernel.h"
#include <cstring>

int32_t msgMsgSink_84C0_gen(void* context); // @ 0x824484C0
void msgSlot_SetFloat(void* variable, float value, uint32_t flags); // @ 0x8244B158

namespace {
struct WaveBank {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual uint8_t* GetDescriptor(uint32_t index) = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual void Unknown06() = 0;
    virtual void Unknown07() = 0;
    virtual void Unknown08() = 0;
    virtual void Unknown09() = 0;
    virtual void Unknown10() = 0;
    virtual const uint8_t* GetHeader(uint32_t probe) = 0;
};
uint16_t waveCount(WaveBank* bank, uint32_t probe) {
    uint16_t count;
    std::memcpy(&count, bank->GetHeader(probe) + 0x0B, sizeof(count));
    return count;
}
RTL_CRITICAL_SECTION* criticalSection(void* cue) {
    auto* context = rage::load_ptr32<uint8_t>(cue, 0x38);
    return reinterpret_cast<RTL_CRITICAL_SECTION*>(context + 0x90);
}
constexpr uint32_t kInvalidVariable = 0x8AC7000Au;
}

// @ 0x82448C60 | size: 0x6C
void* xactBank_GetWaveRecord(void* owner, uint32_t index) {
    auto* bank = rage::load_ptr32<WaveBank>(owner, 0x7C);
    const uint16_t count = waveCount(bank, index);
    const uint32_t slot = static_cast<uint16_t>(index);
    if (slot >= count) return nullptr;
    auto* records = rage::load_ptr32<uint8_t>(bank, 0x7C);
    return records + slot * 0xFC;
}

// @ 0x82448D10 | size: 0x80
void* msgMsgSink_8D10_g(void* owner, uint32_t index) {
    auto* bank = rage::load_ptr32<WaveBank>(owner, 0x7C);
    if (!bank || static_cast<uint16_t>(index) >= waveCount(bank, index)) return nullptr;
    return bank->GetDescriptor(index);
}

// @ 0x82456D70 | size: 0xC8
int32_t xactCue_AcquireWave(void* cue) {
    auto* cs = criticalSection(cue);
    RtlEnterCriticalSection(cs);
    auto* link = rage::load_ptr32<uint8_t>(cue, 0x120);
    auto* descriptor = rage::load_ptr32<uint8_t>(link, 8);
    const uint32_t index = *reinterpret_cast<uint16_t*>(descriptor + 6);
    void* context = rage::load_ptr32<void>(cue, 0x38);
    auto* bank = rage::load_ptr32<WaveBank>(context, 0x7C);
    auto* out = reinterpret_cast<rage::ptr32<void>*>(static_cast<uint8_t*>(cue) + 0x160);
    int32_t status = 0;
    if (!bank || (bank->GetDescriptor(index)[0] & 4)) {
        status = msgMsgSink_EC28_g(cue, index, out, 0);
    } else {
        void* wave = xactBank_GetWaveRecord(rage::load_ptr32<void>(cue, 0x38), index);
        *out = wave;
        if (!wave) status = static_cast<int32_t>(kInvalidVariable);
    }
    RtlLeaveCriticalSection(cs);
    return status;
}

// @ 0x8244F268 | size: 0xC8
uint32_t msgMsgSink::SetPropertyLocked(uint32_t key, float value) {
    auto* cs = criticalSection(this);
    RtlEnterCriticalSection(cs);
    int32_t status = msgMsgSink_84C0_gen(rage::load_ptr32<void>(this, 0x38));
    rage::ptr32<void> variable;
    if (status >= 0) {
        status = msgMsgSink_EC28_g(this, key, &variable, 0);
        if (status >= 0) {
            auto* bytes = static_cast<uint8_t*>(variable.get());
            auto* descriptor = rage::load_ptr32<uint8_t>(bytes, 0x10);
            const uint8_t flags = descriptor[0];
            if (!(flags & 1) || (flags & 2)) status = static_cast<int32_t>(kInvalidVariable);
            else if (value != *reinterpret_cast<float*>(bytes + 0x14))
                msgSlot_SetFloat(bytes, value, 0);
        }
    }
    RtlLeaveCriticalSection(cs);
    return static_cast<uint32_t>(status);
}

// @ 0x8244F330 | size: 0xC8
uint32_t msgMsgSink::GetPropertyLocked(uint32_t key, float* outValue) {
    auto* cs = criticalSection(this);
    RtlEnterCriticalSection(cs);
    int32_t status = msgMsgSink_84C0_gen(rage::load_ptr32<void>(this, 0x38));
    const uint16_t index = static_cast<uint16_t>(key);
    if (status >= 0 && index != 1 && index != 2) {
        rage::ptr32<void> variable;
        status = msgMsgSink_EC28_g(this, key, &variable, 0);
        if (status >= 0) {
            auto* bytes = static_cast<uint8_t*>(variable.get());
            auto* descriptor = rage::load_ptr32<uint8_t>(bytes, 0x10);
            if (descriptor[0] & 1) *outValue = *reinterpret_cast<float*>(bytes + 0x14);
            else status = static_cast<int32_t>(kInvalidVariable);
        }
    }
    RtlLeaveCriticalSection(cs);
    return static_cast<uint32_t>(status);
}
