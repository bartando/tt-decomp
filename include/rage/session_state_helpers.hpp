#pragma once
#include <cstdint>

namespace rage {
struct snLinkedList;
struct snNotifier;
struct hsmStateBase;
namespace snSession_States {
void snSession_RegisterNotifier(snLinkedList* owner, snNotifier* notifier); // @ 0x823DD170
void snSession_SetTimeout(hsmStateBase* state, int32_t milliseconds); // @ 0x823ED4F8
}
}
