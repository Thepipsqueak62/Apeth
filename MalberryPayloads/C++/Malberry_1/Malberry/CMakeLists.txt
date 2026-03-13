cmake_minimum_required(VERSION 3.24)

# Project-specific vcpkg
if(EXISTS "${CMAKE_SOURCE_DIR}/CMakeUserConfig.cmake")
    include("${CMAKE_SOURCE_DIR}/CMakeUserConfig.cmake")
endif()

if(DEFINED VCPKG_ROOT)
    set(CMAKE_TOOLCHAIN_FILE "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE FILEPATH "")
else()
    message(FATAL_ERROR "VCPKG_ROOT not set. Copy CMakeUserConfig.cmake.example to CMakeUserConfig.cmake and set your path.")
endif()

project(Malberry VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ----------------------------
# Find libraries
# ----------------------------
find_package(fmt REQUIRED)

# ----------------------------
# Add library
# ----------------------------
# Automatically get all .cpp files in lib/
file(GLOB LIB_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/lib/*.cpp")

add_library(mylibrary STATIC ${LIB_SOURCES})

target_include_directories(mylibrary
        PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_library(cppTemplate::mylibrary ALIAS mylibrary)

# ----------------------------
# Add executable
# ----------------------------
add_executable(Malberry  src/main.cpp)

# Link core libraries
target_link_libraries(Malberry
        PRIVATE
)

# Link Windows-only libraries
if(WIN32)
    target_link_libraries(Malberry  PRIVATE
            ws2_32
            gdiplus
            ole32
            uuid
    )
endif()

# Hide console window in Release builds only
if(WIN32 AND CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(Malberry  PROPERTIES WIN32_EXECUTABLE TRUE)
endif()

# ----------------------------
# Add tests if they exist
# ----------------------------
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests/CMakeLists.txt)
    add_subdirectory(tests)
endif()

# ----------------------------
# Add SharedDLLExample if it exists
# ----------------------------
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/SharedDLLExample/CMakeLists.txt)
    add_subdirectory(SharedDLLExample)
endif()

# ----------------------------
# Add examples
# ----------------------------
set(EXAMPLES_DIR "${CMAKE_CURRENT_SOURCE_DIR}/examples")
file(GLOB EXAMPLE_SUBDIRS LIST_DIRECTORIES true "${EXAMPLES_DIR}/*")

foreach(EX_DIR ${EXAMPLE_SUBDIRS})
    if(IS_DIRECTORY ${EX_DIR})
        file(GLOB EXAMPLE_FILES "${EX_DIR}/*.cpp")
        foreach(EX_FILE ${EXAMPLE_FILES})
            get_filename_component(EX_NAME ${EX_FILE} NAME_WE)
            add_executable(${EX_NAME} ${EX_FILE})
            target_include_directories(${EX_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
            target_link_libraries(${EX_NAME} PRIVATE mylibrary fmt::fmt-header-only)
        endforeach()
    endif()
endforeach()