cmake_minimum_required(VERSION 3.21)
# Run on the online Mac, then carry this directory to the offline Windows PC.
if(NOT TT_WIN32_DEPS)
    set(TT_WIN32_DEPS "${CMAKE_CURRENT_LIST_DIR}/../build/win32-deps")
endif()
file(MAKE_DIRECTORY "${TT_WIN32_DEPS}/downloads")
function(download_and_extract filename url sha256 directory)
    set(archive "${TT_WIN32_DEPS}/downloads/${filename}")
    file(DOWNLOAD "${url}" "${archive}"
        EXPECTED_HASH "SHA256=${sha256}" TLS_VERIFY ON SHOW_PROGRESS)
    if(NOT EXISTS "${TT_WIN32_DEPS}/${directory}")
        file(ARCHIVE_EXTRACT INPUT "${archive}" DESTINATION "${TT_WIN32_DEPS}")
    endif()
endfunction()
download_and_extract(SDL2-devel-2.32.10-mingw.tar.gz
    https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-devel-2.32.10-mingw.tar.gz
    83a5d74012311edc3c0d40ea6faecbe57ad692aa033fa5dc273cc937e3938ff2 SDL2-2.32.10)
download_and_extract(glew-2.2.0.tgz
    https://github.com/nigels-com/glew/releases/download/glew-2.2.0/glew-2.2.0.tgz
    d4fc82893cfb00109578d0a1a2337fb8ca335b3ceccf97b97e5cc7f08e4353e1 glew-2.2.0)
message(STATUS "32-bit Windows dependencies: ${TT_WIN32_DEPS}")
