// Checked cast used when resolving a camera node's side data.
#include <cstdint>

extern "C" uintptr_t g_cameraNodeType; // @ 0x825C7520

namespace {
// The common node prefix has twenty operations before its type predicate.
// Keep them virtual so dispatch follows the object's native vtable as well.
struct CameraTypeNode {
    virtual void Destroy();
    virtual void ScalarDestroy();
    virtual void Reserved02();
    virtual void Reserved03();
    virtual void Reserved04();
    virtual void Reserved05();
    virtual void Reserved06();
    virtual void Reserved07();
    virtual void Reserved08();
    virtual void Reserved09();
    virtual void Reserved10();
    virtual void Reserved11();
    virtual void Reserved12();
    virtual void Reserved13();
    virtual void Reserved14();
    virtual void Reserved15();
    virtual void Reserved16();
    virtual void Reserved17();
    virtual void Reserved18();
    virtual void Reserved19();
    virtual uint32_t IsType(uintptr_t type);
};
}

// @ 0x82101700 | size: 0x54
void* game_1700(void* object) {
    const uint32_t matches = static_cast<CameraTypeNode*>(object)->IsType(g_cameraNodeType);
    return static_cast<uint8_t>(matches) != 0 ? object : nullptr;
}
