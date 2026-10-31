#pragma once

extern "C" {
void* swfCopyString(const char* text); // @ 0x823FABC0
void* swfReleaseText(void* text, int freeStorage); // @ 0x823F8A38
const char* swfInternText(const char* text); // @ 0x823F9FB0
}
