#pragma once
#include <cstdint>
bool datBitBuffer_ReadS32(void* buffer, int32_t* out, int32_t bits); // @ 0x82260E18
bool datBitBuffer_ReadU32(void* buffer, uint32_t* out, int32_t bits); // @ 0x82238DF8
bool datBitBuffer_ReadU64(void* buffer, uint64_t* out); // @ 0x822609F0
int snBitStream_ReadString(void* buffer, void* destination, int count); // @ 0x82260AF0
int datBitBuffer_ReadShortString(void* buffer, char* destination); // @ 0x82260A70
uint32_t netStream_WriteString(void* buffer, const char* source, uint32_t count); // @ 0x82260738
uint32_t datBitBuffer_WriteShortString(void* buffer, const char* source); // @ 0x82260688
