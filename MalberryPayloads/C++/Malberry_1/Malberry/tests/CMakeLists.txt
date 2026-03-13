cmake_minimum_required(VERSION 3.24)

# Enable CTest
enable_testing()

# Find doctest via vcpkg
find_package(doctest REQUIRED)

# Recursively gather all .cpp test files in tests/unit/
file(GLOB_RECURSE TEST_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/unit/*.cpp")

# Warn if no test files found
if(NOT TEST_SOURCES)
    message(WARNING "No test sources found in ${CMAKE_CURRENT_SOURCE_DIR}/unit/")
else()
    # Create the test executable
    add_executable(mylibrary_tests ${TEST_SOURCES})

    # Include your library headers
    target_include_directories(mylibrary_tests
            PRIVATE
            ${CMAKE_CURRENT_SOURCE_DIR}/../include
    )

    # Link your library and doctest
    target_link_libraries(mylibrary_tests
            PRIVATE
            mylibrary          # Your main library
            doctest::doctest   # doctest framework
    )

    # Optional: MinGW or special flags can go here
    # if(MINGW)
    #     target_compile_definitions(mylibrary_tests PRIVATE FMT_HEADER_ONLY=1)
    # endif()

    # Register the test with CTest
    add_test(NAME mylibrary_tests COMMAND mylibrary_tests)
endif()
