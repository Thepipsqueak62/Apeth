#include <doctest/doctest.h>
#include <mylibrary/mylibrary.h>
#include <iostream>  // Add this
#include <stdexcept>

TEST_CASE("Calculator operations") {
    mylibrary::Calculator calc;

    SUBCASE("Addition") {
        std::cout << "Testing addition..." << std::endl;
        double result1 = calc.add(2.5, 3.5);
        std::cout << "2.5 + 3.5 = " << result1 << std::endl;
        CHECK(result1 == doctest::Approx(6.0));

        double result2 = calc.add(-1.0, 1.0);
        std::cout << "-1.0 + 1.0 = " << result2 << std::endl;
        CHECK(result2 == doctest::Approx(0.0));

        double result3 = calc.add(1.0, 1.0);
        std::cout << "1.0 + 1.0 = " << result3 << std::endl;
        CHECK(result3 == doctest::Approx(2.0));
    }

    SUBCASE("Subtraction") {
        std::cout << "Testing subtraction..." << std::endl;
        double result1 = calc.subtract(5.0, 3.0);
        std::cout << "5.0 - 3.0 = " << result1 << std::endl;
        CHECK(result1 == doctest::Approx(2.0));

        double result2 = calc.subtract(3.0, 5.0);
        std::cout << "3.0 - 5.0 = " << result2 << std::endl;
        CHECK(result2 == doctest::Approx(-2.0));
    }

    SUBCASE("Multiplication") {
        std::cout << "Testing multiplication..." << std::endl;
        double result1 = calc.multiply(3.0, 4.0);
        std::cout << "3.0 * 4.0 = " << result1 << std::endl;
        CHECK(result1 == doctest::Approx(12.0));

        double result2 = calc.multiply(0.0, 100.0);
        std::cout << "0.0 * 100.0 = " << result2 << std::endl;
        CHECK(result2 == doctest::Approx(0.0));
    }

    SUBCASE("Division") {
        std::cout << "Testing division..." << std::endl;
        double result1 = calc.divide(10.0, 2.0);
        std::cout << "10.0 / 2.0 = " << result1 << std::endl;
        CHECK(result1 == doctest::Approx(5.0));

        std::cout << "Testing division by zero..." << std::endl;
        CHECK_THROWS_AS(calc.divide(5.0, 0.0), std::invalid_argument);
        std::cout << "Division by zero correctly threw exception!" << std::endl;
    }
}