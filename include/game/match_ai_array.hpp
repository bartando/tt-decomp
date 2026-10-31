#pragma once
#include <cstdint>
#include "rage/ptr32.hpp"

// Only the two queried virtuals and the linked-list/index fields are known.
// Access state at its game offsets independently of the host vptr's width.
struct gdaiNode {
    virtual void Slot0();
    virtual void Slot1();
    virtual void Slot2();
    virtual void Slot3();
    virtual void Slot4();
    virtual void Slot5();
    virtual void Slot6();
    virtual void Slot7();
    virtual void Slot8();
    virtual void Slot9();
    virtual void Slot10();
    virtual void Slot11();
    virtual void Slot12();
    virtual void Slot13();
    virtual void Slot14();
    virtual void Slot15();
    virtual void Slot16();
    virtual void Slot17();
    virtual void Slot18();
    virtual const char* GetName();
    virtual uint32_t IsA(void* type);

    gdaiNode* Next() const { return rage::load_ptr32<gdaiNode>(this, 8); }
    void SetIndex(int32_t value) {
        *reinterpret_cast<int32_t*>(reinterpret_cast<uint8_t*>(this) + 0x1C) = value;
    }
};

struct gdaiNodeArray {
    rage::ptr32<rage::ptr32<gdaiNode>> m_data;
    uint16_t m_count;
    uint16_t m_capacity;
};
static_assert(sizeof(gdaiNodeArray) == 8, "AI pointer array layout");

void game_DB80(gdaiNodeArray* array, uint32_t capacity); // @ 0x821EDB80
