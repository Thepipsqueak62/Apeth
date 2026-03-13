cmake_minimum_required(VERSION 3.24)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_library(testmylibrary SHARED testmylibrary.cpp)
target_compile_definitions(testmylibrary PRIVATE MYLIBRARY_EXPORTS)
target_include_directories(testmylibrary PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(testmylibrary PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/RelWithDebInfo/Shareddllexample"
)

add_executable(SharedDLLExample testmain.cpp)
target_link_libraries(SharedDLLExample PRIVATE testmylibrary
)
set_target_properties(SharedDLLExample PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/RelWithDebInfo/Shareddllexample"
)