#pragma once

#include <string>

namespace mylibrary {

    class Calculator {
    public:
        double add(double a, double b) const;
        double subtract(double a, double b) const;
        double multiply(double a, double b) const;
        double divide(double a, double b) const;

        static std::string version();
    };

    std::string greet(const std::string& name);

} // namespace mylibrary