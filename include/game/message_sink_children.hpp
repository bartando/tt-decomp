#pragma once
#include <cstdint>

uint32_t msgMsgSink_8E60_sp(void* sink); // @ 0x82458E60
int32_t msgMsgSink_8E88_sp(void* sink, uint32_t paused); // @ 0x82458E88
uint32_t msgChild_HasPendingTarget(void* child); // @ 0x82459D58
int32_t msgChild_SetPaused(void* child, uint32_t paused); // @ 0x82459D70
int32_t msgSink_HasPendingChildren(void* sink); // @ 0x82453F68
void msgMsgSink_4550_g(void* sink); // @ 0x82454550
