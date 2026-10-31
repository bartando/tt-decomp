#pragma once
#include <cstdint>

struct fiTokenizerView;

void fiTokenizer_PushBackToken(void* tokenizer, const char* token, int32_t length); // @ 0x822E5310
bool fiTokenizer_CheckToken(fiTokenizerView* tokenizer, const char* expected, bool consume); // @ 0x822E5908
bool fiTokenizer_CheckTokenInsensitive(void* tokenizer, const char* expected, bool consume); // @ 0x822E59C8
