#include "mylibrary/mylibrary.h"
#include <stdexcept>

namespace mylibrary {

    double Calculator::add(double a, double b) const {
        return a + b;
    }

    double Calculator::subtract(double a, double b) const {
        return a - b;
    }

    double Calculator::multiply(double a, double b) const {
        return a * b;
    }

    double Calculator::divide(double a, double b) const {
        if (b == 0.0) {
            throw std::invalid_argument("Division by zero");
        }
        return a / b;
    }

    std::string Calculator::version() {
        return "cppTemplate v1.0.0";
    }

    std::string greet(const std::string& name) {
        return "Hello, " + name + "! Welcome to cppTemplate!";
    }

} // namespace mylibrary