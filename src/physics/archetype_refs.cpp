#include "archetype_refs.hpp"
#include "rage/ptr32.hpp"

extern "C" uint8_t g_phInstrumentEnabled; // @ 0x826064E1

namespace {
// Borrowed interface: slot 0 takes scalar-delete flags, slot 3 resets an
// archetype that reached zero references but remains allocated.
struct PhysicsReferenceOps {
    virtual void Destroy(uint32_t flags) = 0;
    virtual void ReservedSlot1() = 0;
    virtual void ReservedSlot2() = 0;
    virtual void OnZeroReferences() = 0;
};
}

// @ 0x822C9D98
extern "C" uint32_t util_9D98(void* archetype, int deleteWhenUnused) {
    if (!g_phInstrumentEnabled) return 1;
    auto* bytes = static_cast<uint8_t*>(archetype);
    auto* count = reinterpret_cast<uint16_t*>(bytes + 0x1a);
    *count = static_cast<uint16_t>(*count - 1);
    if (*count != 0) return *count;
    auto* ops = static_cast<PhysicsReferenceOps*>(archetype);
    if ((deleteWhenUnused & 0xff) != 0)
        ops->Destroy(1);
    else
        ops->OnZeroReferences();
    return 0;
}

// @ 0x8228CEE0
uint32_t ph_CEE0(void* bound, int deleteWhenUnused) {
    if (!g_phInstrumentEnabled) return 1;
    auto* bytes = static_cast<uint8_t*>(bound);
    auto* count = reinterpret_cast<uint16_t*>(bytes + 0x60);
    *count = static_cast<uint16_t>(*count - 1);
    if (*count != 0) return *count;
    if ((deleteWhenUnused & 0xff) != 0)
        static_cast<PhysicsReferenceOps*>(bound)->Destroy(1);
    return 0;
}

// @ 0x822C9E50
void ph_9E50(void* archetype, void* newBound) {
    if (newBound && g_phInstrumentEnabled) {
        auto* count = reinterpret_cast<uint16_t*>(static_cast<uint8_t*>(newBound) + 0x60);
        *count = static_cast<uint16_t>(*count + 1);
    }
    if (void* existing = rage::load_ptr32<void>(archetype, 0x0c))
        ph_CEE0(existing, 1);
    auto* bytes = static_cast<uint8_t*>(archetype);
    *reinterpret_cast<rage::ptr32<void>*>(bytes + 0x0c) = newBound;
}
