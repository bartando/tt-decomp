#pragma once

#include <cstdint>
#include "rage/fi_stream.hpp"

namespace rage {

bool fiDevice_Mount(const char* device, const char* path, uint32_t flags);
void* fiPackfile_Open(const char* path, uint32_t flags);

}
