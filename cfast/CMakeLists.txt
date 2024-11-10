cmake_minimum_required(VERSION 3.14)

project(fastupload C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

add_subdirectory(lib/cintelhex)

add_executable(fastupload)
target_sources(fastupload
        PUBLIC
        src/main.c
        )

add_compile_options(-fsanitize=address)

target_link_libraries(fastupload cintelhex)
