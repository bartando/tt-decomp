#pragma once
#include <cstdint>

namespace rage {
float xactGroup_GetVolume(void* owner, uint32_t index); // @ 0x82448AB8
float xactSink_GetCombinedVolume(void* sink); // @ 0x82454AC0
void xactSink_SetTargetVolume(void* sink, float volume); // @ 0x82458D80
void xactChild_UpdateVolume(void* child); // @ 0x82459C10
void xactSink_SetVolume(void* sink, float volume); // @ 0x82454020
}
void msgMsgSink_3DC8_g(void* sink); // @ 0x82453DC8
