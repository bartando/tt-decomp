#pragma once

void* snSession_D418_w(void* from, void* to); // @ 0x823ED418 — strict common parent
void snSession_AssociateConnections(void* context, void* from, void* to); // @ 0x823ED988 — exit states
void snSession_ProcessPendingConnections(void* context, void* unused, void* target); // @ 0x823EDA90 — enter and update states

namespace rage {
struct snSessionData;
struct snListNode;
namespace snSession_States {
void snSession_InsertConnectionNode(snSessionData* context, snListNode* node); // @ 0x823EDD10
void snSession_RemoveConnectionNode(snSessionData* context, snListNode* node); // @ 0x823EDDB8
}
}
