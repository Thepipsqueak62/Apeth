# cppProjectTemplate
A modern C++ project template following best practices, designed to be a solid foundation for any application or tool.

## Setup
This project uses vcpkg for dependency management. Before building, you need to configure your local vcpkg path.

1. Copy or Rename `CMakeUserConfig.cmake.example` to `CMakeUserConfig.cmake`
2. Open `CMakeUserConfig.cmake` and set your vcpkg installation path:
```cmake
set(VCPKG_ROOT "C:/vcpkg")
```
3. Open the project in CLion or generate a solution with CMake GUI

> `CMakeUserConfig.cmake` is gitignored and will never be committed — each developer sets their own path locally.

## Project Structure
```
cppProjectTemplate/
├── src/                  # Main executable source code
├── lib/                  # Core reusable library code
├── include/              # Public header files
├── examples/             # Usage examples
├── tests/                # Unit tests
└── SharedDLLExample/     # Reference example for building shared libraries (DLLs)
```

## Static vs Shared Libraries
This template uses a **static library** by default (`mylibrary`).

**Static (.lib)** — the library code is compiled directly into the executable. Simple to distribute, just ship the `.exe` and nothing else.

**Shared (.dll)** — the library code lives in a separate `.dll` file that the executable loads at runtime. The `.exe` and `.dll` must always be distributed together.

Use static when you have a single executable and want simplicity. Use shared when multiple executables need to share the same library, or when you want a plugin or modding system.

The `SharedDLLExample/` folder demonstrates a working shared library setup with the correct CMake configuration and `__declspec(dllexport/dllimport)` pattern required on Windows.