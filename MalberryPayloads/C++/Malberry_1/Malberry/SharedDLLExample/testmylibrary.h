#pragma once

#ifdef _WIN32
    #ifdef MYLIBRARY_EXPORTS
        #define MYLIB_API __declspec(dllexport)
    #else
        #define MYLIB_API __declspec(dllimport)
    #endif
#endif

MYLIB_API int add(int a, int b);
MYLIB_API void sayHello();