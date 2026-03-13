#include "testmylibrary.h"
#include <iostream>

int add(int a, int b) {
    return a + b;
}

void sayHello() {
    std::cout << "Hello from the DLL!" << std::endl;
}