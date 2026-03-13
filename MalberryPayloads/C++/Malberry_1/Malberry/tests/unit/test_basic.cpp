#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include <doctest/doctest.h>
#include <mylibrary/mylibrary.h>
#include <iostream>  // Add this

TEST_CASE("Basic library functionality") {
    SUBCASE("Greeting function") {
        std::cout << "Testing greeting function..." << std::endl;
        auto result = mylibrary::greet("World");
        std::cout << "Greeting result: " << result << std::endl;
        CHECK(result == "Hello, World! Welcome to cppTemplate!");

        auto result2 = mylibrary::greet("Developer");
        std::cout << "Greeting result 2: " << result2 << std::endl;
        CHECK(result2 == "Hello, Developer! Welcome to cppTemplate!");
    }

    SUBCASE("Version info") {
        std::cout << "Testing version info..." << std::endl;
        auto version = mylibrary::Calculator::version();
        std::cout << "Version: " << version << std::endl;
        CHECK(version.find("cppTemplate") != std::string::npos);
        CHECK(version.find("v1.0.0") != std::string::npos);
    }
}